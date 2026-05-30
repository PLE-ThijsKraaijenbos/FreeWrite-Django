from rest_framework import serializers

from .models import Post


class PostSerializer(serializers.ModelSerializer):
    likes_count = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()
    author_name = serializers.SerializerMethodField()

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked_by_user(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_author_name(self, obj):
        if obj.author and hasattr(obj.author, 'profile'):
            return obj.author.profile.name
        return None

    class Meta:
        model = Post
        fields = ['id', 'title', 'body', 'likes_count', 'is_liked_by_user', 'author_name', 'created_at']


class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'title', 'body']
        read_only_fields = ['id']
