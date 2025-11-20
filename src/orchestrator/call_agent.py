"""Individual call agent that handles a single call."""

import logging
from typing import Dict, Optional, Any
from datetime import datetime
from enum import Enum


logger = logging.getLogger(__name__)


class CallStatus(Enum):
    """Call status enumeration."""
    PENDING = "pending"
    CALLING = "calling"
    CONNECTED = "connected"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    VOICEMAIL = "voicemail"
    APPOINTMENT_SCHEDULED = "appointment_scheduled"


class CallAgent:
    """
    Individual agent responsible for making a single call.

    This agent handles:
    - Making the call via ElevenLabs
    - Tracking call status
    - Recording call results
    - Updating contact in Apollo after call
    """

    def __init__(
        self,
        contact: Dict[str, Any],
        elevenlabs_client,
        apollo_client,
        config: Dict[str, Any]
    ):
        """
        Initialize call agent.

        Args:
            contact: Contact information dictionary
            elevenlabs_client: ElevenLabs API client
            apollo_client: Apollo API client
            config: Configuration dictionary
        """
        self.contact = contact
        self.elevenlabs_client = elevenlabs_client
        self.apollo_client = apollo_client
        self.config = config

        self.status = CallStatus.PENDING
        self.call_id: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.result: Optional[Dict] = None
        self.error: Optional[str] = None
        self.retry_count: int = 0

    @property
    def phone_number(self) -> str:
        """Get contact's phone number."""
        return self.contact.get("phone", "")

    @property
    def contact_name(self) -> str:
        """Get contact's name."""
        return self.contact.get("name", "Unknown")

    @property
    def contact_id(self) -> str:
        """Get contact's Apollo ID."""
        return self.contact.get("id", "")

    async def execute(self) -> Dict[str, Any]:
        """
        Execute the call.

        Returns:
            Call result dictionary
        """
        logger.info(f"CallAgent executing call to {self.contact_name} ({self.phone_number})")

        self.start_time = datetime.now()
        self.status = CallStatus.CALLING

        try:
            # Get agent configuration
            agent_id = self.config.get("agent_id")
            first_message = self._build_first_message()

            # Build metadata
            metadata = {
                "contact_id": self.contact_id,
                "contact_name": self.contact_name,
                "company": self.contact.get("company", ""),
                "title": self.contact.get("title", ""),
                "appointment_config": self.config.get("appointment", {})
            }

            # Make the call
            call_response = self.elevenlabs_client.create_outbound_call(
                phone_number=self.phone_number,
                agent_id=agent_id,
                first_message=first_message,
                metadata=metadata
            )

            self.call_id = call_response.get("call_id")
            self.status = CallStatus.CONNECTED

            # Poll for call completion
            final_status = await self._wait_for_completion()

            # Process result
            self.result = {
                "call_id": self.call_id,
                "status": final_status.value,
                "contact": self.contact,
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "duration": (self.end_time - self.start_time).total_seconds() if self.end_time else 0
            }

            # Update Apollo if appointment was scheduled
            if final_status == CallStatus.APPOINTMENT_SCHEDULED:
                await self._update_apollo_appointment()

            logger.info(f"Call completed: {self.contact_name} - Status: {final_status.value}")
            return self.result

        except Exception as e:
            logger.error(f"Call failed for {self.contact_name}: {e}")
            self.status = CallStatus.FAILED
            self.error = str(e)
            self.end_time = datetime.now()

            self.result = {
                "call_id": self.call_id,
                "status": CallStatus.FAILED.value,
                "contact": self.contact,
                "error": self.error,
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat()
            }

            return self.result

    async def _wait_for_completion(self) -> CallStatus:
        """
        Wait for call to complete by polling status.

        Returns:
            Final call status
        """
        import asyncio

        max_wait = self.config.get("call_timeout_seconds", 300)
        poll_interval = 5
        elapsed = 0

        while elapsed < max_wait:
            try:
                status_response = self.elevenlabs_client.get_call_status(
                    self.call_id,
                    agent_id=self.config.get("agent_id")
                )

                call_status = status_response.get("status", "").lower()

                # Map ElevenLabs status to our status
                if call_status in ["completed", "ended"]:
                    self.end_time = datetime.now()

                    # Check if appointment was scheduled
                    # This would typically be in the call transcript or metadata
                    transcript = status_response.get("transcript", "")
                    if self._check_appointment_in_transcript(transcript):
                        return CallStatus.APPOINTMENT_SCHEDULED
                    return CallStatus.COMPLETED

                elif call_status in ["failed", "error"]:
                    self.end_time = datetime.now()
                    return CallStatus.FAILED

                elif call_status == "no_answer":
                    self.end_time = datetime.now()
                    return CallStatus.NO_ANSWER

                elif call_status == "busy":
                    self.end_time = datetime.now()
                    return CallStatus.BUSY

                elif call_status == "voicemail":
                    self.end_time = datetime.now()
                    return CallStatus.VOICEMAIL

                # Still in progress
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

            except Exception as e:
                logger.error(f"Error checking call status: {e}")
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

        # Timeout
        self.end_time = datetime.now()
        return CallStatus.COMPLETED

    def _build_first_message(self) -> str:
        """
        Build personalized first message for the call.

        Returns:
            First message string
        """
        first_message_template = self.config.get("first_message", "")

        # Personalize with contact info
        message = first_message_template.format(
            name=self.contact.get("first_name", self.contact_name),
            company=self.contact.get("company", "your company"),
            title=self.contact.get("title", "")
        )

        return message or f"Hi, may I speak with {self.contact.get('first_name', self.contact_name)}?"

    def _check_appointment_in_transcript(self, transcript: str) -> bool:
        """
        Check if appointment was scheduled based on transcript.

        Args:
            transcript: Call transcript

        Returns:
            True if appointment was scheduled
        """
        # Keywords indicating appointment scheduling
        appointment_keywords = [
            "scheduled",
            "booked",
            "appointment",
            "meeting set",
            "calendar",
            "confirmed"
        ]

        transcript_lower = transcript.lower()
        return any(keyword in transcript_lower for keyword in appointment_keywords)

    async def _update_apollo_appointment(self):
        """Update Apollo to mark appointment as scheduled."""
        try:
            success = self.apollo_client.mark_appointment_scheduled(self.contact_id)
            if success:
                logger.info(f"Updated Apollo for {self.contact_name} - appointment scheduled")
            else:
                logger.warning(f"Failed to update Apollo for {self.contact_name}")
        except Exception as e:
            logger.error(f"Error updating Apollo for {self.contact_name}: {e}")

    def can_retry(self) -> bool:
        """
        Check if this call can be retried.

        Returns:
            True if retry is possible
        """
        max_retries = self.config.get("retry_attempts", 3)
        retryable_statuses = [CallStatus.FAILED, CallStatus.NO_ANSWER, CallStatus.BUSY]

        return (
            self.retry_count < max_retries and
            self.status in retryable_statuses
        )

    async def retry(self) -> Dict[str, Any]:
        """
        Retry the call.

        Returns:
            Call result dictionary
        """
        self.retry_count += 1
        logger.info(f"Retrying call to {self.contact_name} (attempt {self.retry_count})")

        # Reset status
        self.status = CallStatus.PENDING
        self.call_id = None
        self.error = None

        # Wait before retry
        import asyncio
        retry_delay = self.config.get("retry_delay_seconds", 5)
        await asyncio.sleep(retry_delay * self.retry_count)

        return await self.execute()
