import re

from django.core.exceptions import ValidationError


def validate_slugtag(value):
    if re.search(r'^[-a-zA-Z0-9_]+$', value) is None:
        raise ValidationError(
            (f'Cимволы: "{value}" использовать нельзя'),
            params={'value': value},
        )
