import uuid
import string
from random import choice, randint

from django.db import models

from foodgram.constants import MAX_HASH_GEN


def generate_unique_hash() -> str:
    """Генерирует уникальный идентификатор на основе UUID."""
    return uuid.uuid4().hex[:MAX_HASH_GEN]


MAX_HASH_GEN = 8

class LinkModel(models.Model):
    """Модель коротких ссылок."""

    url_hash = models.CharField(
        max_length=MAX_HASH_GEN, default=generate_unique_hash, unique=True
    )
    original_url = models.URLField(max_length=2000)

    class Meta:
        verbose_name = 'Короткая ссылка'
        verbose_name_plural = 'Короткие ссылки'

    def __str__(self):
        return f'{self.original_url} -> {self.url_hash}'
