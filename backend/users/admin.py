from django.contrib import admin

from recipes.models import Subsription

from .models import FoodgramUser


class FoodgramUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('username', 'email')
    search_fields = ('username', 'email')
    empty_value_display = '-пусто-'


class SubsriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    list_filter = ('user', 'author')
    search_fields = ('user', 'author')
    empty_value_display = '-пусто-'


admin.site.register(Subsription, SubsriptionAdmin)
admin.site.register(FoodgramUser, FoodgramUserAdmin)
