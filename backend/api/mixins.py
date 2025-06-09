from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.response import Response

from .serializers import ShortRecipeSerializer, SubscriptionReadSerializer
from recipes.models import Recipe, Subscription, User


class RecipeFavoriteMixin:
    def add_recipe(self, request, pk, serializer_class):
        """ Добавление рецепта в избранное или корзину. """
        if request.user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        recipe = get_object_or_404(Recipe, id=pk)
        data = {
            'user': request.user.id,
            'recipe': recipe.id
        }
        serializer = serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            ShortRecipeSerializer(recipe).data,
            status=status.HTTP_201_CREATED
        )

    def remove_recipe(self, request, pk, model):
        """ Удаление рецепта из избранного или корзины. """
        if request.user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        obj = get_object_or_404(model, user=request.user, recipe=pk)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscribeMixin:
    def add_subscription(self, request, pk, serializer_class):
        """ Подписаться на автора рецептов. """

        author = get_object_or_404(User, id=pk)
        data = {
            'user': request.user.id,
            'author': author.id
        }
        serializer = serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            SubscriptionReadSerializer(author).data,
            status=status.HTTP_201_CREATED
        )

    def remove_subscription(self, request, pk):
        """ Отписаться от автора рецептов. """

        subscription = get_object_or_404(Subscription, user=request.user,
                                         author=pk)
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
