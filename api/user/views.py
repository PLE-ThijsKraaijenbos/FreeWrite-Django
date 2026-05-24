from django.db.models import Exists, OuterRef
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import AvatarItem, UserAvatarItem
from .serializers import AvatarItemSerializer, LoginSerializer, RegisterSerializer, UserProfileSerializer, UserSerializer
from .services import AvatarService, UserService


class RegisterView(APIView):
    permission_classes = [AllowAny]

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

    def post(self, request):
        serializer = UserProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = UserService.complete_profile(user=request.user, data=serializer.validated_data)
        return Response(UserSerializer(result['user']).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = UserService.login(**serializer.validated_data)
        return Response({
            'access': result['access'],
            'refresh': result['refresh'],
            'user': UserSerializer(result['user']).data,
        })


class AvatarItemListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        unlocked = UserAvatarItem.objects.filter(user=request.user, item=OuterRef('pk'))
        equipped = UserAvatarItem.objects.filter(user=request.user, item=OuterRef('pk'), is_equipped=True)
        items = AvatarItem.objects.annotate(
            is_unlocked=Exists(unlocked),
            is_equipped=Exists(equipped),
        )
        return Response(AvatarItemSerializer(items, many=True).data)


class AvatarItemEquipView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, item_id):
        AvatarService.equip_item(user=request.user, item_id=item_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request, item_id):
        AvatarService.unequip_item(user=request.user, item_id=item_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


