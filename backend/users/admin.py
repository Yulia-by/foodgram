from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('id', 'first_name', 'last_name', 'email',)
    search_fields = ('email', 'first_name',)
    list_filter = ('email', 'first_name',)
