"""Configuration management for Prometheus."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


class Config:
    """Configuration manager for Prometheus app repositories."""

    def __init__(
        self,
        app_name: str | None = None,
        remote_url: str | None = None,
        core_version: str | None = None,
        languages: list[str] | None = None,
        app_remote: str | None = None,
        app_instructions_remote: str | None = None,
        core_remote: str | None = None,
        github_base_url: str | None = None,
    ):
        """Initialize the configuration manager.

        Args:
            app_name: Name of the app
            remote_url: (Deprecated) Use app_remote instead
            core_version: Git commit hash of core version
            languages: List of programming languages used
            app_remote: Remote URL for the app code repository
            app_instructions_remote: Remote URL for the app-specific instructions repository
            core_remote: Remote URL for the core instructions repository
            github_base_url: Base GitHub URL for constructing repo URLs
                (e.g., https://github.com/username)
        """
        self.app_name = app_name
        self.languages = languages or []
        self.remote_url = remote_url or app_remote  # backward compatibility
        self.app_remote = app_remote or remote_url
        self.app_instructions_remote = app_instructions_remote
        self.core_remote = core_remote
        self.core_version = core_version
        # Default GitHub base URL from env or use AlessioPili-KT as default
        self.github_base_url = (
            github_base_url
            or os.environ.get("PROMETHEUS_GITHUB_BASE_URL")
            or "https://github.com/AlessioPili-KT"
        )

    @property
    def project_name(self):
        """Backward compatible alias for older callers."""
        return self.app_name

    @project_name.setter
    def project_name(self, value):
        """Backward compatible alias for older callers."""
        self.app_name = value

    @property
    def remote(self):
        """Backward compatible alias for older callers."""
        return self.remote_url

    @remote.setter
    def remote(self, value):
        """Backward compatible alias for older callers."""
        self.remote_url = value

    def make_github_url(self, repo_name: str) -> str:
        """Construct a full GitHub URL from a repo name.

        If the repo_name is already a full URL, return it as-is.
        Otherwise, construct it from github_base_url and repo_name.

        Args:
            repo_name: Repository name (e.g., 'my-app') or full URL

        Returns:
            Full GitHub repository URL
        """
        if repo_name.startswith("http://") or repo_name.startswith("https://"):
            return repo_name
        # Construct URL: base_url/repo_name.git
        return f"{self.github_base_url}/{repo_name}.git"

    def to_dict(self) -> dict[str, Any]:
        """Serialize configuration to a dictionary."""
        return {
            "app_name": self.app_name,
            "remote_url": self.remote_url,  # backward compatibility
            "app_remote": self.app_remote,
            "app_instructions_remote": self.app_instructions_remote,
            "core_remote": self.core_remote,
            "core_version": self.core_version,
            "languages": self.languages,
            "github_base_url": self.github_base_url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None):
        """Create a configuration object from a dictionary."""
        if not data:
            return cls()

        return cls(
            app_name=data.get("app_name") or data.get("project_name"),
            remote_url=data.get("remote_url") or data.get("remote"),
            app_remote=data.get("app_remote"),
            app_instructions_remote=data.get("app_instructions_remote"),
            core_remote=data.get("core_remote"),
            core_version=data.get("core_version"),
            languages=list(data.get("languages") or []),
            github_base_url=data.get("github_base_url"),
        )

    @classmethod
    def from_file(cls, path):
        """Load a configuration file into a new instance."""
        return cls().load(path)

    def load(self, path):
        """Load configuration from a file.

        Args:
            path: Path to the configuration file.
        """
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with config_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}

        loaded = self.from_dict(data)
        self.app_name = loaded.app_name
        self.languages = loaded.languages
        self.remote_url = loaded.remote_url
        self.app_remote = loaded.app_remote
        self.app_instructions_remote = loaded.app_instructions_remote
        self.core_remote = loaded.core_remote
        self.core_version = loaded.core_version
        self.github_base_url = loaded.github_base_url
        return self

    def save(self, path):
        """Save configuration to a file.

        Args:
            path: Path to save the configuration file.
        """
        config_path = Path(path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with config_path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(self.to_dict(), handle, sort_keys=False)
        return config_path
