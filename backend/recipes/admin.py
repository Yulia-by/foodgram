from django.contrib import admin

from foodgram.constants import INLINE_EXTRA, MIN_NUM
from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    IngredientRecipe,
    ShoppingCart,
    Favorite,
    Subscription
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug',)
    search_fields = ('name',)
    empty_value_display = '-пусто-'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit',)
    list_filter = ('name',)
    search_fields = ('name',)
    empty_value_display = '-пусто-'


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe
    extra = INLINE_EXTRA
    min_num = MIN_NUM


class TagInline(admin.TabularInline):
    model = Recipe.tags.through
    extra = INLINE_EXTRA
    min_num = MIN_NUM


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'likes',
        'author',
    )
    list_filter = ('author', 'name', 'tags',)
    search_fields = ('name', 'author')
    exclude = ('tags',)
    inlines = (IngredientRecipeInline, TagInline,)
    empty_value_display = '-пусто-'

    def likes(self, obj):
        return Favorite.objects.filter(recipe=obj).count()


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author', 'date_added',)
