import base64

from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import exceptions, response, serializers, status

from recipes.models import (Favorite, Ingredients, IngredientsRecipe, Recipe,
                            ShoppingCart, Subsription, Tag, TagsRecipe)
from users.models import FoodgramUser


class ShortRecipeSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField(read_only=True)

    def get_image(self, obj):
        return obj.image.url

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FoodgramUserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели FoodgramUser."""
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user_is_authenticated = request and request.user.is_authenticated
        user_id = request.user.id if user_is_authenticated else None
        return bool(
            user_is_authenticated
            and Subsription.objects.filter(
                author=obj.id,
                user=user_id
            ).exists()
        )

    class Meta:
        model = FoodgramUser
        fields = ('id', 'username', 'first_name', 'last_name',
                  'email', 'is_subscribed')


# class FoodgramUserCreateSerializer(UserCreateSerializer):

#     class Meta:
#         model = FoodgramUser
#         fields = ('id', 'username', 'first_name', 'last_name',
#                   'email', 'password')


class SubsriptionReadSerializer(FoodgramUserSerializer):
    """Сериализатор для модели Subsription."""
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
            try:
                author_recipes = author_recipes[:int(recipes_limit)]
            except ValueError:
                raise exceptions.ValidationError(
                    'Некорректное значение recipes_limit'
                )

        return ShortRecipeSerializer(
            author_recipes,
            context={'request': self.context.get('request')},
            many=True
        ).data
        # return serializer.data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.id).count()
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # if self.context['request'].method == 'POST':
        data['is_subscribed'] = True
        data['recipes_count'] = self.instance.author.recipes.count()
        return data

    class Meta:
        model = Subsription
        fields = (
            'id', 'username', 'first_name', 'last_name',
            'email', 'is_subscribed', 'recipes', 'recipes_count'
        )


class SubsriptionWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Subsription."""
    def validate(self, data):
        user = self.context.get('request').user
        author = data.get('author')
        if user == author:
            raise exceptions.ValidationError(
                'Нельзя подписаться или отписаться от себя!'
            )
        return data

    # def to_representation(self, instance):

    # def create(self, validated_data):
    #     # user = self.context.get('request').user
    #     # author = validated_data.get('author')
    #     return Subsription.objects.create(**validated_data)

    

    class Meta:
        model = Subsription
        fields = ('user', 'author')
        read_only_fields = ('user', 'author')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Subsription.objects.all(),
                fields=('user', 'author'),
                message='Подписка уже оформлена!'
            )
        ]


class IngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Ingredients."""

    class Meta:
        model = Ingredients
        fields = '__all__'


class IngredientsRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели IngredientsRecipe."""
    id = serializers.ReadOnlyField(source='ingredients.id')
    name = serializers.ReadOnlyField(source='ingredients.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredients.measurement_unit'
    )

    class Meta:
        model = IngredientsRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class CreateUpdateIngredientsRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели IngredientsRecipe."""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredients.objects.all())
    amount = serializers.IntegerField(
        min_value=1,
        max_value=32000,
    )

    class Meta:
        model = Ingredients
        fields = ('id', 'amount')


# class Base64ImageField(serializers.ImageField):
#     def to_internal_value(self, data):
#         if isinstance(data, str) and data.startswith('data:image'):
#             format, imgstr = data.split(';base64,')
#             ext = format.split('/')[-1]

#             data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

#         return super().to_internal_value(data)


class TagsSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = '__all__'


# class TagsRecipeSerializer(serializers.ModelSerializer):
#     id = serializers.ReadOnlyField(source='tags.id')
#     name = serializers.ReadOnlyField(source='tags.name')
#     color = serializers.ReadOnlyField(source='tags.color')

#     class Meta:
#         model = TagsRecipe
#         fields = ('id', 'name', 'color')


# class CreateUpdateTagsRecipeSerializer(serializers.ModelSerializer):
#     id = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all())

#     class Meta:
#         model = Tag
#         fields = ('id',)


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe."""
    author = FoodgramUserSerializer(read_only=True)
    tags = TagsSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def get_image(self, obj):
        return obj.image.url

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
    """Сериализатор для модели Recipe."""
    author = FoodgramUserSerializer(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = CreateUpdateIngredientsRecipeSerializer(many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        min_value=1,
        max_value=32000,
    )

    def validate(self, data):
        tags = data.get('tags')
        tag_ids = [item.id for item in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise exceptions.ValidationError(
                'Теги должны быть уникальными.'
            )
        ingredients = data.get('ingredients')
        ingredient_ids = [item['id'] for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise exceptions.ValidationError(
                'Ингредиенты должны быть уникальными.'
            )
        return data
        

    # def validate_tags(self, value):
    #     if not value:
    #         raise exceptions.ValidationError(
    #             'Нужно выбрать хотя бы один тег.'
    #         )
    #     for tag in value:
    #         if value.count(tag) > 1:
    #             raise exceptions.ValidationError(
    #                 'Теги должны быть уникальными.'
    #             )
    #     return value

    # def validate_ingredients(self, value):
    #     if not value:
    #         raise exceptions.ValidationError(
    #             'Нужно выбрать хотя бы один ингредиент.'
    #         )
    #     ingredients = [item['id'] for item in value]
    #     for ingredient in ingredients:
    #         if ingredients.count(ingredient) > 1:
    #             raise exceptions.ValidationError(
    #                 'Ингредиенты должны быть уникальными.'
    #             )
    #     return value

    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)

        # for ingredient in ingredients:
        #     amount = ingredient.get('amount')
        #     ingredient = get_object_or_404(
        #         Ingredients, pk=ingredient.get('id').id
        #     )

        IngredientsRecipe.objects.bulk_create(
            [
                IngredientsRecipe(
                    recipe=recipe,
                    ingredients=ingredient.get('id'),
                    amount=ingredient.get('amount')
                ) for ingredient in ingredients
            ]
        )
        return recipe

    def update(self, instance, validated_data):
        # if not validated_data.get('ingredients'):
        #     return response.Response(
        #         {'ingredients': 'Нужно выбрать хотя бы один ингредиент.'},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )
        # if not validated_data.get('tags'):
        #     return response.Response(
        #         {'tags': 'Нужно выбрать хотя бы один тег.'},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )
        instance.image = validated_data.get('image', instance.image)
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        instance.ingredients.clear()
        for ingredient in ingredients:
            IngredientsRecipe.objects.update_or_create(
                recipe=instance,
                ingredients=ingredient.get('id'),
                defaults={'amount': ingredient.get('amount')}
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
    """Сериализатор для добавления рецепта в избранное."""
    user = serializers.ReadOnlyField(source='user.username')
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    def validate(self, data):
        user = self.context.get('request').user
        recipe = data.get('recipe')
        if user.favorites.filter(recipe=recipe).exists():
            raise exceptions.ValidationError(
                'Рецепт уже добавлен в избранное.'
            )
        return data
    
    def to_representation(self, instance):
        return RecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецепта в корзину."""
    user = serializers.ReadOnlyField(source='user.username')
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    def validate(self, data):
        user = self.context.get('request').user
        recipe = data.get('recipe')
        if user.shopping_cart.filter(recipe=recipe).exists():
            raise exceptions.ValidationError(
                'Рецепт уже добавлен в корзину.'
            )
        return data

    def to_representation(self, instance):
        return RecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
