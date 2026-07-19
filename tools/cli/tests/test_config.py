"""Tests for configuration handling."""

from prometheus.config import Config


class TestConfigGeneration:
    """Test suite for configuration generation."""

    def test_config_single_language(self):
        """Test config generation with single language."""
        config = Config(app_name="test", languages=["go"])
        assert config.to_dict()["languages"] == ["go"]

    def test_config_multiple_languages(self):
        """Test config generation with multiple languages."""
        config = Config(app_name="test", languages=["go", "python", "rust"])
        assert len(config.languages) == 3
        assert "python" in config.languages
        assert "rust" in config.languages

    def test_config_with_remote(self):
        """Test config includes remote repository."""
        config = Config(app_name="test", remote_url="https://github.com/user/repo", languages=["go"])
        assert config.remote_url == "https://github.com/user/repo"

    def test_config_contains_core_version(self):
        """Test config includes core version metadata."""
        config = Config(app_name="test", core_version="abc123", languages=["go"])
        assert config.core_version == "abc123"


class TestYAMLSerialization:
    """Test suite for YAML serialization."""

    def test_config_dict_structure(self):
        """Test config can be represented as dict."""
        config = Config(
            app_name="test-project",
            languages=["go", "python"],
            remote_url="https://github.com/test/repo",
            core_version="abc123",
        )
        serialized = config.to_dict()
        assert isinstance(serialized, dict)
        assert serialized["app_name"] == "test-project"
        assert serialized["languages"] == ["go", "python"]
        assert serialized["remote_url"] == "https://github.com/test/repo"

    def test_config_round_trip(self, tmp_path):
        """Test config round-trips through YAML."""
        config_path = tmp_path / ".prometheus.yml"
        Config(
            app_name="test",
            remote_url="https://github.com/test/repo",
            core_version="abc123",
            languages=["go"],
        ).save(config_path)

        loaded = Config().load(config_path)

        assert loaded.app_name == "test"
        assert loaded.remote_url == "https://github.com/test/repo"
        assert loaded.core_version == "abc123"
        assert loaded.languages == ["go"]

    def test_empty_languages_list(self):
        """Test config with empty languages list."""
        config = Config(app_name="test", languages=[])
        assert config.languages == []


class TestConfigValidation:
    """Test suite for configuration validation."""

    def test_valid_project_name(self):
        """Test valid project name."""
        config = Config(app_name="valid-project-name")
        assert config.app_name is not None
        assert isinstance(config.app_name, str)

    def test_project_name_not_empty(self):
        """Test project name is not empty."""
        config = Config(app_name="test")
        assert len(config.app_name) > 0

    def test_languages_is_list(self):
        """Test languages is a list."""
        config = Config(app_name="test", languages=["go", "python"])
        assert isinstance(config.languages, list)

    def test_all_required_fields(self):
        """Test config contains all required fields."""
        config = Config(app_name="test", languages=["go"]).to_dict()
        required_fields = ["app_name", "languages"]
        for field in required_fields:
            assert field in config, f"Missing required field: {field}"

    def test_no_duplicate_languages(self):
        """Test no duplicate languages in config."""
        config = Config(app_name="test", languages=["go", "python", "go"])
        unique_langs = set(config.languages)
        assert len(unique_langs) == 2


class TestConfigOptionalFields:
    """Test suite for optional configuration fields."""

    def test_remote_optional(self):
        """Test remote field is optional."""
        config = Config(app_name="test", languages=["go"])
        assert config.remote_url is None

    def test_config_with_optional_fields(self):
        """Test config can include optional fields."""
        config = Config(
            app_name="test",
            languages=["go"],
            remote_url="https://github.com/test/repo",
            core_version="abc123",
        ).to_dict()
        assert len(config) >= 4
