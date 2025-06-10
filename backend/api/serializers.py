from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.validators import UniqueTogetherValidator
from djoser.serializers import UserSerializer

from foodgram.constants import (
    PAGE_SIZE,
    MIN_AMOUNT,
    MESSAGE_INGREDIENT_AMOUNT,
    COOKING_TIME_MIN,
    MESSAGE_COOKING_TIME,
    MESSAGE_TAGS_UNIQUE,
    MESSAGE_INGREDIENT_UNIQUE
)
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
from shortener.models import LinkMapped


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
    """ Сериализатор для модели IngredientRecipe
    при небезопасных запросах.
    """

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

    def validate_amount(self, value):
        if value <= MIN_AMOUNT:
            raise serializers.ValidationError(MESSAGE_INGREDIENT_AMOUNT)
        return value


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
        if int(cooking_time) < COOKING_TIME_MIN:
            raise serializers.ValidationError(MESSAGE_COOKING_TIME)
        return cooking_time

    def validate_tags(self, tags):
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(MESSAGE_TAGS_UNIQUE)
        return tags

    def validate_ingredients(self, ingredients):
        ingredient_ids = [item['ingredient'].id for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(MESSAGE_INGREDIENT_UNIQUE)
        return ingredients

    def create_ingredients(self, ingredients, recipe):
        """ Метод для создания рецепта с ингредиентами. """
        IngredientRecipe.objects.bulk_create([
            IngredientRecipe(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ])

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.set(tags)
        IngredientRecipe.objects.filter(recipe=instance).delete()
        self.create_ingredients(ingredients, instance)
        return super().update(instance, validated_data)

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
    """ Сериализатор для вывода подписчиков с
    информацией о рецептах автора.
    """

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes_count_field')

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['recipes_count_field'] =\
            serializers.SerializerMethodField(method_name='get_recipes_count')

    def get_recipes(self, obj):
        """ Возвращает список рецептов пользователя,
        учитывая заданный лимит.
        """
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit', PAGE_SIZE)
        try:
            limit = min(int(limit), PAGE_SIZE)
        except ValueError:
            limit = PAGE_SIZE

        recipes = Recipe.objects.filter(author=obj)[:limit]
        serializer = ShortRecipeSerializer(recipes, many=True,
                                           context=self.context)
        return serializer.data

    def get_recipes_count(self, obj):
        """ Получает общее количество рецептов, созданных автором. """
        return Recipe.objects.filter(author=obj).count()


class ShortlinkSerializer(serializers.ModelSerializer):
    """Сериализатор коротких ссылок"""

    class Meta:
        model = LinkMapped
        fields = ('original_url',)
        write_only_fields = ('original_url',)

    def get_short_link(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(
            reverse('shortlink:load_url', args=[obj.url_hash])
        )

    def create(self, validated_data):
        instance, _ = LinkMapped.objects.get_or_create(**validated_data)
        return instance

    def to_representation(self, instance):
        return {'short-link': self.get_short_link(instance)}
