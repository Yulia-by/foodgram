from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import HttpResponse

from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.filters import RecipeFilter
from api.permissions import IsAuthorOrReadOnly
from api.pagination import CustomLimitPagination
from api.serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    RecipeFavoriteSerializer,
    RecipeGetSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    SubscriptionReadSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserSerializer,
)
from api.utils import create_object, delete_object
from djoser.views import UserViewSet
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Subscription,
    Tag
)
from users.models import User


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ Вьюсет для модели Tag. """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (IsAuthorOrReadOnly,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ Вьюсет для модели Ingredient. """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = (IsAuthorOrReadOnly,)

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        ingredients = self.request.query_params.get('name')
        if ingredients is not None:
            queryset = queryset.filter(name__istartswith=ingredients)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    """ Вьюсет для модели Recipe. """

    pagination_class = CustomLimitPagination
    permission_classes = (IsAuthorOrReadOnly,
                          permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        return (Recipe.objects.prefetch_related(
                'amount_ingredients__ingredient',
                'tags').all())

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeGetSerializer
        return RecipeSerializer

    @action(
        detail=True,
        methods=['GET'],
        permission_classes=[AllowAny],
        url_path='get-link',
        url_name='get-link',
    )
    def get_link(self, request, pk=None):
        _ = get_object_or_404(Recipe, pk=pk)
        url = request.build_absolute_uri(f'/recipes/{pk}/')
        return Response({'short-link': url}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk):
        if request.method == 'POST':
            serializer = create_object(
                request,
                pk,
                FavoriteSerializer,
                RecipeFavoriteSerializer,
                Recipe
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        delete_object(request, pk, Recipe, Favorite)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            serializer = create_object(
                request,
                pk,
                ShoppingCartSerializer,
                RecipeFavoriteSerializer,
                Recipe
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        delete_object(request, pk, Recipe, ShoppingCart)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=(permissions.IsAuthenticated,))
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
        response['Content-Disposition'] = \
            'attachment; filename="shopping_list.txt"'
        return response


class CustomUserViewSet(UserViewSet):
    """ Вьюсет для модели User. """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomLimitPagination
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_permissions(self):
        if self.action == 'me':
            return (IsAuthenticated(),)
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

    @action(
        detail=True,
        methods=['post', 'delete'],
    )
    def subscribe(self, request, id):
        if request.method == 'POST':
            serializer = create_object(
                request,
                id,
                SubscriptionSerializer,
                SubscriptionReadSerializer,
                User
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        delete_object(request, id, User, Subscription)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
    )
    def subscriptions(self, request):
        user = request.user
        authors = User.objects.filter(subscribing__user=user)

        paged_queryset = self.paginate_queryset(authors)
        serializer = SubscriptionReadSerializer(
            paged_queryset,
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(serializer.data)
