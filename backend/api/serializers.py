from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from djoser.serializers import UserSerializer

from foodgram.constants import PAGE_SIZE
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientRecipe,
    Recipe,
    ShoppingCart,
    Subscription,
    Tag,
)
from users.models import User


class UserSerializer(UserSerializer):
    """ Сериализатор для модели User. """

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request_user = self.context['request'].user
        if not request_user.is_authenticated:
            return False
        return request_user.subscriber.filter(author=obj).exists()


class AvatarSerializer(serializers.ModelSerializer):
    """ Сериализатор для аватара пользователя. """

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class IngredientSerializer(serializers.ModelSerializer):
    """ Сериализатор для модели Ingredient. """

    #id = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit'
        )
        read_only_fields = (
            'id',
            'name',
            'measurement_unit'
        )


class IngredientRecipeGetSerializer(serializers.ModelSerializer):
    """ Сериализатор для модели IngredientRecipe при GET запросах. """

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор для модели IngredientRecipe при небезопасных запросах. """

    #id = serializers.IntegerField()
    ingredient_id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )

    class Meta:
        model = IngredientRecipe
        fields = (
            'id',
            'amount'
        )


class TagSerializer(serializers.ModelSerializer):
    """ Сериализатор для модели Tag. """

    id = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'slug'
        )


class RecipeGetSerializer(serializers.ModelSerializer):
    """ Сериализатор для модели Recipe при GET запросах. """

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    ingredients = IngredientRecipeGetSerializer(
        many=True, source='amount_ingredients'
    )
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        """ Метод для is_favorited. """
        user = self.context.get('request').user
        return (user.is_authenticated
                and user.favorites.filter(recipe=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        """ Метод для is_in_shopping_cart. """
        user = self.context.get('request').user
        return (user.is_authenticated
                and user.cart.filter(recipe=obj).exists())


class RecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор для модели Recipe при небезопасных запросах. """
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    author = UserSerializer(read_only=True)
    ingredients = IngredientRecipeSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def validate_cooking_time(self, cooking_time):
        if int(cooking_time) < 1:
            raise serializers.ValidationError(
                'Время готовки не может быть меньше минуты')
        return cooking_time

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Нужен хоть один ингридиент для рецепта'})

        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError('Не указаны тэги')

        if len(data['tags']) > len(set(data['tags'])):
            raise serializers.ValidationError('Теги не могут повторяться!')

        ingredient_list = []
        for ingredient_item in ingredients:
            ingredient = get_object_or_404(Ingredient,
                                           id=ingredient_item['id'])
            if ingredient in ingredient_list:
                raise serializers.ValidationError('Ингридиенты должны '
                                                  'быть уникальными')
            ingredient_list.append(ingredient)
            if int(ingredient_item['amount']) < 0:
                raise serializers.ValidationError({
                    'ingredients': ('Убедитесь, что значение количества '
                                    'ингредиента больше 0')
                })
        data['ingredients'] = ingredients
        return data

    def create_ingredients(self, ingredients, recipe):
        """ Метод для создания рецепта с ингридиентами. """

        IngredientRecipe.objects.bulk_create(
            IngredientRecipe(
                recipe=recipe,
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount'),)
            for ingredient in ingredients
        )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe=recipe, ingredients=ingredients)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.set(tags)
        IngredientRecipe.objects.filter(recipe=instance).delete()
        super().update(instance, validated_data)
        self.create_ingredients(ingredients, instance)
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeGetSerializer(instance, context=context).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """ Сериализатор для Favorite и ShoppingCart. """

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class FavoriteAndShoppingCartSerializerBase(serializers.ModelSerializer):
    """ Сериализатор для модели Favorite. """

    class Meta:
        model = Favorite
        abstract = True
        fields = ('user', 'recipe',)

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']
        if self.Meta.model.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в избранное.'
            )
        return data


class FavoriteSerializer(FavoriteAndShoppingCartSerializerBase):
    """ Сериализатор для модели Favorite.
    Для связи избранных рецептов пользователя между собой.
    """

    class Meta(FavoriteAndShoppingCartSerializerBase.Meta):
        pass


class ShoppingCartSerializer(FavoriteAndShoppingCartSerializerBase):
    """ Сериализатор для модели ShoppingCart.
    Для формирования карзины покупок пользователя.
    """

    class Meta(FavoriteAndShoppingCartSerializerBase.Meta):
        model = ShoppingCart


class SubscriptionSerializer(serializers.ModelSerializer):
    """ Сериализатор для модели Subscription. """

    class Meta:
        model = Subscription
        fields = ('user', 'author',)
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author',),
                message='Вы уже подписаны на этого пользователя'
            )
        ]


class SubscriptionReadSerializer(UserSerializer):
    """ Сериализатор для модели User для полей подписок. """

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit', PAGE_SIZE)
        try:
            limit = int(limit)
        except ValueError:
            pass
        return ShortRecipeSerializer(
            Recipe.objects.filter(author=obj)[:limit],
            many=True,
            context={'request': request},
        ).data

    def get_recipes_count(self, obj):
        """ Подсчет общего числа рецептов, связанных с данным пользователем. """
        return obj.recipes.count()
