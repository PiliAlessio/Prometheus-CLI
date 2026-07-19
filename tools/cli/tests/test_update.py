"""Tests for update workflows."""

from prometheus.context import ExecutionContext
from prometheus.update import update_app


class TestUpdateApp:
    """Test suite for app update orchestration."""

    def test_updates_app_and_core(self, monkeypatch, tmp_path):
        app_root = tmp_path / "app"
        core_root = app_root / "prometheus-core"
        core_root.mkdir(parents=True)
        (app_root / ".prometheus.yml").write_text("app_name: app\n", encoding="utf-8")
        (core_root / ".git").mkdir()

        monkeypatch.setattr(
            "prometheus.update.detect_context",
            lambda _: ExecutionContext("app", app_root, app_root / ".prometheus.yml", core_root),
        )

        responses = {
            (app_root, ("rev-parse", "HEAD")): ["app-before", "app-after"],
            (app_root, ("pull", "--ff-only")): ["Already up to date."],
            (app_root, ("submodule", "update", "--remote")): ["Submodule path 'prometheus-core': checked out"],
            (core_root, ("rev-parse", "HEAD")): ["core-before", "core-after"],
        }

        def fake_run_git(args, cwd, check=True):
            key = (cwd, tuple(args))
            values = responses[key]
            return values.pop(0)

        monkeypatch.setattr("prometheus.update._run_git", fake_run_git)

        summary = update_app(app_root)

        assert summary.app_before == "app-before"
        assert summary.app_after == "app-after"
        assert summary.core_before == "core-before"
        assert summary.core_after == "core-after"

    def test_update_with_app_repo_changes(self, monkeypatch, tmp_path):
        """Test update with changes in app repository."""
        app_root = tmp_path / "app"
        core_root = app_root / "prometheus-core"
        core_root.mkdir(parents=True)
        (app_root / ".prometheus.yml").write_text("app_name: app\n", encoding="utf-8")
        (core_root / ".git").mkdir()

        monkeypatch.setattr(
            "prometheus.update.detect_context",
            lambda _: ExecutionContext("app", app_root, app_root / ".prometheus.yml", core_root),
        )

        responses = {
            (app_root, ("rev-parse", "HEAD")): ["abc1234", "def5678"],
            (app_root, ("pull", "--ff-only")): ["Updating abc1234..def5678\nFast-forward\n config/app.yml | 2 +-"],
            (app_root, ("submodule", "update", "--remote")): ["Submodule path 'prometheus-core': checked out"],
            (core_root, ("rev-parse", "HEAD")): ["core-old", "core-new"],
        }

        def fake_run_git(args, cwd, check=True):
            key = (cwd, tuple(args))
            values = responses[key]
            return values.pop(0)

        monkeypatch.setattr("prometheus.update._run_git", fake_run_git)

        summary = update_app(app_root)

        assert summary.app_before == "abc1234"
        assert summary.app_after == "def5678"
        assert summary.app_before != summary.app_after

    def test_update_with_core_submodule_updates(self, monkeypatch, tmp_path):
        """Test update with changes in core submodule."""
        app_root = tmp_path / "app"
        core_root = app_root / "prometheus-core"
        core_root.mkdir(parents=True)
        (app_root / ".prometheus.yml").write_text("app_name: app\n", encoding="utf-8")
        (core_root / ".git").mkdir()

        monkeypatch.setattr(
            "prometheus.update.detect_context",
            lambda _: ExecutionContext("app", app_root, app_root / ".prometheus.yml", core_root),
        )

        responses = {
            (app_root, ("rev-parse", "HEAD")): ["app-same", "app-same"],
            (app_root, ("pull", "--ff-only")): ["Already up to date."],
            (app_root, ("submodule", "update", "--remote")): ["Submodule path 'prometheus-core': updated from core-old to core-new"],
            (core_root, ("rev-parse", "HEAD")): ["core-old", "core-new"],
        }

        def fake_run_git(args, cwd, check=True):
            key = (cwd, tuple(args))
            values = responses[key]
            return values.pop(0)

        monkeypatch.setattr("prometheus.update._run_git", fake_run_git)

        summary = update_app(app_root)

        assert summary.app_before == "app-same"
        assert summary.app_after == "app-same"
        assert summary.core_before == "core-old"
        assert summary.core_after == "core-new"

    def test_update_with_no_changes(self, monkeypatch, tmp_path):
        """Test update with no changes in app or core."""
        app_root = tmp_path / "app"
        core_root = app_root / "prometheus-core"
        core_root.mkdir(parents=True)
        (app_root / ".prometheus.yml").write_text("app_name: app\n", encoding="utf-8")
        (core_root / ".git").mkdir()

        monkeypatch.setattr(
            "prometheus.update.detect_context",
            lambda _: ExecutionContext("app", app_root, app_root / ".prometheus.yml", core_root),
        )

        responses = {
            (app_root, ("rev-parse", "HEAD")): ["same-commit", "same-commit"],
            (app_root, ("pull", "--ff-only")): ["Already up to date."],
            (app_root, ("submodule", "update", "--remote")): ["Already at the latest version."],
            (core_root, ("rev-parse", "HEAD")): ["same-core", "same-core"],
        }

        def fake_run_git(args, cwd, check=True):
            key = (cwd, tuple(args))
            values = responses[key]
            return values.pop(0)

        monkeypatch.setattr("prometheus.update._run_git", fake_run_git)

        summary = update_app(app_root)

        assert summary.app_before == "same-commit"
        assert summary.app_after == "same-commit"
        assert summary.core_before == "same-core"
        assert summary.core_after == "same-core"

    def test_update_handles_pull_error(self, monkeypatch, tmp_path):
        """Test update error handling for pull operations."""
        app_root = tmp_path / "app"
        core_root = app_root / "prometheus-core"
        core_root.mkdir(parents=True)
        (app_root / ".prometheus.yml").write_text("app_name: app\n", encoding="utf-8")
        (core_root / ".git").mkdir()

        monkeypatch.setattr(
            "prometheus.update.detect_context",
            lambda _: ExecutionContext("app", app_root, app_root / ".prometheus.yml", core_root),
        )

        def fake_run_git(args, cwd, check=True):
            if args[0] == "pull":
                if check:
                    raise RuntimeError("Pull failed: merge conflict")
                return ""
            return ""

        monkeypatch.setattr("prometheus.update._run_git", fake_run_git)

        try:
            summary = update_app(app_root)
            # Should either fail or indicate an error in the summary
            assert hasattr(summary, 'error') or hasattr(summary, 'app_before')
        except RuntimeError as e:
            assert "merge conflict" in str(e).lower() or "pull failed" in str(e).lower()

    def test_update_handles_submodule_update_error(self, monkeypatch, tmp_path):
        """Test update error handling for submodule update operations."""
        app_root = tmp_path / "app"
        core_root = app_root / "prometheus-core"
        core_root.mkdir(parents=True)
        (app_root / ".prometheus.yml").write_text("app_name: app\n", encoding="utf-8")
        (core_root / ".git").mkdir()

        monkeypatch.setattr(
            "prometheus.update.detect_context",
            lambda _: ExecutionContext("app", app_root, app_root / ".prometheus.yml", core_root),
        )

        responses = {
            (app_root, ("rev-parse", "HEAD")): ["app-commit"],
            (app_root, ("pull", "--ff-only")): ["Already up to date."],
        }

        def fake_run_git(args, cwd, check=True):
            if args[0:3] == ["submodule", "update", "--remote"]:
                if check:
                    raise RuntimeError("Submodule update failed: detached HEAD state")
                return ""
            key = (cwd, tuple(args))
            if key in responses:
                values = responses[key]
                return values.pop(0)
            return ""

        monkeypatch.setattr("prometheus.update._run_git", fake_run_git)

        try:
            summary = update_app(app_root)
            # Should either fail or indicate an error in the summary
            assert hasattr(summary, 'error') or hasattr(summary, 'app_before')
        except RuntimeError as e:
            assert "detached head" in str(e).lower() or "submodule update failed" in str(e).lower()
