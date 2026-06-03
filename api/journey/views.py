from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Journey, JourneyStepProgress
from .serializers import JourneySerializer, JourneyStepProgressSerializer
from .services import JourneyService


class JourneyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            journey = JourneyService.get_journey(request.user)
        except Journey.DoesNotExist:
            return Response({'detail': 'Journey not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(JourneySerializer(journey).data)


class JourneyStepProgressStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, progress_id):
        try:
            progress = JourneyService.start_progress(request.user, progress_id)
        except JourneyStepProgress.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(JourneyStepProgressSerializer(progress).data)


class JourneyStepProgressCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, progress_id):
        try:
            journey = JourneyService.complete_progress(
                request.user,
                progress_id,
                request.data.get('response_data'),
            )
        except JourneyStepProgress.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(JourneySerializer(journey).data)
