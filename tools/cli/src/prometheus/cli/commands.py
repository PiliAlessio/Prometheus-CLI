"""Click CLI commands for Prometheus."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from prometheus.init.workflow import InitWorkflow
from prometheus.push import push_changes
from prometheus.pull import pull_app
from prometheus.version import __version__


@click.group()
@click.version_option(version=__version__, prog_name="Prometheus")
def cli():
    """Prometheus - A command-line tool for project initialization and management.

    Use 'prometheus COMMAND --help' for more information on a command.

    Examples:
        prometheus init --app-name my-app
        prometheus push
        prometheus pull
        prometheus sync
        prometheus version
        prometheus help
    """
    pass


@cli.command()
def push():
    """Push committed changes for the app repo and prometheus-core submodule.

    This command pushes changes from both the app repository and the
    prometheus-core git submodule to their respective remotes.

    Examples:
        prometheus push
    """
    try:
        summary = push_changes(Path.cwd())
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc

    _echo_push_summary(summary)


@cli.command()
@click.option("--app-name", required=True, help="Name of the app repository to initialize.")
@click.option(
    "--app-remote",
    default=None,
    help="Remote URL for the app code repository (GitHub, etc). Required unless creating local-only structure.",
)
@click.option(
    "--app-instructions-remote",
    default=None,
    help="Remote URL for the app-specific instructions repository. If not provided, will prompt in interactive mode.",
)
@click.option(
    "--core-remote",
    default=None,
    help="Remote URL for the core instructions repository. Defaults to https://github.com/PiliAlessio/Prometheus.git",
)
@click.option(
    "--create-app-repo",
    is_flag=True,
    default=False,
    help="Create the app repo structure locally (for new apps not yet on GitHub).",
)
def init(app_name, app_remote, app_instructions_remote, core_remote, create_app_repo):
    """Initialize a new Prometheus app repository with three-entity
    governance.

    This command manages three separate Git repositories:

    1. App code repository: Where the CLI is run from
    2. App-specific instructions repository: Optional, separate repo for
       app customization
    3. Core instructions repository: Shared across all apps

    The workflow:
    - Validates all three remotes are accessible
    - Stores remote URLs in .prometheus.yml (local only, not pushed)
    - Creates .github symlink in app code pointing to app's GitHub folder
    - Sets up core as submodule in app-specific instructions repo

    Examples:
        prometheus init --app-name my-app \\
            --app-remote https://github.com/user/my-app.git
        prometheus init --app-name my-app \\
            --app-remote https://github.com/user/my-app.git \\
            --app-instructions-remote \\
            https://github.com/user/my-app-instructions.git
        prometheus init --app-name new-app --create-app-repo
    """
    # Interactive mode: if app-instructions-remote not provided, prompt user
    if not app_instructions_remote and sys.stdin.isatty():
        click.echo("App-specific instructions repository:")
        app_instructions_remote = (
            click.prompt(
                "  Enter URL (leave empty to create locally)",
                default="",
                type=str,
            ).strip()
            or None
        )

    workflow = InitWorkflow(
        app_name=app_name,
        app_remote=app_remote,
        app_instructions_remote=app_instructions_remote,
        core_remote=core_remote,
        create_app_repo=create_app_repo,
    )

    try:
        result = workflow.run()
    except (FileExistsError, RuntimeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"✓ Initialized Prometheus app: {app_name}")
    click.echo(f"  App path: {result.app_path}")
    click.echo(f"  App remote: {result.app_remote}")
    if result.app_instructions_remote:
        click.echo(f"  App instructions remote: {result.app_instructions_remote}")
    else:
        click.echo(
            f"  App instructions: Created locally at " f"~/.prometheus/{app_name}-instructions/"
        )
    click.echo(f"  Core remote: {result.core_remote}")
    click.echo(f"  Core version: {result.core_version}")
    if result.symlink_created:
        click.echo(f"  Symlink: ./.github -> {result.app_path}/.github")
    else:
        click.echo("  ⚠ .github symlink not created (may require admin " "privileges on Windows)")
    click.echo("[OK] Setup complete!")


@cli.command()
def pull():
    """Pull the latest app repo changes and sync the core submodule.

    This command pulls changes from both the app repository and the
    prometheus-core git submodule from their respective remotes.

    Examples:
        prometheus pull
    """
    try:
        summary = pull_app(Path.cwd())
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Updated app repo: {summary.app_path}")
    click.echo(f"  App revision: {summary.app_before} -> {summary.app_after}")
    if summary.core_before or summary.core_after:
        click.echo(f"  Core revision: {summary.core_before} -> {summary.core_after}")
    click.echo("[OK] Pull completed successfully.")


@cli.command()
def sync():
    """Pull the latest changes and push all local commits.

    This command performs a two-step workflow:
    1. Pulls the latest changes from both app and core repositories
    2. Pushes all local commits to their respective remotes

    This ensures your local changes are pushed after pulling any remote updates.

    Examples:
        prometheus sync
    """
    try:
        pull_summary = pull_app(Path.cwd())
        click.echo(f"✓ Pulled changes for {pull_summary.app_path}")
        click.echo(f"  App revision: {pull_summary.app_before} -> {pull_summary.app_after}")
        if pull_summary.core_before or pull_summary.core_after:
            click.echo(f"  Core revision: {pull_summary.core_before} -> {pull_summary.core_after}")

        push_summary = push_changes(Path.cwd())
        click.echo("✓ Pushed changes:")
        _echo_repo_push_state(push_summary.app)
        if push_summary.core:
            _echo_repo_push_state(push_summary.core)
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo("[OK] Sync completed successfully.")


@cli.command()
def help():
    """Show help information about Prometheus commands.

    Displays detailed help for all available commands and their options.

    Examples:
        prometheus help
        prometheus init --help
        prometheus push --help
        prometheus pull --help
        prometheus version --help
    """
    click.echo(_generate_help_output())


@cli.command()
def version():
    """Show version information.

    Displays the current version of Prometheus CLI.

    Examples:
        prometheus version
    """
    click.echo(f"Prometheus v{__version__}")


def _echo_push_summary(summary):
    """Render a push summary for the CLI."""
    click.echo("Push summary:")
    _echo_repo_push_state(summary.app)
    if summary.core:
        _echo_repo_push_state(summary.core)
    click.echo("[OK] Push workflow completed.")


def _echo_repo_push_state(state):
    """Render a single repository push state."""
    status = "pushed" if state.pushed else f"skipped ({state.skipped_reason})"
    click.echo(f"  {state.name}: {status}")
    click.echo(f"    Branch: {state.branch}")
    if state.modified_files:
        click.echo(f"    Modified files: {', '.join(state.modified_files)}")


def _generate_help_output() -> str:
    """Generate reflection-based help output from CLI command group.

    Iterates through all commands in the CLI group and extracts:
    - Command name
    - Short description (first line of docstring)
    - Examples (extracted from Examples section if present)

    Returns:
        Formatted help string with all commands and their descriptions.
    """
    lines = [
        "Prometheus - Project Initialization and Management Tool",
        "",
        "Available Commands:",
    ]

    # Iterate through all commands in the CLI group
    for cmd_name, cmd in sorted(cli.commands.items()):
        # Extract short description from docstring
        description = "No description available"
        examples = []
        if cmd.callback and cmd.callback.__doc__:
            docstring = cmd.callback.__doc__.strip()
            # First line is the short description
            first_line = docstring.split("\n")[0]
            description = first_line if first_line else description

            # Extract Examples section
            if "Examples:" in docstring:
                examples_start = docstring.index("Examples:") + len("Examples:")
                examples_section = docstring[examples_start:].strip()
                # Clean up indentation
                for line in examples_section.split("\n"):
                    cleaned = line.strip()
                    if cleaned and not cleaned.startswith("Examples:"):
                        examples.append(f"        {cleaned}")

        # Format command entry (padded for alignment)
        lines.append(f"  {cmd_name:<14} {description}")

        # Add examples if available
        if examples:
            for example in examples:
                lines.append(example)

    lines.extend(
        [
            "",
            "Use 'prometheus COMMAND --help' for more information on a command.",
        ]
    )

    return "\n".join(lines)


if __name__ == "__main__":
    cli()
