from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from rest_framework_simplejwt.tokens import RefreshToken
from .exceptions import AvatarItemNotOwned, EmailAlreadyExists, InvalidCredentials
from .models import AvatarItem, User, UserAvatarItem, Userprofile


class UserService:
    @staticmethod
    def register(*, email, password):
        if User.objects.filter(email=email).exists():
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
        JourneyService.sync_with_profile(user=user)

        return {
            'user': user,
        }


class AvatarService:
    @staticmethod
    def update_avatar_url(*, user, avatar_url: str) -> None:
        Userprofile.objects.filter(user=user).update(avatar_url=avatar_url)

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
    def unlock_item(*, user, item_id):
        item = AvatarItem.objects.get(pk=item_id)
        UserAvatarItem.objects.get_or_create(user=user, item=item)
