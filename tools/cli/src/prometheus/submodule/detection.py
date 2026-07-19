"""Submodule detection for Prometheus."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from prometheus.config.config import Config


@dataclass(frozen=True)
class SubmoduleInfo:
    """Basic metadata for a Git submodule."""

    name: str
    path: Path
    commit_sha: str | None = None
    initialized: bool = True


@dataclass(frozen=True)
class CoreSubmoduleStatus:
    """Version tracking for the prometheus-core submodule."""

    name: str
    path: Path
    current_commit: str | None = None
    remote_commit: str | None = None
    recorded_commit: str | None = None
    branch: str | None = None
    update_needed: bool = False
    version_changed: bool = False
    exists: bool = False
    error: str | None = None


class SubmoduleDetector:
    """Detects and manages Git submodules."""

    @staticmethod
    def has_submodules(path):
        """Check if a path has Git submodules.

        Args:
            path: Path to check.

        Returns:
            True if submodules detected, False otherwise.
        """
        repo_path = Path(path)
        if not (repo_path / ".gitmodules").exists():
            return False

        output = _run_git(["submodule", "status"], cwd=repo_path, check=False)
        return bool(output and not output.startswith("fatal:"))

    @staticmethod
    def list_submodules(path):
        """List all Git submodules in a path.

        Args:
            path: Path to check.

        Returns:
            List of submodule information.
        """
        repo_path = Path(path)
        output = _run_git(["submodule", "status"], cwd=repo_path, check=False)
        if not output or output.startswith("fatal:"):
            return []

        submodules = []
        for line in output.splitlines():
            if not line:
                continue

            initialized = not line.startswith("-")
            normalized = line[1:] if line[:1] in {" ", "-", "+"} else line
            parts = normalized.split()
            if len(parts) < 2:
                continue

            commit_sha, relative_path = parts[0], parts[1]
            submodules.append(
                SubmoduleInfo(
                    name=Path(relative_path).name,
                    path=repo_path / relative_path,
                    commit_sha=commit_sha,
                    initialized=initialized,
                )
            )
        return submodules

    @staticmethod
    def add_submodule(repo_path, submodule_url, submodule_path):
        """Add a Git submodule.

        Args:
            repo_path: Repository path.
            submodule_url: Submodule URL.
            submodule_path: Path for the submodule.
        """
        _run_git(
            ["submodule", "add", submodule_url, str(submodule_path)],
            cwd=Path(repo_path),
        )

    @staticmethod
    def get_core_submodule_status(path, submodule_name="prometheus-core"):
        """Track the current and remote version of the core submodule."""
        repo_path = Path(path).resolve()
        submodule_path = repo_path / submodule_name
        if not submodule_path.exists():
            return CoreSubmoduleStatus(
                name=submodule_name,
                path=submodule_path,
                exists=False,
                error=f"Submodule not found: {submodule_path}",
            )

        current_commit = _run_git(["rev-parse", "HEAD"], cwd=submodule_path, check=False)
        if not _is_git_value(current_commit):
            return CoreSubmoduleStatus(
                name=submodule_name,
                path=submodule_path,
                exists=True,
                error=current_commit or "Unable to resolve current submodule commit.",
            )

        branch = _run_git(
            ["rev-parse", "--abbrev-ref", "HEAD"],
            cwd=submodule_path,
            check=False,
        )
        if not _is_git_value(branch):
            branch = None

        recorded_commit = _load_recorded_core_commit(repo_path)
        remote_commit = _get_remote_commit(submodule_path, branch)
        update_needed = bool(remote_commit and remote_commit != current_commit)
        version_changed = bool(recorded_commit and recorded_commit != current_commit)

        return CoreSubmoduleStatus(
            name=submodule_name,
            path=submodule_path,
            current_commit=current_commit,
            remote_commit=remote_commit,
            recorded_commit=recorded_commit,
            branch=branch,
            update_needed=update_needed,
            version_changed=version_changed,
            exists=True,
        )


def _load_recorded_core_commit(repo_path: Path) -> str | None:
    config_path = repo_path / ".prometheus.yml"
    if not config_path.exists():
        return None

    try:
        return Config.from_file(config_path).core_version
    except (FileNotFoundError, OSError, ValueError):
        return None


def _get_remote_commit(submodule_path: Path, branch: str | None) -> str | None:
    upstream_ref = _run_git(
        ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"],
        cwd=submodule_path,
        check=False,
    )
    if _is_git_value(upstream_ref) and "/" in upstream_ref:
        remote_name, remote_branch = upstream_ref.split("/", 1)
        remote_commit = _read_ls_remote(submodule_path, remote_name, f"refs/heads/{remote_branch}")
        if remote_commit:
            return remote_commit

    if branch and branch != "HEAD":
        remote_commit = _read_ls_remote(submodule_path, "origin", f"refs/heads/{branch}")
        if remote_commit:
            return remote_commit

    return _read_ls_remote(submodule_path, "origin", "HEAD")


def _read_ls_remote(submodule_path: Path, remote_name: str, ref: str) -> str | None:
    output = _run_git(["ls-remote", remote_name, ref], cwd=submodule_path, check=False)
    if not _is_git_value(output):
        return None

    first_line = output.splitlines()[0]
    parts = first_line.split()
    return parts[0] if parts else None


def _is_git_value(value: str | None) -> bool:
    return bool(value and not value.startswith("fatal:"))


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
