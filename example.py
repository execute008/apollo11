"""Example usage of the Apollo ElevenLabs Call Orchestrator."""

import asyncio
from src.orchestrator import CallOrchestrator
from src.config.settings import get_settings
from src.utils.logger import setup_logger
from pathlib import Path


async def main():
    """Example campaign execution."""

    # Setup logging
    setup_logger("src", level="INFO", log_file=Path("logs/example.log"))

    # Create orchestrator
    print("Creating orchestrator...")
    orchestrator = CallOrchestrator()

    # Fetch contacts from Apollo
    print("Fetching contacts from Apollo...")
    contacts = orchestrator.fetch_contacts(
        limit=5,  # Only fetch 5 contacts for testing
        exclude_with_appointments=True
    )

    print(f"Found {len(contacts)} contacts:")
    for i, contact in enumerate(contacts, 1):
        print(f"  {i}. {contact['name']} - {contact['phone']} ({contact['company']})")

    if not contacts:
        print("No contacts found. Check your Apollo filters.")
        return

    # Ask for confirmation
    response = input(f"\nProceed with calling {len(contacts)} contacts? (y/n): ")
    if response.lower() != 'y':
        print("Campaign cancelled.")
        return

    # Execute campaign
    print("\nStarting call campaign...")
    results = await orchestrator.execute_campaign(
        contacts=contacts,
        save_results=True,
        output_dir=Path("./results")
    )

    # Display results
    print("\n" + "=" * 60)
    print("CAMPAIGN RESULTS")
    print("=" * 60)
    print(f"Total Contacts: {results['total_contacts']}")
    print(f"Completed: {results['completed']}")
    print(f"Failed: {results['failed']}")
    print(f"Appointments Scheduled: {results['appointments_scheduled']}")
    print(f"Success Rate: {results['success_rate']:.2f}%")
    print(f"Appointment Rate: {results['appointment_rate']:.2f}%")
    print("=" * 60)

    # Show appointments
    appointments = orchestrator.get_appointments()
    if appointments:
        print(f"\n{len(appointments)} appointments scheduled:")
        for appt in appointments:
            contact = appt['contact']
            print(f"  - {contact['name']} ({contact['company']})")

    print("\nResults saved to ./results/")


def sync_main():
    """Synchronous wrapper for the example."""
    orchestrator = CallOrchestrator()

    # Fetch contacts
    print("Fetching contacts from Apollo...")
    contacts = orchestrator.fetch_contacts(limit=5)

    print(f"Found {len(contacts)} contacts")

    if contacts:
        # Execute campaign synchronously
        results = orchestrator.execute_campaign_sync(
            contacts=contacts,
            save_results=True
        )

        print(f"Campaign completed: {results['appointments_scheduled']} appointments scheduled")


if __name__ == "__main__":
    # Run async version
    asyncio.run(main())

    # Or run sync version:
    # sync_main()
