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
renaming each file with a ``domain.``, ``core.`` or ``code.`` prefix (based on
its source) so files from different origins never collide, and ensuring each
materialized file carries the minimum frontmatter VS Code expects.

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
    "core/code_instructions": "code.",
}

# Content subfolders copied into the matching .github/<kind> destination.
_CONTENT_KINDS = ("instructions", "prompts", "agents", "skills")

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

        for kind in _CONTENT_KINDS:
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

    return result


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
