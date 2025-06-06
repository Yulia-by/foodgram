from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
from rest_framework.response import Response
from rest_framework import status


class FavoriteMixin(CreateModelMixin, DestroyModelMixin):
    def add_to_favorites(self, request, pk):
        """Добавление рецепта в избранное"""
        serializer = self.favorite_serializer_class(
            data={"user": request.user.id, "recipe": pk})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_from_favorites(self, request, pk):
        """Удаление рецепта из избранного"""
        favorite = self.favorite_model.objects.get(user=request.user, recipe=pk)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartMixin(CreateModelMixin, DestroyModelMixin):
    def add_to_cart(self, request, pk):
        """Добавление рецепта в корзину"""
        serializer = self.cart_serializer_class(
            data={"user": request.user.id, "recipe": pk})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_from_cart(self, request, pk):
        """Удаление рецепта из корзины"""
        cart_item = self.cart_model.objects.get(user=request.user, recipe=pk)
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscribeMixin(CreateModelMixin, DestroyModelMixin):
    def subscribe(self, request, id):
        if request.method == 'POST':
            serializer = self.get_subscription_serializer(request, id)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            subscription = self.get_subscription_instance(request, id)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    def get_subscription_serializer(self, request, id):
        pass

    def get_subscription_instance(self, request, id):
        pass


class AvatarMixin(UpdateModelMixin):
    def avatar(self, request, *args, **kwargs):
        serializer = self.get_avatar_serializer(request)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete_avatar(self, request, *args, **kwargs):
        user = request.user
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_avatar_serializer(self, request):
        pass
