"""Pull support for Prometheus app repositories."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from prometheus.context import detect_context


@dataclass
class PullSummary:
    """Summary returned by pull execution."""

    app_path: Path
    app_before: str
    app_after: str
    core_before: str | None
    core_after: str | None


def pull_app(start_path: str | Path | None = None) -> PullSummary:
    """Pull the app repo and update its prometheus-core submodule."""
    context = detect_context(start_path)
    if not context.is_app:
        raise RuntimeError("The pull workflow only works inside an app repository.")

    app_before = _run_git(["rev-parse", "HEAD"], cwd=context.root_path, check=False) or "unknown"
    core_before = None
    if context.core_path and (context.core_path / ".git").exists():
        core_before = (
            _run_git(["rev-parse", "HEAD"], cwd=context.core_path, check=False) or "unknown"
        )

    _run_git(["pull", "--ff-only"], cwd=context.root_path)

    # The core submodule is registered in .gitmodules of the repository that
    # added it (the app-instructions repo, reached here via the
    # .github/prometheus symlink) - NOT the app code repo itself. Running
    # `submodule update` with cwd=root_path silently no-ops because root_path
    # has no .gitmodules of its own.
    if context.core_path:
        _run_git(["submodule", "update", "--remote"], cwd=context.core_path.parent)

    app_after = _run_git(["rev-parse", "HEAD"], cwd=context.root_path, check=False) or "unknown"
    core_after = None
    if context.core_path and (context.core_path / ".git").exists():
        core_after = (
            _run_git(["rev-parse", "HEAD"], cwd=context.core_path, check=False) or "unknown"
        )

    return PullSummary(
        app_path=context.root_path,
        app_before=app_before,
        app_after=app_after,
        core_before=core_before,
        core_after=core_after,
    )


def _run_git(args, cwd, check=True):
    result = subprocess.run(
        ["git", *args],
        cwd=Path(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise RuntimeError(message)
    return result.stdout.strip() or result.stderr.strip()
