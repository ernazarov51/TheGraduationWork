import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


PHONE_REGEX = re.compile(r"^\+998[0-9]{9}$")


def validate_uzbek_phone(value: str) -> None:
    """Validate that the value matches the Uzbek phone format: +998XXXXXXXXX."""
    if not PHONE_REGEX.match(value):
        raise ValidationError(
            _("Enter a valid phone number in the format: +998XXXXXXXXX"),
            code="invalid_phone",
        )
