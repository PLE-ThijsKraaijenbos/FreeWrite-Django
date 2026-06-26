from django.db.models import Exists, OuterRef
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from drf_spectacular.types import OpenApiTypes
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView

from .models import AvatarItem, UserAvatarItem
from .serializers import (
    AuthResponseSerializer,
    AvatarItemSerializer,
    CompleteProfileRequestSerializer,
    LoginSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    UserSerializer,
)
from .services import AvatarService, UserService


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['User'],
        summary="Register a new account",
        description=(
            "Creates a fresh account from an email and password and signs the user in right "
            "away by returning a token pair. No profile exists yet at this point, so the next "
            "step for a new user is to complete onboarding through the complete-profile endpoint.\n\n"
            "The email is stored in lower case and must be unique."
        ),
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(
                response=AuthResponseSerializer,
                description="Account created. Returns the token pair and the new user.",
            ),
            400: OpenApiResponse(
                description="The email is already taken or the input failed validation.",
                examples=[
                    OpenApiExample(
                        "Email already exists",
                        value={"detail": "A user with this email already exists."},
                    ),
                    OpenApiExample(
                        "Password too short",
                        value={"password": ["Ensure this field has at least 8 characters."]},
                    ),
                ],
            ),
        },
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = UserService.register(**serializer.validated_data)
        return Response({
            'access': result['access'],
            'refresh': result['refresh'],
            'user': UserSerializer(result['user']).data,
        }, status=status.HTTP_201_CREATED)


class CompleteProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['User'],
        summary="Complete onboarding",
        description=(
            "Runs once per account, right after registration. It saves the onboarding answers "
            "as the user's profile, unlocks and equips the avatar items that match the chosen "
            "look, and builds the user's journey from the active steps.\n\n"
            "Because a profile can only be created once, calling this a second time fails with "
            "a conflict."
        ),
        request=CompleteProfileRequestSerializer,
        responses={
            201: OpenApiResponse(
                response=UserSerializer,
                description="Profile created. Returns the user with the freshly built profile.",
            ),
            409: OpenApiResponse(
                description="This account has already completed onboarding.",
                examples=[
                    OpenApiExample(
                        "Already onboarded",
                        value={"detail": "This account has already completed onboarding."},
                    ),
                ],
            ),
        },
    )
    def post(self, request):
        serializer = UserProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = UserService.complete_profile(
            user=request.user,
            data=serializer.validated_data,
            avatar=request.data.get('avatar') or {},
        )
        return Response(UserSerializer(result['user']).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['User'],
        summary="Log in",
        description=(
            "Checks the email and password and, when they match, returns a token pair and the "
            "user. The email is matched case insensitively."
        ),
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                response=AuthResponseSerializer,
                description="Logged in. Returns the token pair and the user.",
            ),
            401: OpenApiResponse(
                description="The email or password is wrong.",
                examples=[
                    OpenApiExample(
                        "Bad credentials",
                        value={"detail": "Invalid email or password."},
                    ),
                ],
            ),
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = UserService.login(**serializer.validated_data)
        return Response({
            'access': result['access'],
            'refresh': result['refresh'],
            'user': UserSerializer(result['user']).data,
        })


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['User'],
        summary="Get the current user",
        description="Returns the signed in user along with their profile. Use it to load the account on app start.",
        responses={200: UserSerializer},
    )
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(
        tags=['User'],
        summary="Update the display name",
        description="Updates the user's display name. This is the only profile field that can be changed after onboarding.",
        request=ProfileUpdateSerializer,
        responses={
            200: OpenApiResponse(response=UserSerializer, description="Name updated. Returns the full user."),
            400: OpenApiResponse(description="The name was empty or otherwise invalid."),
        },
    )
    def patch(self, request):
        serializer = ProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserService.update_profile(user=request.user, **serializer.validated_data)
        return Response(UserSerializer(user).data)


class AvatarItemListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['User'],
        summary="List avatar items",
        description=(
            "Returns the full catalog of avatar items. Each item is annotated for the current "
            "user with `is_unlocked` (do they own it) and `is_equipped` (are they wearing it), "
            "so the wardrobe screen can render the whole catalog in one call."
        ),
        responses={200: AvatarItemSerializer(many=True)},
    )
    def get(self, request):
        unlocked = UserAvatarItem.objects.filter(user=request.user, item=OuterRef('pk'))
        equipped = UserAvatarItem.objects.filter(user=request.user, item=OuterRef('pk'), is_equipped=True)
        items = AvatarItem.objects.annotate(
            is_unlocked=Exists(unlocked),
            is_equipped=Exists(equipped),
        )
        return Response(AvatarItemSerializer(items, many=True).data)


class AvatarItemUnlockView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['User'],
        summary="Unlock an avatar item",
        description=(
            "Unlocks (buys) the avatar item for the current user. If the item has a price, that "
            "many coins are deducted from the profile. If it is free, it is simply added.\n\n"
            "This is idempotent: unlocking an item the user already owns does nothing and still "
            "succeeds. Unlocking certain items also grants a sensible default dependent item, for "
            "example unlocking accessories also grants a default accessories color."
        ),
        parameters=[
            OpenApiParameter(
                name='item_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.UUID,
                description="ID of the avatar item to unlock.",
            ),
        ],
        request=None,
        responses={
            204: OpenApiResponse(description="Item unlocked, or already owned. No body."),
            400: OpenApiResponse(
                description="The user does not have enough coins to buy this item.",
                examples=[
                    OpenApiExample(
                        "Not enough coins",
                        value={"detail": "Not enough coins to purchase this item."},
                    ),
                ],
            ),
        },
    )
    def post(self, request, item_id):
        AvatarService.unlock_item(user=request.user, item_id=item_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AvatarItemEquipView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['User'],
        summary="Equip an avatar item",
        description=(
            "Equips an item the user owns. Any other item that shares the same parameter key is "
            "automatically unequipped first, so only one item per slot is ever worn at a time."
        ),
        parameters=[
            OpenApiParameter(
                name='item_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.UUID,
                description="ID of the avatar item to equip.",
            ),
        ],
        request=None,
        responses={
            204: OpenApiResponse(description="Item equipped. No body."),
            403: OpenApiResponse(
                description="The user does not own this item, so it cannot be equipped.",
                examples=[
                    OpenApiExample(
                        "Item not owned",
                        value={"detail": "You do not own this avatar item."},
                    ),
                ],
            ),
        },
    )
    def post(self, request, item_id):
        AvatarService.equip_item(user=request.user, item_id=item_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=['User'],
        summary="Unequip an avatar item",
        description=(
            "Unequips the item for the current user. This is safe to call even if the item is not "
            "currently equipped; it just makes sure the item ends up unequipped."
        ),
        parameters=[
            OpenApiParameter(
                name='item_id',
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.UUID,
                description="ID of the avatar item to unequip.",
            ),
        ],
        request=None,
        responses={204: OpenApiResponse(description="Item unequipped. No body.")},
    )
    def delete(self, request, item_id):
        AvatarService.unequip_item(user=request.user, item_id=item_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    tags=['User'],
    summary="Refresh the access token",
    description=(
        "Exchanges a valid refresh token for a new access token, so the user stays signed in "
        "without typing their password again. Send `{\"refresh\": \"<refresh token>\"}`. This "
        "endpoint is open and does not need an access token of its own."
    ),
)
class TokenRefreshView(BaseTokenRefreshView):
    """Thin wrapper over SimpleJWT's refresh view so it shows up under the User tag."""
    pass
