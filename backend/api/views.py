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
    RecipeGetSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    SubscriptionReadSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserSerializer,
)
from api.mixins import (
    FavoriteMixin,
    ShoppingCartMixin,
    AvatarMixin,
    SubscribeMixin,
)
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


class RecipeViewSet(viewsets.ModelViewSet, FavoriteMixin, ShoppingCartMixin):
    """ Вьюсет для модели Recipe. """

    pagination_class = CustomLimitPagination
    permission_classes = (IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        return Recipe.objects.prefetch_related(
            'amount_ingredients__ingredient', 'tags').all()

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ("GET", ):
            return RecipeGetSerializer
        return RecipeSerializer

    @action(detail=True, methods=["GET"], permission_classes=[AllowAny])
    def get_link(self, request, pk=None):
        _ = get_object_or_404(Recipe, pk=pk)
        url = request.build_absolute_uri(f"/recipes/{pk}/")
        return Response({"short-link": url}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post", "delete"])
    def favorite(self, request, pk):
        if request.method == "POST":
            return self.add_to_favorites(request, pk)
        return self.remove_from_favorites(request, pk)

    @action(detail=True, methods=["post", "delete"])
    def shopping_cart(self, request, pk):
        if request.method == "POST":
            return self.add_to_cart(request, pk)
        return self.remove_from_cart(request, pk)

    @action(detail=False, methods=["get"],
            permission_classes=(IsAuthenticatedOrReadOnly,))
    def download_shopping_cart(self, request):
        ingredient_lst = ShoppingCart.objects.filter(
            user=request.user).values_list(
            "recipe_id__ingredients__name",
            "recipe_id__ingredients__measurement_unit",
            Sum("recipe_id__ingredients__amount_ingredients__amount"),
        )

        shopping_list = ["Список покупок:"]
        ingredient_lst = set(ingredient_lst)

        for ingredient in ingredient_lst:
            shopping_list.append("{} ({}) - {}".format(*ingredient))

        response = HttpResponse("\n".join(shopping_list),
                                content_type="text/plain")
        response["Content-Disposition"] = 'attachment;' \
            'filename="shopping_list.txt"'
        return response

    # Настройка миксинов
    favorite_model = Favorite
    favorite_serializer_class = FavoriteSerializer
    cart_model = ShoppingCart
    cart_serializer_class = ShoppingCartSerializer


class CustomUserViewSet(AvatarMixin, SubscribeMixin, viewsets.GenericViewSet):
    """ Вьюсет для модели User. """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomLimitPagination
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_permissions(self):
        if self.action == 'me':
            return (IsAuthenticated(),)
        return super().get_permissions()

    @action(['put'], detail=False, permission_classes=(IsAuthenticated,))
    def avatar(self, request, *args, **kwargs):
        return super().avatar(request, *args, **kwargs)

    @avatar.mapping.delete
    def delete_avatar(self, request, *args, **kwargs):
        return super().delete_avatar(request, *args, **kwargs)

    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, id):
        return super().subscribe(request, id)

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        user = request.user
        authors = User.objects.filter(subscribers__user=user)

        paged_queryset = self.paginate_queryset(authors)
        serializer = SubscriptionReadSerializer(
            paged_queryset,
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(serializer.data)

    def get_subscription_serializer(self, request, id):
        return SubscriptionSerializer(data={
            'user': request.user.pk,
            'author': id
        })

    def get_subscription_instance(self, request, id):
        return Subscription.objects.get(user=request.user, author=id)

    def get_avatar_serializer(self, request):
        return AvatarSerializer(instance=request.user, data=request.data)
