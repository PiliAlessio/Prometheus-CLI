"""Pytest configuration and shared fixtures."""

import pytest
from click.testing import CliRunner


@pytest.fixture
def cli_runner():
    """Provide a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_project_dir(tmp_path):
    """Provide a temporary project directory."""
    return tmp_path
