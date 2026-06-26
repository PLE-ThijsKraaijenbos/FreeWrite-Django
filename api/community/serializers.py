from rest_framework import serializers

from .models import Post, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'value']


class PostSerializer(serializers.ModelSerializer):
    likes_count = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()
    is_own_post = serializers.SerializerMethodField()
    author_name = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)

    def get_likes_count(self, obj) -> int:
        return obj.likes.count()

    def get_is_liked_by_user(self, obj) -> bool:
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_is_own_post(self, obj) -> bool:
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.author_id == request.user.id
        return False

    def get_author_name(self, obj) -> str | None:
        if obj.author and hasattr(obj.author, 'profile'):
            return obj.author.profile.name
        return None

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'body', 'image_url',
            'likes_count', 'is_liked_by_user', 'is_own_post',
            'author_name', 'created_at', 'tags',
        ]


class PostCreateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, write_only=True, allow_null=True)
    tag_ids = serializers.ListField(child=serializers.UUIDField(), required=False, write_only=True)

    def create(self, validated_data):
        from .services import PostService
        image = validated_data.pop('image', None)
        tag_ids = validated_data.pop('tag_ids', [])
        return PostService.create_post(image=image, tag_ids=tag_ids, **validated_data)

    class Meta:
        model = Post
        fields = ['id', 'title', 'body', 'image', 'tag_ids']
        read_only_fields = ['id']


class PostUpdateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, write_only=True, allow_null=True)
    tag_ids = serializers.ListField(child=serializers.UUIDField(), required=False, write_only=True)

    def update(self, instance, validated_data):
        from .services import PostService
        image = validated_data.pop('image', None)
        tag_ids = validated_data.pop('tag_ids', None)
        user = validated_data.pop('user')
        return PostService.update_post(post=instance, user=user, image=image, tag_ids=tag_ids, **validated_data)

    class Meta:
        model = Post
        fields = ['title', 'body', 'image', 'tag_ids']
