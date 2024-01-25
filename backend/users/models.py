import re

from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.db import models
from rest_framework.validators import ValidationError


class FoodgramUser(AbstractUser):
    email = models.EmailField('Электронная почта', unique=True, max_length=254)
    username = models.CharField('Имя пользователя', unique=True, max_length=150)
    first_name = models.CharField('Имя',  max_length=150)
    last_name = models.CharField('Фамилия',  max_length=150)
    password = models.CharField('Пароль',  max_length=150)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    def validate_username(value):
        forbidden_characters = ''.join(re.split(r'[\w][.][@][+][-]+$', value))
        if len(forbidden_characters) != 0:
            raise ValidationError(
                ''
            )

    class Meta:
        ordering = ('id',)
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return self.username
