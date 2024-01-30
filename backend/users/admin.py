from django.contrib import admin

from recipes.models import (Ingredients, IngredientsRecipe, Recipe,
                            Subsription, Tag, TagsRecipe)

from .models import FoodgramUser


class IngredientsInLine(admin.TabularInline):
    model = IngredientsRecipe
    extra = 1


class TagsInLine(admin.TabularInline):
    model = TagsRecipe
    extra = 1


class IngredientsAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name', 'measurement_unit')
    search_fields = ('name', 'measurement_unit')
    empty_value_display = '-пусто-'
    inlines = [IngredientsInLine]


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')
    list_filter = ('name', 'color', 'slug')
    search_fields = ('name', 'color', 'slug')
    empty_value_display = '-пусто-'
    inlines = [TagsInLine]


class FoodgramUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('username', 'email')
    search_fields = ('username', 'email')
    empty_value_display = '-пусто-'


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'count_favorites')
    list_filter = ('name', 'author', 'tags')
    search_fields = ('name', 'author', 'tags')
    empty_value_display = '-пусто-'
    inlines = [IngredientsInLine, TagsInLine]
    readonly_fields = ('count_favorites',)

    def count_favorites(self, obj):
        return obj.is_favorited.count()

    count_favorites.short_description = 'Кол-во добавлений в избранное'


class SubsriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    list_filter = ('user', 'author')
    search_fields = ('user', 'author')
    empty_value_display = '-пусто-'


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Subsription, SubsriptionAdmin)
admin.site.register(FoodgramUser, FoodgramUserAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Ingredients, IngredientsAdmin)
