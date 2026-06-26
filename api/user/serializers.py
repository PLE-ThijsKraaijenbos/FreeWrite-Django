from django.db.models import Exists, OuterRef
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from .models import AvatarItem, User, UserAvatarItem, Userprofile


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        return value.lower()


class UserProfileSerializer(serializers.ModelSerializer):
    # The avatar is derived from the user's equipped items (single source of
    # truth) rather than stored — a {param_key: param_value} map the client
    # turns into a DiceBear URL. Read-only; ignored on complete-profile input.
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Userprofile
        fields = [
            'id',
            'name',
            'avatar',
            'substance',
            'usage_duration',
            'goal',
            'usage_times',
            'frequency',
            'previous_attempts',
            'coins',
        ]

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_avatar(self, obj):
        equipped = obj.user.avatar_items.filter(is_equipped=True).select_related('item')
        params = {ua.item.param_key: ua.item.param_value for ua in equipped}
        # Probability gates aren't items — derive them from the equipped parents.
        if 'accessories' in params:
            params['accessoriesProbability'] = '100'
        if 'facialHair' in params:
            params['facialHairProbability'] = '100'
        return params


class ProfileUpdateSerializer(serializers.Serializer):
    # Partial profile update. Mirrors the onboarding name rule (non-empty after trim).
    name = serializers.CharField(min_length=1)


class AvatarItemSerializer(serializers.ModelSerializer):
    is_unlocked = serializers.BooleanField(read_only=True)
    is_equipped = serializers.BooleanField(read_only=True)

    class Meta:
        model = AvatarItem
        fields = ['id', 'name', 'param_key', 'param_value', 'price', 'is_unlocked', 'is_equipped']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'last_login', 'profile']


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        return value.lower()


class AuthResponseSerializer(serializers.Serializer):
    """Shape of the body returned by register and login: a token pair plus the user."""

    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()


class CompleteProfileRequestSerializer(UserProfileSerializer):
    """Request body for completing onboarding: the profile answers plus the chosen avatar."""

    avatar = serializers.DictField(child=serializers.CharField(), required=False)
