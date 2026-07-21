"""Tests for pull workflows."""

from prometheus.context import ExecutionContext
from prometheus.pull import pull_app


class TestPullApp:
    """Test suite for app pull orchestration."""

    def test_pulls_app_and_core(self, monkeypatch, tmp_path):
        app_root = tmp_path / "app"
        core_root = app_root / "prometheus-core"
        core_root.mkdir(parents=True)
        (app_root / ".prometheus.yml").write_text("app_name: app\n", encoding="utf-8")
        (core_root / ".git").mkdir()

        monkeypatch.setattr(
            "prometheus.pull.detect_context",
            lambda _: ExecutionContext("app", app_root, app_root / ".prometheus.yml", core_root),
        )

        responses = {
            (app_root, ("rev-parse", "HEAD")): ["app-before", "app-after"],
            (app_root, ("pull", "--ff-only")): ["Already up to date."],
            (app_root, ("submodule", "sync", "--recursive")): [""],
            (app_root, ("submodule", "update", "--init", "--remote", "--force")): [
                "Submodule path 'prometheus-core': checked out"
            ],
            (core_root, ("rev-parse", "HEAD")): ["core-before", "core-after"],
            (core_root, ("sparse-checkout", "init", "--no-cone")): [""],
            (core_root, ("sparse-checkout", "set", "/*", "!/tools/cli", "!/docs")): [""],
            (core_root, ("clean", "-ffd")): [""],
        }

        def fake_run_git(args, cwd, check=True):
            key = (cwd, tuple(args))
            values = responses[key]
            return values.pop(0)

        monkeypatch.setattr("prometheus.pull._run_git", fake_run_git)

        summary = pull_app(app_root)

        assert summary.app_before == "app-before"
        assert summary.app_after == "app-after"
        assert summary.core_before == "core-before"
        assert summary.core_after == "core-after"

    def test_pull_with_app_repo_changes(self, monkeypatch, tmp_path):
        """Test pull with changes in app repository."""
        app_root = tmp_path / "app"
        core_root = app_root / "prometheus-core"
        core_root.mkdir(parents=True)
        (app_root / ".prometheus.yml").write_text("app_name: app\n", encoding="utf-8")
        (core_root / ".git").mkdir()

        monkeypatch.setattr(
            "prometheus.pull.detect_context",
            lambda _: ExecutionContext("app", app_root, app_root / ".prometheus.yml", core_root),
        )

        responses = {
            (app_root, ("rev-parse", "HEAD")): ["abc1234", "def5678"],
            (app_root, ("pull", "--ff-only")): [
                "Updating abc1234..def5678\nFast-forward\n config/app.yml | 2 +-"
            ],
            (app_root, ("submodule", "sync", "--recursive")): [""],
            (app_root, ("submodule", "update", "--init", "--remote", "--force")): [
                "Submodule path 'prometheus-core': checked out"
            ],
            (core_root, ("rev-parse", "HEAD")): ["core-old", "core-new"],
            (core_root, ("sparse-checkout", "init", "--no-cone")): [""],
            (core_root, ("sparse-checkout", "set", "/*", "!/tools/cli", "!/docs")): [""],
            (core_root, ("clean", "-ffd")): [""],
        }

        def fake_run_git(args, cwd, check=True):
            key = (cwd, tuple(args))
            values = responses[key]
            return values.pop(0)

        monkeypatch.setattr("prometheus.pull._run_git", fake_run_git)

        summary = pull_app(app_root)

        assert summary.app_before == "abc1234"
        assert summary.app_after == "def5678"
        assert summary.app_before != summary.app_after

    def test_pull_with_core_submodule_updates(self, monkeypatch, tmp_path):
        """Test pull with changes in core submodule."""
        app_root = tmp_path / "app"
        core_root = app_root / "prometheus-core"
        core_root.mkdir(parents=True)
        (app_root / ".prometheus.yml").write_text("app_name: app\n", encoding="utf-8")
        (core_root / ".git").mkdir()

        monkeypatch.setattr(
            "prometheus.pull.detect_context",
            lambda _: ExecutionContext("app", app_root, app_root / ".prometheus.yml", core_root),
        )

        responses = {
            (app_root, ("rev-parse", "HEAD")): ["app-same", "app-same"],
            (app_root, ("pull", "--ff-only")): ["Already up to date."],
            (app_root, ("submodule", "sync", "--recursive")): [""],
            (app_root, ("submodule", "update", "--init", "--remote", "--force")): [
                "Submodule path 'prometheus-core': updated from core-old to core-new"
            ],
            (core_root, ("rev-parse", "HEAD")): ["core-old", "core-new"],
            (core_root, ("sparse-checkout", "init", "--no-cone")): [""],
            (core_root, ("sparse-checkout", "set", "/*", "!/tools/cli", "!/docs")): [""],
            (core_root, ("clean", "-ffd")): [""],
        }

        def fake_run_git(args, cwd, check=True):
            key = (cwd, tuple(args))
            values = responses[key]
            return values.pop(0)

        monkeypatch.setattr("prometheus.pull._run_git", fake_run_git)

        summary = pull_app(app_root)

        assert summary.app_before == "app-same"
        assert summary.app_after == "app-same"
        assert summary.core_before == "core-old"
        assert summary.core_after == "core-new"
        assert summary.core_before != summary.core_after

    def test_pull_outside_app_repo_raises_error(self, monkeypatch, tmp_path):
        """Test that pull fails when not in app context."""
        monkeypatch.setattr(
            "prometheus.pull.detect_context",
            lambda _: ExecutionContext("unknown", tmp_path, None, None),
        )

        try:
            pull_app(tmp_path)
            assert False, "Expected RuntimeError"
        except RuntimeError as e:
            assert "pull workflow only works inside an app repository" in str(e)
