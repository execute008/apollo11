"""ElevenLabs API client for making AI-powered calls."""

import logging
from typing import Optional, Dict, List, Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config.settings import get_settings


logger = logging.getLogger(__name__)


class ElevenLabsClient:
    """Client for interacting with ElevenLabs Conversational AI API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        agent_id: Optional[str] = None
    ):
        """
        Initialize ElevenLabs client.

        Args:
            api_key: ElevenLabs API key
            base_url: Base URL for ElevenLabs API
            agent_id: Default agent ID to use for calls
        """
        settings = get_settings()
        self.api_key = api_key or settings.elevenlabs_api_key
        self.base_url = base_url or settings.elevenlabs_base_url
        self.agent_id = agent_id or settings.elevenlabs_agent_id

        self.session = requests.Session()
        self.session.headers.update({
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        })

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict:
        """
        Make a request to ElevenLabs API with retry logic.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json_data: JSON body data

        Returns:
            Response JSON

        Raises:
            requests.exceptions.RequestException: On API error
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        logger.debug(f"Making {method} request to {url}")

        response = self.session.request(
            method=method,
            url=url,
            params=params,
            json=json_data,
            timeout=30
        )

        response.raise_for_status()

        # Some endpoints return empty responses
        if response.text:
            return response.json()
        return {}

    def create_outbound_call(
        self,
        phone_number: str,
        agent_id: Optional[str] = None,
        first_message: Optional[str] = None,
        metadata: Optional[Dict] = None,
        **kwargs
    ) -> Dict:
        """
        Create an outbound call to a phone number.

        Args:
            phone_number: Phone number to call (E.164 format)
            agent_id: Agent ID to use (defaults to configured agent)
            first_message: First message the agent should say
            metadata: Additional metadata to attach to the call
            **kwargs: Additional parameters for the call

        Returns:
            Call response with call_id and status
        """
        agent_id = agent_id or self.agent_id
        if not agent_id:
            raise ValueError("Agent ID must be provided or configured in settings")

        endpoint = f"convai/agents/{agent_id}/calls"

        payload = {
            "phone_number": phone_number,
            **({"first_message": first_message} if first_message else {}),
            **({"metadata": metadata} if metadata else {}),
            **kwargs
        }

        logger.info(f"Creating outbound call to {phone_number} with agent {agent_id}")

        try:
            response = self._make_request("POST", endpoint, json_data=payload)
            logger.info(f"Call created successfully: {response.get('call_id')}")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create call to {phone_number}: {e}")
            raise

    def create_batch_calls(
        self,
        calls: List[Dict[str, Any]],
        agent_id: Optional[str] = None,
        max_concurrency: int = 5
    ) -> Dict:
        """
        Create a batch of outbound calls.

        Args:
            calls: List of call configurations, each with 'phone_number' and optional params
            agent_id: Agent ID to use for all calls
            max_concurrency: Maximum concurrent calls

        Returns:
            Batch creation response with batch_id
        """
        agent_id = agent_id or self.agent_id
        if not agent_id:
            raise ValueError("Agent ID must be provided or configured in settings")

        endpoint = f"convai/agents/{agent_id}/batch-calls"

        payload = {
            "calls": calls,
            "max_concurrency": max_concurrency
        }

        logger.info(f"Creating batch of {len(calls)} calls with agent {agent_id}")

        try:
            response = self._make_request("POST", endpoint, json_data=payload)
            logger.info(f"Batch created successfully: {response.get('batch_id')}")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create batch calls: {e}")
            raise

    def get_call_status(self, call_id: str, agent_id: Optional[str] = None) -> Dict:
        """
        Get the status of a call.

        Args:
            call_id: Call ID
            agent_id: Agent ID (defaults to configured agent)

        Returns:
            Call status information
        """
        agent_id = agent_id or self.agent_id
        if not agent_id:
            raise ValueError("Agent ID must be provided or configured in settings")

        endpoint = f"convai/agents/{agent_id}/calls/{call_id}"

        try:
            response = self._make_request("GET", endpoint)
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get call status for {call_id}: {e}")
            raise

    def get_batch_status(self, batch_id: str, agent_id: Optional[str] = None) -> Dict:
        """
        Get the status of a batch of calls.

        Args:
            batch_id: Batch ID
            agent_id: Agent ID (defaults to configured agent)

        Returns:
            Batch status information
        """
        agent_id = agent_id or self.agent_id
        if not agent_id:
            raise ValueError("Agent ID must be provided or configured in settings")

        endpoint = f"convai/agents/{agent_id}/batch-calls/{batch_id}"

        try:
            response = self._make_request("GET", endpoint)
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get batch status for {batch_id}: {e}")
            raise

    def cancel_call(self, call_id: str, agent_id: Optional[str] = None) -> bool:
        """
        Cancel an ongoing call.

        Args:
            call_id: Call ID to cancel
            agent_id: Agent ID (defaults to configured agent)

        Returns:
            True if successful
        """
        agent_id = agent_id or self.agent_id
        if not agent_id:
            raise ValueError("Agent ID must be provided or configured in settings")

        endpoint = f"convai/agents/{agent_id}/calls/{call_id}"

        try:
            self._make_request("DELETE", endpoint)
            logger.info(f"Call {call_id} cancelled successfully")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to cancel call {call_id}: {e}")
            return False

    def list_agents(self) -> List[Dict]:
        """
        List all available agents.

        Returns:
            List of agent configurations
        """
        endpoint = "convai/agents"

        try:
            response = self._make_request("GET", endpoint)
            agents = response.get("agents", [])
            logger.info(f"Found {len(agents)} agents")
            return agents
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list agents: {e}")
            return []

    def get_agent(self, agent_id: Optional[str] = None) -> Optional[Dict]:
        """
        Get agent configuration.

        Args:
            agent_id: Agent ID (defaults to configured agent)

        Returns:
            Agent configuration or None
        """
        agent_id = agent_id or self.agent_id
        if not agent_id:
            raise ValueError("Agent ID must be provided or configured in settings")

        endpoint = f"convai/agents/{agent_id}"

        try:
            response = self._make_request("GET", endpoint)
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get agent {agent_id}: {e}")
            return None

    def create_agent(
        self,
        name: str,
        prompt: str,
        voice_id: str,
        first_message: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Create a new conversational agent.

        Args:
            name: Agent name
            prompt: System prompt for the agent
            voice_id: ElevenLabs voice ID to use
            first_message: Optional first message
            **kwargs: Additional agent configuration

        Returns:
            Created agent configuration
        """
        endpoint = "convai/agents"

        payload = {
            "name": name,
            "prompt": prompt,
            "voice_id": voice_id,
            **({"first_message": first_message} if first_message else {}),
            **kwargs
        }

        logger.info(f"Creating agent: {name}")

        try:
            response = self._make_request("POST", endpoint, json_data=payload)
            logger.info(f"Agent created successfully: {response.get('agent_id')}")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create agent: {e}")
            raise

    def update_agent(self, agent_id: str, updates: Dict) -> Dict:
        """
        Update an existing agent.

        Args:
            agent_id: Agent ID to update
            updates: Fields to update

        Returns:
            Updated agent configuration
        """
        endpoint = f"convai/agents/{agent_id}"

        logger.info(f"Updating agent {agent_id}")

        try:
            response = self._make_request("PATCH", endpoint, json_data=updates)
            logger.info(f"Agent {agent_id} updated successfully")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update agent {agent_id}: {e}")
            raise
