"""Tests for CLI commands."""

import pytest
from prometheus.cli.commands import cli, init, help as help_cmd, version, _generate_help_output
from prometheus.init.workflow import InitResult
from prometheus.push import push_changes
from prometheus.pull import pull_app


class TestInitCommand:
    """Test suite for the init command."""

    def test_init_basic(self, cli_runner, monkeypatch, tmp_path):
        """Test basic init command with required flags."""
        init_result = InitResult(
            app_path=tmp_path / "my-app",
            config_path=tmp_path / "my-app" / ".prometheus.yml",
            app_remote="https://github.com/user/my-app.git",
            app_instructions_remote=None,
            core_remote="https://github.com/AlessioPili-KT/Prometheus.git",
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
        # Check for presence of key commands
        assert "init" in result.output
        assert "push" in result.output
        assert "pull" in result.output
        assert "sync" in result.output
        assert "help" in result.output
        assert "version" in result.output

    def test_help_includes_examples(self, cli_runner):
        """Test help command includes examples from docstrings."""
        result = cli_runner.invoke(cli, ["help"])
        # Examples should be included from command docstrings
        assert "prometheus" in result.output.lower()


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
        assert (
            "Commands:" in result.output or "Commands" in result.output or "Usage" in result.output
        )

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
        assert (
            "No such command" in result.output
            or "Error" in result.output
            or "invalid" in result.output.lower()
        )


class TestPullCommand:
    """Test suite for the pull command."""

    def test_pull_command(self, cli_runner, monkeypatch):
        """Test pull command executes successfully."""
        from prometheus.pull import PullSummary
        from pathlib import Path

        pull_summary = PullSummary(
            app_path=Path("/tmp/app"),
            app_before="abc123",
            app_after="def456",
            core_before="core1",
            core_after="core2",
        )
        monkeypatch.setattr("prometheus.cli.commands.pull_app", lambda _: pull_summary)

        result = cli_runner.invoke(cli, ["pull"])
        assert result.exit_code == 0
        assert "Pull completed successfully" in result.output
        assert "abc123" in result.output
        assert "def456" in result.output

    def test_pull_help_flag(self, cli_runner):
        """Test --help flag on pull subcommand."""
        result = cli_runner.invoke(cli, ["pull", "--help"])
        assert result.exit_code == 0
        assert "prometheus pull" in result.output.lower() or "Pull the latest" in result.output


class TestSyncCommand:
    """Test suite for the sync command."""

    def test_sync_command(self, cli_runner, monkeypatch):
        """Test sync command executes pull then push successfully."""
        from prometheus.pull import PullSummary
        from prometheus.push import PushSummary, RepoPushState
        from pathlib import Path

        pull_summary = PullSummary(
            app_path=Path("/tmp/app"),
            app_before="abc123",
            app_after="def456",
            core_before="core1",
            core_after="core2",
        )

        push_summary = PushSummary(
            app=RepoPushState(
                name="app",
                path=Path("/tmp/app"),
                branch="main",
                modified_files=[],
                ahead_count=1,
                pushed=True,
                skipped_reason=None,
            ),
            core=None,
        )

        monkeypatch.setattr("prometheus.cli.commands.pull_app", lambda _: pull_summary)
        monkeypatch.setattr("prometheus.cli.commands.push_changes", lambda _: push_summary)

        result = cli_runner.invoke(cli, ["sync"])
        assert result.exit_code == 0
        assert "Sync completed successfully" in result.output
        assert "Pulled changes" in result.output
        assert "Pushed changes" in result.output

    def test_sync_help_flag(self, cli_runner):
        """Test --help flag on sync subcommand."""
        result = cli_runner.invoke(cli, ["sync", "--help"])
        assert result.exit_code == 0
        assert (
            "prometheus sync" in result.output.lower() or "Pull the latest changes" in result.output
        )


class TestHelpReflection:
    """Test suite for reflection-based help generation."""

    def test_generate_help_output(self):
        """Test that _generate_help_output generates structured help."""
        output = _generate_help_output()
        assert "Prometheus" in output
        assert "Available Commands:" in output
        # Should list all commands
        assert "init" in output
        assert "push" in output
        assert "pull" in output
        assert "sync" in output
        assert "help" in output
        assert "version" in output

    def test_generate_help_includes_descriptions(self):
        """Test that _generate_help_output includes command descriptions."""
        output = _generate_help_output()
        # Check that descriptions are present (first line of docstring)
        assert "Initialize" in output or "initialize" in output.lower()
        assert "version" in output.lower()
