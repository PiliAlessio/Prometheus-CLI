"""Tests for CLI commands."""

import pytest
from prometheus.cli.commands import cli, init, help as help_cmd, version
from prometheus.init.workflow import InitResult


class TestInitCommand:
    """Test suite for the init command."""

    def test_init_basic(self, cli_runner, monkeypatch, tmp_path):
        """Test basic init command with required flags."""
        init_result = InitResult(
            app_path=tmp_path / "my-app",
            config_path=tmp_path / "my-app" / ".prometheus.yml",
            app_remote="https://github.com/user/my-app.git",
            app_instructions_remote=None,
            core_remote="https://github.com/PiliAlessio/Prometheus.git",
            core_version="abc123",
            symlink_created=True,
        )
        monkeypatch.setattr("prometheus.cli.commands.InitWorkflow.run", lambda self: init_result)

        result = cli_runner.invoke(cli, ["init", "--app-name", "my-app"])
        assert result.exit_code == 0
        assert "Initialized Prometheus app: my-app" in result.output or "my-app" in result.output
        assert "Core version: abc123" in result.output
        assert "Setup complete" in result.output

    def test_init_reports_errors(self, cli_runner, monkeypatch):
        """Test init surfaces workflow errors cleanly."""
        monkeypatch.setattr(
            "prometheus.cli.commands.InitWorkflow.run",
            lambda self: (_ for _ in ()).throw(FileExistsError("already exists")),
        )

        result = cli_runner.invoke(cli, ["init", "--app-name", "my-app"])

        assert result.exit_code != 0
        assert "already exists" in result.output

    def test_init_missing_project_name(self, cli_runner):
        """Test init command without required app-name flag."""
        result = cli_runner.invoke(cli, ["init"])
        assert result.exit_code != 0
        assert "Missing option '--app-name'" in result.output

    def test_init_help_flag(self, cli_runner):
        """Test --help flag on init subcommand."""
        result = cli_runner.invoke(cli, ["init", "--help"])
        assert result.exit_code == 0
        assert "--app-name" in result.output


class TestHelpCommand:
    """Test suite for the help command."""

    def test_help_command(self, cli_runner):
        """Test help command displays information."""
        result = cli_runner.invoke(cli, ["help"])
        assert result.exit_code == 0
        assert "Prometheus" in result.output
        assert "Available Commands:" in result.output
        assert "init" in result.output
        assert "version" in result.output

    def test_help_shows_commands(self, cli_runner):
        """Test help command lists all commands."""
        result = cli_runner.invoke(cli, ["help"])
        assert "init       Initialize a new Prometheus app repository" in result.output
        assert "update     Pull the app repo and sync prometheus-core" in result.output
        assert "help       Show this help message" in result.output
        assert "version    Show version information" in result.output


class TestVersionCommand:
    """Test suite for the version command."""

    def test_version_command(self, cli_runner):
        """Test version command displays version."""
        result = cli_runner.invoke(cli, ["version"])
        assert result.exit_code == 0
        assert "Prometheus v" in result.output

    def test_version_format(self, cli_runner):
        """Test version output format is correct."""
        result = cli_runner.invoke(cli, ["version"])
        # Should match pattern like "Prometheus v0.1.0"
        assert "v0.1" in result.output or "Prometheus" in result.output


class TestGlobalFlags:
    """Test suite for global CLI flags."""

    def test_version_global_flag(self, cli_runner):
        """Test --version global flag."""
        result = cli_runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "Prometheus" in result.output or "0.1" in result.output

    def test_help_flag(self, cli_runner):
        """Test --help flag on main command."""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Commands:" in result.output or "Commands" in result.output or "Usage" in result.output

    def test_push_command(self, cli_runner, monkeypatch, tmp_path):
        """Test push command."""
        class State:
            def __init__(self, name, pushed):
                self.name = name
                self.pushed = pushed
                self.skipped_reason = None if pushed else "no commits to push"
                self.branch = "main"
                self.modified_files = []

        class Summary:
            def __init__(self):
                self.app = State("app repo", True)
                self.core = State("prometheus-core submodule", False)

        monkeypatch.setattr("prometheus.cli.commands.push_changes", lambda _: Summary())

        result = cli_runner.invoke(cli, ["push"])

        assert result.exit_code == 0
        assert "Push summary:" in result.output
        assert "app repo: pushed" in result.output

    def test_invalid_command(self, cli_runner):
        """Test invalid command returns error."""
        result = cli_runner.invoke(cli, ["invalid-command"])
        assert result.exit_code != 0
        assert "No such command" in result.output or "Error" in result.output or "invalid" in result.output.lower()


class TestUpdateCommand:
    """Test suite for the update command."""

    def test_update_command(self, cli_runner, monkeypatch, tmp_path):
        """Test update command output."""
        class Summary:
            app_path = tmp_path / "my-app"
            app_before = "before-app"
            app_after = "after-app"
            core_before = "before-core"
            core_after = "after-core"

        monkeypatch.setattr("prometheus.cli.commands.update_app", lambda _: Summary())

        result = cli_runner.invoke(cli, ["update"])

        assert result.exit_code == 0
        assert "Updated app repo" in result.output
        assert "before-app -> after-app" in result.output
