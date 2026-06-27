from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Comment, CommentLike, Post, PostLike, Tag


@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = ['id', 'author', 'title', 'created_at']

@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ['id', 'value']


@admin.register(PostLike)
class PostLikeAdmin(ModelAdmin):
    list_display = ['id', 'user', 'post', 'created_at']


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ['id', 'post', 'body']


@admin.register(CommentLike)
class CommentLikeAdmin(ModelAdmin):
    list_display = ['id', 'user', 'comment', 'created_at']