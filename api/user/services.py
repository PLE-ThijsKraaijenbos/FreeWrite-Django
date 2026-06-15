from urllib.parse import parse_qsl, urlparse

from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.db import transaction
from django.db.models import F
from rest_framework_simplejwt.tokens import RefreshToken
from .exceptions import AvatarItemNotOwned, EmailAlreadyExists, InsufficientCoins, InvalidCredentials
from .models import AvatarItem, User, UserAvatarItem, Userprofile


class UserService:
    @staticmethod
    def register(*, email, password):
        if User.objects.filter(email__iexact=email).exists():
            raise EmailAlreadyExists()

        user = User.objects.create_user(email=email, password=password)
        update_last_login(User, user)
        refresh = RefreshToken.for_user(user)

        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': user,
        }

    @staticmethod
    def login(*, email, password):
        user = authenticate(username=email, password=password)

        if user is None:
            raise InvalidCredentials()

        update_last_login(User, user)
        refresh = RefreshToken.for_user(user)

        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': user,
        }

    @staticmethod
    def complete_profile(*, user, data):
        from journey.services import JourneyService
        Userprofile.objects.create(user=user, **data)
        AvatarService.grant_default_items(user=user, avatar_url=data.get('avatar_url', ''))
        JourneyService.sync_with_profile(user=user)

        return {
            'user': user,
        }


class AvatarService:
    @staticmethod
    def update_avatar_url(*, user, avatar_url: str) -> None:
        Userprofile.objects.filter(user=user).update(avatar_url=avatar_url)

    @staticmethod
    def _parse_avatar_params(avatar_url: str) -> dict:
        query = urlparse(avatar_url or '').query
        return {k.replace('[]', ''): v for k, v in parse_qsl(query)}

    @staticmethod
    @transaction.atomic
    def grant_default_items(*, user, avatar_url: str) -> None:
        """
        auto unlock default items after onboarding.
        items are parsed from the avatar_url that's provided by the frontend.
        """
        params = AvatarService._parse_avatar_params(avatar_url)
        for param_key, param_value in params.items():
            item = AvatarItem.objects.filter(param_key=param_key, param_value=param_value).first()
            if item is None:
                continue
            user_item, _ = UserAvatarItem.objects.get_or_create(user=user, item=item)
            if not user_item.is_equipped:
                user_item.is_equipped = True
                user_item.save(update_fields=['is_equipped'])

    @staticmethod
    def equip_item(*, user, item_id):
        try:
            user_item = UserAvatarItem.objects.select_related('item').get(user=user, item_id=item_id)
        except UserAvatarItem.DoesNotExist:
            raise AvatarItemNotOwned()

        UserAvatarItem.objects.filter(
            user=user,
            item__param_key=user_item.item.param_key,
            is_equipped=True,
        ).update(is_equipped=False)

        user_item.is_equipped = True
        user_item.save(update_fields=['is_equipped'])

    @staticmethod
    def unequip_item(*, user, item_id):
        UserAvatarItem.objects.filter(user=user, item_id=item_id).update(is_equipped=False)

    @staticmethod
    @transaction.atomic
    def unlock_item(*, user, item_id):
        item = AvatarItem.objects.get(pk=item_id)

        if UserAvatarItem.objects.filter(user=user, item=item).exists():
            return

        if item.price > 0:
            deducted = Userprofile.objects.filter(user=user, coins__gte=item.price).update(
                coins=F('coins') - item.price
            )
            if not deducted:
                raise InsufficientCoins()

        UserAvatarItem.objects.create(user=user, item=item)
