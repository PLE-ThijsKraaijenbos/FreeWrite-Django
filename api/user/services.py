from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from rest_framework_simplejwt.tokens import RefreshToken
from .exceptions import EmailAlreadyExists, InvalidCredentials
from .models import User, Userprofile

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


def complete_profile(*, user, data):
    Userprofile.objects.create(user=user, **data)

    return {
        'user': user,
    }


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
