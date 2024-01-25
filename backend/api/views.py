from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import HttpResponse
from django.db.models import Avg, Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet, generics
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework import status, viewsets, exceptions
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from .permissions import IsAuthorOrAdmin
from .filters import RecipeFilter

from .serializers import (
    RecipeSerializer,
    IngredientsSerializer,
    TagsSerializer,
    RecipeCreateUpdateSerializer,
    FoodgramUserSerializer,
    SubsriptionSerializer,
    FavoriteSerializer,
    # TagsRecipeSerializer,
    ShortRecipeSerializer
)
from recipes.models import (
    Tag, Recipe, Ingredients, Favorite,
    ShoppingCart, Subsription, IngredientsRecipe, TagsRecipe
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
    # filterset_fields = ('ext',)
    # search_fields = ('ext',) 
    filterset_class = RecipeFilter
    # pagination_class = CustomPageNumberPagination
    
    # serializer_class = RecipeSerializer
    # http_method_names = ('get', 'post', 'patch', 'delete')

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeSerializer
    
    # def perform_create(self, serializer):
    #     return serializer.save(author=self.request.user)

    def add(self, model, user, pk, name):
        recipe = get_object_or_404(Recipe, pk=pk)
        relation = model.objects.filter(user=user, recipe=recipe)
        if relation.exists():
            return Response(
                {'errors': f'Нельзя повторно добавить рецепт в {name}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        model.objects.create(user=user, recipe=recipe)
        serializer = ShortRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def delete_rel(self, model, user, pk, name):
        recipe = get_object_or_404(Recipe, pk=pk)
        relation = model.objects.filter(user=user, recipe=recipe)
        if not relation.exists():
            return Response(
                {'errors': f'Нельзя повторно удалить рецепт из {name}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        relation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='favorite',
        url_name='favorite'
    )
    def favorite(self, request, pk=None):
        user = request.user
        # recipe = get_object_or_404(Recipe, pk=pk)
        if self.request.method == 'POST':
            name = 'избранное'
            return self.add(Favorite, user, pk, name)
            # if Favorite.objects.filter(
            #     user=user,
            #     recipe=recipe
            # ).exists():
            #     raise exceptions.ValidationError('')
            # Favorite.objects.create(user=user, recipe=recipe)
            # serializer = RecipeSerializer()
            # return Response(serializer.data, status=status.HTTP_201_CREATED)
        if self.request.method == 'DELETE':
            name = 'избранного'
            return self.delete_rel(Favorite, user, pk, name)
            # if not Favorite.objects.filter(
            #     user=user,
            #     recipe=recipe
            # ).exists():
            #     raise exceptions.ValidationError('')
            # favorite = Favorite.objects.filter(user=user, recipe=recipe)
            # # favorite = get_object_or_404(Favorite, user=user, recipe=recipe)
            # favorite.delete()
            # return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='shopping_cart',
        url_name='shopping_cart'
    )
    def shopping_cart(self, request, pk=None):
        user = self.request.user
        # recipe = get_object_or_404(Recipe, pk=pk)
        if self.request.method == 'POST':
            name = 'список покупок'
            return self.add(ShoppingCart, user, pk, name)
            # if ShoppingCart.objects.filter(
            #     user=user,
            #     recipe=recipe
            # ).exists():
            #     raise exceptions.ValidationError('')
            # ShoppingCart.objects.create(user=user, recipe=recipe)
            # serializer = RecipeSerializer()
            # return Response(serializer.data, status=status.HTTP_201_CREATED)
        if self.request.method == 'DELETE':
            name = 'списка покупок'
            return self.delete_rel(ShoppingCart, user, pk, name)
            # if not ShoppingCart.objects.filter(
            #     user=user,
            #     recipe=recipe
            # ).exists():
            #     raise exceptions.ValidationError('')
            # shopping_cart = ShoppingCart.objects.filter(user=user, recipe=recipe)
            # # shopping_cart = get_object_or_404(ShoppingCart, user=user, recipe=recipe)
            # shopping_cart.delete()
            # return Response(status=status.HTTP_204_NO_CONTENT)
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
    # permission_classes = (IsAuthenticatedOrReadOnly,)
    # http_method_names = ('get',)


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer


class FoodgramUserViewSet(UserViewSet):
    # queryset = FoodgramUser.objects.all()
    # serializer_class = FoodgramUserSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,)
        # serializer_class=SubsriptionSerializer,
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
        # user_subscriptions = user.subscribes.all()
        # authors = [item.author.id for item in user_subscriptions]
        # queryset = FoodgramUser.objects.filter(pk__in=authors)
        # paginated_queryset = self.paginate_queryset(queryset)
        # serializer = self.get_serializer(paginated_queryset, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete'),
        # serializer_class=SubsriptionSerializer,
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
