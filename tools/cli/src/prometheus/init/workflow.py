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
            app_remote: Remote URL or repo name for app code repository
                (can be just repo name like 'my-app')
            app_instructions_remote: Remote URL or repo name for app-specific instructions repo
                (can be just repo name like 'my-app-instructions')
            core_remote: Remote URL for core instructions repo
            create_app_repo: If True, create app repo structure locally for new apps
            base_path: Where to store app repos (~/.prometheus by default)
            current_dir: Current working directory for symlink creation
        """
        self.config = Config()
        self.app_name = app_name
        # Convert repo names to full URLs if needed (skip full URLs)
        self.app_remote = (
            app_remote if (app_remote.startswith("http://") or
                          app_remote.startswith("https://"))
            else self.config.make_github_url(app_remote)
        ) if app_remote else None
        self.app_instructions_remote = (
            app_instructions_remote if (app_instructions_remote.startswith("http://") or
                                       app_instructions_remote.startswith("https://"))
            else self.config.make_github_url(app_instructions_remote)
        ) if app_instructions_remote else None
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

        # Phase 6: Create .github/prometheus symlink in app code
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
        if (
            self.app_instructions_remote
            and not self._is_remote_accessible(self.app_instructions_remote)
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
        The .github/prometheus folder will be created as a symlink to the
        app-instructions repo root.

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
        # Ensure the default branch is "main" regardless of the local git version's
        # init.defaultBranch setting.
        self._run_git(["symbolic-ref", "HEAD", "refs/heads/main"], cwd=self.app_path, check=False)

        # Create .gitignore to exclude .prometheus.yml (local config, not pushed)
        self._create_gitignore()

    def _setup_app_instructions_repository(self) -> None:
        """Clone and configure the app-specific instructions repository.

        The app-specific instructions repo is a SEPARATE repository that contains
        the core as a submodule. It is stored at ~/.prometheus/{app_name}-instructions/

        Behavior:
        - If app_instructions_remote is provided and accessible: clones from that URL
        - If app_instructions_remote is not provided: creates a local git repo
          (user can push later)
        - Either way: ensures app/ folder structure exists and adds core as submodule
        - If remote exists, commits and pushes the submodule setup

        Raises:
            RuntimeError: If critical operations fail.
        """
        # Check if instructions repo already exists
        instructions_exists = (self.instructions_path / ".git").exists()

        # If it already exists, just ensure folders are created and push changes
        if instructions_exists:
            print(f"[DEBUG] App-instructions repo already exists at {self.instructions_path}")
            # Rename a lingering "master" branch to "main" (older/broken checkouts)
            self._ensure_main_branch(self.instructions_path)
            # Ensure origin remote is configured (older/broken local repos may lack it)
            self._ensure_instructions_remote()
            # Detect and optionally clean up an older (pre app/+core/) layout
            self._maybe_clean_legacy_structure()
            # Ensure standard folder structure exists
            self._create_folder_structure()
            # Create .gitignore (app repo excludes .prometheus.yml)
            self._create_gitignore()
            # Ensure core submodule exists
            self._add_core_submodule_to_instructions()
            # Push any new folders/submodule
            if self.app_instructions_remote:
                self._push_instructions_setup()
            return

        # Try to clone app instructions repo if a remote was provided
        if self.app_instructions_remote:
            try:
                print(f"[DEBUG] Attempting to clone {self.app_instructions_remote}...")
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

                print(f"[DEBUG] Clone returned: {result.returncode}")
                if result.returncode != 0:
                    print(f"[DEBUG] Clone stderr: {result.stderr}")
                    print(f"[DEBUG] Clone stdout: {result.stdout}")

                if result.returncode == 0:
                    print("[DEBUG] Clone successful, setting up submodule...")
                    # Detect and optionally clean up an older (pre app/+core/) layout
                    self._maybe_clean_legacy_structure()
                    # Create standard folder structure with .gitkeep files
                    self._create_folder_structure()
                    # Create .gitignore (app repo excludes .prometheus.yml)
                    self._create_gitignore()
                    # Add core as submodule in the app instructions repo
                    self._add_core_submodule_to_instructions()
                    # Push the setup to remote if this was a newly created repo
                    self._push_instructions_setup()
                    return

            except Exception as e:
                print(f"[DEBUG] Exception during clone: {e}")
                pass

        # If no remote provided or clone failed, create structure locally
        # User can add origin remote later if desired: git remote add origin <url>
        self.instructions_path.mkdir(parents=True, exist_ok=True)
        self._run_git(["init"], cwd=self.instructions_path)
        # Ensure the default branch is "main" regardless of the local git version's
        # init.defaultBranch setting.
        self._run_git(
            ["symbolic-ref", "HEAD", "refs/heads/main"], cwd=self.instructions_path, check=False
        )
        if self.app_instructions_remote:
            # This shouldn't happen (clone succeeded above), but be defensive
            self._run_git(
                ["remote", "add", "origin", self.app_instructions_remote],
                cwd=self.instructions_path,
            )

        # Create standard folder structure with .gitkeep files
        self._create_folder_structure()

        # Create .gitignore (app repo excludes .prometheus.yml)
        self._create_gitignore()

        # Add core as submodule in the app instructions repo
        self._add_core_submodule_to_instructions()
        # Push if remote exists
        if self.app_instructions_remote:
            self._push_instructions_setup()

    def _ensure_main_branch(self, repo_path: Path) -> None:
        """Rename a lingering 'master' branch to 'main' if present.

        Older or interrupted local checkouts may have been created with git's
        legacy default branch name. Since all push/pull operations in this
        tool target "main", rename the branch if needed so pushes succeed.
        """
        current_branch = self._run_git(
            ["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path, check=False
        )
        if current_branch == "master":
            print(f"[DEBUG] Renaming branch 'master' to 'main' in {repo_path}")
            self._run_git(["branch", "-m", "master", "main"], cwd=repo_path, check=False)

    def _ensure_instructions_remote(self) -> None:
        """Ensure the instructions repo has an 'origin' remote configured.

        Older/broken local checkouts may have been created without a remote
        (e.g. if a previous clone attempt failed and the tool fell back to a
        local-only repo). If app_instructions_remote is provided but no origin
        remote exists yet, add it now so pushes can succeed.
        """
        if not self.app_instructions_remote:
            return

        existing_remotes = self._run_git(
            ["remote"], cwd=self.instructions_path, check=False
        )
        remote_names = (existing_remotes or "").split()
        if "origin" in remote_names:
            return

        print(f"[DEBUG] No 'origin' remote found, adding {self.app_instructions_remote}")
        self._run_git(
            ["remote", "add", "origin", self.app_instructions_remote],
            cwd=self.instructions_path,
            check=False,
        )

    def _maybe_clean_legacy_structure(self) -> None:
        """Detect an older instructions-repo layout and offer to clean it up.

        Older versions of this tool created content folders (instructions/,
        prompts/, skills/, config/, docs/) and the core submodule directly at
        the repo root instead of under app/ and core/. If leftover entries from
        that layout are detected, ask the user whether to remove them so the
        repo can be rebuilt cleanly with the current app/ + core/ structure.

        If the user declines, the legacy entries are left in place and will
        simply coexist alongside the new app/ and core/ folders.
        """
        expected_entries = {".git", ".gitignore", ".gitmodules", "app", "core"}
        try:
            entries = [p.name for p in self.instructions_path.iterdir()]
        except OSError:
            return

        legacy_entries = sorted(name for name in entries if name not in expected_entries)
        if not legacy_entries:
            return

        print(f"[DEBUG] Detected legacy entries in instructions repo: {legacy_entries}")
        try:
            answer = (
                input(
                    "\nThe app-instructions repository contains files from an older "
                    f"layout ({', '.join(legacy_entries)}).\n"
                    "Remove them and rebuild with the current app/ + core/ structure? "
                    "[y/N]: "
                )
                .strip()
                .lower()
            )
        except (EOFError, KeyboardInterrupt):
            answer = "n"

        if answer not in ("y", "yes"):
            print("[DEBUG] Keeping legacy entries as-is.")
            return

        import shutil

        for name in legacy_entries:
            path = self.instructions_path / name
            # Try removing via git first so tracked files/submodules are staged
            # for deletion (handles .gitmodules bookkeeping correctly).
            self._run_git(["rm", "-rf", "--", name], cwd=self.instructions_path, check=False)
            try:
                if path.is_symlink() or path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)
                print(f"[DEBUG] Removed legacy entry: {path}")
            except OSError as e:
                print(f"[DEBUG] Failed to remove {path}: {e}")

    def _create_folder_structure(self) -> None:
        """Create standard folder structure with .gitkeep files.

        Creates content folders under app/ in the app-specific instructions repository:
        - app/instructions/ - for app-specific instructions
        - app/prompts/ - for AI prompts and instructions
        - app/skills/ - for domain-specific skills
        - app/config/ - for configuration files
        - app/docs/ - for documentation

        The core/ submodule lives as a sibling of app/ at the repo root, so the
        final layout is:
            {app_name}-instructions/
            ├── app/
            │   ├── instructions/
            │   ├── prompts/
            │   ├── skills/
            │   ├── config/
            │   └── docs/
            └── core/ (git submodule)

        Each folder gets a .gitkeep file to ensure Git tracks empty directories.
        """
        folders = [
            "app/instructions",
            "app/prompts",
            "app/skills",
            "app/config",
            "app/docs",
        ]

        print(f"[DEBUG] Creating folder structure in {self.instructions_path}")
        for folder_name in folders:
            folder_path = self.instructions_path / folder_name
            folder_path.mkdir(parents=True, exist_ok=True)
            print(f"[DEBUG] Created folder: {folder_path}")

            # Create .gitkeep file to ensure Git tracks the empty directory
            gitkeep_path = folder_path / ".gitkeep"
            if not gitkeep_path.exists():
                gitkeep_path.write_text("")
                print(f"[DEBUG] Created .gitkeep: {gitkeep_path}")
            else:
                print(f"[DEBUG] .gitkeep already exists: {gitkeep_path}")

    def _push_instructions_setup(self) -> None:
        """Commit and push the instructions setup to remote.

        Commits the .gitmodules and core submodule setup, then pushes to origin.
        Handles failures gracefully - doesn't block initialization.
        """
        try:
            # Ensure git user config is set for this repo (needed for commits)
            # Check if user.name and user.email are configured
            user_name_result = subprocess.run(
                ["git", "config", "user.name"],
                cwd=self.instructions_path,
                capture_output=True,
                text=True,
                check=False,
            )

            if not user_name_result.stdout.strip():
                print("[DEBUG] Setting git user.name...")
                self._run_git(
                    ["config", "user.name", "Prometheus"],
                    cwd=self.instructions_path,
                    check=False,
                )

            user_email_result = subprocess.run(
                ["git", "config", "user.email"],
                cwd=self.instructions_path,
                capture_output=True,
                text=True,
                check=False,
            )

            if not user_email_result.stdout.strip():
                print("[DEBUG] Setting git user.email...")
                self._run_git(
                    ["config", "user.email", "prometheus@localhost"],
                    cwd=self.instructions_path,
                    check=False,
                )

            # Stage all changes (including .gitmodules and submodule)
            self._run_git(["add", "-A"], cwd=self.instructions_path)

            # Check if there are changes to commit
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.instructions_path,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

            print(f"[DEBUG] Git status output:\n{result.stdout}")

            if result.stdout.strip():
                print(f"[DEBUG] Found changes to commit in {self.instructions_path}")
                print(f"[DEBUG] Changes:\n{result.stdout}")

                # Check if this is the initial commit (no HEAD yet)
                head_result = subprocess.run(
                    ["git", "rev-parse", "--verify", "HEAD"],
                    cwd=self.instructions_path,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                is_initial_commit = head_result.returncode != 0
                print(f"[DEBUG] Is initial commit: {is_initial_commit}")

                # There are changes to commit
                commit_result = self._run_git(
                    ["commit", "-m", "Setup: Initialize repository structure"],
                    cwd=self.instructions_path,
                    check=False,
                )
                print(f"[DEBUG] Commit output: {commit_result}")

                # Check current branch info
                branch_result = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=self.instructions_path,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                current_branch = branch_result.stdout.strip()
                print(f"[DEBUG] Current branch: {current_branch}")

                # Check if origin exists
                remote_result = subprocess.run(
                    ["git", "remote", "-v"],
                    cwd=self.instructions_path,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                print(f"[DEBUG] Remotes: {remote_result.stdout}")

                # If we have a non-detached branch, try to push it
                if current_branch and current_branch != "HEAD":
                    print(f"[DEBUG] Attempting to push current branch {current_branch}...")
                    push_result = subprocess.run(
                        ["git", "push", "-u", "origin", current_branch],
                        cwd=self.instructions_path,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        check=False,
                    )
                    print(f"[DEBUG] Push returned: {push_result.returncode}")
                    if push_result.returncode != 0:
                        print(f"[DEBUG] Push stderr: {push_result.stderr}")
                        print(f"[DEBUG] Push stdout: {push_result.stdout}")
                    else:
                        print(f"[INFO] Successfully pushed to origin {current_branch}")
                        return

                # If that didn't work, push to main (default branch)
                print(f"[DEBUG] Attempting to push to origin main...")
                push_result = subprocess.run(
                    ["git", "push", "-u", "origin", "main"],
                    cwd=self.instructions_path,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                print(f"[DEBUG] Push to main returned: {push_result.returncode}")
                if push_result.returncode != 0:
                    print(f"[DEBUG] Push stderr: {push_result.stderr}")
                    print(f"[DEBUG] Push stdout: {push_result.stdout}")
                if push_result.returncode == 0:
                    print(f"[INFO] Successfully pushed to origin main")
                    return  # Push succeeded

                # If specific branches failed, try forcing push with --set-upstream (creates branch if needed)
                print("[DEBUG] Trying forced push with HEAD refspec...")
                push_result = subprocess.run(
                    ["git", "push", "-f", "origin", "HEAD"],
                    cwd=self.instructions_path,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                print(f"[DEBUG] Push HEAD returned: {push_result.returncode}")
                if push_result.returncode != 0:
                    print(f"[DEBUG] Push stderr: {push_result.stderr}")
                    print(f"[DEBUG] Push stdout: {push_result.stdout}")
                else:
                    print(f"[INFO] Successfully pushed to origin HEAD")
            else:
                print("[DEBUG] No changes to commit in instructions repo")
        except Exception as e:
            # Don't fail initialization if push fails
            # User can manually push later
            import traceback
            print(f"[ERROR] Failed to push instructions setup: {e}")
            traceback.print_exc()

    def _add_core_submodule_to_instructions(self) -> None:
        """Add core as a submodule in the app-specific instructions repository.

        Removes CLI and docs folders to keep only essential core structure.
        """
        core_submodule_path = self.instructions_path / "core"

        # Check if already a submodule
        if (core_submodule_path / ".git").exists():
            # Already added - but a previous run may have left core/core/ nested.
            # Flatten it so existing repos get fixed up too.
            self._flatten_core_submodule(core_submodule_path)
            self._cleanup_submodule_folders(core_submodule_path)
            return

        try:
            # Add core as submodule
            self._run_git(
                ["submodule", "add", self.core_remote, "core"],
                cwd=self.instructions_path,
                check=False,
            )

            # Initialize and update submodule to fetch content
            self._run_git(
                ["submodule", "update", "--init", "--recursive"],
                cwd=self.instructions_path,
                check=False,
            )

            # The Prometheus core repo has its own nested core/ folder; flatten
            # it so we don't end up with core/core/ inside the submodule.
            self._flatten_core_submodule(core_submodule_path)

            # Remove unnecessary folders to save space (docs and tools/cli)
            self._cleanup_submodule_folders(core_submodule_path)

        except Exception:
            # If submodule add fails, that's ok - the app/ folder structure was created
            pass

    def _create_gitignore(self) -> None:
        """Create .gitignore files in app repo.

        App repo: excludes .prometheus.yml (local config)
        Instructions repo: no gitignore needed (contains tracked content folders and core submodule)
        """
        # App code repo .gitignore
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

    def _flatten_core_submodule(self, submodule_path: Path) -> None:
        """Flatten a nested core/ folder from within the core submodule.

        The Prometheus core remote repository has its own top-level core/
        folder (used by detect_context to identify the main Prometheus repo).
        Adding that whole repo as a submodule named "core" would otherwise
        result in core/core/ nesting. This moves the nested core/ content up
        to the submodule root and removes the now-empty nested folder.

        Args:
            submodule_path: Path to the core submodule.
        """
        nested_core = submodule_path / "core"
        if not nested_core.is_dir():
            return

        try:
            import shutil

            for item in list(nested_core.iterdir()):
                target = submodule_path / item.name
                if target.exists():
                    if target.is_dir() and not target.is_symlink():
                        shutil.rmtree(target)
                    else:
                        target.unlink()
                shutil.move(str(item), str(target))

            shutil.rmtree(nested_core)
        except Exception:
            # Flattening is best-effort - if it fails, the submodule still works
            pass

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
        core_submodule_path = self.instructions_path / "core"

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
        """Create .github/prometheus symlink pointing to the app-instructions repo root.

        In the app code repo (current directory), creates a symlink:
        ./.github/prometheus -> ~/.prometheus/{app_name}-instructions/

        The "prometheus" layer only exists in the app code repo - the
        instructions repo itself stays flat (app/ and core/ at its root).
        This allows the app code repo to reference the full instructions repo
        (app/ content folders and the core/ submodule) through
        .github/prometheus/app and .github/prometheus/core.

        Returns:
            True if symlink was created, False if creation failed.
        """
        # Ensure base path exists for instructions
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Ensure the instructions repo directory exists
        if not self.instructions_path.exists():
            try:
                self.instructions_path.mkdir(parents=True, exist_ok=True)
            except OSError:
                # If we can't create it, we can't create the symlink
                return False

        github_path = self.app_path / ".github"

        try:
            # .github is a real directory in the app repo; if it previously was
            # a symlink itself (older layout), remove it and recreate as a dir.
            if github_path.is_symlink():
                github_path.unlink()
            github_path.mkdir(parents=True, exist_ok=True)

            symlink_path = github_path / "prometheus"

            # If prometheus already exists as a regular directory, remove it first
            if symlink_path.exists() and not symlink_path.is_symlink():
                import shutil

                shutil.rmtree(symlink_path)

            SymlinkManager.create_symlink(source=self.instructions_path, target=symlink_path)
            return True
        except (OSError, RuntimeError, FileExistsError) as e:
            # Print warning about symlink failure but don't block initialization
            import sys

            print(
                f"⚠ Warning: Could not create .github/prometheus symlink: {str(e)}",
                file=sys.stderr,
            )
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
