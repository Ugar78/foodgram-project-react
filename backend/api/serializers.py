import base64
import datetime as dt

import webcolors
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from django.conf import settings
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.shortcuts import get_object_or_404
# from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers, exceptions

from djoser.serializers import UserSerializer, UserCreateSerializer

from recipes.models import (
    Tag, Recipe, Ingredients, IngredientsRecipe,
    Favorite, ShoppingCart, Subsription, TagsRecipe
)
from users.models import FoodgramUser
from .pagination import PageNumberPagination


class ShortRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FoodgramUserSerializer(UserSerializer):
    # id = serializers.PrimaryKeyRelatedField(read_only=True)
    # username = serializers.CharField()
    # first_name = serializers.CharField()
    # last_name = serializers.CharField()
    # email = serializers.EmailField()
    # is_subscribed = serializers.BooleanField(
    #     default=False,
    #     read_only=True
    # )
    # password = serializers.CharField()
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
    # id = serializers.PrimaryKeyRelatedField(read_only=True)
    # username = serializers.CharField()
    # first_name = serializers.CharField()
    # last_name = serializers.CharField()
    # email = serializers.EmailField()
    # is_subscribed = serializers.BooleanField(
    #     default=False,
    #     read_only=True
    # )
    # password = serializers.CharField(write_only=True)

    # def create(self, validated_data):
    #     password = validated_data.pop('password')
    #     user = FoodgramUser.objects.create_user(**validated_data)
    #     user.set_password(password)
    #     user.save()
    #     return user

    class Meta:
        model = FoodgramUser
        fields = ('id', 'username', 'first_name', 'last_name',
                  'email', 'password')


class SubsriptionSerializer(
    FoodgramUserSerializer,
    PageNumberPagination
):
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    recipes = serializers.SerializerMethodField(
        # method_name='get_recipes'
    )
    recipes_count = serializers.ReadOnlyField(source='author.recipes.count')    
    is_subscribed = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        author_recipes = obj.author.recipes.all()
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
        # fields = ('id', 'name', 'measurement_unit')
        # read_only_fields = fields


class IngredientsRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredients.id')
    name = serializers.ReadOnlyField(read_only=True, source='ingredients.name')
    measurement_unit = serializers.ReadOnlyField(
    #    read_only=True,
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
    # name = serializers.CharField(
    #     required=True
    # )
    # slug = serializers.SlugField()

    class Meta:
        model = Tag
        fields = '__all__'
        # fields = ('id', 'name', 'color')
        # lookup_field = 'slug'


class TagsRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='tags.id')
    # tags = serializers.SerializerMethodField(method_name='get_tags')
    name = serializers.ReadOnlyField(read_only=True, source='tags.name')
    color = serializers.ReadOnlyField(
       read_only=True, source='tags.color'
    )
    # slug = serializers.ReadOnlyField(read_only=True, source='tags.slug')

    # def get_tags(self, obj):
    #     return obj.tags.values_list('id', flat=True)

    # def get_id(self, obj):
    #     return obj.tags.id

    # def get_name(self, obj):
    #     return obj.tags.name

    # def get_color(self, obj):
    #     return obj.tags.color

    # def get_slug(self, obj):
    #     return obj.tags.slug

    class Meta:
        model = TagsRecipe
        fields = ('id', 'name', 'color')


class CreateUpdateTagsRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all())
    # amount = serializers.IntegerField()
    # def to_representation(self, instance):
    #     return instance.id

    class Meta:
        model = Tag
        fields = ('id',)


class RecipeSerializer(serializers.ModelSerializer):
    author = FoodgramUserSerializer(read_only=True)
    # tags = serializers.SerializerMethodField()
    tags = TagsSerializer(
        # Tag.objects.all(),
        # read_only=True,
        many=True
    )
    ingredients = serializers.SerializerMethodField(
        # method_name='get_ingredients'
    )
    is_favorited = serializers.SerializerMethodField(
        # method_name='get_is_favorited'
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        # method_name='get_is_shopping_cart'
    )
    # name = serializers.CharField(required=True)
    
    # tags = serializers.SerializerMethodField(
    #     method_name='get_tags'
    # )
    
    

    def get_ingredients(self, obj):
        ingredients = IngredientsRecipe.objects.filter(recipe=obj)
        serializer = IngredientsRecipeSerializer(
            # IngredientsRecipe.objects.filter(recipe=obj),
            ingredients,
            many=True
        )
        return serializer.data

    # def get_tags(self, obj):
    #     tags = TagsRecipe.objects.filter(recipe=obj)
    #     serializer = TagsRecipeSerializer(
    #         tags,
    #         many=True
    #     )
    #     return serializer.data

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
    # tags = CreateUpdateTagsRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = CreateUpdateIngredientsRecipeSerializer(many=True)
    image = Base64ImageField(
        # required=False, allow_null=True
    )
    cooking_time = serializers.IntegerField(
        validators=(
            MinValueValidator(
                1, message=''
            ),
        )
    )
    # def get_tags(self, obj):
    #     return obj.tags.values_list('id', flat=True)
    def validate_tags(self, value):
        if not value:
            raise exceptions.ValidationError('')
        # tags = [item['id'] for item in value]
        # for tag in tags:
        #     if tags.count(tag) > 1:
        #         raise exceptions.ValidationError('')
        return value
    
    def validate_ingredients(self, value):
        if not value:
            raise exceptions.ValidationError('')
        ingredients = [item['id'] for item in value]
        for ingredient in ingredients:
            if ingredients.count(ingredient) > 1:
                raise exceptions.ValidationError('')
        return value

    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)

        for ingredient in ingredients:
            amount = ingredient.get('amount')
            ingredient = get_object_or_404(Ingredients, pk=ingredient.get('id').id)

            IngredientsRecipe.objects.create(
                recipe=recipe,
                ingredients=ingredient,
                amount=amount
            )
        # for tag in tags:
        #     # amount = ingredient.get('amount')
        #     tag = get_object_or_404(Tag, pk=tag.get('id').id)

        #     TagsRecipe.objects.create(
        #         recipe=recipe,
        #         tags=tag,
        #         amount=amount
        #     )
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.set(tags)
        ingredients = validated_data.pop('ingredients', None)
        if ingredients is not None:
            instance.ingredients.clear()

            for ingredient in ingredients:
                amount = ingredient.get('amount')
                ingredient = get_object_or_404(Ingredients, pk=ingredient.get('id').id)

                IngredientsRecipe.objects.update_or_create(
                    recipe=instance,
                    ingredients=ingredient,
                    # amount=amount
                    defaults={'amount': amount}
                )
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance,
            # context=self.context
            context={'request': self.context.get('request')}
        )
        return serializer.data

    class Meta:
        model = Recipe
        exclude = ('created_at',)


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tags."""
    # id = serializers.PrimaryKeyRelatedField(read_only=True)
    # name = serializers.CharField()
    # color = Hex2NameColor()

    class Meta:
        model = Favorite
        fields = '__all__'
        # fields = ('id', 'name', 'color', 'slug')