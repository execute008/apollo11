"""Phone number validation and formatting utilities."""

import re
from typing import Optional
import phonenumbers
from phonenumbers import NumberParseException


def validate_phone_number(phone: str, default_region: str = "US") -> bool:
    """
    Validate a phone number.

    Args:
        phone: Phone number string
        default_region: Default region code (e.g., 'US', 'GB')

    Returns:
        True if valid, False otherwise
    """
    if not phone:
        return False

    try:
        parsed = phonenumbers.parse(phone, default_region)
        return phonenumbers.is_valid_number(parsed)
    except NumberParseException:
        return False


def format_phone_number(
    phone: str,
    format_type: str = "E164",
    default_region: str = "US"
) -> Optional[str]:
    """
    Format a phone number to a standard format.

    Args:
        phone: Phone number string
        format_type: Format type ('E164', 'INTERNATIONAL', 'NATIONAL')
        default_region: Default region code

    Returns:
        Formatted phone number or None if invalid
    """
    if not phone:
        return None

    try:
        parsed = phonenumbers.parse(phone, default_region)

        if not phonenumbers.is_valid_number(parsed):
            return None

        format_map = {
            "E164": phonenumbers.PhoneNumberFormat.E164,
            "INTERNATIONAL": phonenumbers.PhoneNumberFormat.INTERNATIONAL,
            "NATIONAL": phonenumbers.PhoneNumberFormat.NATIONAL,
        }

        format_enum = format_map.get(format_type.upper(), phonenumbers.PhoneNumberFormat.E164)
        return phonenumbers.format_number(parsed, format_enum)

    except NumberParseException:
        return None


def extract_phone_numbers(text: str) -> list[str]:
    """
    Extract phone numbers from text.

    Args:
        text: Text containing phone numbers

    Returns:
        List of extracted phone numbers
    """
    numbers = []

    # Try to find phone numbers in the text
    for match in phonenumbers.PhoneNumberMatcher(text, "US"):
        formatted = phonenumbers.format_number(
            match.number,
            phonenumbers.PhoneNumberFormat.E164
        )
        numbers.append(formatted)

    return numbers
