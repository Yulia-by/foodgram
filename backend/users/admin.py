from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import TokenProxy

from users.models import User


@admin.register(User)
class UserAdmin(UserAdmin):
    model = User
    list_display = ('id', 'first_name', 'last_name', 'email',)
    search_fields = ('email', 'first_name',)
    list_filter = ('email', 'first_name',)


admin.site.unregister([Group, TokenProxy])
