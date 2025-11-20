"""Main entry point for TUI application."""

from .tui.app import CallOrchestratorApp


def main():
    """Run the TUI application."""
    app = CallOrchestratorApp()
    app.run()


if __name__ == "__main__":
    main()
