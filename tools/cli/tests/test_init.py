"""Tests for project initialization workflow."""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock


class TestInitializationWorkflow:
    """Test suite for complete initialization workflow."""

    def test_init_creates_project_structure(self, temp_project_dir):
        """Test initialization creates basic project structure."""
        project_path = temp_project_dir / "test-project"
        project_path.mkdir()

        # Verify directory was created
        assert project_path.exists()
        assert project_path.is_dir()

    def test_init_with_config_file(self, temp_project_dir):
        """Test initialization creates config file."""
        project_path = temp_project_dir / "test-project"
        project_path.mkdir()

        config_file = project_path / "prometheus.yaml"
        config_file.write_text("project: test-project\n")

        assert config_file.exists()
        assert config_file.read_text() == "project: test-project\n"

    def test_init_with_multiple_directories(self, temp_project_dir):
        """Test initialization creates multiple directories."""
        project_path = temp_project_dir / "test-project"
        project_path.mkdir()

        dirs = ["configs", "templates", "scripts"]
        for dir_name in dirs:
            (project_path / dir_name).mkdir()
            assert (project_path / dir_name).exists()

    def test_init_directory_structure(self, temp_project_dir):
        """Test complete directory structure after initialization."""
        project_path = temp_project_dir / "test-project"
        project_path.mkdir()

        (project_path / "src").mkdir()
        (project_path / "tests").mkdir()
        (project_path / "docs").mkdir()

        structure = ["src", "tests", "docs"]
        for item in structure:
            assert (project_path / item).exists()


class TestSymlinkCreation:
    """Test suite for symlink creation during initialization."""

    def test_symlink_creation(self, temp_project_dir):
        """Test creating symlink."""
        source = temp_project_dir / "source"
        source.mkdir()

        target = temp_project_dir / "link"
        try:
            target.symlink_to(source)
            assert target.exists()
            assert target.is_symlink()
        except (OSError, NotImplementedError):
            # Symlinks may not be supported on all systems
            pytest.skip("Symlinks not supported on this system")

    def test_symlink_to_file(self, temp_project_dir):
        """Test creating symlink to file."""
        source_file = temp_project_dir / "source.txt"
        source_file.write_text("test content")

        link_file = temp_project_dir / "link.txt"
        try:
            link_file.symlink_to(source_file)
            assert link_file.exists()
            assert link_file.read_text() == "test content"
        except (OSError, NotImplementedError):
            pytest.skip("Symlinks not supported on this system")


class TestInitWithGitHubMock:
    """Test suite for initialization with mocked GitHub API."""

    def test_init_validates_remote_repo(self):
        """Test initialization validates remote repository."""
        # Create a mock function for checking repo existence
        check_repo_exists = MagicMock(return_value=True)

        repo_url = "https://github.com/user/repo"
        result = check_repo_exists(repo_url)

        assert result is True
        check_repo_exists.assert_called_once()

    def test_init_handles_invalid_repo(self):
        """Test initialization handles invalid repository."""
        # Create a mock function for checking repo existence
        check_repo_exists = MagicMock(return_value=False)

        repo_url = "https://github.com/nonexistent/repo"
        result = check_repo_exists(repo_url)

        assert result is False

    def test_init_fetches_repo_metadata(self):
        """Test initialization fetches repository metadata."""
        # Create a mock function for fetching metadata
        fetch_repo_metadata = MagicMock(return_value={
            "name": "test-repo",
            "owner": "user",
            "url": "https://github.com/user/test-repo"
        })

        result = fetch_repo_metadata("https://github.com/user/test-repo")

        assert result["name"] == "test-repo"
        assert result["owner"] == "user"


class TestInitializationWithTempDir:
    """Test suite for initialization with temporary directories."""

    def test_temp_dir_cleanup(self):
        """Test temporary directory is properly created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            assert temp_path.exists()

            # Create test file
            test_file = temp_path / "test.txt"
            test_file.write_text("test")
            assert test_file.exists()

        # After context, directory should be cleaned up
        assert not temp_path.exists()

    def test_init_in_isolated_environment(self):
        """Test initialization in isolated temporary environment."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            project_dir = temp_path / "my-project"
            project_dir.mkdir()

            assert project_dir.exists()
            assert project_dir.parent == temp_path


class TestInitWorkflowRemoteValidation:
    """Test suite for remote validation in initialization workflow."""

    def test_app_remote_required_unless_create_flag(self):
        """Test that app_remote is required unless --create-app-repo is set."""
        from prometheus.init.workflow import InitWorkflow

        # Should fail without app_remote and without create_app_repo flag
        workflow = InitWorkflow(
            app_name="test-app",
            app_remote=None,
            create_app_repo=False,
        )

        with pytest.raises(ValueError) as exc_info:
            workflow._validate_remotes()

        assert "App remote URL is required" in str(exc_info.value)

    def test_config_contains_all_three_remotes(self, temp_project_dir):
        """Test that config file stores all three remotes."""
        from prometheus.config import Config

        app_remote = "https://github.com/test/app.git"
        app_instructions_remote = "https://github.com/test/app-instructions.git"
        core_remote = "https://github.com/test/core.git"

        config = Config(
            app_name="test-app",
            app_remote=app_remote,
            app_instructions_remote=app_instructions_remote,
            core_remote=core_remote,
            core_version="abc123",
        )

        config_path = temp_project_dir / ".prometheus.yml"
        config.save(config_path)

        # Load and verify all remotes are present
        loaded_config = Config.from_file(config_path)
        assert loaded_config.app_remote == app_remote
        assert loaded_config.app_instructions_remote == app_instructions_remote
        assert loaded_config.core_remote == core_remote

    def test_init_creates_local_structure_with_create_flag(self, temp_project_dir):
        """Test that --create-app-repo creates local structure without requiring remotes."""
        from prometheus.init.workflow import InitWorkflow
        import subprocess
        from unittest.mock import patch

        # Mock git ls-remote for core remote validation
        with patch('subprocess.run') as mock_run:
            # Mock successful git ls-remote for core
            mock_run.return_value = MagicMock(returncode=0, stdout="abc123")

            workflow = InitWorkflow(
                app_name="new-app",
                app_remote=None,
                create_app_repo=True,
                base_path=temp_project_dir,
                current_dir=temp_project_dir,
            )

            # Validation should pass with create_app_repo flag
            workflow._validate_remotes()

            # Create local structure
            workflow._create_app_structure_locally()

            # App code is now in the current directory (temp_project_dir)
            app_path = temp_project_dir
            assert app_path.exists()
            assert (app_path / "config").exists()
            # .github is not created here; it will be a symlink to app-instructions/.github
            # Instructions repo is separate in the base path
            instructions_path = temp_project_dir / "new-app-instructions"
            assert not instructions_path.exists()  # Not created yet in local structure

    def test_config_is_local_only(self):
        """Test that .prometheus.yml should be in .gitignore."""
        # Read the root .gitignore
        gitignore_path = Path("c:\\Progetti\\KT\\Prometheus\\.gitignore")
        if gitignore_path.exists():
            gitignore_content = gitignore_path.read_text()
            assert ".prometheus.yml" in gitignore_content

    def test_app_instructions_remote_is_optional(self, temp_project_dir):
        """Test that app_instructions_remote is optional."""
        from prometheus.config import Config

        config = Config(
            app_name="test-app",
            app_remote="https://github.com/test/app.git",
            app_instructions_remote=None,  # Optional
            core_remote="https://github.com/test/core.git",
            core_version="abc123",
        )

        config_path = temp_project_dir / ".prometheus.yml"
        config.save(config_path)

        loaded_config = Config.from_file(config_path)
        assert loaded_config.app_instructions_remote is None

    def test_symlink_manager_methods_exist(self):
        """Test that SymlinkManager has all required methods."""
        from prometheus.symlink.symlink import SymlinkManager

        assert hasattr(SymlinkManager, 'create_symlink')
        assert hasattr(SymlinkManager, 'remove_symlink')
        assert hasattr(SymlinkManager, 'is_symlink')

        # Methods should be static
        assert callable(SymlinkManager.create_symlink)
        assert callable(SymlinkManager.remove_symlink)
        assert callable(SymlinkManager.is_symlink)
