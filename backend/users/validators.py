import re

from django.core.exceptions import ValidationError


def validate_username(value):
    if value.lower() == 'me':
        raise ValidationError('"me" - Недопустимое имя пользователя.')

    if re.search(r'^[\w.@+-]+$', value) is None:
        raise ValidationError(
            (f'Cимволы: "{value}" использовать нельзя'),
            params={'value': value},
        )
