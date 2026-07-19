"""Language detection for Prometheus."""


class LanguageDetector:
    """Detects programming languages in a project."""

    @staticmethod
    def detect_languages(path):
        """Detect programming languages in a project.

        Args:
            path: Path to the project directory.

        Returns:
            List of detected languages.
        """
        pass

    @staticmethod
    def is_go_project(path):
        """Check if a path contains a Go project.

        Args:
            path: Path to check.

        Returns:
            True if Go project detected, False otherwise.
        """
        pass

    @staticmethod
    def is_python_project(path):
        """Check if a path contains a Python project.

        Args:
            path: Path to check.

        Returns:
            True if Python project detected, False otherwise.
        """
        pass
