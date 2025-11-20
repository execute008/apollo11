"""Apollo.io API client for fetching contacts."""

import logging
from typing import Optional, Dict, List, Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config.settings import get_settings
from ..utils.phone_validator import validate_phone_number, format_phone_number


logger = logging.getLogger(__name__)


class ApolloClient:
    """Client for interacting with Apollo.io API."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize Apollo client.

        Args:
            api_key: Apollo API key (defaults to settings)
            base_url: Base URL for Apollo API (defaults to settings)
        """
        settings = get_settings()
        self.api_key = api_key or settings.apollo_api_key
        self.base_url = base_url or settings.apollo_base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
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
        Make a request to Apollo API with retry logic.

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

        # Add API key to request
        if params is None:
            params = {}
        params["api_key"] = self.api_key

        logger.debug(f"Making {method} request to {url}")

        response = self.session.request(
            method=method,
            url=url,
            params=params,
            json=json_data,
            timeout=30
        )

        response.raise_for_status()
        return response.json()

    def search_people(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        per_page: int = 100
    ) -> Dict:
        """
        Search for people/contacts in Apollo.

        Args:
            filters: Search filters (e.g., titles, locations, etc.)
            page: Page number
            per_page: Results per page (max 100)

        Returns:
            Search results with contacts
        """
        endpoint = "mixed_people/search"

        payload = {
            "page": page,
            "per_page": min(per_page, 100),
            **(filters or {})
        }

        logger.info(f"Searching people with filters: {filters}, page: {page}")
        return self._make_request("POST", endpoint, json_data=payload)

    def get_contacts_with_phones(
        self,
        exclude_with_appointments: bool = True,
        additional_filters: Optional[Dict] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get contacts that have phone numbers.

        Args:
            exclude_with_appointments: Exclude contacts with existing appointments
            additional_filters: Additional Apollo search filters
            limit: Maximum number of contacts to return

        Returns:
            List of contact dictionaries with phone numbers
        """
        contacts = []
        page = 1
        per_page = 100

        filters = additional_filters or {}

        # Note: Apollo API filtering depends on your subscription level
        # Adjust these filters based on available fields

        while True:
            try:
                response = self.search_people(
                    filters=filters,
                    page=page,
                    per_page=per_page
                )

                people = response.get("people", [])
                if not people:
                    break

                for person in people:
                    # Check if person has a phone number
                    phone = self._extract_phone(person)
                    if not phone:
                        continue

                    # Validate phone number
                    if not validate_phone_number(phone):
                        logger.debug(f"Invalid phone number for {person.get('name')}: {phone}")
                        continue

                    # Check for existing appointments if requested
                    if exclude_with_appointments and self._has_appointments(person):
                        logger.debug(f"Skipping {person.get('name')} - has existing appointments")
                        continue

                    # Format contact data
                    contact = {
                        "id": person.get("id"),
                        "name": person.get("name"),
                        "first_name": person.get("first_name"),
                        "last_name": person.get("last_name"),
                        "title": person.get("title"),
                        "email": person.get("email"),
                        "phone": format_phone_number(phone),
                        "phone_raw": phone,
                        "company": person.get("organization_name"),
                        "linkedin_url": person.get("linkedin_url"),
                        "city": person.get("city"),
                        "state": person.get("state"),
                        "country": person.get("country"),
                        "raw_data": person
                    }

                    contacts.append(contact)
                    logger.info(f"Added contact: {contact['name']} - {contact['phone']}")

                    # Check limit
                    if limit and len(contacts) >= limit:
                        logger.info(f"Reached limit of {limit} contacts")
                        return contacts

                # Check if there are more pages
                pagination = response.get("pagination", {})
                total_pages = pagination.get("total_pages", 1)

                if page >= total_pages:
                    break

                page += 1

            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching contacts on page {page}: {e}")
                break

        logger.info(f"Total contacts found: {len(contacts)}")
        return contacts

    def _extract_phone(self, person: Dict) -> Optional[str]:
        """
        Extract phone number from person data.

        Args:
            person: Person dictionary from Apollo

        Returns:
            Phone number string or None
        """
        # Try multiple fields where phone might be stored
        phone_fields = [
            "phone_number",
            "sanitized_phone",
            "mobile_phone",
            "direct_phone",
            "corporate_phone"
        ]

        for field in phone_fields:
            phone = person.get(field)
            if phone:
                return str(phone).strip()

        # Check in phone_numbers array
        phone_numbers = person.get("phone_numbers", [])
        if phone_numbers and isinstance(phone_numbers, list):
            return phone_numbers[0].get("sanitized_number") or phone_numbers[0].get("raw_number")

        return None

    def _has_appointments(self, person: Dict) -> bool:
        """
        Check if a person has existing appointments.

        Args:
            person: Person dictionary from Apollo

        Returns:
            True if person has appointments, False otherwise
        """
        # This depends on how you track appointments in Apollo
        # Common approaches:

        # 1. Check custom fields
        has_appointment = person.get("has_appointment", False)
        if has_appointment:
            return True

        # 2. Check contact stage
        stage = person.get("contact_stage_id") or person.get("stage")
        appointment_stages = ["appointment_scheduled", "meeting_scheduled"]
        if stage in appointment_stages:
            return True

        # 3. Check tags
        tags = person.get("tags", [])
        if isinstance(tags, list):
            appointment_tags = ["appointment", "scheduled", "meeting"]
            if any(tag.lower() in appointment_tags for tag in tags):
                return True

        # 4. Check activities/tasks
        activities = person.get("activities", [])
        if activities:
            # If there are recent activities, might indicate appointment
            return len(activities) > 0

        return False

    def get_person_by_id(self, person_id: str) -> Optional[Dict]:
        """
        Get a specific person by ID.

        Args:
            person_id: Apollo person ID

        Returns:
            Person dictionary or None
        """
        try:
            endpoint = f"people/{person_id}"
            return self._make_request("GET", endpoint)
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching person {person_id}: {e}")
            return None

    def update_person(self, person_id: str, data: Dict) -> bool:
        """
        Update a person's data in Apollo.

        Args:
            person_id: Apollo person ID
            data: Data to update

        Returns:
            True if successful, False otherwise
        """
        try:
            endpoint = f"people/{person_id}"
            self._make_request("PATCH", endpoint, json_data=data)
            logger.info(f"Updated person {person_id}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating person {person_id}: {e}")
            return False

    def mark_appointment_scheduled(self, person_id: str) -> bool:
        """
        Mark a person as having an appointment scheduled.

        Args:
            person_id: Apollo person ID

        Returns:
            True if successful, False otherwise
        """
        # Update with custom field or tag
        data = {
            "has_appointment": True,
            "tags": ["appointment_scheduled"]
        }

        return self.update_person(person_id, data)
