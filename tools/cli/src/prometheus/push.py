"""Push support for Prometheus app repositories."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from prometheus.config import Config
from prometheus.context import detect_context


@dataclass(frozen=True)
class ModifiedFile:
    """Details about a modified file reported by Git."""

    path: str
    status: str


@dataclass
class RepoPushState:
    """Push-related status for a git repository."""

    name: str
    path: Path
    branch: str
    modified_files: list[str] = field(default_factory=list)
    modified_details: list[ModifiedFile] = field(default_factory=list)
    ahead_count: int = 0
    pushed: bool = False
    skipped_reason: str | None = None


@dataclass
class PushSummary:
    """Summary returned by push execution."""

    app: RepoPushState
    core: RepoPushState | None = None

    @property
    def modified_repositories(self) -> dict[str, list[str]]:
        """Return modified files keyed by repository name."""
        repositories = {}
        for state in (self.app, self.core):
            if state and state.modified_files:
                repositories[state.name] = list(state.modified_files)
        return repositories


def detect_push_state(start_path: str | Path | None = None) -> PushSummary:
    """Detect app-instructions repository state before attempting a push."""
    context = detect_context(start_path)
    if not context.is_app:
        raise RuntimeError("The --push workflow only works inside an app repository.")

    # Load config to get app_name
    config = Config.from_file(context.config_path)
    if not config.app_name:
        raise RuntimeError(
            "app_name not found in .prometheus.yml. Unable to locate app-instructions repo."
        )

    # Determine instructions repo path: ~/.prometheus/{app_name}-instructions
    # Allow override via PROMETHEUS_INSTRUCTIONS_BASE environment variable (for testing)
    base_path = os.environ.get("PROMETHEUS_INSTRUCTIONS_BASE")
    if base_path:
        instructions_path = Path(base_path) / f"{config.app_name}-instructions"
    else:
        instructions_path = Path.home() / ".prometheus" / f"{config.app_name}-instructions"

    if not instructions_path.exists():
        raise RuntimeError(
            f"App-instructions repository not found at {instructions_path}. "
            f"Please run 'prometheus init' first."
        )

    # The instructions repo might have a core submodule at .github/prometheus-core
    instructions_state = _inspect_repo(instructions_path, "app-instructions")
    core_state = None
    core_path = instructions_path / ".github" / "prometheus-core"
    if core_path.exists() and (core_path / ".git").exists():
        core_state = _inspect_repo(core_path, "prometheus-core submodule")

    return PushSummary(app=instructions_state, core=core_state)


def push_changes(start_path: str | Path | None = None) -> PushSummary:
    """Push changes to app-instructions repository and its core submodule."""
    summary = detect_push_state(start_path)
    _push_repo(summary.app)
    if summary.core:
        _push_repo(summary.core)
    return summary


def _inspect_repo(path: Path, name: str) -> RepoPushState:
    branch = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=path)
    modified_details = _get_modified_files(path)
    ahead_count = _get_ahead_count(path)
    state = RepoPushState(name=name, path=path, branch=branch, ahead_count=ahead_count)
    state.modified_details = modified_details
    state.modified_files = [item.path for item in modified_details]
    return state


def _push_repo(state: RepoPushState) -> RepoPushState:
    if state.modified_files:
        # Add and commit modified files before pushing
        try:
            print(f"[DEBUG] Adding and committing {len(state.modified_files)} modified files in {state.name}...")
            _run_git(["add", "-A"], cwd=state.path)
            _run_git(
                ["commit", "-m", f"Update: Changes from {state.name} repository"],
                cwd=state.path,
            )
            state.modified_files = []  # Clear modified files list since we committed
            # Recalculate ahead_count after committing
            state.ahead_count = _get_ahead_count(state.path)
        except RuntimeError as e:
            state.skipped_reason = f"failed to commit changes: {e}"
            return state

    if state.ahead_count <= 0:
        state.skipped_reason = "no commits to push"
        return state

    # Use -u flag to set up upstream tracking for new branches
    _run_git(["push", "-u", "origin", state.branch], cwd=state.path)
    state.pushed = True
    return state


def _get_modified_files(path: Path) -> list[ModifiedFile]:
    output = _run_git(["status", "--porcelain=v1", "-z"], cwd=path, check=False)
    if not output or output.startswith("fatal:"):
        return []

    files: list[ModifiedFile] = []
    entries = output.split("\0")
    index = 0
    while index < len(entries):
        entry = entries[index]
        if not entry:
            index += 1
            continue

        status = entry[:2]
        file_path = entry[3:]
        if status[0] in {"R", "C"} or status[1] in {"R", "C"}:
            next_index = index + 1
            renamed_to = entries[next_index] if next_index < len(entries) else ""
            display_path = f"{file_path} -> {renamed_to}" if renamed_to else file_path
            index += 2
        else:
            display_path = file_path
            index += 1

        files.append(ModifiedFile(path=display_path, status=status.strip() or status))
    return files


def _get_ahead_count(path: Path) -> int:
    output = _run_git(["status", "--branch", "--porcelain"], cwd=path, check=False)
    for line in output.splitlines():
        if line.startswith("## ") and "ahead " in line:
            ahead_part = line.split("ahead ", 1)[1].split("]", 1)[0]
            try:
                return int(ahead_part.split(",", 1)[0])
            except ValueError:
                return 0
    return 0


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
