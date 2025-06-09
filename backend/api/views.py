from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import HttpResponse

from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.reverse import reverse

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAuthorOrReadOnly
from api.pagination import CustomLimitPagination
from api.serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeGetSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    SubscriptionReadSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserSerializer,
    ShortlinkSerializer,
)
from api.mixins import SubscribeMixin, RecipeFavoriteMixin
from djoser.views import UserViewSet
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag
)
from users.models import User
from shortlink.models import LinkMapped, generate_hash


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ Вьюсет для модели Tag. """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (IsAuthorOrReadOnly,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ Вьюсет для модели Ingredient. """

    permission_classes = (IsAuthorOrReadOnly,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet, RecipeFavoriteMixin):
    """Вьюсет для модели Recipe."""

    queryset = Recipe.objects.select_related(
        'author').prefetch_related('tags', 'amount_ingredients__ingredient')
    pagination_class = CustomLimitPagination
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ('GET', 'HEAD'):
            return RecipeGetSerializer
        return RecipeSerializer

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[permissions.AllowAny],
        serializer_class=ShortlinkSerializer,
        url_path='get-link',
        url_name='get-link',
    )
    def get_link(self, request, pk=None):
        """ Получение короткой ссылки на рецепт. Возвращает короткую ссылку,
        которая ведет на исходный рецепт.
        """

        # Шаг 2: Формируем полную оригинальную ссылку на рецепт
        full_original_url = request.build_absolute_uri(
            reverse('recipes-detail', kwargs={'pk': pk}))

        # Шаг 3: Создаем новую запись в таблице shortlinks с уникальным хешем
        link_mapped = LinkMapped.objects.create(
            original_url=full_original_url,
            url_hash=generate_hash(),
        )

        # Шаг 4: Формирование конечной короткой ссылки
        short_link = request.build_absolute_uri(
            reverse('shortlink:load_url',
                    kwargs={'url_hash': link_mapped.url_hash}))

        # Шаг 5: Возврат результата
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk):
        if request.method == 'POST':
            return self.add_recipe(request, pk, FavoriteSerializer)
        return self.remove_recipe(request, pk, Favorite)

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            return self.add_recipe(request, pk, ShoppingCartSerializer)
        return self.remove_recipe(request, pk, ShoppingCart)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(permissions.IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        ingredient_lst = ShoppingCart.objects.filter(
            user=request.user
        ).values_list(
            'recipe_id__ingredients__name',
            'recipe_id__ingredients__measurement_unit',
            Sum('recipe_id__ingredients__amount_ingredients__amount'))
        shopping_list = ['Список покупок:']
        ingredient_lst = set(ingredient_lst)
        for ingredient in ingredient_lst:
            shopping_list.append('{} ({}) - {}'.format(*ingredient))
        response = HttpResponse('\n'.join(shopping_list),
                                content_type='text/plain')
        response['Content-Disposition'] = 'attachment;' \
            'filename="shopping_list.txt"'
        return response


class UserViewSet(UserViewSet, SubscribeMixin):
    """Вьюсет для модели User."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomLimitPagination
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_permissions(self):
        if self.action == 'me':
            return (permissions.IsAuthenticated(),)
        return super().get_permissions()

    @action(
        ['put'],
        detail=False,
        permission_classes=(IsAuthorOrReadOnly,),
        url_path='me/avatar',
    )
    def avatar(self, request, *args, **kwargs):
        serializer = AvatarSerializer(
            instance=request.user,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request, *args, **kwargs):
        user = self.request.user
        user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, id):
        if request.method == 'POST':
            return self.add_subscription(request, id,
                                         SubscriptionReadSerializer)
        return self.remove_subscription(request, id)

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        authors = User.objects.filter(subscribers__user=request.user)
        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(page, many=True,
                                            context={'request': request})
        return self.get_paginated_response(serializer.data)
