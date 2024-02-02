from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredients, IngredientsRecipe, Recipe,
                            ShoppingCart, Subsription, Tag)
from users.models import FoodgramUser

from .filters import RecipeFilter
from .permissions import IsAuthorOrAdmin
from .serializers import (FavoriteSerializer, IngredientsSerializer,
                          RecipeCreateUpdateSerializer, RecipeSerializer,
                          ShoppingCartSerializer, SubsriptionReadSerializer,
                          SubsriptionWriteSerializer, TagsSerializer)


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Представление модели Recipe.
    Обрабатывает все запросы с учетом прав доступа.
    """
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrAdmin,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def add(self, serializer, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer_add = serializer(
            data={'user': user.id, 'recipe': recipe.id},
            context={'request': request}
        )
        serializer_add.is_valid(raise_exception=True)
        serializer_add.save()
        return Response(serializer_add.data, status=status.HTTP_201_CREATED)

    def delete_rel(self, model, request, pk, name):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        relation = model.objects.filter(user=user, recipe=recipe)
        relation.delete()
        if relation.exists():
            return Response(
                {'errors': f'Нельзя повторно удалить рецепт из {name}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post', 'delete'),
    )
    def favorite(self, request, pk=None):
        if self.request.method == 'POST':
            return self.add(FavoriteSerializer, request, pk)
        if self.request.method == 'DELETE':
            name = 'избранного'
            return self.delete_rel(Favorite, request, pk, name)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=True,
        methods=('post', 'delete'),
    )
    def shopping_cart(self, request, pk=None):
        if self.request.method == 'POST':
            return self.add(ShoppingCartSerializer, request, pk)
        if self.request.method == 'DELETE':
            name = 'списка покупок'
            return self.delete_rel(ShoppingCart, request, pk, name)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        shopping_cart = ShoppingCart.objects.filter(user=self.request.user)
        recipes = [item.recipe.id for item in shopping_cart]
        buy_list = IngredientsRecipe.objects.filter(
            recipe__in=recipes
        ).values(
            'ingredients'
        ).annotate(
            amount=Sum('amount')
        )
        buy_list_text = ['to buy:']
        for item in buy_list:
            ingredient = Ingredients.objects.get(pk=item['ingredients'])
            amount = item['amount']
            buy_list_text.append(
                f'{ingredient.name}, {amount} '
                f'{ingredient.measurement_unit}'
            )
            buy_list_text_file = '\n'.join(buy_list_text)
        responce = HttpResponse(buy_list_text_file, content_type='text/plain')
        responce['Content-Disposition'] = (
            'attachment; filename=shopping-list.txt'
        )
        return responce


class CreateRecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeCreateUpdateSerializer


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = None
    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('^name',)


class TagsViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = None
    queryset = Tag.objects.all()
    serializer_class = TagsSerializer


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer


class FoodgramUserViewSet(UserViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        user = self.request.user
        queryset = user.follower.all()
        pages = self.paginate_queryset(queryset)
        serializer = SubsriptionReadSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)

    )
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(FoodgramUser, pk=id)

        if self.request.method == 'POST':
            serializer = SubsriptionWriteSerializer(
                data={'user': user, 'author': id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == 'DELETE':
            Subsription.objects.filter(user=user, author=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def get_permissions(self):
        if self.action == 'me':
            return (IsAuthenticated(),)
        return super().get_permissions()
