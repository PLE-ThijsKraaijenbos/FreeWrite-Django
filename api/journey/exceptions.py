from rest_framework.exceptions import APIException
from rest_framework import status


class StepNotAvailable(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Step is not available.'
    default_code = 'step_not_available'


class StepAlreadyCompleted(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Step is already completed.'
    default_code = 'step_already_completed'
