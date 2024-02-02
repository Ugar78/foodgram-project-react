from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from foodgram.constants import MAX_LENGTH_USER_FIELDS


class FoodgramUser(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    email = models.EmailField('Электронная почта', unique=True)
    username = models.CharField(
        'Имя пользователя', unique=True, max_length=MAX_LENGTH_USER_FIELDS,
        validators=[UnicodeUsernameValidator()]
    )
    first_name = models.CharField('Имя', max_length=MAX_LENGTH_USER_FIELDS)
    last_name = models.CharField('Фамилия', max_length=MAX_LENGTH_USER_FIELDS)
    password = models.CharField('Пароль', max_length=MAX_LENGTH_USER_FIELDS)

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username
