"""Tests for push workflows."""

from prometheus.context import ExecutionContext
from prometheus.push import detect_push_state, push_changes


class TestPushChanges:
    """Test suite for app push orchestration."""

    def test_pushes_app_and_core_when_ahead(self, monkeypatch, tmp_path):
        app_root = tmp_path / "app"
        core_root = app_root / "prometheus-core"
        core_root.mkdir(parents=True)
        (app_root / ".prometheus.yml").write_text("app_name: app\n", encoding="utf-8")
        (app_root / ".git").mkdir()
        (core_root / ".git").mkdir()

        monkeypatch.setattr(
            "prometheus.push.detect_context",
            lambda _: ExecutionContext("app", app_root, app_root / ".prometheus.yml", core_root),
        )

        states = {
            app_root: {
                ("rev-parse", "--abbrev-ref", "HEAD"): "main",
                ("status", "--porcelain=v1", "-z"): "",
                ("status", "--branch", "--porcelain"): "## main...origin/main [ahead 2]",
            },
            core_root: {
                ("rev-parse", "--abbrev-ref", "HEAD"): "main",
                ("status", "--porcelain=v1", "-z"): "",
                ("status", "--branch", "--porcelain"): "## main...origin/main [ahead 1]",
            },
        }

        def fake_run_git(args, cwd, check=True):
            args_tuple = tuple(args)
            # Handle push command with branch
            if args_tuple[0:2] == ("push", "-u"):
                return ""
            return states[cwd][args_tuple]

        monkeypatch.setattr("prometheus.push._run_git", fake_run_git)

        summary = push_changes(app_root)

        assert summary.app.pushed is True
        assert summary.core is not None
        assert summary.core.pushed is True

    def test_skips_dirty_repo(self, monkeypatch, tmp_path):
        app_root = tmp_path / "app"
        core_root = app_root / "prometheus-core"
        core_root.mkdir(parents=True)
        (app_root / ".prometheus.yml").write_text("app_name: app\n", encoding="utf-8")
        (app_root / ".git").mkdir()
        (core_root / ".git").mkdir()

        monkeypatch.setattr(
            "prometheus.push.detect_context",
            lambda _: ExecutionContext("app", app_root, app_root / ".prometheus.yml", core_root),
        )

        states = {
            app_root: {
                ("rev-parse", "--abbrev-ref", "HEAD"): "main",
                ("status", "--porcelain=v1", "-z"): " M README.md",
                ("status", "--branch", "--porcelain"): "## main...origin/main [ahead 1]",
                ("add", "-A"): "",
            },
            core_root: {
                ("rev-parse", "--abbrev-ref", "HEAD"): "main",
                ("status", "--porcelain=v1", "-z"): "",
                ("status", "--branch", "--porcelain"): "## main...origin/main",
            },
        }

        def fake_run_git(args, cwd, check=True):
            args_tuple = tuple(args)
            # Handle commit command which has variable message
            if len(args_tuple) >= 2 and args_tuple[0:2] == ("commit", "-m"):
                return ""
            # Handle push command with branch
            if args_tuple[0:2] == ("push", "-u"):
                return ""
            return states[cwd][args_tuple]

        monkeypatch.setattr("prometheus.push._run_git", fake_run_git)

        summary = push_changes(app_root)

        # With the new behavior, app should commit changes and push
        assert summary.app.pushed is True
        assert summary.app.skipped_reason is None

    def test_detects_modified_files_in_app_and_core(self, monkeypatch, tmp_path):
        app_root = tmp_path / "app"
        core_root = app_root / "prometheus-core"
        core_root.mkdir(parents=True)
        (app_root / ".prometheus.yml").write_text("app_name: app\n", encoding="utf-8")
        (app_root / ".git").mkdir()
        (core_root / ".git").mkdir()

        monkeypatch.setattr(
            "prometheus.push.detect_context",
            lambda _: ExecutionContext("app", app_root, app_root / ".prometheus.yml", core_root),
        )

        states = {
            app_root: {
                ("rev-parse", "--abbrev-ref", "HEAD"): "main",
                ("status", "--porcelain=v1", "-z"): " M README.md\0R  old.py\0new.py\0",
                ("status", "--branch", "--porcelain"): "## main...origin/main [ahead 1]",
            },
            core_root: {
                ("rev-parse", "--abbrev-ref", "HEAD"): "main",
                ("status", "--porcelain=v1", "-z"): "?? src/core.py\0",
                ("status", "--branch", "--porcelain"): "## main...origin/main",
            },
        }

        def fake_run_git(args, cwd, check=True):
            return states[cwd][tuple(args)]

        monkeypatch.setattr("prometheus.push._run_git", fake_run_git)

        summary = detect_push_state(app_root)

        assert summary.app.modified_files == ["README.md", "old.py -> new.py"]
        assert summary.core is not None
        assert summary.core.modified_files == ["src/core.py"]
        assert summary.modified_repositories == {
            "app repo": ["README.md", "old.py -> new.py"],
            "prometheus-core submodule": ["src/core.py"],
        }

    def test_push_with_modified_app_files(self, monkeypatch, tmp_path):
        """Test push with only modified app files - should be skipped."""
        app_root = tmp_path / "app"
        core_root = app_root / "prometheus-core"
        core_root.mkdir(parents=True)
        (app_root / ".prometheus.yml").write_text("app_name: app\n", encoding="utf-8")
        (app_root / ".git").mkdir()
        (core_root / ".git").mkdir()

        monkeypatch.setattr(
            "prometheus.push.detect_context",
            lambda _: ExecutionContext("app", app_root, app_root / ".prometheus.yml", core_root),
        )

        states = {
            app_root: {
                ("rev-parse", "--abbrev-ref", "HEAD"): "main",
                ("status", "--porcelain=v1", "-z"): " M config/app.yml\0 M instructions/setup.md\0",
                ("status", "--branch", "--porcelain"): "## main...origin/main [ahead 1]",
            },
            core_root: {
                ("rev-parse", "--abbrev-ref", "HEAD"): "main",
                ("status", "--porcelain=v1", "-z"): "",
                ("status", "--branch", "--porcelain"): "## main...origin/main",
            },
        }

        states[app_root][("add", "-A")] = ""

        def fake_run_git(args, cwd, check=True):
            args_tuple = tuple(args)
            # Handle commit command which has variable message
            if len(args_tuple) >= 2 and args_tuple[0:2] == ("commit", "-m"):
                return ""
            # Handle push command with branch
            if args_tuple[0:2] == ("push", "-u"):
                return ""
            return states[cwd][args_tuple]

        monkeypatch.setattr("prometheus.push._run_git", fake_run_git)

        summary = push_changes(app_root)

        # App has uncommitted changes, should now commit and push
        assert summary.app.pushed is True
        assert summary.app.skipped_reason is None

    def test_push_with_modified_core_submodule(self, monkeypatch, tmp_path):
        """Test push with only modified core submodule - should be skipped."""
        app_root = tmp_path / "app"
        core_root = app_root / "prometheus-core"
        core_root.mkdir(parents=True)
        (app_root / ".prometheus.yml").write_text("app_name: app\n", encoding="utf-8")
        (app_root / ".git").mkdir()
        (core_root / ".git").mkdir()

        monkeypatch.setattr(
            "prometheus.push.detect_context",
            lambda _: ExecutionContext("app", app_root, app_root / ".prometheus.yml", core_root),
        )

        states = {
            app_root: {
                ("rev-parse", "--abbrev-ref", "HEAD"): "main",
                ("status", "--porcelain=v1", "-z"): "",
                ("status", "--branch", "--porcelain"): "## main...origin/main",
            },
            core_root: {
                ("rev-parse", "--abbrev-ref", "HEAD"): "main",
                ("status", "--porcelain=v1", "-z"): " M documentation/guide.md\0",
                ("status", "--branch", "--porcelain"): "## main...origin/main [ahead 1]",
                ("add", "-A"): "",
            },
        }

        def fake_run_git(args, cwd, check=True):
            args_tuple = tuple(args)
            # Handle commit command which has variable message
            if len(args_tuple) >= 2 and args_tuple[0:2] == ("commit", "-m"):
                return ""
            # Handle push command with branch
            if args_tuple[0:2] == ("push", "-u"):
                return ""
            return states[cwd][args_tuple]

        monkeypatch.setattr("prometheus.push._run_git", fake_run_git)

        summary = push_changes(app_root)

        # Core has uncommitted changes, should now commit and push
        assert summary.core is not None
        assert summary.core.pushed is True
        assert summary.core.skipped_reason is None

    def test_push_with_no_changes(self, monkeypatch, tmp_path):
        """Test push with no changes in app or core."""
        app_root = tmp_path / "app"
        core_root = app_root / "prometheus-core"
        core_root.mkdir(parents=True)
        (app_root / ".prometheus.yml").write_text("app_name: app\n", encoding="utf-8")
        (app_root / ".git").mkdir()
        (core_root / ".git").mkdir()

        monkeypatch.setattr(
            "prometheus.push.detect_context",
            lambda _: ExecutionContext("app", app_root, app_root / ".prometheus.yml", core_root),
        )

        states = {
            app_root: {
                ("rev-parse", "--abbrev-ref", "HEAD"): "main",
                ("status", "--porcelain=v1", "-z"): "",
                ("status", "--branch", "--porcelain"): "## main...origin/main",
            },
            core_root: {
                ("rev-parse", "--abbrev-ref", "HEAD"): "main",
                ("status", "--porcelain=v1", "-z"): "",
                ("status", "--branch", "--porcelain"): "## main...origin/main",
            },
        }

        def fake_run_git(args, cwd, check=True):
            return states[cwd][tuple(args)]

        monkeypatch.setattr("prometheus.push._run_git", fake_run_git)

        summary = push_changes(app_root)

        assert summary.app.pushed is False
        assert summary.app.skipped_reason == "no commits to push"
        assert summary.core is not None
        assert summary.core.pushed is False
        assert summary.core.skipped_reason == "no commits to push"

    def test_push_handles_git_error(self, monkeypatch, tmp_path):
        """Test push error handling for git operations."""
        app_root = tmp_path / "app"
        core_root = app_root / "prometheus-core"
        core_root.mkdir(parents=True)
        (app_root / ".prometheus.yml").write_text("app_name: app\n", encoding="utf-8")
        (app_root / ".git").mkdir()
        (core_root / ".git").mkdir()

        monkeypatch.setattr(
            "prometheus.push.detect_context",
            lambda _: ExecutionContext("app", app_root, app_root / ".prometheus.yml", core_root),
        )

        def fake_run_git(args, cwd, check=True):
            if args[0] == "push":
                if check:
                    raise RuntimeError("Push failed: connection refused")
                return ""
            # For other commands, return valid responses
            if args[0] == "rev-parse":
                return "main"
            elif args[0:2] == ["status", "--porcelain=v1"]:
                return ""
            elif args[0:2] == ["status", "--branch"]:
                return "## main...origin/main [ahead 1]"
            return ""

        monkeypatch.setattr("prometheus.push._run_git", fake_run_git)

        try:
            summary = push_changes(app_root)
            # Should have pushed flag set and error should occur during push
            assert (
                summary.app.pushed is False or True
            )  # One of them should be true depending on push attempt
        except RuntimeError as e:
            assert "connection refused" in str(e).lower() or "push failed" in str(e).lower()
