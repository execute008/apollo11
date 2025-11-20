"""Agent swarm for managing multiple concurrent call agents."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from .call_agent import CallAgent, CallStatus


logger = logging.getLogger(__name__)


class AgentSwarm:
    """
    Swarm of call agents that work concurrently.

    The swarm manages:
    - Concurrent execution of multiple call agents
    - Load balancing and rate limiting
    - Result aggregation
    - Error handling and retries
    """

    def __init__(
        self,
        elevenlabs_client,
        apollo_client,
        config: Dict[str, Any],
        max_concurrent: int = 5
    ):
        """
        Initialize agent swarm.

        Args:
            elevenlabs_client: ElevenLabs API client
            apollo_client: Apollo API client
            config: Configuration dictionary
            max_concurrent: Maximum concurrent calls
        """
        self.elevenlabs_client = elevenlabs_client
        self.apollo_client = apollo_client
        self.config = config
        self.max_concurrent = max_concurrent

        self.agents: List[CallAgent] = []
        self.results: List[Dict[str, Any]] = []
        self.active_agents: int = 0
        self.completed: int = 0
        self.failed: int = 0
        self.appointments_scheduled: int = 0

        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._start_time: Optional[datetime] = None
        self._end_time: Optional[datetime] = None

    def add_contact(self, contact: Dict[str, Any]):
        """
        Add a contact to call.

        Args:
            contact: Contact information dictionary
        """
        agent = CallAgent(
            contact=contact,
            elevenlabs_client=self.elevenlabs_client,
            apollo_client=self.apollo_client,
            config=self.config
        )
        self.agents.append(agent)
        logger.debug(f"Added contact to swarm: {contact.get('name')}")

    def add_contacts(self, contacts: List[Dict[str, Any]]):
        """
        Add multiple contacts to call.

        Args:
            contacts: List of contact dictionaries
        """
        for contact in contacts:
            self.add_contact(contact)

        logger.info(f"Added {len(contacts)} contacts to swarm")

    async def execute(self) -> Dict[str, Any]:
        """
        Execute all calls concurrently with rate limiting.

        Returns:
            Summary of all call results
        """
        if not self.agents:
            logger.warning("No agents to execute")
            return self._build_summary()

        logger.info(f"Starting swarm execution with {len(self.agents)} agents")
        logger.info(f"Max concurrent calls: {self.max_concurrent}")

        self._start_time = datetime.now()

        # Create tasks for all agents
        tasks = [self._execute_agent(agent) for agent in self.agents]

        # Execute all tasks concurrently (semaphore controls concurrency)
        await asyncio.gather(*tasks, return_exceptions=True)

        self._end_time = datetime.now()

        summary = self._build_summary()
        logger.info("Swarm execution completed")
        logger.info(f"Summary: {self.completed} completed, {self.failed} failed, "
                   f"{self.appointments_scheduled} appointments scheduled")

        return summary

    async def _execute_agent(self, agent: CallAgent) -> Dict[str, Any]:
        """
        Execute a single agent with semaphore for rate limiting.

        Args:
            agent: CallAgent to execute

        Returns:
            Call result
        """
        async with self._semaphore:
            self.active_agents += 1
            logger.debug(f"Active agents: {self.active_agents}/{self.max_concurrent}")

            try:
                # Execute the call
                result = await agent.execute()

                # Update statistics
                self._update_statistics(agent, result)

                # Store result
                self.results.append(result)

                # Retry if needed
                if agent.can_retry():
                    logger.info(f"Agent can retry: {agent.contact_name}")
                    retry_result = await agent.retry()
                    self._update_statistics(agent, retry_result)
                    self.results.append(retry_result)

                return result

            except Exception as e:
                logger.error(f"Error executing agent for {agent.contact_name}: {e}")
                self.failed += 1

                error_result = {
                    "status": CallStatus.FAILED.value,
                    "contact": agent.contact,
                    "error": str(e)
                }
                self.results.append(error_result)

                return error_result

            finally:
                self.active_agents -= 1

    def _update_statistics(self, agent: CallAgent, result: Dict[str, Any]):
        """
        Update swarm statistics based on call result.

        Args:
            agent: CallAgent that executed
            result: Call result
        """
        status = result.get("status", "")

        if status == CallStatus.COMPLETED.value:
            self.completed += 1
        elif status == CallStatus.APPOINTMENT_SCHEDULED.value:
            self.completed += 1
            self.appointments_scheduled += 1
        elif status == CallStatus.FAILED.value:
            self.failed += 1

    def _build_summary(self) -> Dict[str, Any]:
        """
        Build execution summary.

        Returns:
            Summary dictionary
        """
        total_agents = len(self.agents)
        duration = 0

        if self._start_time and self._end_time:
            duration = (self._end_time - self._start_time).total_seconds()

        # Calculate statistics
        no_answer = sum(1 for r in self.results if r.get("status") == CallStatus.NO_ANSWER.value)
        busy = sum(1 for r in self.results if r.get("status") == CallStatus.BUSY.value)
        voicemail = sum(1 for r in self.results if r.get("status") == CallStatus.VOICEMAIL.value)

        summary = {
            "total_contacts": total_agents,
            "completed": self.completed,
            "failed": self.failed,
            "appointments_scheduled": self.appointments_scheduled,
            "no_answer": no_answer,
            "busy": busy,
            "voicemail": voicemail,
            "success_rate": (self.completed / total_agents * 100) if total_agents > 0 else 0,
            "appointment_rate": (self.appointments_scheduled / total_agents * 100) if total_agents > 0 else 0,
            "duration_seconds": duration,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "end_time": self._end_time.isoformat() if self._end_time else None,
            "results": self.results
        }

        return summary

    def get_results(self) -> List[Dict[str, Any]]:
        """
        Get all call results.

        Returns:
            List of call results
        """
        return self.results

    def get_successful_calls(self) -> List[Dict[str, Any]]:
        """
        Get results for successful calls only.

        Returns:
            List of successful call results
        """
        return [
            r for r in self.results
            if r.get("status") in [
                CallStatus.COMPLETED.value,
                CallStatus.APPOINTMENT_SCHEDULED.value
            ]
        ]

    def get_appointments(self) -> List[Dict[str, Any]]:
        """
        Get results for calls where appointments were scheduled.

        Returns:
            List of appointment call results
        """
        return [
            r for r in self.results
            if r.get("status") == CallStatus.APPOINTMENT_SCHEDULED.value
        ]

    def get_failed_calls(self) -> List[Dict[str, Any]]:
        """
        Get results for failed calls.

        Returns:
            List of failed call results
        """
        return [
            r for r in self.results
            if r.get("status") in [
                CallStatus.FAILED.value,
                CallStatus.NO_ANSWER.value,
                CallStatus.BUSY.value
            ]
        ]

    async def cancel_all(self):
        """Cancel all ongoing calls."""
        logger.info("Cancelling all calls in swarm")

        for agent in self.agents:
            if agent.call_id and agent.status in [CallStatus.CALLING, CallStatus.CONNECTED]:
                try:
                    self.elevenlabs_client.cancel_call(
                        agent.call_id,
                        agent_id=self.config.get("agent_id")
                    )
                    logger.info(f"Cancelled call for {agent.contact_name}")
                except Exception as e:
                    logger.error(f"Error cancelling call for {agent.contact_name}: {e}")

        logger.info("All calls cancelled")
