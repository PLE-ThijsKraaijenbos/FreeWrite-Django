from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.db import transaction
from django.db.models import F
from rest_framework_simplejwt.tokens import RefreshToken
from .exceptions import AvatarItemNotOwned, EmailAlreadyExists, InsufficientCoins, InvalidCredentials, ProfileAlreadyExists
from .models import AvatarItem, User, UserAvatarItem, Userprofile

# `top` values that are head coverings rather than hair (mirror of the frontend
# HAT_TOPS in src/lib/avatar.ts) — DiceBear lumps hats and hair under `top`.
HAT_TOPS = {'hat', 'hijab', 'turban', 'winterHat1', 'winterHat02', 'winterHat03', 'winterHat04'}

# Default dependent-param values, granted free the first time their parent item is
# unlocked. Mirror of the DEPENDENT_RULES defaults in src/lib/avatar.ts.
DEFAULT_ACCESSORIES_COLOR = '262e33'
DEFAULT_CLOTHING_GRAPHIC = 'skullOutline'
DEFAULT_HAT_COLOR = '262e33'
DEFAULT_HAIR_COLOR = '4a312c'


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
    @transaction.atomic
    def complete_profile(*, user, data, avatar):
        from journey.services import JourneyService
        if Userprofile.objects.filter(user=user).exists():
            raise ProfileAlreadyExists()

        Userprofile.objects.create(user=user, **data)
        AvatarService.grant_default_items(user=user, avatar=avatar)
        JourneyService.sync_with_profile(user=user)

        return {
            'user': user,
        }

    @staticmethod
    def update_profile(*, user, name):
        profile = user.profile
        profile.name = name
        profile.save(update_fields=['name'])
        return user


class AvatarService:
    @staticmethod
    def _grant(*, user, item, equip):
        """Own `item` (idempotent); when `equip`, make it the equipped one of its key."""
        user_item, _ = UserAvatarItem.objects.get_or_create(user=user, item=item)
        if equip and not user_item.is_equipped:
            UserAvatarItem.objects.filter(
                user=user, item__param_key=item.param_key, is_equipped=True
            ).exclude(pk=user_item.pk).update(is_equipped=False)
            user_item.is_equipped = True
            user_item.save(update_fields=['is_equipped'])
        return user_item

    @staticmethod
    @transaction.atomic
    def grant_default_items(*, user, avatar: dict) -> None:
        """Equip the items described by the chosen onboarding avatar params.

        `avatar` is a {param_key: param_value} map; matching AvatarItems are
        unlocked + equipped for free. Derived `*Probability` keys are skipped.
        """
        for param_key, param_value in (avatar or {}).items():
            if param_key.endswith('Probability'):
                continue
            item = AvatarItem.objects.filter(param_key=param_key, param_value=param_value).first()
            if item is not None:
                AvatarService._grant(user=user, item=item, equip=True)

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
        AvatarService._grant_dependent(user=user, item=item)

    @staticmethod
    def _current_hair_color(user) -> str:
        ua = UserAvatarItem.objects.select_related('item').filter(
            user=user, item__param_key='hairColor', is_equipped=True
        ).first()
        return ua.item.param_value if ua else DEFAULT_HAIR_COLOR

    @staticmethod
    def _dependent_for(user, item):
        # The default dependent param to grant when `item` is first unlocked, or
        # (None, None) when it has none. Mirrors DEPENDENT_RULES in src/lib/avatar.ts.
        key, value = item.param_key, item.param_value
        if key == 'accessories':
            return 'accessoriesColor', DEFAULT_ACCESSORIES_COLOR
        if key == 'clothing' and value == 'graphicShirt':
            return 'clothingGraphic', DEFAULT_CLOTHING_GRAPHIC
        if key == 'facialHair':
            return 'facialHairColor', AvatarService._current_hair_color(user)
        if key == 'top' and value in HAT_TOPS:
            return 'hatColor', DEFAULT_HAT_COLOR
        return None, None

    @staticmethod
    def _grant_dependent(*, user, item):
        dep_key, dep_value = AvatarService._dependent_for(user, item)
        if dep_key is None:
            return
        # First time only — never override a value the user already owns.
        if UserAvatarItem.objects.filter(user=user, item__param_key=dep_key).exists():
            return
        dependent = AvatarItem.objects.filter(param_key=dep_key, param_value=dep_value).first()
        if dependent is None:
            return  # row not seeded — skip silently
        AvatarService._grant(user=user, item=dependent, equip=True)
