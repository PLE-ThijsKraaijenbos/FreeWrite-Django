from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import AvatarItem, User, UserAvatarItem, Userprofile


@admin.register(User)
class UserAdmin(ModelAdmin, BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    ordering = ['email']
    list_display = ['email', 'is_active', 'is_staff', 'is_superuser']
    search_fields = ['email']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )


@admin.register(Userprofile)
class UserprofileAdmin(ModelAdmin):
    list_display = ['user', 'name', 'substance', 'goal']
    search_fields = ['user__email', 'name']
    autocomplete_fields = ['user']


@admin.register(AvatarItem)
class AvatarItemAdmin(ModelAdmin):
    list_display = ['name', 'param_key', 'param_value']
    search_fields = ['name', 'param_key', 'param_value']
    list_filter = ['param_key']


@admin.register(UserAvatarItem)
class UserAvatarItemAdmin(ModelAdmin):
    list_display = ['user', 'item', 'is_equipped', 'unlocked_at']
    list_filter = ['is_equipped']
    autocomplete_fields = ['user', 'item']
    search_fields = ['user__email', 'item__name']
