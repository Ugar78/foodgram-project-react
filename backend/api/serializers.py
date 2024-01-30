import base64

from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from django.shortcuts import get_object_or_404
from rest_framework import serializers, exceptions, response, status

from djoser.serializers import UserSerializer, UserCreateSerializer

from recipes.models import (
    Tag, Recipe, Ingredients, IngredientsRecipe,
    Favorite, ShoppingCart, Subsription, TagsRecipe
)
from users.models import FoodgramUser


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FoodgramUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        user_id = self.context.get('request').user.id
        return Subsription.objects.filter(
            author=obj.id,
            user=user_id
        ).exists()

    class Meta:
        model = FoodgramUser
        fields = ('id', 'username', 'first_name', 'last_name',
                  'email', 'is_subscribed')


class FoodgramUserCreateSerializer(UserCreateSerializer):

    class Meta:
        model = FoodgramUser
        fields = ('id', 'username', 'first_name', 'last_name',
                  'email', 'password')


class SubsriptionSerializer(FoodgramUserSerializer):
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='author.recipes.count')
    is_subscribed = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        author_recipes = obj.author.recipes.all()

        if 'recipes_limit' in self.context.get('request').GET:
            recipes_limit = self.context.get('request').GET['recipes_limit']
            author_recipes = author_recipes[:int(recipes_limit)]

        if author_recipes:
            serializer = ShortRecipeSerializer(
                author_recipes,
                context={'request': self.context.get('request')},
                many=True
            )
            return serializer.data
        return []

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.id).count()

    class Meta:
        model = Subsription
        fields = (
            'id', 'username', 'first_name', 'last_name',
            'email', 'is_subscribed', 'recipes', 'recipes_count'
        )


class IngredientsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredients
        fields = '__all__'


class IngredientsRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredients.id')
    name = serializers.ReadOnlyField(source='ingredients.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredients.measurement_unit'
    )

    class Meta:
        model = IngredientsRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class CreateUpdateIngredientsRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredients.objects.all())
    amount = serializers.IntegerField(
        validators=(
            MinValueValidator(
                1, message=''
            ),
        )
    )

    class Meta:
        model = Ingredients
        fields = ('id', 'amount')


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class TagsSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tags."""

    class Meta:
        model = Tag
        fields = '__all__'


class TagsRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='tags.id')
    name = serializers.ReadOnlyField(source='tags.name')
    color = serializers.ReadOnlyField(source='tags.color')

    class Meta:
        model = TagsRecipe
        fields = ('id', 'name', 'color')


class CreateUpdateTagsRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all())

    class Meta:
        model = Tag
        fields = ('id',)


class RecipeSerializer(serializers.ModelSerializer):
    author = FoodgramUserSerializer(read_only=True)
    tags = TagsSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def get_ingredients(self, obj):
        ingredients = IngredientsRecipe.objects.filter(recipe=obj)
        serializer = IngredientsRecipeSerializer(
            ingredients,
            many=True
        )
        return serializer.data

    def get_is_favorited(self, obj):
        user_id = self.context.get('request').user.id
        return Favorite.objects.filter(
            user=user_id,
            recipe=obj.id
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        user_id = self.context.get('request').user.id
        return ShoppingCart.objects.filter(
            user=user_id,
            recipe=obj
        ).exists()

    class Meta:
        model = Recipe
        exclude = ('created_at',)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    author = FoodgramUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = CreateUpdateIngredientsRecipeSerializer(many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        validators=(
            MinValueValidator(
                1, message='Время приготовления должно быть больше нуля.'
            ),
        )
    )

    def validate_tags(self, value):
        if not value:
            raise exceptions.ValidationError(
                'Нужно выбрать хотя бы один тег.'
            )
        for tag in value:
            if value.count(tag) > 1:
                raise exceptions.ValidationError(
                    'Теги должны быть уникальными.'
                )
        return value

    def validate_ingredients(self, value):
        if not value:
            raise exceptions.ValidationError(
                'Нужно выбрать хотя бы один ингредиент.'
            )
        ingredients = [item['id'] for item in value]
        for ingredient in ingredients:
            if ingredients.count(ingredient) > 1:
                raise exceptions.ValidationError(
                    'Ингредиенты должны быть уникальными.'
                )
        return value

    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)

        for ingredient in ingredients:
            amount = ingredient.get('amount')
            ingredient = get_object_or_404(
                Ingredients, pk=ingredient.get('id').id
            )

            IngredientsRecipe.objects.create(
                recipe=recipe,
                ingredients=ingredient,
                amount=amount
            )
        return recipe

    def update(self, instance, validated_data):
        if not validated_data.get('ingredients'):
            return response.Response(
                {'ingredients': 'Нужно выбрать хотя бы один ингредиент.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not validated_data.get('tags'):
            return response.Response(
                {'tags': 'Нужно выбрать хотя бы один тег.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        instance.image = validated_data.get('image', instance.image)
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.tags.set(tags)

        for ingredient in ingredients:
            amount = ingredient.get('amount')
            ingredient = get_object_or_404(
                Ingredients, pk=ingredient.get('id').id
            )

            IngredientsRecipe.objects.update_or_create(
                recipe=instance,
                ingredients=ingredient,
                amount=amount
            )
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data

    class Meta:
        model = Recipe
        exclude = ('created_at',)


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tags."""

    class Meta:
        model = Favorite
        fields = '__all__'
