from django.contrib.auth.models import AbstractUser
from django.db import models

from users.validators import validate_username
from foodgram.constants import (
    MAX_LENGTH_USERNAME,
    MAX_LENGTH_EMAIL,
    MAX_LENGTH_FIRST_NAME,
    MAX_LENGTH_LAST_NAME
)


class User(AbstractUser):
    """Переопределяем модель User"""

    username = models.CharField(
        'Пользователь',
        max_length=MAX_LENGTH_USERNAME,
        unique=True,
        validators=[validate_username]
    )
    email = models.EmailField(
        'Эл.почта',
        unique=True,
        max_length=MAX_LENGTH_EMAIL
    )
    first_name = models.CharField(
        'Имя',
        max_length=MAX_LENGTH_FIRST_NAME
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=MAX_LENGTH_LAST_NAME
    )
    avatar = models.ImageField(
        blank=True,
        null=True,
        upload_to='avatars/photo/',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name',
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self) -> str:
        """Строковое представление объекта модели."""
        return self.username
