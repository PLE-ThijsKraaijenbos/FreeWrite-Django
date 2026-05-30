from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Post, PostLike


@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = ['id', 'author', 'title', 'created_at']


@admin.register(PostLike)
class PostLikeAdmin(ModelAdmin):
    list_display = ['id', 'user', 'post', 'created_at']
