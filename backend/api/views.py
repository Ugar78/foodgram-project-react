from django.http import HttpResponse, HttpResponseNotFound
from django.db.models import Sum
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework import status, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.response import Response

from .permissions import IsAuthorOrAdmin
from .filters import RecipeFilter

from .serializers import (
    RecipeSerializer,
    IngredientsSerializer,
    TagsSerializer,
    RecipeCreateUpdateSerializer,
    SubsriptionSerializer,
    FavoriteSerializer,
    ShortRecipeSerializer
)
from recipes.models import (
    Tag, Recipe, Ingredients, Favorite,
    ShoppingCart, Subsription, IngredientsRecipe
    )
from users.models import FoodgramUser


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

    def add(self, model, user, pk, name):
        try:
            recipe = Recipe.objects.get(id=pk)
        except Recipe.DoesNotExist:
            return Response(
                {'errors': f'рецепт отсутствует в {name}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        relation = model.objects.filter(user=user, recipe=recipe)
        if relation.exists():
            return Response(
                {'errors': f'Нельзя повторно добавить рецепт в {name}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        model.objects.create(user=user, recipe=recipe)
        serializer = ShortRecipeSerializer(
            recipe,
            context={'request': self.request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_rel(self, model, user, pk, name):
        recipe = get_object_or_404(Recipe, pk=pk)
        relation = model.objects.filter(user=user, recipe=recipe)
        if not relation.exists():
            return Response(
                {'errors': f'Нельзя повторно удалить рецепт из {name}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        rel = get_object_or_404(model, user=user, recipe=recipe)
        rel.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='favorite',
        url_name='favorite'
    )
    def favorite(self, request, pk=None):
        user = self.request.user
        if self.request.method == 'POST':
            name = 'избранное'
            return self.add(Favorite, user, pk, name)
        if self.request.method == 'DELETE':
            name = 'избранного'
            return self.delete_rel(Favorite, user, pk, name)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='shopping_cart',
        url_name='shopping_cart'
    )
    def shopping_cart(self, request, pk=None):
        user = self.request.user
        if self.request.method == 'POST':
            name = 'список покупок'
            return self.add(ShoppingCart, user, pk, name)
        if self.request.method == 'DELETE':
            name = 'списка покупок'
            return self.delete_rel(ShoppingCart, user, pk, name)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
        url_name='download_shopping_cart'
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
        serializer = SubsriptionSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete'),
    )
    def subscribe(self, request, id):
        user = self.request.user
        author = get_object_or_404(FoodgramUser, pk=id)

        if user == author:
            return Response(
                {'errors': 'Нельзя подписаться или отписаться от себя!'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if self.request.method == 'POST':
            if Subsription.objects.filter(user=user, author=author).exists():
                return Response(
                    {'errors': 'Подписка уже оформлена!'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = Subsription.objects.create(author=author, user=user)
            serializer = SubsriptionSerializer(
                queryset, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == 'DELETE':
            if not Subsription.objects.filter(
                user=user,
                author=author
            ).exists():
                return Response(
                    {'errors': 'Вы уже отписаны!'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subsription = get_object_or_404(
                Subsription,
                user=user,
                author=author
            )
            subsription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='me'
    )
    def get_me(self, request):
        user = self.request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


def page_not_found(request, exception):
    url = reverse('home')
    return HttpResponseNotFound(
        f'<h1>Custom 404</h1>'
        f'<p>Страницы с адресом {request.path} не существует</p>'
        f'<a href="{request.build_absolute_uri(url)}">Идите на главную</a>'
    )
