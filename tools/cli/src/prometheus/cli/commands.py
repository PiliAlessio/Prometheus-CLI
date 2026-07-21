"""Click CLI commands for Prometheus."""

from __future__ import annotations

import subprocess
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
    """Push committed changes for the app-specific instructions repository.

    This command pushes changes from the app-instructions repository
    (domain/ content and the core submodule pointer). The core submodule
    itself is shared, read-only content: its local state is reported but
    never committed or pushed - use 'prometheus pull' to sync it instead.

    Examples:
        prometheus push
    """
    try:
        summary = push_changes(Path.cwd())
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc

    _echo_push_summary(summary)


def _create_repo_with_gh(repo_name: str) -> str | None:
    """Create a GitHub repository using GitHub CLI (gh).

    Args:
        repo_name: Name for the repository (e.g., 'my-app-instructions')

    Returns:
        Repository HTTPS URL if created successfully, None if gh unavailable
        or creation failed.
    """
    try:
        # Check if gh command is available
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

        if result.returncode != 0:
            print("[DEBUG] gh command not available")
            return None  # gh not available

        # Try to create repo (public, no automatic push - we'll do manual push later)
        print(f"[DEBUG] Creating GitHub repository '{repo_name}'...")
        result = subprocess.run(
            ["gh", "repo", "create", repo_name, "--public"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        print(f"[DEBUG] gh repo create returned: {result.returncode}")
        print(f"[DEBUG] gh repo create stdout: {result.stdout}")
        print(f"[DEBUG] gh repo create stderr: {result.stderr}")

        if result.returncode == 0:
            # Get GitHub username and construct the URL
            try:
                user_result = subprocess.run(
                    ["gh", "api", "user", "-q", ".login"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                if user_result.returncode == 0:
                    username = user_result.stdout.strip()
                    repo_url = f"https://github.com/{username}/{repo_name}.git"
                    print(f"[DEBUG] Created repo URL: {repo_url}")
                    return repo_url
            except Exception as e:
                print(f"[DEBUG] Error getting username: {e}")
                pass

        return None
    except Exception as e:
        print(f"[DEBUG] Exception in _create_repo_with_gh: {e}")
        return None


@cli.command()
@click.option("--app-name", required=True, help="Name of the app repository to initialize.")
@click.option(
    "--app-remote",
    default=None,
    help="App code repository: full URL or just repo name (e.g., 'my-app'). "
    "Required unless creating local-only structure.",
)
@click.option(
    "--app-instructions-remote",
    default=None,
    help="App instructions repository: full URL or just repo name. "
    "If not provided, will prompt in interactive mode.",
)
@click.option(
    "--core-remote",
    default=None,
    help="Core instructions repository URL. "
    "Defaults to https://github.com/AlessioPili-KT/Prometheus.git",
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
    - Creates .github/prometheus symlink in app code pointing to the
      app-instructions repo (domain/ and core/)
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

        # If empty, offer to create on GitHub using gh CLI
        if not app_instructions_remote:
            if click.confirm("  Create on GitHub using gh CLI? (requires GitHub CLI)"):
                gh_repo_name = click.prompt(
                    "  Repository name (e.g., my-app-instructions)",
                    default=f"{app_name}-instructions",
                    type=str,
                ).strip()
                # Create the repo directly with gh CLI
                click.echo("  Creating repository on GitHub...")
                repo_url = _create_repo_with_gh(gh_repo_name)
                if repo_url:
                    app_instructions_remote = repo_url
                    click.echo(f"  ✓ Created: {repo_url}")
                else:
                    click.echo(
                        "  ✗ Failed to create repository. Please ensure:"
                    )
                    click.echo("    - GitHub CLI is installed (gh --version)")
                    click.echo("    - You are authenticated (gh auth status)")
                    click.echo("    - You have permission to create repositories")
                    click.echo("  Continuing with local-only setup.")

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
        click.echo(f"  Symlink: ./.github/prometheus -> ~/.prometheus/{app_name}-instructions")
    else:
        click.echo(
            "  \u26a0 .github/prometheus symlink not created (may require admin "
            "privileges on Windows)"
        )
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
    1. Pulls the latest app and core changes (core is shared/read-only)
    2. Pushes local app-instructions commits to their remote

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
