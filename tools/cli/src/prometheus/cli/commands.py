"""Click CLI commands for Prometheus."""

from __future__ import annotations

from pathlib import Path

import click
from prometheus.init.workflow import InitWorkflow
from prometheus.push import push_changes
from prometheus.update import update_app
from prometheus.version import __version__


@click.group()
@click.version_option(version=__version__, prog_name="Prometheus")
def cli():
    """Prometheus - A command-line tool for project initialization and management.

    Use 'prometheus COMMAND --help' for more information on a command.

    Examples:
        prometheus init --app-name my-app
        prometheus push
        prometheus update
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
@click.option(
    "--app-name",
    required=True,
    help="Name of the app repository to initialize."
)
@click.option(
    "--app-remote",
    default=None,
    help="Remote URL for the app code repository (GitHub, etc). Required unless creating local-only structure."
)
@click.option(
    "--app-instructions-remote",
    default=None,
    help="Remote URL for the app-specific instructions repository. Optional, can be added later."
)
@click.option(
    "--core-remote",
    default=None,
    help="Remote URL for the core instructions repository. Defaults to https://github.com/PiliAlessio/Prometheus.git"
)
@click.option(
    "--create-app-repo",
    is_flag=True,
    default=False,
    help="Create the app repo structure locally (for new apps not yet on GitHub)."
)
def init(app_name, app_remote, app_instructions_remote, core_remote, create_app_repo):
    """Initialize a new Prometheus app repository with three-entity governance.

    This command manages three separate Git repositories:

    1. App code repository: Where the CLI is run from
    2. App-specific instructions repository: Optional, separate repo for app customization
    3. Core instructions repository: Shared across all apps

    The workflow:
    - Validates all three remotes are accessible
    - Stores remote URLs in .prometheus.yml (local only, not pushed)
    - Creates .github symlink in app code pointing to app's GitHub folder
    - Sets up core as submodule in app-specific instructions repo

    Examples:
        prometheus init --app-name my-app --app-remote https://github.com/user/my-app.git
        prometheus init --app-name my-app --app-remote https://github.com/user/my-app.git \\
            --app-instructions-remote https://github.com/user/my-app-instructions.git
        prometheus init --app-name new-app --create-app-repo
    """
    from prometheus.init.workflow import InitWorkflow

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
    click.echo(f"  Core remote: {result.core_remote}")
    click.echo(f"  Core version: {result.core_version}")
    if result.symlink_created:
        click.echo(f"  Symlink: ./.github -> {result.app_path}/.github")
    else:
        click.echo(f"  ⚠ .github symlink not created (may require admin privileges on Windows)")
    click.echo("[OK] Setup complete!")


@cli.command()
def update():
    """Pull the latest app repo changes and sync the core submodule."""
    try:
        summary = update_app(Path.cwd())
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Updated app repo: {summary.app_path}")
    click.echo(f"  App revision: {summary.app_before} -> {summary.app_after}")
    if summary.core_before or summary.core_after:
        click.echo(f"  Core revision: {summary.core_before} -> {summary.core_after}")
    click.echo("[OK] Update completed successfully.")


@cli.command()
def help():
    """Show help information about Prometheus commands.

    Displays detailed help for all available commands and their options.

    Examples:
        prometheus help
        prometheus init --help
        prometheus push --help
        prometheus update --help
        prometheus version --help
    """
    click.echo("Prometheus - Project Initialization and Management Tool")
    click.echo("\nAvailable Commands:")
    click.echo("  init       Initialize a new Prometheus app repository")
    click.echo("  push       Push app repo and prometheus-core changes to remotes")
    click.echo("  update     Pull the app repo and sync prometheus-core")
    click.echo("  help       Show this help message")
    click.echo("  version    Show version information")
    click.echo("\nUse 'prometheus COMMAND --help' for more information on a command.")


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


if __name__ == "__main__":
    cli()
