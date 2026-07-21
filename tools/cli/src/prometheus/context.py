"""Execution context detection for Prometheus CLI."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from prometheus.config import Config

APP_CONFIG_FILE = ".prometheus.yml"
INSTRUCTIONS_BASE_ENV_VAR = "PROMETHEUS_INSTRUCTIONS_BASE"


@dataclass(frozen=True)
class ExecutionContext:
    """Represents the repository context used by the CLI."""

    context_type: str
    root_path: Path
    config_path: Path | None = None
    core_path: Path | None = None

    @property
    def is_app(self) -> bool:
        """Return True when the CLI is running inside an app repository."""
        return self.context_type == "app"

    @property
    def is_prometheus(self) -> bool:
        """Return True when the CLI is running inside the Prometheus repository."""
        return self.context_type == "prometheus"


def detect_context(start_path: str | Path | None = None) -> ExecutionContext:
    """Detect whether the current directory is an app repo or the core repo."""
    current_path = Path(start_path or Path.cwd()).resolve()
    search_roots = [current_path, *current_path.parents]

    for candidate in search_roots:
        config_path = candidate / APP_CONFIG_FILE
        if config_path.is_file():
            return ExecutionContext(
                context_type="app",
                root_path=candidate,
                config_path=config_path,
                core_path=_detect_core_path(config_path),
            )

    for candidate in search_roots:
        if (candidate / "core").is_dir() and (candidate / "tools" / "cli").is_dir():
            return ExecutionContext(
                context_type="prometheus",
                root_path=candidate,
                core_path=candidate / "core",
            )

    return ExecutionContext(context_type="unknown", root_path=current_path)


def _detect_core_path(config_path: Path) -> Path | None:
    """Locate the core submodule inside the cached app-instructions repo.

    The app-instructions repo (and its core/ submodule) live outside the app
    code repo, cached at ~/.prometheus/{app_name}-instructions/ (or under
    PROMETHEUS_INSTRUCTIONS_BASE when overridden for testing). There is no
    longer a .github/prometheus symlink into the app code repo pointing at
    it - materialized content is copied directly into the app repo's
    .github/ folder instead, so this path is only used to locate the source
    repo for pull/update/push operations.
    """
    try:
        config = Config.from_file(config_path)
    except (FileNotFoundError, OSError):
        return None

    if not config.app_name:
        return None

    base_path = os.environ.get(INSTRUCTIONS_BASE_ENV_VAR)
    base = Path(base_path) if base_path else Path.home() / ".prometheus"
    return base / f"{config.app_name}-instructions" / "core"
