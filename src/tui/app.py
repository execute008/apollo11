"""Main TUI application."""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Button, Static, TabbedContent, TabPane
from textual.binding import Binding

from .screens.contact_browser import ContactBrowserScreen
from .screens.calendar_config import CalendarConfigScreen
from .screens.script_composer import ScriptComposerScreen
from .screens.workflow_creator import WorkflowCreatorScreen
from .screens.campaign_monitor import CampaignMonitorScreen


class CallOrchestratorApp(App):
    """Main TUI application for Call Orchestrator."""

    CSS = """
    Screen {
        background: $surface;
    }

    #welcome {
        width: 100%;
        height: 100%;
        content-align: center middle;
    }

    #welcome-box {
        width: 80;
        height: 25;
        border: heavy $primary;
        background: $panel;
        padding: 2;
    }

    .welcome-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .welcome-subtitle {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
    }

    .menu-button {
        width: 100%;
        margin: 1;
    }

    .info-text {
        text-align: center;
        color: $text;
        margin: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("h", "show_help", "Help"),
        Binding("escape", "app.pop_screen", "Back"),
    ]

    TITLE = "Apollo ElevenLabs Call Orchestrator"
    SUB_TITLE = "AI-Powered Call Campaign Manager"

    def compose(self) -> ComposeResult:
        """Compose the main UI."""
        yield Header()
        yield Container(
            Static(
                "[bold cyan]Apollo ElevenLabs Call Orchestrator[/bold cyan]\n\n"
                "[dim]AI-Powered Call Campaign Manager[/dim]\n\n"
                "Welcome! Choose an option to get started:\n",
                classes="welcome-title"
            ),
            Vertical(
                Button("📋 Browse & Select Contacts", id="btn_contacts", classes="menu-button"),
                Button("📅 Configure Calendar Slots", id="btn_calendar", classes="menu-button"),
                Button("✍️  Compose Call Script (AI)", id="btn_script", classes="menu-button"),
                Button("🎯 Create Campaign Workflow", id="btn_workflow", classes="menu-button"),
                Button("📊 Monitor Active Campaign", id="btn_monitor", classes="menu-button"),
                Button("❌ Exit", id="btn_exit", classes="menu-button"),
                id="welcome-box"
            ),
            id="welcome"
        )
        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.title = self.TITLE
        self.sub_title = self.SUB_TITLE

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn_contacts":
            self.push_screen(ContactBrowserScreen())
        elif button_id == "btn_calendar":
            self.push_screen(CalendarConfigScreen())
        elif button_id == "btn_script":
            self.push_screen(ScriptComposerScreen())
        elif button_id == "btn_workflow":
            self.push_screen(WorkflowCreatorScreen())
        elif button_id == "btn_monitor":
            self.push_screen(CampaignMonitorScreen())
        elif button_id == "btn_exit":
            self.exit()

    def action_show_help(self) -> None:
        """Show help information."""
        self.push_screen(HelpScreen())


class HelpScreen(Static):
    """Help screen."""

    def compose(self) -> ComposeResult:
        """Compose help screen."""
        yield Static(
            """
[bold cyan]Apollo ElevenLabs Call Orchestrator - Help[/bold cyan]

[bold]Key Bindings:[/bold]
  q           - Quit application
  h           - Show this help
  ESC         - Go back to previous screen

[bold]Workflow:[/bold]
  1. Browse & Select Contacts - View and select contacts from Apollo.io
  2. Configure Calendar Slots - Set available times for appointments
  3. Compose Call Script - Use AI to generate professional call scripts
  4. Create Campaign - Configure and launch your calling campaign
  5. Monitor Campaign - Watch real-time progress and results

[bold]Tips:[/bold]
  - Start with a small batch of contacts to test your script
  - Use the AI script composer to create effective conversation flows
  - Configure multiple calendar slots for flexibility
  - Monitor campaigns in real-time to track performance

Press ESC to return to main menu.
            """,
            id="help-content"
        )
