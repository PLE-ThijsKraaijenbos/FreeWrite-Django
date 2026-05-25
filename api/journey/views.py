from django.db import transaction
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Journey, JourneyStepProgress
from .serializers import JourneySerializer, JourneyStepProgressSerializer
from .services import JourneyService


def _prefetched_journey(journey_id):
    return (
        Journey.objects
        .prefetch_related(
            'step_progresses__step__phase',
            'step_progresses__step__journal_content',
            'step_progresses__step__letter_content',
            'step_progresses__step__choice_story_content',
            'step_progresses__step__speech_bubble_content',
            'step_progresses__step__bubble_pop_content',
            'step_progresses__step__scale_content',
        )
        .get(id=journey_id)
    )


class JourneyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            journey = _prefetched_journey(request.user.journey.id)
        except Journey.DoesNotExist:
            return Response({'detail': 'Journey not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(JourneySerializer(journey).data)


class JourneyStepProgressStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, progress_id):
        with transaction.atomic():
            try:
                progress = JourneyStepProgress.objects.select_for_update().get(
                    id=progress_id, journey__user=request.user,
                )
            except JourneyStepProgress.DoesNotExist:
                return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

            if progress.status != JourneyStepProgress.Status.AVAILABLE:
                return Response(
                    {'detail': 'Step is not available to start.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            progress.status = JourneyStepProgress.Status.IN_PROGRESS
            progress.started_at = timezone.now()
            progress.save(update_fields=['status', 'started_at'])

        progress.refresh_from_db()
        return Response(JourneyStepProgressSerializer(progress).data)


class JourneyStepProgressCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, progress_id):
        with transaction.atomic():
            try:
                progress = JourneyStepProgress.objects.select_for_update().get(
                    id=progress_id, journey__user=request.user,
                )
            except JourneyStepProgress.DoesNotExist:
                return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

            if progress.status in (
                JourneyStepProgress.Status.COMPLETED,
                JourneyStepProgress.Status.UNAVAILABLE,
            ):
                return Response(
                    {'detail': 'Step cannot be completed.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            progress.status = JourneyStepProgress.Status.COMPLETED
            progress.completed_at = timezone.now()
            progress.response_data = request.data.get('response_data')
            progress.save(update_fields=['status', 'completed_at', 'response_data'])

            JourneyService.sync_with_profile(user=request.user)

            next_progress_id = (
                JourneyStepProgress.objects
                .filter(
                    journey_id=progress.journey_id,
                    status=JourneyStepProgress.Status.UNAVAILABLE,
                )
                .select_related('step__phase')
                .order_by('step__phase__order', 'step__order')
                .values_list('id', flat=True)
                .first()
            )
            if next_progress_id:
                JourneyStepProgress.objects.filter(id=next_progress_id).update(
                    status=JourneyStepProgress.Status.AVAILABLE,
                )

        return Response(JourneySerializer(_prefetched_journey(progress.journey_id)).data)
