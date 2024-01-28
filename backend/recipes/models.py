import re

from django.db import models
from django.core.validators import MinValueValidator
from rest_framework.validators import ValidationError

from users.models import FoodgramUser

MAX_LENGTH = 200


class Ingredients(models.Model):
    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH,
    )
    measurement_unit = models.CharField(
        'Единицы измерения',
        max_length=MAX_LENGTH,
    )

    class Meta:
        verbose_name = 'Игредиент'
        verbose_name_plural = 'Игредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit',),
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH,
    )
    color = models.CharField(
        max_length=16,
        null=True,
    )
    slug = models.SlugField(
        'Слаг',
        null=True,
        unique=True,
        max_length=MAX_LENGTH,
        help_text='',
    )

    def validate_color(value):
        match = re.search(r'^#[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}', value)
        if not match:
            raise ValidationError(
                'Недопустимый формат цвета.'
            )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(
        'Название',
        max_length=MAX_LENGTH,
    )
    text = models.TextField(
        'Описание',
    )
    ingredients = models.ManyToManyField(
        Ingredients,
        through='IngredientsRecipe',
        verbose_name='Ингредиенты',
        related_name='recipes'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=(MinValueValidator(1),),
        verbose_name='Время приготовления'
    )
    image = models.ImageField(
        'Фото',
        # upload_to='recipes/images/',
        null=True,
        # default=None
    )

    created_at = models.DateTimeField(
        'Добавлено',
        auto_now_add=True
    )
    author = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта',
    )
    tags = models.ManyToManyField(
        Tag,
        through='TagsRecipe',
        verbose_name='Теги',
        related_name='recipes'
    )

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientsRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients_recipe'
    )
    ingredients = models.ForeignKey(
        Ingredients,
        on_delete=models.PROTECT,
        related_name='ingredients_recipe'
    )
    amount = models.PositiveSmallIntegerField(
        validators=(MinValueValidator(1, ''),),
        null=True
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'

    def __str__(self):
        return f'{self.recipe} {self.ingredients}'


class TagsRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='tags_recipe'
    )
    tags = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='tags_recipe'
    )

    def __str__(self):
        return f'{self.tags} {self.recipe}'


class Favorite(models.Model):
    user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='is_favorited',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='is_favorited',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe',),
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return self.recipe


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='is_in_shopping_cart',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='is_in_shopping_cart',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe',),
                name='unique_shopping'
            )
        ]

    def __str__(self):
        return self.recipe


class Subsription(models.Model):
    user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='',
    )
    author = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author',),
                name='unique_subscription'
            )
        ]

    def __str__(self):
        return f'{self.user}  {self.author}'
