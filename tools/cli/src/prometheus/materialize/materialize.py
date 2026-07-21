"""Materialize domain/core/code content into native VS Code discovery folders.

Prometheus keeps the app-specific content (``domain/``) and the shared core
content (``core/core/`` and ``core/code_instructions/``, the latter reached
via a git submodule) as separate sibling source trees. VS Code's native
Copilot customization surfaces (``.github/instructions``, ``.github/prompts``,
``.github/agents``, ``.github/skills``) only look in one location each, and a
plain symlink or git submodule cannot merge two sibling repos' folders into
that single native location by itself.

This module copies the markdown content from those source trees into the
app repository's ``.github/instructions|prompts|agents|skills`` folders,
renaming each file with a ``domain.`` or ``core.`` prefix (based on its
source) so files from different origins never collide, and ensuring each
materialized file carries the minimum frontmatter VS Code expects.

``core/code_instructions`` is organized differently: it has no content
folders of its own, only per-stack layer folders (e.g. ``backend/``,
``frontend/``), each containing the usual
``instructions|prompts|agents|skills`` structure. Files found there are
materialized using the layer folder's name as the naming pattern instead of
a fixed prefix - e.g. ``backend/instructions/foo.md`` becomes
``.github/instructions/backend.foo.instructions.md`` - so files from
different stack layers never collide and their origin stays obvious.

Each source tree can also contain a ``helpers/`` folder (scripts and other
non-instructional utility files). Unlike the other kinds, helper files are
copied verbatim into ``.github/helpers`` - no frontmatter handling, no
forced ``.md`` extension - just renamed with the same origin prefix (e.g.
``domain.``, ``core.``, ``backend.``) so files from different sources never
collide.

Each materialized destination folder is fully cleared and rebuilt on every
run, so the app repo's ``.github/`` content always mirrors the current
source trees exactly - never accumulating stale files left over from
renamed/removed/relocated sources.

``ensure_gitignore_entries``/``commit_gitignore_if_pending`` must be called
before ``materialize()`` ever writes a file. This guarantees the ignore
rules that exclude the materialized folders are already committed to the
app repo's git history strictly before those folders can contain any
content, so no commit (manual or automated) can ever bundle the .gitignore
change together with materialized instructions in the same commit.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# Maps a source folder (relative to the app-instructions repo root) to the
# filename prefix applied when materializing its content.
_SOURCE_PREFIXES: dict[str, str] = {
    "domain": "domain.",
    "core/core": "core.",
}

# core/code_instructions has no content folders of its own - it only has
# per-stack layer folders (e.g. backend/, frontend/), each containing the
# usual instructions|prompts|agents|skills(|helpers) structure. Materialized
# as <layer>.<filename>.<kind>.md instead of a fixed prefix, so files from
# different layers never collide.
_LAYERED_SOURCE = "core/code_instructions"

# Markdown content subfolders, frontmatter-processed and copied into the
# matching .github/<kind> destination.
_MARKDOWN_KINDS = ("instructions", "prompts", "agents", "skills")

# Non-markdown utility content (scripts, etc.) copied verbatim - no
# frontmatter handling, original filename/extension preserved aside from the
# origin prefix.
_HELPERS_KIND = "helpers"

# All content subfolders, including helpers, used for .github/ dest dirs and
# .gitignore entries.
_CONTENT_KINDS = _MARKDOWN_KINDS + (_HELPERS_KIND,)

_FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)

# .gitignore entries excluding the materialized folders above from the app
# code repo - they are local copies rebuilt from the app-instructions repo
# on every init/pull/update, never the app repo's own content.
GITIGNORE_ENTRIES = tuple(f".github/{kind}/" for kind in _CONTENT_KINDS)


@dataclass
class MaterializeResult:
    """Result of a materialization pass."""

    written: list[Path] = field(default_factory=list)

    @property
    def written_count(self) -> int:
        """Number of files written."""
        return len(self.written)


def materialize(instructions_path: Path, app_path: Path) -> MaterializeResult:
    """Copy domain/core/code content folders into native .github/ locations.

    Each ``.github/<kind>`` destination folder is fully cleared before being
    rebuilt from the current source trees, so the app repo's ``.github/``
    content is always a compact, exact mirror of ``domain/`` and ``core/`` -
    files from sources that were renamed, removed, or relocated never linger.

    Args:
        instructions_path: Root of the app-instructions repo (contains the
            ``domain/`` folder and the ``core/`` submodule).
        app_path: Root of the app code repo (contains/will contain
            ``.github/``).

    Returns:
        A `MaterializeResult` listing every file written.
    """
    result = MaterializeResult()

    for kind in _CONTENT_KINDS:
        dest_dir = app_path / ".github" / kind
        if dest_dir.exists():
            shutil.rmtree(dest_dir)

    for source_rel, prefix in _SOURCE_PREFIXES.items():
        source_root = instructions_path / source_rel
        if not source_root.is_dir():
            continue

        for kind in _MARKDOWN_KINDS:
            source_dir = source_root / kind
            if not source_dir.is_dir():
                continue

            dest_dir = app_path / ".github" / kind
            for source_file in sorted(source_dir.glob("*.md")):
                dest_file = dest_dir / f"{prefix}{source_file.name}"
                content = _ensure_frontmatter(source_file, kind)

                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_file.write_text(content, encoding="utf-8")
                result.written.append(dest_file)

        _materialize_helpers(source_root / _HELPERS_KIND, app_path, prefix, result)

    # Also materialize helpers from core/ root (at the submodule root level)
    _materialize_helpers(instructions_path / "core" / _HELPERS_KIND, app_path, "core.", result)

    _materialize_layered_source(instructions_path / _LAYERED_SOURCE, app_path, result)

    return result


def _materialize_layered_source(
    source_root: Path, app_path: Path, result: MaterializeResult
) -> None:
    """Materialize a per-stack-layer source tree (e.g. core/code_instructions).

    Unlike the flat sources handled in `materialize()`, this source has no
    content folders of its own - only per-stack layer folders (e.g.
    ``backend/``, ``frontend/``), each containing the usual
    ``instructions|prompts|agents|skills(|helpers)`` structure. Materialized
    files are named ``<layer>.<filename>.<kind>.md`` instead of using a
    fixed prefix, so files from different layers never collide.

    Args:
        source_root: Root of the layered source tree (e.g.
            ``{instructions_path}/core/code_instructions``).
        app_path: Root of the app code repo.
        result: `MaterializeResult` to append written files to.
    """
    if not source_root.is_dir():
        return

    for layer_dir in sorted(p for p in source_root.iterdir() if p.is_dir()):
        layer = layer_dir.name
        prefix = f"{layer}."

        for kind in _MARKDOWN_KINDS:
            source_dir = layer_dir / kind
            if not source_dir.is_dir():
                continue

            dest_dir = app_path / ".github" / kind
            for source_file in sorted(source_dir.glob("*.md")):
                dest_file = dest_dir / f"{prefix}{source_file.stem}.{kind}.md"
                content = _ensure_frontmatter(source_file, kind)

                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_file.write_text(content, encoding="utf-8")
                result.written.append(dest_file)

        _materialize_helpers(layer_dir / _HELPERS_KIND, app_path, prefix, result)


def _materialize_helpers(
    source_dir: Path, app_path: Path, prefix: str, result: MaterializeResult
) -> None:
    """Copy helper files (scripts, other utilities) verbatim into .github/helpers.

    Unlike the markdown kinds, helper files are not required to be markdown
    and receive no frontmatter processing - they are copied byte-for-byte,
    only renamed with the given origin prefix so files from different
    sources never collide.

    Args:
        source_dir: The source ``helpers`` folder (may not exist).
        app_path: Root of the app code repo.
        prefix: Origin prefix to apply to each filename (e.g. ``domain.``,
            ``core.``, ``backend.``).
        result: `MaterializeResult` to append written files to.
    """
    if not source_dir.is_dir():
        return

    dest_dir = app_path / ".github" / _HELPERS_KIND
    for source_file in sorted(p for p in source_dir.iterdir() if p.is_file()):
        dest_file = dest_dir / f"{prefix}{source_file.name}"

        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, dest_file)
        result.written.append(dest_file)


def _ensure_frontmatter(source_file: Path, kind: str) -> str:
    """Return source file content with the minimum required frontmatter.

    Every materialized file requires at least a ``description``.
    Instructions additionally require ``applyTo``; agents and skills
    additionally require ``name``. Missing fields are filled in with
    reasonable defaults derived from the filename rather than rejecting or
    dropping the file.

    Args:
        source_file: Path to the source markdown file.
        kind: Content kind ("instructions", "prompts", "agents", "skills").

    Returns:
        File content with valid frontmatter guaranteed at the top.
    """
    raw = source_file.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(raw)

    frontmatter: dict = {}
    body = raw
    if match:
        try:
            parsed = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            parsed = None
        if isinstance(parsed, dict):
            frontmatter = parsed
        body = raw[match.end():]

    default_label = source_file.stem.replace("_", " ").replace("-", " ").strip()
    frontmatter.setdefault("description", f"{default_label} ({kind})")

    if kind == "instructions":
        frontmatter.setdefault("applyTo", "**")
    elif kind in ("agents", "skills"):
        frontmatter.setdefault("name", source_file.stem)

    frontmatter_text = yaml.safe_dump(frontmatter, sort_keys=False).strip()
    return f"---\n{frontmatter_text}\n---\n\n{body.strip()}\n"


def ensure_gitignore_entries(app_path: Path, entries: tuple[str, ...] = GITIGNORE_ENTRIES) -> bool:
    """Ensure the app repo's .gitignore contains the given entries.

    Args:
        app_path: Root of the app code repo.
        entries: Entries to ensure are present (defaults to `GITIGNORE_ENTRIES`).

    Returns:
        True if the .gitignore file was created or modified, False if all
        entries were already present.
    """
    gitignore_path = app_path / ".gitignore"

    if gitignore_path.exists():
        content = gitignore_path.read_text(encoding="utf-8")
        missing = [entry for entry in entries if entry not in content]
        if not missing:
            return False
        with open(gitignore_path, "a", encoding="utf-8") as handle:
            if content and not content.endswith("\n"):
                handle.write("\n")
            handle.write("\n".join(missing) + "\n")
        return True

    gitignore_path.write_text("\n".join(entries) + "\n", encoding="utf-8")
    return True


def commit_gitignore_if_pending(app_path: Path) -> bool:
    """Commit (and best-effort push) any uncommitted .gitignore change.

    Must be called before `materialize()` ever writes a file, so the ignore
    rules excluding the materialized folders are guaranteed to already be
    recorded in the app repo's git history strictly before those folders
    can contain any content - this way no commit (manual or automated) can
    ever bundle the .gitignore change together with materialized
    instructions in the same commit.

    Args:
        app_path: Root of the app code repo.

    Returns:
        True if a commit was made, False otherwise (not a git repo, or
        nothing pending).
    """
    if not (app_path / ".git").exists():
        return False

    status = _run_git(["status", "--porcelain", "--", ".gitignore"], app_path, check=False)
    if not status.strip():
        return False

    _ensure_git_identity(app_path)
    _run_git(["add", "--", ".gitignore"], app_path, check=False)
    _run_git(
        ["commit", "-m", "Ignore materialized Copilot instructions folders"],
        app_path,
        check=False,
    )

    branch = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], app_path, check=False)
    remotes = (_run_git(["remote"], app_path, check=False) or "").split()
    if branch and branch != "HEAD" and "origin" in remotes:
        _run_git(["push", "origin", branch], app_path, check=False)

    return True


def _ensure_git_identity(repo_path: Path) -> None:
    """Ensure git user.name/user.email are set so a commit can succeed."""
    name = _run_git(["config", "user.name"], repo_path, check=False)
    if not name.strip():
        _run_git(["config", "user.name", "Prometheus"], repo_path, check=False)

    email = _run_git(["config", "user.email"], repo_path, check=False)
    if not email.strip():
        _run_git(["config", "user.email", "prometheus@localhost"], repo_path, check=False)


def _run_git(args: list[str], cwd: Path, check: bool = True) -> str:
    """Run a git command, returning stdout (or stderr on failure).

    Args:
        args: Git command arguments.
        cwd: Working directory.
        check: If True, raise RuntimeError on non-zero return code.
    """
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )

    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise RuntimeError(message)

    return result.stdout.strip() or result.stderr.strip()
