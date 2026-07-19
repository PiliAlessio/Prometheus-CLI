#!/usr/bin/env python
"""Test repo name shorthand feature end-to-end."""

from prometheus.init.workflow import InitWorkflow
from prometheus.config import Config
from pathlib import Path
import tempfile

print("Test 1: Config.make_github_url() method")
config = Config()
print(f"  make_github_url('MyApp') = {config.make_github_url('MyApp')}")
print(f"  make_github_url('my-repo') = {config.make_github_url('my-repo')}")
print(f"  make_github_url full URL = {config.make_github_url('https://github.com/someone/repo.git')}")

print("\nTest 2: InitWorkflow with repo names (shorthand)")
# Use temp dir without .git to avoid auto-detection
with tempfile.TemporaryDirectory() as tmpdir:
    workflow = InitWorkflow(
        app_name="TestApp",
        app_remote="TestApp",
        app_instructions_remote="TestApp-instructions",
        current_dir=tmpdir
    )
    print(f"  app_remote: {workflow.app_remote}")
    print(f"  app_instructions_remote: {workflow.app_instructions_remote}")
    assert workflow.app_remote == "https://github.com/PiliAlessio/TestApp.git", "app_remote not converted!"
    assert workflow.app_instructions_remote == "https://github.com/PiliAlessio/TestApp-instructions.git", "app_instructions_remote not converted!"
    print("  ✓ Both remotes correctly converted from shorthand to full URL")

print("\nTest 3: InitWorkflow with full URLs (should pass through)")
with tempfile.TemporaryDirectory() as tmpdir:
    workflow2 = InitWorkflow(
        app_name="OtherApp",
        app_remote="https://github.com/someone/other-app.git",
        app_instructions_remote="https://github.com/someone/other-app-instructions.git",
        current_dir=tmpdir
    )
    print(f"  app_remote: {workflow2.app_remote}")
    print(f"  app_instructions_remote: {workflow2.app_instructions_remote}")
    assert workflow2.app_remote == "https://github.com/someone/other-app.git", "Full URL app_remote was modified!"
    assert workflow2.app_instructions_remote == "https://github.com/someone/other-app-instructions.git", "Full URL app_instructions_remote was modified!"
    print("  ✓ Full URLs passed through unchanged")

print("\nTest 4: InitWorkflow with None values and create_app_repo=True (skips auto-detect)")
with tempfile.TemporaryDirectory() as tmpdir:
    workflow3 = InitWorkflow(
        app_name="NoRemotes",
        app_remote=None,
        app_instructions_remote=None,
        create_app_repo=True,
        current_dir=tmpdir
    )
    print(f"  app_remote: {workflow3.app_remote}")
    print(f"  app_instructions_remote: {workflow3.app_instructions_remote}")
    assert workflow3.app_remote is None, "None app_remote was modified!"
    assert workflow3.app_instructions_remote is None, "None app_instructions_remote was modified!"
    print("  ✓ None values remain None (with create_app_repo=True)")

print("\n✓ All tests passed! Repo name shorthand feature is working correctly.")
