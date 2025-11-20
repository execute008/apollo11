"""Script composer screen with AI-powered script generation."""

import asyncio
from typing import Dict, Any, Optional

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Button, Static, Input, TextArea, Select, Label, ProgressBar, TabbedContent, TabPane
)
from textual.binding import Binding

from ...llm import LLMClient


class ScriptComposerScreen(Screen):
    """Screen for composing call scripts with AI assistance."""

    CSS = """
    ScriptComposerScreen {
        background: $surface;
    }

    #header-section {
        height: auto;
        padding: 1;
        background: $panel;
        border: solid $primary;
    }

    #input-form {
        height: auto;
        padding: 1;
        background: $panel;
        border: solid $accent;
        margin: 1;
    }

    #script-display {
        height: 1fr;
        padding: 1;
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

    .script-section {
        margin: 1 0;
        padding: 1;
        border: solid $primary;
    }

    TextArea {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("g", "generate_script", "Generate Script"),
        Binding("r", "refine_script", "Refine Script"),
        Binding("c", "continue_workflow", "Continue →"),
        Binding("escape", "app.pop_screen", "Back"),
    ]

    def __init__(self):
        """Initialize screen."""
        super().__init__()
        self.llm_client: Optional[LLMClient] = None
        self.current_script: Dict[str, str] = {}
        self.is_generating = False

        try:
            self.llm_client = LLMClient()
        except Exception as e:
            self.notify(f"LLM client not available: {e}", severity="warning")

    def compose(self) -> ComposeResult:
        """Compose the UI."""
        yield Header()

        # Header
        yield Container(
            Static("[bold cyan]AI-Powered Call Script Composer[/bold cyan]\n"
                   "[dim]Generate professional call scripts using AI[/dim]"),
            id="header-section"
        )

        # Input form
        yield Container(
            Static("[bold]Campaign Configuration[/bold]", classes="form-label"),
            Horizontal(
                Label("Campaign Purpose:", classes="form-label"),
                Input(
                    placeholder="e.g., Schedule product demo for SaaS platform",
                    id="purpose_input",
                    classes="form-input"
                ),
                classes="form-row"
            ),
            Horizontal(
                Label("Target Audience:", classes="form-label"),
                Input(
                    placeholder="e.g., CTOs and Technical Leads at B2B companies",
                    id="audience_input",
                    classes="form-input"
                ),
                classes="form-row"
            ),
            Horizontal(
                Label("Company/Product:", classes="form-label"),
                Input(
                    placeholder="e.g., TechCorp - AI-powered analytics platform",
                    id="company_input",
                    classes="form-input"
                ),
                classes="form-row"
            ),
            Horizontal(
                Label("Value Proposition:", classes="form-label"),
                Input(
                    placeholder="e.g., Reduce data analysis time by 70%",
                    id="value_input",
                    classes="form-input"
                ),
                classes="form-row"
            ),
            Horizontal(
                Label("Tone:", classes="form-label"),
                Select(
                    [
                        ("Professional", "professional"),
                        ("Friendly", "friendly"),
                        ("Consultative", "consultative"),
                        ("Direct", "direct"),
                        ("Casual", "casual"),
                    ],
                    value="professional",
                    id="tone_select",
                    classes="form-input"
                ),
                Label("LLM Provider:", classes="form-label"),
                Select(
                    [
                        ("Anthropic Claude", "anthropic"),
                        ("OpenAI GPT", "openai"),
                    ],
                    value="anthropic",
                    id="provider_select",
                    classes="form-input"
                ),
                classes="form-row"
            ),
            Horizontal(
                Button("🤖 Generate Script with AI", id="btn_generate", variant="primary"),
                Button("📝 Load Template", id="btn_template", variant="default"),
                ProgressBar(total=100, show_eta=False, id="generation_progress"),
                classes="form-row"
            ),
            id="input-form"
        )

        # Script display with tabs
        yield Container(
            TabbedContent(
                TabPane("Full Script", id="tab_full"),
                TabPane("Opening", id="tab_opening"),
                TabPane("Value Prop", id="tab_value"),
                TabPane("Objections", id="tab_objections"),
                TabPane("Closing", id="tab_closing"),
                TabPane("Instructions", id="tab_instructions"),
                id="script_tabs"
            ),
            id="script-display"
        )

        # Actions
        yield Container(
            Horizontal(
                Button("🔄 Refine Script", id="btn_refine", variant="default", classes="action-button"),
                Button("💾 Save Script", id="btn_save", variant="default", classes="action-button"),
                Button("⏭️  Continue to Workflow", id="btn_continue", variant="success", classes="action-button"),
            ),
            id="actions"
        )

        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Add text areas to tabs
        tab_full = self.query_one("#tab_full", TabPane)
        tab_full.mount(TextArea(id="script_full", language="markdown"))

        tab_opening = self.query_one("#tab_opening", TabPane)
        tab_opening.mount(TextArea(id="script_opening", language="markdown"))

        tab_value = self.query_one("#tab_value", TabPane)
        tab_value.mount(TextArea(id="script_value", language="markdown"))

        tab_objections = self.query_one("#tab_objections", TabPane)
        tab_objections.mount(TextArea(id="script_objections", language="markdown"))

        tab_closing = self.query_one("#tab_closing", TabPane)
        tab_closing.mount(TextArea(id="script_closing", language="markdown"))

        tab_instructions = self.query_one("#tab_instructions", TabPane)
        tab_instructions.mount(TextArea(id="script_instructions", language="markdown"))

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn_generate":
            await self.action_generate_script()
        elif button_id == "btn_refine":
            await self.action_refine_script()
        elif button_id == "btn_template":
            self.load_template()
        elif button_id == "btn_save":
            self.save_script()
        elif button_id == "btn_continue":
            self.action_continue_workflow()

    async def action_generate_script(self) -> None:
        """Generate script using AI."""
        if not self.llm_client:
            self.notify("LLM client not configured. Check API keys.", severity="error")
            return

        if self.is_generating:
            self.notify("Generation in progress...", severity="warning")
            return

        try:
            self.is_generating = True
            progress = self.query_one("#generation_progress", ProgressBar)
            progress.update(progress=0)

            # Get input values
            purpose = self.query_one("#purpose_input", Input).value
            audience = self.query_one("#audience_input", Input).value
            company = self.query_one("#company_input", Input).value
            value_prop = self.query_one("#value_input", Input).value
            tone = self.query_one("#tone_select", Select).value

            # Validate
            if not purpose or not audience or not company:
                self.notify("Please fill in all required fields", severity="warning")
                progress.update(progress=0)
                self.is_generating = False
                return

            self.notify("Generating script with AI... This may take 10-20 seconds", timeout=3)
            progress.update(progress=20)

            # Build appointment details from calendar slots
            calendar_slots = getattr(self.app, 'calendar_slots', [])
            appointment_details = self._format_appointment_details(calendar_slots)

            progress.update(progress=40)

            # Generate script in thread to avoid blocking
            loop = asyncio.get_event_loop()
            script = await loop.run_in_executor(
                None,
                lambda: self.llm_client.generate_call_script(
                    campaign_purpose=purpose,
                    target_audience=audience,
                    company_info=company,
                    appointment_details=appointment_details,
                    tone=tone,
                    additional_context=value_prop
                )
            )

            progress.update(progress=90)

            # Store and display script
            self.current_script = script
            self.display_script(script)

            progress.update(progress=100)
            self.notify("Script generated successfully!", severity="information")

        except Exception as e:
            self.notify(f"Error generating script: {e}", severity="error")
        finally:
            self.is_generating = False
            progress.update(progress=0)

    async def action_refine_script(self) -> None:
        """Refine the current script."""
        if not self.llm_client:
            self.notify("LLM client not configured", severity="error")
            return

        if not self.current_script:
            self.notify("No script to refine. Generate a script first.", severity="warning")
            return

        # For now, just notify - could add a feedback dialog
        self.notify("Refining script... (This feature will open a feedback dialog)", timeout=3)

    def load_template(self) -> None:
        """Load a default template script."""
        template = {
            "full_text": "Default template loaded. Click Generate to create a custom script.",
            "opening": "Hi, this is [Your Name] calling from [Company]. Is this a good time to talk for just a moment?",
            "value_proposition": "We help companies like yours [value proposition]. We've worked with [similar companies] and helped them achieve [results].",
            "appointment_request": "I'd love to show you how we can help. Do you have 30 minutes next week for a quick demo?",
            "closing": "Great! I'll send you a calendar invite for [time]. Looking forward to speaking with you then!",
            "agent_instructions": "Be professional and concise. Listen actively and respond to objections calmly."
        }

        self.current_script = template
        self.display_script(template)
        self.notify("Loaded default template")

    def display_script(self, script: Dict[str, str]) -> None:
        """Display generated script in text areas."""
        # Full script
        full_area = self.query_one("#script_full", TextArea)
        full_area.text = script.get("full_text", "")

        # Individual sections
        opening_area = self.query_one("#script_opening", TextArea)
        opening_area.text = script.get("opening", "")

        value_area = self.query_one("#script_value", TextArea)
        value_area.text = script.get("value_proposition", "")

        objections_area = self.query_one("#script_objections", TextArea)
        objections = script.get("objection_handling", {})
        objections_text = "\n\n".join([
            f"**{obj}**\n{response}"
            for obj, response in objections.items()
        ])
        objections_area.text = objections_text

        closing_area = self.query_one("#script_closing", TextArea)
        closing_area.text = script.get("closing", "")

        instructions_area = self.query_one("#script_instructions", TextArea)
        instructions_area.text = script.get("agent_instructions", "")

    def save_script(self) -> None:
        """Save the current script."""
        if not self.current_script:
            self.notify("No script to save", severity="warning")
            return

        # Get text from all areas
        self.current_script["full_text"] = self.query_one("#script_full", TextArea).text
        self.current_script["opening"] = self.query_one("#script_opening", TextArea).text
        self.current_script["value_proposition"] = self.query_one("#script_value", TextArea).text
        self.current_script["closing"] = self.query_one("#script_closing", TextArea).text
        self.current_script["agent_instructions"] = self.query_one("#script_instructions", TextArea).text

        # Store in app state
        self.app.call_script = self.current_script

        self.notify("Script saved to workflow")

    def action_continue_workflow(self) -> None:
        """Continue to next step in workflow."""
        if not self.current_script:
            self.notify("Please generate or load a script first", severity="warning")
            return

        # Auto-save before continuing
        self.save_script()

        self.notify("Script saved. Proceeding to workflow creator...")

        # Move to workflow creator
        from .workflow_creator import WorkflowCreatorScreen
        self.app.pop_screen()
        self.app.push_screen(WorkflowCreatorScreen())

    def _format_appointment_details(self, calendar_slots: list) -> str:
        """Format calendar slots for LLM prompt."""
        if not calendar_slots:
            return "30-minute appointments during business hours"

        details = "Available appointment times:\n"
        for slot in calendar_slots:
            details += f"- {slot['day']}: {slot['start_time']} - {slot['end_time']} {slot['timezone']} "
            details += f"({slot['duration_minutes']} min slots)\n"

        return details
