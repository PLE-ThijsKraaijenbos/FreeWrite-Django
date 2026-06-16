from rest_framework.exceptions import APIException
from rest_framework import status


class EmailAlreadyExists(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A user with this email already exists."


class InvalidCredentials(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Invalid email or password."


class ProfileAlreadyExists(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "This account has already completed onboarding."
    default_code = "profile_already_exists"


class AvatarItemNotOwned(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not own this avatar item."


class InsufficientCoins(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Not enough coins to purchase this item."
    default_code = "insufficient_coins"
