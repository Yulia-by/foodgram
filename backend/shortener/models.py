import string
from random import choice, randint

from django.db import models

from foodgram.constants import (
    MAX_HASH_GEN,
    MAX_HASH_LENGTH,
    MIN_HASH_GEN,
    URL_MAX_LENGTH,
)


def generate_hash() -> str:
    """Генерирует случайную строку"""

    return ''.join(
        choice(string.ascii_letters + string.digits)
        for _ in range(randint(MIN_HASH_GEN, MAX_HASH_GEN))
    )


class LinkMapped(models.Model):
    """Модель коротких ссылок. """

    url_hash = models.CharField(
        max_length=MAX_HASH_LENGTH, default=generate_hash, unique=True
    )
    original_url = models.CharField(max_length=URL_MAX_LENGTH)

    class Meta:
        verbose_name = 'Ссылка'
        verbose_name_plural = 'Ссылки'

    def __str__(self):
        return f'{self.original_url} -> {self.url_hash}'
