import uuid

from django.conf import settings
from django.db import models


class Post(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts',
        null=True,
        blank=True,
    )
    title = models.TextField()
    body = models.TextField()
    image_url = models.TextField(blank=True, null=True)
    tags = models.ManyToManyField('Tag', through='PostTag', related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'post'


class PostLike(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='post_likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'post_like'
        unique_together = [('user', 'post')]


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    body = models.TextField()

    class Meta:
        db_table = 'comment'


class CommentLike(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comment_likes')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'comment_like'
        unique_together = [('user', 'comment')]


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    value = models.TextField(unique=True)

    class Meta:
        db_table = 'tag'


class PostTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_tags')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='post_tags')

    class Meta:
        db_table = 'post_tag'