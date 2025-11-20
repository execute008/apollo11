"""Contact browser screen for viewing and selecting Apollo contacts."""

import asyncio
from typing import List, Dict, Any, Optional

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, DataTable, Button, Static, Input, Select,
    Checkbox, Label, ProgressBar
)
from textual.binding import Binding
from rich.text import Text

from ...clients import ApolloClient
from ...config.settings import get_settings


class ContactBrowserScreen(Screen):
    """Screen for browsing and selecting contacts from Apollo."""

    CSS = """
    ContactBrowserScreen {
        background: $surface;
    }

    #controls {
        height: auto;
        padding: 1;
        background: $panel;
        border: solid $primary;
    }

    #filters {
        height: auto;
        padding: 1;
        margin-bottom: 1;
    }

    #contact-table-container {
        height: 1fr;
        border: solid $accent;
    }

    #selection-info {
        height: 3;
        padding: 1;
        background: $panel;
        border: solid $primary;
    }

    #actions {
        height: auto;
        padding: 1;
        background: $panel;
    }

    .filter-input {
        width: 1fr;
        margin: 0 1;
    }

    .action-button {
        margin: 0 1;
    }

    .info-label {
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("f", "fetch_contacts", "Fetch Contacts"),
        Binding("a", "select_all", "Select All"),
        Binding("n", "select_none", "Deselect All"),
        Binding("c", "continue_workflow", "Continue →"),
        Binding("escape", "app.pop_screen", "Back"),
    ]

    def __init__(self):
        """Initialize screen."""
        super().__init__()
        self.apollo_client = ApolloClient()
        self.contacts: List[Dict[str, Any]] = []
        self.selected_contacts: set = set()
        self.current_batch = 0
        self.batch_size = 50

    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Header()

        # Filters and controls
        yield Container(
            Static("[bold cyan]Browse Apollo Contacts[/bold cyan]", classes="info-label"),
            Horizontal(
                Input(placeholder="Search by name...", id="search_input", classes="filter-input"),
                Input(placeholder="Company filter...", id="company_input", classes="filter-input"),
                Input(placeholder="Title filter...", id="title_input", classes="filter-input"),
                id="filters"
            ),
            Horizontal(
                Button("🔍 Fetch Contacts", id="btn_fetch", variant="primary"),
                Button("⬅️ Previous Batch", id="btn_prev", variant="default"),
                Button("➡️ Next Batch", id="btn_next", variant="default"),
                Static("Batch: 1", id="batch_info", classes="info-label"),
                id="controls"
            ),
            id="controls"
        )

        # Contact table
        yield Container(
            DataTable(id="contact_table", zebra_stripes=True),
            id="contact-table-container"
        )

        # Selection info
        yield Container(
            Horizontal(
                Static("Selected: 0", id="selected_count", classes="info-label"),
                Static("Total: 0", id="total_count", classes="info-label"),
                ProgressBar(total=100, show_eta=False, id="progress", classes="info-label"),
            ),
            id="selection-info"
        )

        # Actions
        yield Container(
            Horizontal(
                Button("✓ Select All", id="btn_select_all", classes="action-button"),
                Button("✗ Deselect All", id="btn_deselect_all", classes="action-button"),
                Button("⏭️  Continue to Calendar", id="btn_continue", variant="success", classes="action-button"),
            ),
            id="actions"
        )

        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Setup table
        table = self.query_one("#contact_table", DataTable)
        table.add_columns("☑️", "Name", "Phone", "Company", "Title", "Email")
        table.cursor_type = "row"

        # Auto-fetch on mount
        self.fetch_contacts_async()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn_fetch":
            await self.action_fetch_contacts()
        elif button_id == "btn_prev":
            if self.current_batch > 0:
                self.current_batch -= 1
                await self.action_fetch_contacts()
        elif button_id == "btn_next":
            self.current_batch += 1
            await self.action_fetch_contacts()
        elif button_id == "btn_select_all":
            self.action_select_all()
        elif button_id == "btn_deselect_all":
            self.action_select_none()
        elif button_id == "btn_continue":
            await self.action_continue_workflow()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection to toggle contact."""
        row_key = event.row_key
        contact_id = str(row_key.value)

        if contact_id in self.selected_contacts:
            self.selected_contacts.remove(contact_id)
        else:
            self.selected_contacts.add(contact_id)

        self.update_table_selection()
        self.update_selection_info()

    def fetch_contacts_async(self) -> None:
        """Fetch contacts asynchronously."""
        asyncio.create_task(self.action_fetch_contacts())

    async def action_fetch_contacts(self) -> None:
        """Fetch contacts from Apollo."""
        progress = self.query_one("#progress", ProgressBar)
        progress.update(progress=0)

        try:
            # Get filter values
            search = self.query_one("#search_input", Input).value
            company = self.query_one("#company_input", Input).value
            title = self.query_one("#title_input", Input).value

            # Build filters
            filters = {}
            if search:
                filters["person_name"] = search
            if company:
                filters["organization_name"] = company
            if title:
                filters["person_titles"] = [title]

            # Fetch contacts
            progress.update(progress=30)

            # Run in thread to avoid blocking
            loop = asyncio.get_event_loop()
            self.contacts = await loop.run_in_executor(
                None,
                lambda: self.apollo_client.get_contacts_with_phones(
                    exclude_with_appointments=True,
                    additional_filters=filters,
                    limit=self.batch_size
                )
            )

            progress.update(progress=70)

            # Update table
            self.update_contact_table()

            progress.update(progress=100)

            # Update batch info
            batch_info = self.query_one("#batch_info", Static)
            batch_info.update(f"Batch: {self.current_batch + 1}")

        except Exception as e:
            self.notify(f"Error fetching contacts: {e}", severity="error")
            progress.update(progress=0)

    def update_contact_table(self) -> None:
        """Update the contact table with fetched contacts."""
        table = self.query_one("#contact_table", DataTable)
        table.clear()

        for contact in self.contacts:
            contact_id = contact.get("id", "")
            is_selected = str(contact_id) in self.selected_contacts
            checkbox = "✓" if is_selected else "☐"

            table.add_row(
                checkbox,
                contact.get("name", ""),
                contact.get("phone", ""),
                contact.get("company", ""),
                contact.get("title", ""),
                contact.get("email", ""),
                key=str(contact_id)
            )

        self.update_selection_info()

    def update_table_selection(self) -> None:
        """Update table to reflect selection changes."""
        table = self.query_one("#contact_table", DataTable)

        for row_key in table.rows:
            contact_id = str(row_key.value)
            is_selected = contact_id in self.selected_contacts
            checkbox = "✓" if is_selected else "☐"

            # Update checkbox column
            table.update_cell(row_key, "☑️", checkbox)

    def update_selection_info(self) -> None:
        """Update selection information."""
        selected_count = self.query_one("#selected_count", Static)
        total_count = self.query_one("#total_count", Static)
        progress = self.query_one("#progress", ProgressBar)

        selected = len(self.selected_contacts)
        total = len(self.contacts)

        selected_count.update(f"Selected: {selected}")
        total_count.update(f"Total: {total}")

        if total > 0:
            progress.update(total=total, progress=selected)

    def action_select_all(self) -> None:
        """Select all contacts."""
        for contact in self.contacts:
            contact_id = str(contact.get("id", ""))
            if contact_id:
                self.selected_contacts.add(contact_id)

        self.update_table_selection()
        self.update_selection_info()
        self.notify(f"Selected all {len(self.contacts)} contacts")

    def action_select_none(self) -> None:
        """Deselect all contacts."""
        self.selected_contacts.clear()
        self.update_table_selection()
        self.update_selection_info()
        self.notify("Cleared selection")

    async def action_continue_workflow(self) -> None:
        """Continue to next step in workflow."""
        if not self.selected_contacts:
            self.notify("Please select at least one contact", severity="warning")
            return

        # Get selected contact objects
        selected = [
            c for c in self.contacts
            if str(c.get("id", "")) in self.selected_contacts
        ]

        self.notify(f"Proceeding with {len(selected)} contacts...")

        # Store in app state and move to calendar config
        self.app.selected_contacts = selected

        from .calendar_config import CalendarConfigScreen
        self.app.pop_screen()
        self.app.push_screen(CalendarConfigScreen())

    def get_selected_contacts(self) -> List[Dict[str, Any]]:
        """Get list of selected contacts."""
        return [
            c for c in self.contacts
            if str(c.get("id", "")) in self.selected_contacts
        ]
