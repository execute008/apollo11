"""Campaign monitoring screen with real-time progress tracking."""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Button, Static, ProgressBar, DataTable, Label, Log
)
from textual.binding import Binding
from rich.text import Text

from ...orchestrator import CallOrchestrator
from ...config.settings import get_settings


class CampaignMonitorScreen(Screen):
    """Screen for monitoring active campaign progress."""

    CSS = """
    CampaignMonitorScreen {
        background: $surface;
    }

    #header-section {
        height: auto;
        padding: 1;
        background: $panel;
        border: solid $primary;
    }

    #stats-section {
        height: 12;
        padding: 1;
        border: solid $accent;
        margin: 1;
    }

    #progress-section {
        height: auto;
        padding: 1;
        background: $panel;
        border: solid $primary;
        margin: 1;
    }

    #calls-table-container {
        height: 1fr;
        border: solid $accent;
        margin: 1;
    }

    #log-container {
        height: 15;
        border: solid $accent;
        margin: 1;
    }

    #actions {
        height: auto;
        padding: 1;
        background: $panel;
    }

    .stat-box {
        width: 1fr;
        padding: 1;
        margin: 0 1;
        border: solid $primary;
        text-align: center;
    }

    .stat-value {
        text-style: bold;
        text-align: center;
    }

    .stat-label {
        text-align: center;
        color: $text-muted;
    }

    .action-button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("p", "pause_campaign", "Pause"),
        Binding("r", "resume_campaign", "Resume"),
        Binding("x", "cancel_campaign", "Cancel"),
        Binding("escape", "confirm_exit", "Exit"),
    ]

    def __init__(self, test_mode: bool = False, test_contacts: Optional[List[Dict]] = None):
        """Initialize screen."""
        super().__init__()
        self.test_mode = test_mode
        self.test_contacts = test_contacts
        self.orchestrator: Optional[CallOrchestrator] = None
        self.is_running = False
        self.is_paused = False
        self.start_time: Optional[datetime] = None
        self.campaign_task: Optional[asyncio.Task] = None
        self.stats = {
            "total": 0,
            "completed": 0,
            "in_progress": 0,
            "failed": 0,
            "appointments": 0,
            "success_rate": 0.0,
            "appointment_rate": 0.0
        }

    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Header()

        # Header
        yield Container(
            Static("[bold cyan]Campaign Monitor[/bold cyan] " +
                   ("[yellow][TEST MODE][/yellow]" if self.test_mode else "")),
            Static("[dim]Real-time campaign progress and results[/dim]"),
            id="header-section"
        )

        # Stats section
        yield Container(
            Horizontal(
                Container(
                    Static("0", id="stat_total", classes="stat-value"),
                    Static("Total Contacts", classes="stat-label"),
                    classes="stat-box"
                ),
                Container(
                    Static("0", id="stat_completed", classes="stat-value"),
                    Static("Completed", classes="stat-label"),
                    classes="stat-box"
                ),
                Container(
                    Static("0", id="stat_inprogress", classes="stat-value"),
                    Static("In Progress", classes="stat-label"),
                    classes="stat-box"
                ),
                Container(
                    Static("0", id="stat_failed", classes="stat-value"),
                    Static("Failed", classes="stat-label"),
                    classes="stat-box"
                ),
                Container(
                    Static("0", id="stat_appointments", classes="stat-value success-text"),
                    Static("Appointments", classes="stat-label"),
                    classes="stat-box"
                ),
            ),
            Horizontal(
                Container(
                    Static("0%", id="stat_success_rate", classes="stat-value"),
                    Static("Success Rate", classes="stat-label"),
                    classes="stat-box"
                ),
                Container(
                    Static("0%", id="stat_appt_rate", classes="stat-value"),
                    Static("Appointment Rate", classes="stat-label"),
                    classes="stat-box"
                ),
                Container(
                    Static("00:00:00", id="stat_elapsed", classes="stat-value"),
                    Static("Elapsed Time", classes="stat-label"),
                    classes="stat-box"
                ),
            ),
            id="stats-section"
        )

        # Progress section
        yield Container(
            Label("Campaign Progress:"),
            ProgressBar(total=100, show_eta=True, id="campaign_progress"),
            id="progress-section"
        )

        # Calls table
        yield Container(
            Static("[bold]Call Details[/bold]"),
            DataTable(id="calls_table", zebra_stripes=True),
            id="calls-table-container"
        )

        # Log
        yield Container(
            Static("[bold]Activity Log[/bold]"),
            Log(id="activity_log", auto_scroll=True),
            id="log-container"
        )

        # Actions
        yield Container(
            Horizontal(
                Button("⏸️  Pause", id="btn_pause", variant="warning", classes="action-button"),
                Button("▶️  Resume", id="btn_resume", variant="primary", classes="action-button", disabled=True),
                Button("❌ Cancel Campaign", id="btn_cancel", variant="error", classes="action-button"),
                Button("📊 Export Results", id="btn_export", variant="default", classes="action-button"),
            ),
            id="actions"
        )

        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Setup calls table
        table = self.query_one("#calls_table", DataTable)
        table.add_columns("Contact", "Phone", "Status", "Duration", "Result")

        # Start campaign
        self.start_campaign()

    def start_campaign(self) -> None:
        """Start the campaign execution."""
        self.is_running = True
        self.start_time = datetime.now()

        log = self.query_one("#activity_log", Log)
        log.write_line("[bold cyan]Campaign started[/bold cyan]")

        # Start campaign task
        self.campaign_task = asyncio.create_task(self.run_campaign())

        # Start stats update task
        asyncio.create_task(self.update_stats_loop())

    async def run_campaign(self) -> None:
        """Run the actual campaign."""
        try:
            log = self.query_one("#activity_log", Log)

            # Get campaign data
            if self.test_mode and self.test_contacts:
                contacts = self.test_contacts
                log.write_line(f"[yellow]TEST MODE: Using {len(contacts)} test contact(s)[/yellow]")
            else:
                contacts = getattr(self.app, 'selected_contacts', [])

            if not contacts:
                log.write_line("[red]Error: No contacts selected[/red]")
                return

            calendar_slots = getattr(self.app, 'calendar_slots', [])
            script = getattr(self.app, 'call_script', {})

            # Update total
            self.stats["total"] = len(contacts)
            self.update_stat_displays()

            log.write_line(f"Initializing orchestrator for {len(contacts)} contacts...")

            # Create orchestrator
            self.orchestrator = CallOrchestrator()

            # Note: In a real implementation, we would:
            # 1. Configure the ElevenLabs agent with the script
            # 2. Set up calendar integration
            # 3. Run the actual campaign

            # For demonstration, we'll simulate the campaign
            await self.simulate_campaign(contacts)

        except Exception as e:
            log = self.query_one("#activity_log", Log)
            log.write_line(f"[red]Campaign error: {e}[/red]")
            self.notify(f"Campaign error: {e}", severity="error")

    async def simulate_campaign(self, contacts: List[Dict]) -> None:
        """Simulate campaign execution (for demonstration)."""
        log = self.query_one("#activity_log", Log)
        table = self.query_one("#calls_table", DataTable)
        progress = self.query_one("#campaign_progress", ProgressBar)

        progress.update(total=len(contacts), progress=0)

        for i, contact in enumerate(contacts):
            if not self.is_running:
                log.write_line("[yellow]Campaign cancelled[/yellow]")
                break

            while self.is_paused:
                await asyncio.sleep(0.5)

            # Simulate call
            log.write_line(f"Calling {contact.get('name', 'Unknown')}...")

            self.stats["in_progress"] = 1

            # Add to table
            row_key = table.add_row(
                contact.get("name", "Unknown"),
                contact.get("phone", ""),
                "Calling...",
                "-",
                "-"
            )

            self.update_stat_displays()

            # Simulate call duration
            await asyncio.sleep(2 if self.test_mode else 5)

            # Random outcome (70% success, 30% of success = appointment)
            import random
            success = random.random() < 0.7
            appointment = success and random.random() < 0.3

            if appointment:
                status = "Completed"
                result = "Appointment Scheduled ✓"
                self.stats["appointments"] += 1
                log.write_line(f"[green]✓ Appointment scheduled with {contact.get('name')}[/green]")
            elif success:
                status = "Completed"
                result = "No appointment"
                log.write_line(f"Call completed with {contact.get('name')}")
            else:
                status = "Failed"
                result = "No answer"
                self.stats["failed"] += 1
                log.write_line(f"[yellow]Failed to reach {contact.get('name')}[/yellow]")

            # Update table
            table.update_cell(row_key, "Status", status)
            table.update_cell(row_key, "Duration", f"{random.randint(30, 180)}s")
            table.update_cell(row_key, "Result", result)

            self.stats["in_progress"] = 0
            self.stats["completed"] += 1

            progress.update(progress=i + 1)
            self.update_stat_displays()

        # Campaign complete
        self.is_running = False
        log.write_line("[bold green]Campaign completed![/bold green]")
        self.notify("Campaign completed successfully!", severity="information")

    async def update_stats_loop(self) -> None:
        """Update statistics display periodically."""
        while self.is_running:
            self.update_stat_displays()
            await asyncio.sleep(1)

    def update_stat_displays(self) -> None:
        """Update all stat displays."""
        self.query_one("#stat_total", Static).update(str(self.stats["total"]))
        self.query_one("#stat_completed", Static).update(str(self.stats["completed"]))
        self.query_one("#stat_inprogress", Static).update(str(self.stats["in_progress"]))
        self.query_one("#stat_failed", Static).update(str(self.stats["failed"]))
        self.query_one("#stat_appointments", Static).update(str(self.stats["appointments"]))

        # Calculate rates
        if self.stats["total"] > 0:
            success_rate = (self.stats["completed"] / self.stats["total"]) * 100
            appt_rate = (self.stats["appointments"] / self.stats["total"]) * 100
        else:
            success_rate = 0
            appt_rate = 0

        self.query_one("#stat_success_rate", Static).update(f"{success_rate:.1f}%")
        self.query_one("#stat_appt_rate", Static).update(f"{appt_rate:.1f}%")

        # Update elapsed time
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            hours = elapsed.seconds // 3600
            minutes = (elapsed.seconds % 3600) // 60
            seconds = elapsed.seconds % 60
            self.query_one("#stat_elapsed", Static).update(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn_pause":
            self.action_pause_campaign()
        elif button_id == "btn_resume":
            self.action_resume_campaign()
        elif button_id == "btn_cancel":
            self.action_cancel_campaign()
        elif button_id == "btn_export":
            self.export_results()

    def action_pause_campaign(self) -> None:
        """Pause the campaign."""
        if not self.is_paused:
            self.is_paused = True
            self.query_one("#btn_pause", Button).disabled = True
            self.query_one("#btn_resume", Button).disabled = False

            log = self.query_one("#activity_log", Log)
            log.write_line("[yellow]Campaign paused[/yellow]")
            self.notify("Campaign paused")

    def action_resume_campaign(self) -> None:
        """Resume the campaign."""
        if self.is_paused:
            self.is_paused = False
            self.query_one("#btn_pause", Button).disabled = False
            self.query_one("#btn_resume", Button).disabled = True

            log = self.query_one("#activity_log", Log)
            log.write_line("[cyan]Campaign resumed[/cyan]")
            self.notify("Campaign resumed")

    def action_cancel_campaign(self) -> None:
        """Cancel the campaign."""
        if self.is_running:
            self.is_running = False

            if self.campaign_task:
                self.campaign_task.cancel()

            log = self.query_one("#activity_log", Log)
            log.write_line("[red]Campaign cancelled by user[/red]")
            self.notify("Campaign cancelled", severity="warning")

    def action_confirm_exit(self) -> None:
        """Confirm before exiting."""
        if self.is_running:
            self.notify("Campaign is running. Cancel it first or wait for completion.", severity="warning")
        else:
            self.app.pop_screen()

    def export_results(self) -> None:
        """Export campaign results."""
        from pathlib import Path
        from datetime import datetime
        import json

        try:
            results_dir = Path("results")
            results_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"campaign_results_{timestamp}.json"

            filepath = results_dir / filename

            results = {
                "timestamp": timestamp,
                "test_mode": self.test_mode,
                "stats": self.stats,
                "duration": str(datetime.now() - self.start_time) if self.start_time else "0"
            }

            with open(filepath, "w") as f:
                json.dump(results, f, indent=2)

            self.notify(f"Results exported to {filepath}", severity="information")

            log = self.query_one("#activity_log", Log)
            log.write_line(f"Results exported to {filepath}")

        except Exception as e:
            self.notify(f"Error exporting results: {e}", severity="error")
