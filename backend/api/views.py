from django.db.models import Count, Sum
from django.http import HttpResponse

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.reverse import reverse

from djoser.views import UserViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAdminAuthorOrReadOnly
from api.pagination import LimitPagination
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
    ShortenerSerializer,
)
from api.mixins import SubscribeMixin, RecipeFavoriteMixin
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag
)
from users.models import User


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ Вьюсет для модели Tag. """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (IsAdminAuthorOrReadOnly,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ Вьюсет для модели Ingredient. """

    permission_classes = (AllowAny,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet, RecipeFavoriteMixin):
    """Вьюсет для модели Recipe."""

    queryset = Recipe.objects.all()
    pagination_class = LimitPagination
    permission_classes = (IsAdminAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ('list', 'retrieve'):
            return RecipeGetSerializer
        elif self.action == 'get_link':
            return ShortenerSerializer
        return RecipeSerializer

    @action(
        methods=['get'],
        detail=True,
        permission_classes=[AllowAny],

        url_path='get-link',
        url_name='get-link',
    )
    def get_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт"""
        self.get_object()
        original_url = request.META.get('HTTP_REFERER')
        if original_url is None:
            url = reverse('api:recipe-detail', kwargs={'pk': pk})
            original_url = request.build_absolute_uri(url)
        serializer = self.get_serializer(
            data={'original_url': original_url},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

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
        permission_classes=(IsAuthenticated,)
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
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response


class UserViewSet(UserViewSet, SubscribeMixin):
    """Вьюсет для модели User."""

    queryset = User.objects.annotate(recipes_count=Count('recipe_author'))
    serializer_class = UserSerializer
    pagination_class = LimitPagination
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_permissions(self):
        if self.action == 'me':
            return (IsAuthenticated(),)
        return super().get_permissions()

    @action(
        ['put'],
        detail=False,
        permission_classes=(IsAdminAuthorOrReadOnly,),
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
            return self.add_subscription(request, id, SubscriptionSerializer)
        return self.remove_subscription(request, id)

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        authors = User.objects.filter(subscribers__user=request.user)
        page = self.paginate_queryset(authors)
        serializer = SubscriptionReadSerializer(
            page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)
