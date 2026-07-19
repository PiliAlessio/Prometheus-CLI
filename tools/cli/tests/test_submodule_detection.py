"""Tests for submodule detection helpers."""

from prometheus.submodule.detection import SubmoduleDetector


class TestSubmoduleDetector:
    """Test suite for submodule detection."""

    def test_has_submodules(self, monkeypatch, tmp_path):
        repo_root = tmp_path / "app"
        repo_root.mkdir()
        (repo_root / ".gitmodules").write_text("[submodule]\n", encoding="utf-8")

        monkeypatch.setattr(
            "prometheus.submodule.detection._run_git",
            lambda args, cwd, check=False: " abc123 prometheus-core (heads/main)",
        )

        assert SubmoduleDetector.has_submodules(repo_root) is True

    def test_lists_submodules(self, monkeypatch, tmp_path):
        repo_root = tmp_path / "app"
        repo_root.mkdir()

        monkeypatch.setattr(
            "prometheus.submodule.detection._run_git",
            lambda args, cwd, check=False: (
                " abc123 prometheus-core (heads/main)\n"
                "-def456 vendor/shared-lib (heads/main)"
            ),
        )

        submodules = SubmoduleDetector.list_submodules(repo_root)

        assert len(submodules) == 2
        assert submodules[0].name == "prometheus-core"
        assert submodules[0].commit_sha == "abc123"
        assert submodules[0].initialized is True
        assert submodules[1].name == "shared-lib"
        assert submodules[1].initialized is False

    def test_get_core_submodule_status(self, monkeypatch, tmp_path):
        repo_root = tmp_path / "app"
        core_root = repo_root / "prometheus-core"
        core_root.mkdir(parents=True)
        (repo_root / ".prometheus.yml").write_text(
            "app_name: app\ncore_version: recorded-sha\n",
            encoding="utf-8",
        )

        responses = {
            (core_root.resolve(), ("rev-parse", "HEAD")): "current-sha",
            (core_root.resolve(), ("rev-parse", "--abbrev-ref", "HEAD")): "main",
            (
                core_root.resolve(),
                ("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"),
            ): "origin/main",
            (core_root.resolve(), ("ls-remote", "origin", "refs/heads/main")): "remote-sha\trefs/heads/main",
        }

        def fake_run_git(args, cwd, check=False):
            return responses[(cwd.resolve(), tuple(args))]

        monkeypatch.setattr("prometheus.submodule.detection._run_git", fake_run_git)

        status = SubmoduleDetector.get_core_submodule_status(repo_root)

        assert status.exists is True
        assert status.current_commit == "current-sha"
        assert status.remote_commit == "remote-sha"
        assert status.recorded_commit == "recorded-sha"
        assert status.update_needed is True
        assert status.version_changed is True

    def test_get_core_submodule_status_handles_missing_submodule(self, tmp_path):
        repo_root = tmp_path / "app"
        repo_root.mkdir()

        status = SubmoduleDetector.get_core_submodule_status(repo_root)

        assert status.exists is False
        assert status.error is not None
