"""Calendar configuration screen for setting appointment slots."""

from typing import List, Dict, Any
from datetime import datetime, time, timedelta
from dateutil import parser as date_parser

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Button, Static, Input, Select, DataTable, Label, Checkbox
)
from textual.binding import Binding
from rich.text import Text


class CalendarConfigScreen(Screen):
    """Screen for configuring calendar slots for appointments."""

    CSS = """
    CalendarConfigScreen {
        background: $surface;
    }

    #header-section {
        height: auto;
        padding: 1;
        background: $panel;
        border: solid $primary;
    }

    #slot-form {
        height: auto;
        padding: 1;
        background: $panel;
        border: solid $accent;
        margin: 1;
    }

    #slots-table-container {
        height: 1fr;
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
        width: 20;
        padding: 1;
    }

    .action-button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("a", "add_slot", "Add Slot"),
        Binding("d", "delete_slot", "Delete Slot"),
        Binding("c", "continue_workflow", "Continue →"),
        Binding("escape", "app.pop_screen", "Back"),
    ]

    def __init__(self):
        """Initialize screen."""
        super().__init__()
        self.calendar_slots: List[Dict[str, Any]] = []

        # Default slots
        self.calendar_slots = [
            {
                "day": "Monday-Friday",
                "start_time": "09:00 AM",
                "end_time": "12:00 PM",
                "timezone": "EST",
                "duration_minutes": 30
            },
            {
                "day": "Monday-Friday",
                "start_time": "02:00 PM",
                "end_time": "05:00 PM",
                "timezone": "EST",
                "duration_minutes": 30
            }
        ]

    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Header()

        # Header
        yield Container(
            Static("[bold cyan]Configure Calendar & Appointment Slots[/bold cyan]\n"
                   "[dim]Set up available times for scheduling appointments[/dim]"),
            id="header-section"
        )

        # Slot form
        yield Container(
            Static("[bold]Add New Time Slot[/bold]", classes="form-label"),
            Horizontal(
                Label("Day(s):", classes="form-label"),
                Select(
                    [
                        ("Monday", "Monday"),
                        ("Tuesday", "Tuesday"),
                        ("Wednesday", "Wednesday"),
                        ("Thursday", "Thursday"),
                        ("Friday", "Friday"),
                        ("Saturday", "Saturday"),
                        ("Sunday", "Sunday"),
                        ("Monday-Friday", "Monday-Friday"),
                        ("Saturday-Sunday", "Saturday-Sunday"),
                        ("Every Day", "Every Day"),
                    ],
                    value="Monday-Friday",
                    id="day_select",
                    classes="form-input"
                ),
                classes="form-row"
            ),
            Horizontal(
                Label("Start Time:", classes="form-label"),
                Input(placeholder="09:00 AM", id="start_time_input", classes="form-input"),
                Label("End Time:", classes="form-label"),
                Input(placeholder="05:00 PM", id="end_time_input", classes="form-input"),
                classes="form-row"
            ),
            Horizontal(
                Label("Timezone:", classes="form-label"),
                Select(
                    [
                        ("EST", "EST"),
                        ("CST", "CST"),
                        ("MST", "MST"),
                        ("PST", "PST"),
                        ("UTC", "UTC"),
                    ],
                    value="EST",
                    id="timezone_select",
                    classes="form-input"
                ),
                Label("Duration (min):", classes="form-label"),
                Input(placeholder="30", value="30", id="duration_input", classes="form-input"),
                classes="form-row"
            ),
            Horizontal(
                Button("➕ Add Slot", id="btn_add_slot", variant="primary"),
                classes="form-row"
            ),
            id="slot-form"
        )

        # Slots table
        yield Container(
            Static("[bold]Configured Time Slots[/bold]"),
            DataTable(id="slots_table", zebra_stripes=True),
            id="slots-table-container"
        )

        # Actions
        yield Container(
            Horizontal(
                Button("🗑️  Delete Selected", id="btn_delete", variant="error", classes="action-button"),
                Button("📋 Load Defaults", id="btn_load_defaults", variant="default", classes="action-button"),
                Button("⏭️  Continue to Script Composer", id="btn_continue", variant="success", classes="action-button"),
            ),
            id="actions"
        )

        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Setup table
        table = self.query_one("#slots_table", DataTable)
        table.add_columns("Day(s)", "Start Time", "End Time", "Timezone", "Duration (min)")
        table.cursor_type = "row"

        # Load existing slots
        self.update_slots_table()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn_add_slot":
            self.action_add_slot()
        elif button_id == "btn_delete":
            self.action_delete_slot()
        elif button_id == "btn_load_defaults":
            self.load_default_slots()
        elif button_id == "btn_continue":
            self.action_continue_workflow()

    def action_add_slot(self) -> None:
        """Add a new calendar slot."""
        try:
            day = self.query_one("#day_select", Select).value
            start_time = self.query_one("#start_time_input", Input).value
            end_time = self.query_one("#end_time_input", Input).value
            timezone = self.query_one("#timezone_select", Select).value
            duration = self.query_one("#duration_input", Input).value

            # Validate
            if not start_time or not end_time:
                self.notify("Please enter start and end times", severity="warning")
                return

            # Add slot
            slot = {
                "day": day,
                "start_time": start_time,
                "end_time": end_time,
                "timezone": timezone,
                "duration_minutes": int(duration) if duration else 30
            }

            self.calendar_slots.append(slot)
            self.update_slots_table()

            # Clear inputs
            self.query_one("#start_time_input", Input).value = ""
            self.query_one("#end_time_input", Input).value = ""

            self.notify(f"Added slot: {day} {start_time} - {end_time}")

        except Exception as e:
            self.notify(f"Error adding slot: {e}", severity="error")

    def action_delete_slot(self) -> None:
        """Delete selected slot."""
        table = self.query_one("#slots_table", DataTable)

        if table.cursor_row is not None:
            row_index = table.cursor_row
            if 0 <= row_index < len(self.calendar_slots):
                deleted = self.calendar_slots.pop(row_index)
                self.update_slots_table()
                self.notify(f"Deleted slot: {deleted['day']} {deleted['start_time']}")
        else:
            self.notify("Please select a slot to delete", severity="warning")

    def load_default_slots(self) -> None:
        """Load default calendar slots."""
        self.calendar_slots = [
            {
                "day": "Monday-Friday",
                "start_time": "09:00 AM",
                "end_time": "12:00 PM",
                "timezone": "EST",
                "duration_minutes": 30
            },
            {
                "day": "Monday-Friday",
                "start_time": "02:00 PM",
                "end_time": "05:00 PM",
                "timezone": "EST",
                "duration_minutes": 30
            }
        ]

        self.update_slots_table()
        self.notify("Loaded default slots")

    def update_slots_table(self) -> None:
        """Update the slots table."""
        table = self.query_one("#slots_table", DataTable)
        table.clear()

        for slot in self.calendar_slots:
            table.add_row(
                slot["day"],
                slot["start_time"],
                slot["end_time"],
                slot["timezone"],
                str(slot["duration_minutes"])
            )

    def action_continue_workflow(self) -> None:
        """Continue to next step in workflow."""
        if not self.calendar_slots:
            self.notify("Please add at least one time slot", severity="warning")
            return

        # Store in app state
        self.app.calendar_slots = self.calendar_slots

        self.notify(f"Configured {len(self.calendar_slots)} time slots")

        # Move to script composer
        from .script_composer import ScriptComposerScreen
        self.app.pop_screen()
        self.app.push_screen(ScriptComposerScreen())

    def get_calendar_slots(self) -> List[Dict[str, Any]]:
        """Get configured calendar slots."""
        return self.calendar_slots
