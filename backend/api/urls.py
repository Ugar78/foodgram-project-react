from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (FoodgramUserViewSet, IngredientsViewSet, RecipeViewSet,
                    TagsViewSet)

router = DefaultRouter()

router.register(
    'users',
    FoodgramUserViewSet,
    basename='users'
)

router.register(
    'recipes',
    RecipeViewSet,
    basename='recipes'
)

router.register(
    'tags',
    TagsViewSet,
    basename='tags'
)

router.register(
    'ingredients',
    IngredientsViewSet,
    basename='ingredients'
)

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
]
