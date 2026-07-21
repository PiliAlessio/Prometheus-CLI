"""Update support for Prometheus app repositories."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from prometheus.context import detect_context


@dataclass
class UpdateSummary:
    """Summary returned by update execution."""

    app_path: Path
    app_before: str
    app_after: str
    core_before: str | None
    core_after: str | None


def update_app(start_path: str | Path | None = None) -> UpdateSummary:
    """Pull the app repo and update its prometheus-core submodule."""
    context = detect_context(start_path)
    if not context.is_app:
        raise RuntimeError("The update workflow only works inside an app repository.")

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
        instructions_root = context.core_path.parent
        # `submodule sync` refreshes the submodule's local remote URL from
        # .gitmodules. Without this, a stale cached URL (e.g. left over from
        # an older core_remote value) causes `--remote` to silently fetch
        # from the wrong place and appear "up to date" while missing commits.
        _run_git(["submodule", "sync", "--recursive"], cwd=instructions_root, check=False)
        # --force discards any dirty/untracked state in the submodule that
        # would otherwise block checking out the newly fetched commit.
        _run_git(
            ["submodule", "update", "--init", "--remote", "--force"],
            cwd=instructions_root,
        )
        _repair_core_sparse_checkout(context.core_path)

    app_after = _run_git(["rev-parse", "HEAD"], cwd=context.root_path, check=False) or "unknown"
    core_after = None
    if context.core_path and (context.core_path / ".git").exists():
        core_after = (
            _run_git(["rev-parse", "HEAD"], cwd=context.core_path, check=False) or "unknown"
        )

    return UpdateSummary(
        app_path=context.root_path,
        app_before=app_before,
        app_after=app_after,
        core_before=core_before,
        core_after=core_after,
    )


def _repair_core_sparse_checkout(core_path: Path) -> None:
    """Ensure the core submodule's sparse-checkout uses non-cone mode.

    Older versions of this CLI applied gitignore-style exclude patterns
    (e.g. "!/docs") via plain `sparse-checkout init`, which defaults to
    cone mode. Cone mode silently discards those patterns and collapses
    the checkout down to root-level files only, making most of the
    submodule disappear from the working tree even though HEAD is correct.
    Re-applying with --no-cone repairs any submodule stuck in that state.
    """
    if not (core_path / ".git").exists():
        return
    _run_git(["sparse-checkout", "init", "--no-cone"], cwd=core_path, check=False)
    _run_git(
        ["sparse-checkout", "set", "/*", "!/tools/cli", "!/docs"],
        cwd=core_path,
        check=False,
    )
    # The core submodule is entirely upstream-controlled/read-only, so any
    # untracked leftovers from the broken cone-mode state above are always
    # safe to discard.
    _run_git(["clean", "-ffd"], cwd=core_path, check=False)


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
