"""Tests for domain/core/code content materialization."""

import subprocess
from pathlib import Path

import yaml

from prometheus.materialize.materialize import (
    commit_gitignore_if_pending,
    ensure_gitignore_entries,
    materialize,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestMaterialize:
    """Test suite for materializing content into .github/ locations."""

    def test_materializes_domain_and_core_sources_with_prefixes(self, tmp_path):
        instructions_path = tmp_path / "app-instructions"
        app_path = tmp_path / "app"

        _write(
            instructions_path / "domain" / "instructions" / "style.md",
            "---\ndescription: Domain style rules\napplyTo: '**/*.py'\n---\n\nBody text.\n",
        )
        _write(
            instructions_path / "core" / "core" / "prompts" / "review.md",
            "No frontmatter here, just a prompt body.\n",
        )
        _write(
            instructions_path / "core" / "code_instructions" / "backend" / "skills" / "helper.md",
            "---\nname: helper\n---\n\nSkill body.\n",
        )

        result = materialize(instructions_path, app_path)

        assert result.written_count == 3

        domain_file = app_path / ".github" / "instructions" / "domain.style.md"
        core_file = app_path / ".github" / "prompts" / "core.review.md"
        code_file = app_path / ".github" / "skills" / "backend.helper.skills.md"

        assert domain_file.exists()
        assert core_file.exists()
        assert code_file.exists()

    def test_materializes_code_instructions_layers_with_layer_naming(self, tmp_path):
        instructions_path = tmp_path / "app-instructions"
        app_path = tmp_path / "app"

        _write(
            instructions_path
            / "core"
            / "code_instructions"
            / "backend"
            / "instructions"
            / "style.md",
            "---\ndescription: Backend style\n---\n\nBackend body.\n",
        )
        _write(
            instructions_path
            / "core"
            / "code_instructions"
            / "frontend"
            / "instructions"
            / "style.md",
            "---\ndescription: Frontend style\n---\n\nFrontend body.\n",
        )
        _write(
            instructions_path
            / "core"
            / "code_instructions"
            / "backend"
            / "prompts"
            / "review.md",
            "Backend prompt body.\n",
        )

        result = materialize(instructions_path, app_path)

        assert result.written_count == 3

        backend_instructions = (
            app_path / ".github" / "instructions" / "backend.style.instructions.md"
        )
        frontend_instructions = (
            app_path / ".github" / "instructions" / "frontend.style.instructions.md"
        )
        backend_prompt = app_path / ".github" / "prompts" / "backend.review.prompts.md"

        assert backend_instructions.exists()
        assert frontend_instructions.exists()
        assert backend_prompt.exists()

    def test_materializes_helpers_verbatim_with_origin_prefix(self, tmp_path):
        instructions_path = tmp_path / "app-instructions"
        app_path = tmp_path / "app"

        _write(
            instructions_path / "domain" / "helpers" / "setup.sh",
            "#!/bin/sh\necho domain helper\n",
        )
        _write(
            instructions_path / "core" / "core" / "helpers" / "lint.py",
            "print('core helper')\n",
        )
        _write(
            instructions_path
            / "core"
            / "code_instructions"
            / "backend"
            / "helpers"
            / "seed.py",
            "print('backend helper')\n",
        )

        result = materialize(instructions_path, app_path)

        assert result.written_count == 3

        domain_helper = app_path / ".github" / "helpers" / "domain.setup.sh"
        core_helper = app_path / ".github" / "helpers" / "core.lint.py"
        backend_helper = app_path / ".github" / "helpers" / "backend.seed.py"

        assert domain_helper.read_text(encoding="utf-8") == "#!/bin/sh\necho domain helper\n"
        assert core_helper.read_text(encoding="utf-8") == "print('core helper')\n"
        assert backend_helper.read_text(encoding="utf-8") == "print('backend helper')\n"

    def test_materializes_helpers_from_core_root(self, tmp_path):
        """Test that helpers from core/ root (submodule root level) are materialized."""
        instructions_path = tmp_path / "app-instructions"
        app_path = tmp_path / "app"

        _write(
            instructions_path / "core" / "helpers" / "setup.ps1",
            "$PSVersionTable\n",
        )

        result = materialize(instructions_path, app_path)

        assert result.written_count == 1

        core_root_helper = app_path / ".github" / "helpers" / "core.setup.ps1"
        assert core_root_helper.exists()
        assert core_root_helper.read_text(encoding="utf-8") == "$PSVersionTable\n"

    def test_fills_in_missing_required_frontmatter(self, tmp_path):
        instructions_path = tmp_path / "app-instructions"
        app_path = tmp_path / "app"

        _write(
            instructions_path / "domain" / "instructions" / "no_frontmatter.md",
            "Just body content, no frontmatter at all.\n",
        )
        _write(
            instructions_path / "core" / "core" / "agents" / "no_name.md",
            "---\ndescription: An agent\n---\n\nBody.\n",
        )

        materialize(instructions_path, app_path)

        instructions_content = (
            app_path / ".github" / "instructions" / "domain.no_frontmatter.md"
        ).read_text(encoding="utf-8")
        frontmatter = yaml.safe_load(instructions_content.split("---")[1])
        assert "description" in frontmatter
        assert frontmatter["applyTo"] == "**"

        agent_content = (app_path / ".github" / "agents" / "core.no_name.md").read_text(
            encoding="utf-8"
        )
        agent_frontmatter = yaml.safe_load(agent_content.split("---")[1])
        assert agent_frontmatter["name"] == "no_name"
        assert agent_frontmatter["description"] == "An agent"

    def test_rerun_rewrites_all_files(self, tmp_path):
        instructions_path = tmp_path / "app-instructions"
        app_path = tmp_path / "app"

        _write(
            instructions_path / "domain" / "prompts" / "greet.md",
            "---\ndescription: Greeting prompt\n---\n\nHello.\n",
        )

        first = materialize(instructions_path, app_path)
        assert first.written_count == 1

        second = materialize(instructions_path, app_path)
        assert second.written_count == 1

    def test_missing_source_folders_is_a_noop(self, tmp_path):
        instructions_path = tmp_path / "app-instructions"
        app_path = tmp_path / "app"

        result = materialize(instructions_path, app_path)

        assert result.written_count == 0
        assert not (app_path / ".github").exists()

    def test_removes_stale_materialized_files_when_source_disappears(self, tmp_path):
        instructions_path = tmp_path / "app-instructions"
        app_path = tmp_path / "app"

        _write(
            instructions_path / "domain" / "instructions" / "one.md",
            "---\ndescription: One\napplyTo: '**'\n---\n\nBody.\n",
        )
        materialize(instructions_path, app_path)

        stale_file = app_path / ".github" / "instructions" / "domain.one.md"
        assert stale_file.exists()

        # Remove the source file; the destination folder is fully rebuilt on
        # every run, so the stale file must be gone afterwards.
        (instructions_path / "domain" / "instructions" / "one.md").unlink()

        materialize(instructions_path, app_path)
        assert not stale_file.exists()

    def test_compacts_destination_when_all_sources_removed(self, tmp_path):
        instructions_path = tmp_path / "app-instructions"
        app_path = tmp_path / "app"

        _write(
            instructions_path / "core" / "core" / "skills" / "only.md",
            "---\nname: only\ndescription: Only skill\n---\n\nBody.\n",
        )
        materialize(instructions_path, app_path)
        skills_dir = app_path / ".github" / "skills"
        assert skills_dir.exists()

        (instructions_path / "core" / "core" / "skills" / "only.md").unlink()

        materialize(instructions_path, app_path)
        assert not skills_dir.exists()


class TestEnsureGitignoreEntries:
    """Test suite for ensuring the app repo's .gitignore is up to date."""

    def test_creates_gitignore_when_missing(self, tmp_path):
        app_path = tmp_path / "app"
        app_path.mkdir()

        changed = ensure_gitignore_entries(app_path)

        assert changed is True
        content = (app_path / ".gitignore").read_text(encoding="utf-8")
        assert ".github/instructions/" in content
        assert ".github/prompts/" in content
        assert ".github/agents/" in content
        assert ".github/skills/" in content
        assert ".github/helpers/" in content

    def test_appends_missing_entries_to_existing_gitignore(self, tmp_path):
        app_path = tmp_path / "app"
        app_path.mkdir()
        (app_path / ".gitignore").write_text(".prometheus.yml\n", encoding="utf-8")

        changed = ensure_gitignore_entries(app_path)

        assert changed is True
        content = (app_path / ".gitignore").read_text(encoding="utf-8")
        assert ".prometheus.yml" in content
        assert ".github/instructions/" in content

    def test_returns_false_when_entries_already_present(self, tmp_path):
        app_path = tmp_path / "app"
        app_path.mkdir()
        ensure_gitignore_entries(app_path)

        changed = ensure_gitignore_entries(app_path)

        assert changed is False


class TestCommitGitignoreIfPending:
    """Test suite for committing pending .gitignore changes in the app repo."""

    def test_returns_false_when_not_a_git_repo(self, tmp_path):
        app_path = tmp_path / "app"
        app_path.mkdir()
        ensure_gitignore_entries(app_path)

        assert commit_gitignore_if_pending(app_path) is False

    def test_commits_pending_gitignore_change(self, tmp_path):
        app_path = tmp_path / "app"
        app_path.mkdir()
        subprocess.run(["git", "init"], cwd=app_path, capture_output=True, check=True)
        ensure_gitignore_entries(app_path)

        committed = commit_gitignore_if_pending(app_path)

        assert committed is True
        status = subprocess.run(
            ["git", "status", "--porcelain", "--", ".gitignore"],
            cwd=app_path,
            capture_output=True,
            text=True,
            check=True,
        )
        assert status.stdout.strip() == ""

    def test_returns_false_when_nothing_pending(self, tmp_path):
        app_path = tmp_path / "app"
        app_path.mkdir()
        subprocess.run(["git", "init"], cwd=app_path, capture_output=True, check=True)
        ensure_gitignore_entries(app_path)
        commit_gitignore_if_pending(app_path)

        assert commit_gitignore_if_pending(app_path) is False
