"""Execution context detection for Prometheus CLI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

APP_CONFIG_FILE = ".prometheus.yml"
CORE_SUBMODULE_DIR = ".github/prometheus-core"


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
                core_path=candidate / CORE_SUBMODULE_DIR,
            )

    for candidate in search_roots:
        if (candidate / "core").is_dir() and (candidate / "tools" / "cli").is_dir():
            return ExecutionContext(
                context_type="prometheus",
                root_path=candidate,
                core_path=candidate / "core",
            )

    return ExecutionContext(context_type="unknown", root_path=current_path)
