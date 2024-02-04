from drf_extra_fields.fields import Base64ImageField
from rest_framework import exceptions, serializers

from foodgram.constants import MAX_VALUE, MIN_VALUE
from recipes.models import (Favorite, Ingredients, IngredientsRecipe, Recipe,
                            ShoppingCart, Subsription, Tag)
from users.models import FoodgramUser


class FoodgramUserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели FoodgramUser."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = FoodgramUser
        fields = ('id', 'username', 'first_name', 'last_name',
                  'email', 'is_subscribed')
        read_only_fields = ('username', 'first_name', 'last_name', 'email')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user_is_authenticated = request and request.user.is_authenticated
        user_id = request.user.id
        return bool(
            user_is_authenticated
            and Subsription.objects.filter(
                author=obj.id,
                user=user_id
            ).exists()
        )


class SubsriptionReadSerializer(FoodgramUserSerializer):
    """Сериализатор для модели Subsription."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(FoodgramUserSerializer.Meta):
        model = FoodgramUser
        fields = (
            FoodgramUserSerializer.Meta.fields
            + ('recipes', 'recipes_count', 'is_subscribed')
        )

    def get_recipes(self, obj):
        author_recipes = obj.recipes.all()
        request = self.context.get('request')

        if 'recipes_limit' in request.GET:
            recipes_limit = request.GET.get('recipes_limit')
            try:
                author_recipes = author_recipes[:int(recipes_limit)]
            except ValueError:
                pass
        return ShortRecipeSerializer(author_recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubsriptionWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Subsription."""
    author = serializers.SlugRelatedField(
        slug_field='id',
        queryset=FoodgramUser.objects.all()
    )
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Subsription
        fields = ('user', 'author')
        read_only_fields = ('user', 'author')

    def validate(self, data):
        user = self.context.get('request').user
        author = data.get('author')
        if user == author:
            raise exceptions.ValidationError(
                'Нельзя подписаться или отписаться от себя!'
            )
        if Subsription.objects.filter(
            user=user, author=author
        ).exists():
            raise exceptions.ValidationError(
                'Вы уже подписаны на этого пользователя!'
            )
        return data

    def to_representation(self, instance):
        return SubsriptionReadSerializer(
            instance.author, context={'request': self.context.get('request')}
        ).data


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
        min_value=MIN_VALUE,
        max_value=MAX_VALUE,
    )

    class Meta:
        model = Ingredients
        fields = ('id', 'amount')


class TagsSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Tag."""

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Recipe."""
    author = FoodgramUserSerializer(read_only=True)
    tags = TagsSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        exclude = ('created_at',)

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
        min_value=MIN_VALUE,
        max_value=MAX_VALUE,
    )

    class Meta:
        model = Recipe
        exclude = ('created_at',)

    def validate(self, data):
        image = data.get('image')
        if not image:
            raise exceptions.ValidationError(
                'Необходимо добавить изображение.'
            )
        tags = data.get('tags')
        if not tags:
            raise exceptions.ValidationError(
                'Необходимо добавить хотя бы один тег.'
            )
        tag_ids = [item.id for item in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise exceptions.ValidationError(
                'Теги должны быть уникальными.'
            )
        ingredients = data.get('ingredients')
        if not ingredients:
            raise exceptions.ValidationError(
                'Необходимо добавить хотя бы один ингредиент.'
            )
        ingredient_ids = [item['id'] for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise exceptions.ValidationError(
                'Ингредиенты должны быть уникальными.'
            )
        return data

    def ingredients_recipe_objects_create(
            self, model, ingredients, recipe
    ):
        model.objects.bulk_create(
            [
                model(
                    recipe=recipe,
                    ingredients=ingredient.get('id'),
                    amount=ingredient.get('amount')
                ) for ingredient in ingredients
            ]
        )

    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)

        self.ingredients_recipe_objects_create(
            IngredientsRecipe, ingredients, recipe
        )
        return recipe

    def update(self, instance, validated_data):
        instance.image = validated_data.get('image', instance.image)
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.ingredients_recipe_objects_create(
            IngredientsRecipe, ingredients, instance
        )
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        serializer = RecipeSerializer(
            instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data


class ShortRecipeSerializer(RecipeSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецепта в избранное."""
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')

    def validate(self, data):
        favorite = Favorite.objects.filter(
            user=data.get('user'),
            recipe=data.get('recipe')
        )
        if favorite.exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в избранное.'
            )
        return data

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецепта в корзину."""
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        shopping_cart = ShoppingCart.objects.filter(
            user=data.get('user'),
            recipe=data.get('recipe')
        )
        if shopping_cart.exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в корзину.'
            )
        return data

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data
