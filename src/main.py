"""Main entry point for the Call Agent Orchestrator."""

import asyncio
import logging
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config.settings import get_settings, get_config
from .utils.logger import setup_logger
from .orchestrator import CallOrchestrator


console = Console()


@click.group()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file (default: config.yaml)"
)
@click.option(
    "--log-level",
    "-l",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    default="INFO",
    help="Logging level"
)
@click.pass_context
def cli(ctx, config, log_level):
    """Apollo ElevenLabs Call Agent Orchestrator.

    Automatically call contacts from Apollo.io using ElevenLabs AI agents
    to schedule appointments.
    """
    # Setup logging
    log_file = Path("logs") / "orchestrator.log"
    setup_logger("src", level=log_level, log_file=log_file)

    # Store config path in context
    ctx.ensure_object(dict)
    if config:
        ctx.obj["CONFIG_FILE"] = config


@cli.command()
def tui():
    """Launch interactive TUI (Text User Interface).

    Open an interactive terminal interface with:
    - Contact browser and batch selector
    - Calendar configuration
    - AI-powered script composer
    - Workflow creator
    - Real-time campaign monitoring
    """
    console.print("[bold green]Launching TUI...[/bold green]")

    try:
        from .tui.app import CallOrchestratorApp
        app = CallOrchestratorApp()
        app.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]TUI closed[/yellow]")
    except Exception as e:
        console.print(f"[red]Error launching TUI: {e}[/red]")
        raise


@cli.command()
@click.option(
    "--limit",
    "-n",
    type=int,
    help="Maximum number of contacts to call"
)
@click.option(
    "--include-with-appointments",
    is_flag=True,
    help="Include contacts that already have appointments"
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default="./results",
    help="Directory to save results"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Fetch contacts but don't make calls"
)
def run(limit, include_with_appointments, output_dir, dry_run):
    """Run a call campaign.

    Fetches contacts from Apollo.io and calls them using ElevenLabs agents
    to schedule appointments.
    """
    console.print("[bold green]Apollo ElevenLabs Call Orchestrator[/bold green]")
    console.print()

    try:
        # Create orchestrator
        orchestrator = CallOrchestrator()

        # Fetch contacts
        console.print("[cyan]Fetching contacts from Apollo...[/cyan]")
        contacts = orchestrator.fetch_contacts(
            limit=limit,
            exclude_with_appointments=not include_with_appointments
        )

        if not contacts:
            console.print("[yellow]No contacts found matching criteria[/yellow]")
            return

        # Display contacts
        _display_contacts(contacts)

        if dry_run:
            console.print("\n[yellow]Dry run - no calls will be made[/yellow]")
            return

        # Confirm before calling
        if not click.confirm(f"\nProceed with calling {len(contacts)} contacts?"):
            console.print("[yellow]Campaign cancelled[/yellow]")
            return

        # Execute campaign
        console.print("\n[cyan]Starting call campaign...[/cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Calling contacts...", total=None)

            results = orchestrator.execute_campaign_sync(
                contacts=contacts,
                save_results=True,
                output_dir=Path(output_dir)
            )

            progress.update(task, completed=True)

        # Display results
        _display_results(results)

        console.print(f"\n[green]Results saved to {output_dir}[/green]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Campaign interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        raise


@cli.command()
@click.option(
    "--limit",
    "-n",
    type=int,
    help="Maximum number of contacts to fetch"
)
@click.option(
    "--include-with-appointments",
    is_flag=True,
    help="Include contacts that already have appointments"
)
def fetch(limit, include_with_appointments):
    """Fetch contacts from Apollo without calling.

    Useful for testing filters and seeing which contacts would be called.
    """
    try:
        orchestrator = CallOrchestrator()

        console.print("[cyan]Fetching contacts from Apollo...[/cyan]")

        contacts = orchestrator.fetch_contacts(
            limit=limit,
            exclude_with_appointments=not include_with_appointments
        )

        if not contacts:
            console.print("[yellow]No contacts found matching criteria[/yellow]")
            return

        _display_contacts(contacts)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise


@cli.command()
def config_info():
    """Display current configuration."""
    try:
        settings = get_settings()
        config = get_config()

        console.print("[bold]Configuration[/bold]\n")

        # API Configuration
        table = Table(title="API Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Apollo API Key", "***" + settings.apollo_api_key[-4:] if settings.apollo_api_key else "[red]Not set[/red]")
        table.add_row("Apollo Base URL", settings.apollo_base_url)
        table.add_row("ElevenLabs API Key", "***" + settings.elevenlabs_api_key[-4:] if settings.elevenlabs_api_key else "[red]Not set[/red]")
        table.add_row("ElevenLabs Agent ID", settings.elevenlabs_agent_id or "[red]Not set[/red]")

        console.print(table)
        console.print()

        # Orchestrator Configuration
        orch_config = config.get("orchestrator", {})

        table2 = Table(title="Orchestrator Configuration")
        table2.add_column("Setting", style="cyan")
        table2.add_column("Value", style="green")

        table2.add_row("Max Concurrent Calls", str(orch_config.get("max_concurrent_calls", settings.max_concurrent_calls)))
        table2.add_row("Retry Attempts", str(orch_config.get("retry_attempts", settings.call_retry_attempts)))
        table2.add_row("Call Timeout", f"{orch_config.get('call_timeout_seconds', settings.call_timeout_seconds)}s")

        console.print(table2)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise


@cli.command()
def test_connection():
    """Test API connections to Apollo and ElevenLabs."""
    from .clients import ApolloClient, ElevenLabsClient

    console.print("[cyan]Testing API connections...[/cyan]\n")

    # Test Apollo
    console.print("Testing Apollo.io connection...")
    try:
        apollo = ApolloClient()
        # Try a simple search
        result = apollo.search_people(page=1, per_page=1)
        console.print("[green]✓ Apollo.io: Connected[/green]")
    except Exception as e:
        console.print(f"[red]✗ Apollo.io: Failed - {e}[/red]")

    # Test ElevenLabs
    console.print("Testing ElevenLabs connection...")
    try:
        elevenlabs = ElevenLabsClient()
        agents = elevenlabs.list_agents()
        console.print(f"[green]✓ ElevenLabs: Connected ({len(agents)} agents found)[/green]")

        if agents:
            table = Table(title="Available Agents")
            table.add_column("Agent ID", style="cyan")
            table.add_column("Name", style="green")

            for agent in agents:
                table.add_row(
                    agent.get("agent_id", ""),
                    agent.get("name", "")
                )

            console.print()
            console.print(table)

    except Exception as e:
        console.print(f"[red]✗ ElevenLabs: Failed - {e}[/red]")


def _display_contacts(contacts):
    """Display contacts in a table."""
    table = Table(title=f"Contacts ({len(contacts)} found)")
    table.add_column("Name", style="cyan")
    table.add_column("Phone", style="green")
    table.add_column("Company", style="yellow")
    table.add_column("Title", style="magenta")

    for contact in contacts[:20]:  # Show first 20
        table.add_row(
            contact.get("name", ""),
            contact.get("phone", ""),
            contact.get("company", ""),
            contact.get("title", "")
        )

    if len(contacts) > 20:
        table.add_row("...", "...", "...", "...")

    console.print()
    console.print(table)


def _display_results(results):
    """Display campaign results."""
    console.print("\n[bold]Campaign Results[/bold]\n")

    # Summary table
    table = Table(title="Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Contacts", str(results.get("total_contacts", 0)))
    table.add_row("Completed Calls", str(results.get("completed", 0)))
    table.add_row("Failed Calls", str(results.get("failed", 0)))
    table.add_row("Appointments Scheduled", f"[bold green]{results.get('appointments_scheduled', 0)}[/bold green]")
    table.add_row("No Answer", str(results.get("no_answer", 0)))
    table.add_row("Busy", str(results.get("busy", 0)))
    table.add_row("Voicemail", str(results.get("voicemail", 0)))
    table.add_row("Success Rate", f"{results.get('success_rate', 0):.2f}%")
    table.add_row("Appointment Rate", f"{results.get('appointment_rate', 0):.2f}%")
    table.add_row("Duration", f"{results.get('duration_seconds', 0):.2f}s")

    console.print(table)


def main():
    """Main entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
