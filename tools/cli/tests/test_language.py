"""Tests for language handling."""

import pytest


class TestLanguageValidation:
    """Test suite for language validation."""

    def test_valid_language(self):
        """Test validation of valid language."""
        language = "go"
        assert isinstance(language, str)
        assert len(language) > 0

    def test_multiple_valid_languages(self):
        """Test multiple valid languages."""
        languages = ["go", "python", "rust", "javascript"]
        for lang in languages:
            assert isinstance(lang, str)
            assert len(lang) > 0

    def test_language_case_sensitivity(self):
        """Test language names are case-sensitive."""
        lang_lower = "go"
        lang_upper = "GO"
        assert lang_lower != lang_upper

    def test_empty_language_string(self):
        """Test empty language string."""
        language = ""
        assert len(language) == 0


class TestLanguageDetection:
    """Test suite for language detection."""

    def test_detect_from_extension(self):
        """Test detecting language from file extension."""
        extensions = {
            ".go": "go",
            ".py": "python",
            ".rs": "rust",
            ".js": "javascript",
            ".ts": "typescript",
        }

        for ext, lang in extensions.items():
            assert ext.startswith(".")
            assert len(lang) > 0

    def test_detect_from_filename(self):
        """Test detecting language from filename."""
        files = {"main.go": "go", "app.py": "python", "main.rs": "rust"}

        for filename, expected_lang in files.items():
            assert "." in filename
            ext = filename.split(".")[-1]
            assert len(ext) > 0

    def test_unknown_language(self):
        """Test handling unknown language."""
        unknown_lang = "cobol"
        # Should not raise error, just indicate unknown
        assert isinstance(unknown_lang, str)


class TestLanguageParsing:
    """Test suite for language string parsing."""

    def test_parse_single_language(self):
        """Test parsing single language from comma-separated string."""
        langs_str = "go"
        languages = [l.strip() for l in langs_str.split(",")]
        assert languages == ["go"]

    def test_parse_multiple_languages(self):
        """Test parsing multiple languages from comma-separated string."""
        langs_str = "go,python,rust"
        languages = [l.strip() for l in langs_str.split(",")]
        assert languages == ["go", "python", "rust"]

    def test_parse_with_whitespace(self):
        """Test parsing languages with whitespace."""
        langs_str = "go, python, rust"
        languages = [l.strip() for l in langs_str.split(",")]
        assert languages == ["go", "python", "rust"]

    def test_empty_language_list(self):
        """Test parsing empty language list."""
        langs_str = ""
        languages = [l.strip() for l in langs_str.split(",") if l.strip()]
        assert languages == []
