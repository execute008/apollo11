"""Main call orchestrator that coordinates Apollo and ElevenLabs."""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from ..clients import ApolloClient, ElevenLabsClient
from ..config.settings import get_settings, get_config
from .agent_swarm import AgentSwarm


logger = logging.getLogger(__name__)


class CallOrchestrator:
    """
    Main orchestrator for Apollo-ElevenLabs call campaigns.

    Coordinates:
    - Fetching contacts from Apollo
    - Creating agent swarm
    - Executing calls via ElevenLabs
    - Tracking and reporting results
    """

    def __init__(
        self,
        apollo_client: Optional[ApolloClient] = None,
        elevenlabs_client: Optional[ElevenLabsClient] = None,
        config: Optional[Dict] = None
    ):
        """
        Initialize orchestrator.

        Args:
            apollo_client: Apollo API client (creates default if not provided)
            elevenlabs_client: ElevenLabs API client (creates default if not provided)
            config: Configuration dictionary (loads from file if not provided)
        """
        self.settings = get_settings()
        self.config = config or get_config()

        self.apollo_client = apollo_client or ApolloClient()
        self.elevenlabs_client = elevenlabs_client or ElevenLabsClient()

        self.contacts: List[Dict[str, Any]] = []
        self.swarm: Optional[AgentSwarm] = None
        self.results: Optional[Dict[str, Any]] = None

    def fetch_contacts(
        self,
        limit: Optional[int] = None,
        exclude_with_appointments: bool = True,
        additional_filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch contacts from Apollo that have phone numbers.

        Args:
            limit: Maximum number of contacts to fetch
            exclude_with_appointments: Exclude contacts with existing appointments
            additional_filters: Additional Apollo search filters

        Returns:
            List of contacts
        """
        logger.info("Fetching contacts from Apollo...")

        # Get filters from config
        apollo_config = self.config.get("apollo", {})
        config_filters = apollo_config.get("filters", {})

        # Merge with additional filters
        filters = {**config_filters, **(additional_filters or {})}

        # Fetch contacts
        self.contacts = self.apollo_client.get_contacts_with_phones(
            exclude_with_appointments=exclude_with_appointments,
            additional_filters=filters,
            limit=limit
        )

        logger.info(f"Fetched {len(self.contacts)} contacts from Apollo")
        return self.contacts

    def prepare_swarm(self, contacts: Optional[List[Dict[str, Any]]] = None):
        """
        Prepare agent swarm with contacts.

        Args:
            contacts: List of contacts (uses fetched contacts if not provided)
        """
        contacts = contacts or self.contacts

        if not contacts:
            raise ValueError("No contacts to prepare. Call fetch_contacts() first or provide contacts.")

        # Get orchestrator config
        orchestrator_config = self.config.get("orchestrator", {})
        max_concurrent = orchestrator_config.get(
            "max_concurrent_calls",
            self.settings.max_concurrent_calls
        )

        # Prepare swarm config
        swarm_config = {
            "agent_id": self.settings.elevenlabs_agent_id,
            "retry_attempts": orchestrator_config.get("retry_attempts", 3),
            "retry_delay_seconds": orchestrator_config.get("retry_delay_seconds", 5),
            "call_timeout_seconds": orchestrator_config.get(
                "call_timeout_seconds",
                self.settings.call_timeout_seconds
            ),
            "first_message": self.config.get("agent_prompt", {}).get("first_message", ""),
            "appointment": self.config.get("appointment", {})
        }

        # Create swarm
        self.swarm = AgentSwarm(
            elevenlabs_client=self.elevenlabs_client,
            apollo_client=self.apollo_client,
            config=swarm_config,
            max_concurrent=max_concurrent
        )

        # Add contacts to swarm
        self.swarm.add_contacts(contacts)

        logger.info(f"Prepared swarm with {len(contacts)} contacts")

    async def execute_campaign(
        self,
        contacts: Optional[List[Dict[str, Any]]] = None,
        save_results: bool = True,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Execute full call campaign.

        Args:
            contacts: List of contacts (fetches if not provided)
            save_results: Whether to save results to file
            output_dir: Directory to save results

        Returns:
            Campaign results summary
        """
        logger.info("=== Starting Call Campaign ===")

        # Fetch contacts if not provided
        if not contacts and not self.contacts:
            self.fetch_contacts()
            contacts = self.contacts
        elif contacts:
            self.contacts = contacts

        if not self.contacts:
            logger.error("No contacts available for campaign")
            return {
                "error": "No contacts available",
                "total_contacts": 0
            }

        # Prepare swarm
        self.prepare_swarm(contacts)

        # Execute swarm
        logger.info(f"Executing campaign for {len(self.contacts)} contacts...")
        self.results = await self.swarm.execute()

        # Save results if requested
        if save_results:
            self._save_results(output_dir)

        logger.info("=== Campaign Completed ===")
        self._log_summary()

        return self.results

    def execute_campaign_sync(
        self,
        contacts: Optional[List[Dict[str, Any]]] = None,
        save_results: bool = True,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Synchronous wrapper for execute_campaign.

        Args:
            contacts: List of contacts
            save_results: Whether to save results
            output_dir: Directory to save results

        Returns:
            Campaign results summary
        """
        return asyncio.run(
            self.execute_campaign(
                contacts=contacts,
                save_results=save_results,
                output_dir=output_dir
            )
        )

    def _save_results(self, output_dir: Optional[Path] = None):
        """
        Save campaign results to file.

        Args:
            output_dir: Directory to save results (defaults to ./results)
        """
        if not self.results:
            return

        output_dir = output_dir or Path("./results")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"campaign_results_{timestamp}.json"
        filepath = output_dir / filename

        with open(filepath, "w") as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"Results saved to {filepath}")

        # Also save CSV summary
        self._save_csv_summary(output_dir, timestamp)

    def _save_csv_summary(self, output_dir: Path, timestamp: str):
        """
        Save CSV summary of results.

        Args:
            output_dir: Output directory
            timestamp: Timestamp string
        """
        try:
            import csv

            filename = f"campaign_summary_{timestamp}.csv"
            filepath = output_dir / filename

            if not self.results or "results" not in self.results:
                return

            with open(filepath, "w", newline="") as f:
                fieldnames = [
                    "contact_name",
                    "phone",
                    "company",
                    "title",
                    "status",
                    "call_id",
                    "duration",
                    "appointment_scheduled"
                ]

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for result in self.results["results"]:
                    contact = result.get("contact", {})
                    writer.writerow({
                        "contact_name": contact.get("name", ""),
                        "phone": contact.get("phone", ""),
                        "company": contact.get("company", ""),
                        "title": contact.get("title", ""),
                        "status": result.get("status", ""),
                        "call_id": result.get("call_id", ""),
                        "duration": result.get("duration", 0),
                        "appointment_scheduled": result.get("status") == "appointment_scheduled"
                    })

            logger.info(f"CSV summary saved to {filepath}")

        except Exception as e:
            logger.error(f"Error saving CSV summary: {e}")

    def _log_summary(self):
        """Log campaign summary."""
        if not self.results:
            return

        logger.info("=" * 60)
        logger.info("CAMPAIGN SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Contacts: {self.results.get('total_contacts', 0)}")
        logger.info(f"Completed Calls: {self.results.get('completed', 0)}")
        logger.info(f"Failed Calls: {self.results.get('failed', 0)}")
        logger.info(f"Appointments Scheduled: {self.results.get('appointments_scheduled', 0)}")
        logger.info(f"No Answer: {self.results.get('no_answer', 0)}")
        logger.info(f"Busy: {self.results.get('busy', 0)}")
        logger.info(f"Voicemail: {self.results.get('voicemail', 0)}")
        logger.info(f"Success Rate: {self.results.get('success_rate', 0):.2f}%")
        logger.info(f"Appointment Rate: {self.results.get('appointment_rate', 0):.2f}%")
        logger.info(f"Duration: {self.results.get('duration_seconds', 0):.2f} seconds")
        logger.info("=" * 60)

    def get_results(self) -> Optional[Dict[str, Any]]:
        """
        Get campaign results.

        Returns:
            Results dictionary or None
        """
        return self.results

    def get_appointments(self) -> List[Dict[str, Any]]:
        """
        Get contacts where appointments were scheduled.

        Returns:
            List of appointment results
        """
        if not self.swarm:
            return []

        return self.swarm.get_appointments()

    async def cancel_campaign(self):
        """Cancel ongoing campaign."""
        if self.swarm:
            await self.swarm.cancel_all()
            logger.info("Campaign cancelled")
