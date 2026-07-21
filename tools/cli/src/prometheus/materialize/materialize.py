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
"""

from __future__ import annotations

import re
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


@dataclass
class MaterializeResult:
    """Result of a materialization pass."""

    written: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)

    @property
    def written_count(self) -> int:
        """Number of files written or updated."""
        return len(self.written)


def materialize(instructions_path: Path, app_path: Path) -> MaterializeResult:
    """Copy domain/core/code content folders into native .github/ locations.

    Existing materialized files are only overwritten when their content
    would actually change; files are never deleted, so any stale
    materialized file from a source that no longer exists is left in place.

    Args:
        instructions_path: Root of the app-instructions repo (contains the
            ``domain/`` folder and the ``core/`` submodule).
        app_path: Root of the app code repo (contains/will contain
            ``.github/``).

    Returns:
        A `MaterializeResult` listing files written and files left unchanged.
    """
    result = MaterializeResult()

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

                if (
                    dest_file.exists()
                    and dest_file.read_text(encoding="utf-8") == content
                ):
                    result.skipped.append(dest_file)
                    continue

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
