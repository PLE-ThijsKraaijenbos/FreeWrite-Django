from django.db.models import Exists, OuterRef
from rest_framework import serializers
from .models import AvatarItem, User, UserAvatarItem, Userprofile


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Userprofile
        fields = [
            'id',
            'name',
            'avatar_url',
            'substance',
            'usage_duration',
            'goal',
            'usage_times',
            'frequency',
            'previous_attempts',
        ]


class AvatarItemSerializer(serializers.ModelSerializer):
    is_unlocked = serializers.BooleanField(read_only=True)
    is_equipped = serializers.BooleanField(read_only=True)

    class Meta:
        model = AvatarItem
        fields = ['id', 'name', 'param_key', 'param_value', 'is_unlocked', 'is_equipped']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'last_login', 'profile']


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
