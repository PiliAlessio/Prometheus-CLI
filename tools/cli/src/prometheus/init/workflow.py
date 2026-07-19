"""Project initialization workflow for Prometheus."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from prometheus.config import Config
from prometheus.symlink.symlink import SymlinkManager

DEFAULT_CORE_REPO_URL = "https://github.com/PiliAlessio/Prometheus.git"


@dataclass
class InitResult:
    """Result of an app repository initialization."""

    app_path: Path
    config_path: Path
    app_remote: str
    app_instructions_remote: str | None
    core_remote: str
    core_version: str
    symlink_created: bool


class InitWorkflow:
    """Handles the initialization workflow for Prometheus app repositories.

    This workflow manages three separate Git repositories:
    1. App code repository (where CLI runs)
    2. App-specific instructions repository (optional, separate repo)
    3. Core instructions repository (shared, always exists)
    """

    def __init__(
        self,
        app_name: str,
        app_remote: str | None = None,
        app_instructions_remote: str | None = None,
        core_remote: str | None = None,
        create_app_repo: bool = False,
        base_path: str | Path | None = None,
        current_dir: str | Path | None = None,
    ):
        """Initialize the workflow.

        Args:
            app_name: Name of the app repository
            app_remote: Remote URL for app code repository
            app_instructions_remote: Remote URL for app-specific instructions repo
            core_remote: Remote URL for core instructions repo
            create_app_repo: If True, create app repo structure locally for new apps
            base_path: Where to store app repos (~/.prometheus by default)
            current_dir: Current working directory for symlink creation
        """
        self.app_name = app_name
        self.app_remote = app_remote
        self.app_instructions_remote = app_instructions_remote
        self.core_remote = core_remote or DEFAULT_CORE_REPO_URL
        self.create_app_repo = create_app_repo
        self.base_path = Path(base_path or Path.home() / ".prometheus")
        # App code repo is in the current directory (where the command is run)
        self.app_path = Path(current_dir or Path.cwd())
        # App instructions repo is in the cache
        self.instructions_path = self.base_path / f"{app_name}-instructions"
        self.current_dir = Path(current_dir or Path.cwd())

        # If app_remote not provided, try to detect from existing Git repo
        if not self.app_remote and not self.create_app_repo:
            detected_remote = self._detect_git_remote()
            if detected_remote:
                self.app_remote = detected_remote

    def run(self) -> InitResult:
        """Run the initialization workflow.

        Returns:
            InitResult with details about the initialized app.

        Raises:
            ValueError: If required remotes are missing or invalid.
            RuntimeError: If any operation fails.
        """
        # Phase 1: Validate all three remotes
        self._validate_remotes()

        # Phase 2: Initialize app code repository
        self._initialize_app_repository()

        # Phase 3: Set up app-specific instructions repository
        # Always set up, even if no remote provided (creates locally)
        self._setup_app_instructions_repository()

        # Phase 4: Get core version
        core_version = self._get_core_version()

        # Phase 5: Create configuration file
        config_path = self._create_config_file(core_version)

        # Phase 6: Create .github symlink in app code
        symlink_created = self._create_github_symlink()

        return InitResult(
            app_path=self.app_path,
            config_path=config_path,
            app_remote=self.app_remote,
            app_instructions_remote=self.app_instructions_remote,
            core_remote=self.core_remote,
            core_version=core_version,
            symlink_created=symlink_created,
        )

    def _validate_remotes(self) -> None:
        """Validate that all three remotes are accessible.

        Raises:
            ValueError: If app_remote is missing or any remote is inaccessible.
        """
        # App remote is required
        if not self.app_remote and not self.create_app_repo:
            raise ValueError(
                "App remote URL is required unless --create-app-repo flag is used.\n"
                "Either:\n"
                "  1. Run from a Git repository with an 'origin' remote (auto-detected)\n"
                "  2. Provide: --app-remote https://github.com/user/my-app.git\n"
                "  3. Use: --create-app-repo (for new apps)"
            )

        # Validate core remote
        if not self._is_remote_accessible(self.core_remote):
            raise RuntimeError(
                f"Core instructions remote is not accessible: {self.core_remote}\n"
                f"Ensure the URL is correct and you have network access."
            )

        # Validate app remote (if provided and not creating locally)
        if self.app_remote and not self._is_remote_accessible(self.app_remote):
            raise RuntimeError(
                f"App remote is not accessible: {self.app_remote}\n"
                f"Ensure the URL is correct and you have network access."
            )

        # Validate app instructions remote (if provided)
        if self.app_instructions_remote and not self._is_remote_accessible(
            self.app_instructions_remote
        ):
            raise RuntimeError(
                f"App instructions remote is not accessible: {self.app_instructions_remote}\n"
                f"Ensure the URL is correct and you have network access."
            )

    def _detect_git_remote(self) -> str | None:
        """Detect Git remote from the current directory if it's a Git repo.

        Looks for 'origin' remote in the current directory's .git/config.

        Returns:
            Remote URL if found, None otherwise.
        """
        try:
            # Check if current directory is a Git repo
            git_dir = self.app_path / ".git"
            if not git_dir.exists():
                return None

            # Get the remote URL using git config
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=self.app_path,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0 and result.stdout:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return None

    def _is_remote_accessible(self, remote_url: str) -> bool:
        """Check if a Git remote URL is accessible via git ls-remote.

        Args:
            remote_url: URL to check.

        Returns:
            True if accessible, False otherwise.
        """
        try:
            result = subprocess.run(
                ["git", "ls-remote", "--heads", remote_url],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _initialize_app_repository(self) -> None:
        """Initialize the app code repository.

        Handles three scenarios:
        1. Current directory is already a Git repo with remote (use as-is)
        2. Clone from remote if app_remote is provided
        3. Create local structure if --create-app-repo flag is set
        """
        # Check if current directory is already a Git repo
        if (self.app_path / ".git").exists():
            # Already a Git repo, just use it
            return

        if self.app_remote:
            self._clone_app_repository()
        elif self.create_app_repo:
            self._create_app_structure_locally()
        else:
            # This should not happen due to validation, but be safe
            raise RuntimeError("Unable to initialize app repository")

    def _clone_app_repository(self) -> None:
        """Clone app repository from remote into current directory.

        Raises:
            FileExistsError: If current directory already has content.
            RuntimeError: If clone fails.
        """
        # Check if current directory is empty
        if self.app_path.exists() and any(self.app_path.iterdir()):
            raise FileExistsError(
                f"Current directory has content: {self.app_path}\n"
                f"Initialize in an empty directory."
            )

        # Clone into current directory by cloning into a temp location then moving files
        # Or clone directly into current directory if empty
        result = subprocess.run(
            ["git", "clone", self.app_remote, "."],
            cwd=self.app_path,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Failed to clone app repository from {self.app_remote}:\n"
                f"{result.stderr.strip() or result.stdout.strip()}"
            )

        # Create .gitignore to exclude .prometheus.yml (local config, not pushed)
        self._create_gitignore()

    def _create_app_structure_locally(self) -> None:
        """Create app repository structure locally for new apps.

        The app code repo is minimal, containing only config and other app files.
        The .github folder will be created as a symlink to app-instructions/.github

        Raises:
            FileExistsError: If app directory already has content.
        """
        if self.app_path.exists() and any(self.app_path.iterdir()):
            raise FileExistsError(
                f"Current directory has content: {self.app_path}\n"
                f"Initialize in an empty directory."
            )

        # Create app code directory (may already exist if using current_dir)
        self.app_path.mkdir(parents=True, exist_ok=True)

        # Create only config folder (not .github - that will be a symlink)
        (self.app_path / "config").mkdir(parents=True, exist_ok=True)

        # Initialize as git repo
        self._run_git(["init"], cwd=self.app_path)

        # Create .gitignore to exclude .prometheus.yml (local config, not pushed)
        self._create_gitignore()

    def _setup_app_instructions_repository(self) -> None:
        """Clone and configure the app-specific instructions repository.

        The app-specific instructions repo is a SEPARATE repository that contains
        the core as a submodule. It is stored at ~/.prometheus/{app_name}-instructions/

        Behavior:
        - If app_instructions_remote is provided and accessible: clones from that URL
        - If app_instructions_remote starts with __CREATE_WITH_GH__: tries GitHub CLI
        - If app_instructions_remote is not provided: creates a local git repo
          (user can push later)
        - Either way: ensures .github structure exists and adds core as submodule

        Raises:
            RuntimeError: If critical operations fail.
        """
        # If instructions already exists and has .git, skip
        if (self.instructions_path / ".git").exists():
            return

        # Check if this is a GitHub CLI creation request
        if self.app_instructions_remote and self.app_instructions_remote.startswith(
            "__CREATE_WITH_GH__"
        ):
            repo_name = self.app_instructions_remote.replace("__CREATE_WITH_GH__", "").strip()
            # Create local repo first
            self.instructions_path.mkdir(parents=True, exist_ok=True)
            self._run_git(["init"], cwd=self.instructions_path)

            # Try to create on GitHub
            gh_url = self._try_create_repo_with_gh(repo_name)
            if gh_url:
                self.app_instructions_remote = gh_url
                self._run_git(
                    ["remote", "add", "origin", gh_url],
                    cwd=self.instructions_path,
                )
            else:
                # gh failed or not available, continue with local-only
                self.app_instructions_remote = None

            # Ensure .github directory exists for core submodule
            (self.instructions_path / ".github").mkdir(parents=True, exist_ok=True)
            # Add core as submodule in the app instructions repo
            self._add_core_submodule_to_instructions()
            return

        # Try to clone app instructions repo if a remote was provided
        if self.app_instructions_remote:
            try:
                result = subprocess.run(
                    [
                        "git",
                        "clone",
                        self.app_instructions_remote,
                        str(self.instructions_path),
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if result.returncode == 0:
                    # Successfully cloned, ensure .github exists
                    (self.instructions_path / ".github").mkdir(parents=True, exist_ok=True)
                    # Add core as submodule in the app instructions repo
                    self._add_core_submodule_to_instructions()
                    return

            except Exception:
                pass

        # If no remote provided or clone failed, create structure locally
        # User can add origin remote later if desired: git remote add origin <url>
        self.instructions_path.mkdir(parents=True, exist_ok=True)
        self._run_git(["init"], cwd=self.instructions_path)
        if self.app_instructions_remote:
            # This shouldn't happen (clone succeeded above), but be defensive
            self._run_git(
                ["remote", "add", "origin", self.app_instructions_remote],
                cwd=self.instructions_path,
            )

        # Ensure .github directory exists for core submodule
        (self.instructions_path / ".github").mkdir(parents=True, exist_ok=True)

        # Add core as submodule in the app instructions repo
        self._add_core_submodule_to_instructions()

    def _try_create_repo_with_gh(self, repo_name: str) -> str | None:
        """Attempt to create a GitHub repository using GitHub CLI.

        Args:
            repo_name: Name for the repository (e.g., 'my-app-instructions')

        Returns:
            Repository HTTPS URL if created successfully, None if gh unavailable
            or creation failed. Falls back gracefully.
        """
        try:
            # Check if gh command is available
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

            if result.returncode != 0:
                return None  # gh not available

            # Try to create repo
            result = subprocess.run(
                [
                    "gh",
                    "repo",
                    "create",
                    repo_name,
                    "--public",
                    "--source=.",
                    "--remote=origin",
                    "--push=false",
                ],
                cwd=self.instructions_path,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            if result.returncode == 0:
                # Extract repo URL from gh output or construct it
                # gh outputs: "✓ Created repository {owner}/{repo} on GitHub"
                # We need to construct the HTTPS URL
                try:
                    # Get GitHub username if not in output
                    user_result = subprocess.run(
                        ["gh", "api", "user", "-q", ".login"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        check=False,
                    )
                    if user_result.returncode == 0:
                        username = user_result.stdout.strip()
                        repo_url = f"https://github.com/{username}/{repo_name}.git"
                        return repo_url
                except Exception:
                    pass

            return None

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None
        except Exception:
            return None

    def _add_core_submodule_to_instructions(self) -> None:
        """Add core as a submodule in the app-specific instructions repository.

        Removes CLI and docs folders to keep only essential core structure.
        """
        core_submodule_path = self.instructions_path / ".github" / "prometheus-core"

        # Check if already a submodule
        if (core_submodule_path / ".git").exists():
            return

        try:
            # Add core as submodule
            self._run_git(
                ["submodule", "add", self.core_remote, ".github/prometheus-core"],
                cwd=self.instructions_path,
                check=False,
            )

            # Initialize and update submodule to fetch content
            self._run_git(
                ["submodule", "update", "--init", "--recursive"],
                cwd=self.instructions_path,
                check=False,
            )

            # Remove unnecessary folders to save space (docs and tools/cli)
            self._cleanup_submodule_folders(core_submodule_path)

        except Exception:
            # If submodule add fails, that's ok - the .github structure was created
            pass

    def _create_gitignore(self) -> None:
        """Create .gitignore in app code repo to exclude .prometheus.yml (local config)."""
        gitignore_path = self.app_path / ".gitignore"

        # If .gitignore already exists, just ensure .prometheus.yml is in it
        if gitignore_path.exists():
            content = gitignore_path.read_text()
            if ".prometheus.yml" not in content:
                with open(gitignore_path, "a") as f:
                    f.write("\n.prometheus.yml\n")
        else:
            # Create new .gitignore with .prometheus.yml
            gitignore_path.write_text(".prometheus.yml\n")

    def _cleanup_submodule_folders(self, submodule_path: Path) -> None:
        """Remove unnecessary folders from the core submodule to save space.

        Removes:
        - tools/cli/ - CLI implementation (not needed in app repo)
        - docs/ - Documentation (can be accessed from main Prometheus repo)

        Args:
            submodule_path: Path to the core submodule.
        """
        try:
            import shutil

            # Folders to remove
            cleanup_paths = [submodule_path / "tools" / "cli", submodule_path / "docs"]

            for path in cleanup_paths:
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()

        except Exception:
            # Cleanup is optional - if it fails, the submodule still works
            pass

    def _get_core_version(self) -> str:
        """Get the current version (commit hash) of core.

        Returns:
            Git commit hash of core HEAD, or "unknown" if unable to retrieve.
        """
        # Try to get from app-specific instructions repo if it exists
        core_submodule_path = self.instructions_path / ".github" / "prometheus-core"

        if (core_submodule_path / ".git").exists():
            revision = self._run_git(["rev-parse", "HEAD"], cwd=core_submodule_path, check=False)
            if revision and not revision.startswith("fatal:"):
                return revision

        # Fall back to getting from core remote directly
        try:
            result = subprocess.run(
                ["git", "ls-remote", "--refs", "heads/main", self.core_remote],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout:
                # First column is the commit hash
                return result.stdout.split()[0]
        except (subprocess.TimeoutExpired, IndexError):
            pass

        return "unknown"

    def _create_config_file(self, core_version: str) -> Path:
        """Create .prometheus.yml configuration file.

        The config file stores remote URLs and is local only (should be gitignored).

        Args:
            core_version: Git commit hash of core.

        Returns:
            Path to the created config file.
        """
        config = Config(
            app_name=self.app_name,
            app_remote=self.app_remote,
            app_instructions_remote=self.app_instructions_remote,
            core_remote=self.core_remote,
            core_version=core_version,
        )
        config_path = self.app_path / ".prometheus.yml"
        config.save(config_path)
        return config_path

    def _create_github_symlink(self) -> bool:
        """Create .github symlink pointing from app code to app-instructions .github.

        In the app code repo (current directory), creates a symlink:
        ./.github -> ~/.prometheus/{app_name}-instructions/.github

        This allows the app code repo to reference the workflows and core from app-instructions.

        Returns:
            True if symlink was created, False if creation failed.
        """
        # Ensure base path exists for instructions
        self.base_path.mkdir(parents=True, exist_ok=True)

        instructions_github = self.instructions_path / ".github"

        # Ensure .github folder exists in app-instructions repo
        # (create it if it doesn't exist)
        if not instructions_github.exists():
            try:
                instructions_github.mkdir(parents=True, exist_ok=True)
            except OSError:
                # If we can't create it, we can't create the symlink
                return False

        symlink_path = self.app_path / ".github"

        try:
            # If .github already exists as a regular directory, remove it first
            if symlink_path.exists() and not symlink_path.is_symlink():
                import shutil

                shutil.rmtree(symlink_path)

            SymlinkManager.create_symlink(source=instructions_github, target=symlink_path)
            return True
        except (OSError, RuntimeError, FileExistsError) as e:
            # Print warning about symlink failure but don't block initialization
            import sys

            print(f"⚠ Warning: Could not create .github symlink: {str(e)}", file=sys.stderr)
            return False

    def _run_git(self, args: list[str], cwd: str | Path, check: bool = True) -> str:
        """Run a git command.

        Args:
            args: Git command arguments.
            cwd: Working directory.
            check: If True, raise exception on non-zero return code.

        Returns:
            stdout from the command.

        Raises:
            RuntimeError: If check=True and command fails.
        """
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
