"""Tests for domain/core/code content materialization."""

from pathlib import Path

import yaml

from prometheus.materialize.materialize import materialize


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
            instructions_path / "core" / "code_instructions" / "skills" / "helper.md",
            "---\nname: helper\n---\n\nSkill body.\n",
        )

        result = materialize(instructions_path, app_path)

        assert result.written_count == 3

        domain_file = app_path / ".github" / "instructions" / "domain.style.md"
        core_file = app_path / ".github" / "prompts" / "core.review.md"
        code_file = app_path / ".github" / "skills" / "code.helper.md"

        assert domain_file.exists()
        assert core_file.exists()
        assert code_file.exists()

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

    def test_rerun_skips_unchanged_files(self, tmp_path):
        instructions_path = tmp_path / "app-instructions"
        app_path = tmp_path / "app"

        _write(
            instructions_path / "domain" / "prompts" / "greet.md",
            "---\ndescription: Greeting prompt\n---\n\nHello.\n",
        )

        first = materialize(instructions_path, app_path)
        assert first.written_count == 1

        second = materialize(instructions_path, app_path)
        assert second.written_count == 0
        assert len(second.skipped) == 1

    def test_missing_source_folders_is_a_noop(self, tmp_path):
        instructions_path = tmp_path / "app-instructions"
        app_path = tmp_path / "app"

        result = materialize(instructions_path, app_path)

        assert result.written_count == 0
        assert not (app_path / ".github").exists()

    def test_never_deletes_stale_materialized_files(self, tmp_path):
        instructions_path = tmp_path / "app-instructions"
        app_path = tmp_path / "app"

        _write(
            instructions_path / "domain" / "instructions" / "one.md",
            "---\ndescription: One\napplyTo: '**'\n---\n\nBody.\n",
        )
        materialize(instructions_path, app_path)

        # Remove the source file; a previously materialized file should remain.
        (instructions_path / "domain" / "instructions" / "one.md").unlink()

        stale_file = app_path / ".github" / "instructions" / "domain.one.md"
        assert stale_file.exists()

        materialize(instructions_path, app_path)
        assert stale_file.exists()
