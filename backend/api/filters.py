from django_filters import ModelMultipleChoiceFilter
from django_filters.rest_framework import FilterSet, filters

from recipes.models import Recipe, Tag
from users.models import FoodgramUser


class RecipeFilter(FilterSet):
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_favorited = filters.BooleanFilter(method='favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='in_shopping_cart')
    author = filters.ModelChoiceFilter(queryset=FoodgramUser.objects.all())

    def favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(is_favorited__user=self.request.user)
        return queryset

    def in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(is_in_shopping_cart__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = ('author', 'tags')
