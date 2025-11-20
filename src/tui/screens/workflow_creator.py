"""Workflow creator screen for configuring and launching campaigns."""

import asyncio
from typing import Dict, Any, Optional, List

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Button, Static, Input, Select, Label, Checkbox, TabbedContent, TabPane
)
from textual.binding import Binding

from ...orchestrator import CallOrchestrator
from ...config.settings import get_settings


class WorkflowCreatorScreen(Screen):
    """Screen for creating and reviewing the complete campaign workflow."""

    CSS = """
    WorkflowCreatorScreen {
        background: $surface;
    }

    #header-section {
        height: auto;
        padding: 1;
        background: $panel;
        border: solid $primary;
    }

    #review-section {
        height: 1fr;
        padding: 1;
        border: solid $accent;
        margin: 1;
    }

    #config-section {
        height: auto;
        padding: 1;
        background: $panel;
        border: solid $accent;
        margin: 1;
    }

    #actions {
        height: auto;
        padding: 1;
        background: $panel;
    }

    .form-row {
        height: auto;
        padding: 0 1;
        margin: 1 0;
    }

    .form-input {
        width: 1fr;
        margin: 0 1;
    }

    .form-label {
        width: 25;
        padding: 1;
    }

    .action-button {
        margin: 0 1;
    }

    .review-box {
        margin: 1;
        padding: 1;
        border: solid $primary;
    }

    .success-text {
        color: $success;
    }

    .warning-text {
        color: $warning;
    }
    """

    BINDINGS = [
        Binding("l", "launch_campaign", "Launch Campaign"),
        Binding("s", "save_workflow", "Save Workflow"),
        Binding("escape", "app.pop_screen", "Back"),
    ]

    def __init__(self):
        """Initialize screen."""
        super().__init__()
        self.orchestrator: Optional[CallOrchestrator] = None

    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Header()

        # Header
        yield Container(
            Static("[bold cyan]Campaign Workflow Creator[/bold cyan]\n"
                   "[dim]Review and configure your complete calling campaign[/dim]"),
            id="header-section"
        )

        # Review section
        yield ScrollableContainer(
            TabbedContent(
                TabPane("📋 Summary", id="tab_summary"),
                TabPane("👥 Contacts", id="tab_contacts"),
                TabPane("📅 Calendar", id="tab_calendar"),
                TabPane("📝 Script", id="tab_script"),
                id="review_tabs"
            ),
            id="review-section"
        )

        # Configuration section
        yield Container(
            Static("[bold]Campaign Settings[/bold]", classes="form-label"),
            Horizontal(
                Label("Campaign Name:", classes="form-label"),
                Input(
                    placeholder="e.g., Q4 2025 Product Demo Campaign",
                    id="campaign_name_input",
                    classes="form-input"
                ),
                classes="form-row"
            ),
            Horizontal(
                Label("Max Concurrent Calls:", classes="form-label"),
                Select(
                    [
                        ("1 (Sequential)", "1"),
                        ("3 (Conservative)", "3"),
                        ("5 (Balanced)", "5"),
                        ("10 (Aggressive)", "10"),
                        ("15 (Maximum)", "15"),
                    ],
                    value="5",
                    id="concurrency_select",
                    classes="form-input"
                ),
                Label("Retry Attempts:", classes="form-label"),
                Select(
                    [
                        ("0 (No retry)", "0"),
                        ("1", "1"),
                        ("2", "2"),
                        ("3 (Recommended)", "3"),
                        ("5", "5"),
                    ],
                    value="3",
                    id="retry_select",
                    classes="form-input"
                ),
                classes="form-row"
            ),
            Horizontal(
                Label("Call Timeout (sec):", classes="form-label"),
                Select(
                    [
                        ("60", "60"),
                        ("120", "120"),
                        ("180", "180"),
                        ("300 (5 min)", "300"),
                        ("600 (10 min)", "600"),
                    ],
                    value="300",
                    id="timeout_select",
                    classes="form-input"
                ),
                classes="form-row"
            ),
            Horizontal(
                Checkbox("Save results to file", value=True, id="save_results_check"),
                Checkbox("Update Apollo after calls", value=True, id="update_apollo_check"),
                Checkbox("Record calls", value=True, id="record_calls_check"),
                classes="form-row"
            ),
            id="config-section"
        )

        # Actions
        yield Container(
            Horizontal(
                Button("💾 Save Workflow", id="btn_save", variant="default", classes="action-button"),
                Button("🧪 Test with 1 Contact", id="btn_test", variant="default", classes="action-button"),
                Button("🚀 Launch Campaign", id="btn_launch", variant="success", classes="action-button"),
            ),
            id="actions"
        )

        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Add content to tabs
        self.populate_summary_tab()
        self.populate_contacts_tab()
        self.populate_calendar_tab()
        self.populate_script_tab()

    def populate_summary_tab(self) -> None:
        """Populate the summary tab."""
        tab = self.query_one("#tab_summary", TabPane)

        # Get workflow data from app
        contacts = getattr(self.app, 'selected_contacts', [])
        calendar_slots = getattr(self.app, 'calendar_slots', [])
        script = getattr(self.app, 'call_script', {})

        summary_text = f"""[bold]Campaign Overview[/bold]

[bold cyan]Contacts:[/bold cyan]
  • Total selected: [bold]{len(contacts)}[/bold]
  • Ready to call: [bold class='success-text']✓ {len(contacts)}[/bold]

[bold cyan]Calendar Configuration:[/bold cyan]
  • Time slots configured: [bold]{len(calendar_slots)}[/bold]
  • Status: [bold class='{"success-text" if calendar_slots else "warning-text"}']{"✓ Ready" if calendar_slots else "⚠ Not configured"}[/bold]

[bold cyan]Call Script:[/bold cyan]
  • Script status: [bold class='{"success-text" if script else "warning-text"}']{"✓ Ready" if script else "⚠ Not generated"}[/bold]
  • Has opening: [bold]{"✓" if script.get("opening") else "✗"}[/bold]
  • Has objection handling: [bold]{"✓" if script.get("objection_handling") else "✗"}[/bold]
  • Has agent instructions: [bold]{"✓" if script.get("agent_instructions") else "✗"}[/bold]

[bold cyan]Campaign Readiness:[/bold cyan]
  {"[bold class='success-text']✓ All requirements met - Ready to launch![/bold]" if (contacts and calendar_slots and script) else "[bold class='warning-text']⚠ Please complete all sections before launching[/bold]"}

[bold cyan]Estimated Campaign Duration:[/bold cyan]
  • With 5 concurrent calls: ~{self._estimate_duration(len(contacts), 5)} minutes
  • With 10 concurrent calls: ~{self._estimate_duration(len(contacts), 10)} minutes

[bold cyan]API Usage Estimate:[/bold cyan]
  • ElevenLabs calls: {len(contacts)} outbound calls
  • Apollo updates: {len(contacts)} contact updates (if appointments scheduled)
"""

        tab.mount(Static(summary_text))

    def populate_contacts_tab(self) -> None:
        """Populate the contacts tab."""
        tab = self.query_one("#tab_contacts", TabPane)

        contacts = getattr(self.app, 'selected_contacts', [])

        if not contacts:
            tab.mount(Static("[yellow]No contacts selected. Go back to Contact Browser.[/yellow]"))
            return

        contacts_text = f"[bold]Selected Contacts ({len(contacts)})[/bold]\n\n"

        for i, contact in enumerate(contacts[:20], 1):  # Show first 20
            contacts_text += f"{i}. [cyan]{contact.get('name', 'Unknown')}[/cyan]\n"
            contacts_text += f"   📞 {contact.get('phone', 'No phone')}\n"
            contacts_text += f"   🏢 {contact.get('company', 'No company')}\n"
            contacts_text += f"   💼 {contact.get('title', 'No title')}\n\n"

        if len(contacts) > 20:
            contacts_text += f"\n... and {len(contacts) - 20} more contacts\n"

        tab.mount(Static(contacts_text))

    def populate_calendar_tab(self) -> None:
        """Populate the calendar tab."""
        tab = self.query_one("#tab_calendar", TabPane)

        calendar_slots = getattr(self.app, 'calendar_slots', [])

        if not calendar_slots:
            tab.mount(Static("[yellow]No calendar slots configured. Go back to Calendar Config.[/yellow]"))
            return

        calendar_text = f"[bold]Configured Time Slots ({len(calendar_slots)})[/bold]\n\n"

        for i, slot in enumerate(calendar_slots, 1):
            calendar_text += f"{i}. [cyan]{slot.get('day', 'Unknown')}[/cyan]\n"
            calendar_text += f"   ⏰ {slot.get('start_time', '')} - {slot.get('end_time', '')} {slot.get('timezone', '')}\n"
            calendar_text += f"   ⏱️  {slot.get('duration_minutes', 30)} minute appointments\n\n"

        tab.mount(Static(calendar_text))

    def populate_script_tab(self) -> None:
        """Populate the script tab."""
        tab = self.query_one("#tab_script", TabPane)

        script = getattr(self.app, 'call_script', {})

        if not script:
            tab.mount(Static("[yellow]No script generated. Go back to Script Composer.[/yellow]"))
            return

        script_text = f"""[bold]Call Script Preview[/bold]

[bold cyan]Opening:[/bold cyan]
{script.get('opening', 'Not configured')}

[bold cyan]Value Proposition:[/bold cyan]
{script.get('value_proposition', 'Not configured')}

[bold cyan]Appointment Request:[/bold cyan]
{script.get('appointment_request', 'Not configured')}

[bold cyan]Agent Instructions:[/bold cyan]
{script.get('agent_instructions', 'Not configured')}

[dim]Use the tabs above to see the full script and objection handling.[/dim]
"""

        tab.mount(Static(script_text))

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn_save":
            self.action_save_workflow()
        elif button_id == "btn_test":
            await self.test_campaign()
        elif button_id == "btn_launch":
            await self.action_launch_campaign()

    def action_save_workflow(self) -> None:
        """Save the workflow configuration."""
        import json
        from pathlib import Path
        from datetime import datetime

        try:
            workflow = {
                "campaign_name": self.query_one("#campaign_name_input", Input).value or "Unnamed Campaign",
                "created_at": datetime.now().isoformat(),
                "contacts": getattr(self.app, 'selected_contacts', []),
                "calendar_slots": getattr(self.app, 'calendar_slots', []),
                "script": getattr(self.app, 'call_script', {}),
                "settings": {
                    "max_concurrent_calls": int(self.query_one("#concurrency_select", Select).value),
                    "retry_attempts": int(self.query_one("#retry_select", Select).value),
                    "timeout_seconds": int(self.query_one("#timeout_select", Select).value),
                    "save_results": self.query_one("#save_results_check", Checkbox).value,
                    "update_apollo": self.query_one("#update_apollo_check", Checkbox).value,
                    "record_calls": self.query_one("#record_calls_check", Checkbox).value,
                }
            }

            # Save to file
            workflows_dir = Path("workflows")
            workflows_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            campaign_name = workflow["campaign_name"].replace(" ", "_").lower()
            filename = f"workflow_{campaign_name}_{timestamp}.json"

            filepath = workflows_dir / filename

            with open(filepath, "w") as f:
                json.dump(workflow, f, indent=2)

            self.notify(f"Workflow saved to {filepath}", severity="information")

        except Exception as e:
            self.notify(f"Error saving workflow: {e}", severity="error")

    async def test_campaign(self) -> None:
        """Test campaign with 1 contact."""
        contacts = getattr(self.app, 'selected_contacts', [])

        if not contacts:
            self.notify("No contacts selected", severity="warning")
            return

        self.notify("Starting test with 1 contact...", timeout=3)

        # Launch campaign monitor with test mode
        from .campaign_monitor import CampaignMonitorScreen
        self.app.pop_screen()
        self.app.push_screen(CampaignMonitorScreen(test_mode=True, test_contacts=[contacts[0]]))

    async def action_launch_campaign(self) -> None:
        """Launch the campaign."""
        contacts = getattr(self.app, 'selected_contacts', [])
        calendar_slots = getattr(self.app, 'calendar_slots', [])
        script = getattr(self.app, 'call_script', {})

        # Validate
        if not contacts:
            self.notify("No contacts selected. Go back to Contact Browser.", severity="error")
            return

        if not calendar_slots:
            self.notify("No calendar slots configured. Go back to Calendar Config.", severity="error")
            return

        if not script:
            self.notify("No script generated. Go back to Script Composer.", severity="error")
            return

        # Confirm
        campaign_name = self.query_one("#campaign_name_input", Input).value or "Unnamed Campaign"

        self.notify(f"Launching campaign '{campaign_name}' with {len(contacts)} contacts...", timeout=3)

        # Launch campaign monitor
        from .campaign_monitor import CampaignMonitorScreen
        self.app.pop_screen()
        self.app.push_screen(CampaignMonitorScreen(test_mode=False))

    def _estimate_duration(self, num_contacts: int, concurrency: int) -> int:
        """Estimate campaign duration in minutes."""
        # Assume average 2 minutes per call
        avg_call_duration = 2
        total_time = (num_contacts * avg_call_duration) / concurrency
        return int(total_time)
