"""Tests for execution context detection."""

from prometheus.context import detect_context


class TestDetectContext:
    """Test suite for CLI context detection."""

    def test_detects_app_repo(self, tmp_path):
        app_root = tmp_path / "my-app"
        app_root.mkdir()
        (app_root / ".prometheus.yml").write_text("app_name: my-app\n", encoding="utf-8")
        nested = app_root / "src"
        nested.mkdir()

        context = detect_context(nested)

        assert context.context_type == "app"
        assert context.root_path == app_root
        assert context.config_path == app_root / ".prometheus.yml"

    def test_detects_prometheus_repo(self, tmp_path):
        repo_root = tmp_path / "Prometheus"
        (repo_root / "core").mkdir(parents=True)
        (repo_root / "tools" / "cli").mkdir(parents=True)

        context = detect_context(repo_root / "tools")

        assert context.context_type == "prometheus"
        assert context.root_path == repo_root

    def test_returns_unknown_for_other_paths(self, tmp_path):
        context = detect_context(tmp_path)
        assert context.context_type == "unknown"
