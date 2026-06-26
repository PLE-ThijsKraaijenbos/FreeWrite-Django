from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from drf_spectacular.types import OpenApiTypes
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Journey, JourneyStepProgress
from .serializers import (
    CompleteStepRequestSerializer,
    JourneySerializer,
    JourneyStepProgressSerializer,
)
from .services import JourneyService


_PROGRESS_ID_PARAM = OpenApiParameter(
    name='progress_id',
    location=OpenApiParameter.PATH,
    type=OpenApiTypes.UUID,
    description="ID of the step progress record, taken from the journey's `step_progresses`.",
)


class JourneyView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Journey'],
        summary="Get the user's journey",
        description=(
            "Returns the current user's whole journey: every step they have, each with its "
            "content and its progress (status, bookmark, timestamps, and any saved response). "
            "Steps are ordered by phase and then by step order, which is the order the app "
            "should show them in.\n\n"
            "A journey is created during onboarding, so a user who has not completed onboarding "
            "yet will not have one."
        ),
        responses={
            200: JourneySerializer,
            404: OpenApiResponse(
                description="This user has no journey yet, usually because onboarding is not done.",
                examples=[OpenApiExample("No journey", value={"detail": "Journey not found."})],
            ),
        },
    )
    def get(self, request):
        try:
            journey = JourneyService.get_journey(request.user)
        except Journey.DoesNotExist:
            return Response({'detail': 'Journey not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(JourneySerializer(journey).data)


class JourneyStepProgressStartView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Journey'],
        summary="Start a step",
        description=(
            "Moves a step from AVAILABLE to IN_PROGRESS and stamps its start time. Only a step "
            "that is currently AVAILABLE can be started. Returns the updated progress record."
        ),
        parameters=[_PROGRESS_ID_PARAM],
        request=None,
        responses={
            200: JourneyStepProgressSerializer,
            400: OpenApiResponse(
                description="The step is not in a state that can be started.",
                examples=[OpenApiExample("Not available", value={"detail": "Step is not available."})],
            ),
            404: OpenApiResponse(
                description="No such step progress for this user.",
                examples=[OpenApiExample("Not found", value={"detail": "Not found."})],
            ),
        },
    )
    def post(self, request, progress_id):
        try:
            progress = JourneyService.start_progress(request.user, progress_id)
        except JourneyStepProgress.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(JourneyStepProgressSerializer(progress).data)


class JourneyStepProgressCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Journey'],
        summary="Complete a step",
        description=(
            "Marks a step COMPLETED, stamps the completion time, and saves the user's "
            "`response_data`. Completing a step rewards the user with 50 coins and may unlock the "
            "next step in the journey.\n\n"
            "A step that is already completed or still unavailable cannot be completed. On success "
            "the whole refreshed journey is returned, so the client can see the reward and any "
            "newly unlocked step in one response."
        ),
        parameters=[_PROGRESS_ID_PARAM],
        request=CompleteStepRequestSerializer,
        responses={
            200: OpenApiResponse(response=JourneySerializer, description="Step completed. Returns the refreshed journey."),
            400: OpenApiResponse(
                description="The step is already completed or is not available.",
                examples=[
                    OpenApiExample("Already completed", value={"detail": "Step is already completed."}),
                    OpenApiExample("Not available", value={"detail": "Step is not available."}),
                ],
            ),
            404: OpenApiResponse(
                description="No such step progress for this user.",
                examples=[OpenApiExample("Not found", value={"detail": "Not found."})],
            ),
        },
    )
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


class JourneyBookmarkView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Journey'],
        summary="Toggle a bookmark",
        description=(
            "Flips the bookmark flag on a step. If it was bookmarked it becomes unbookmarked, and "
            "the other way around. Returns the updated progress record so the client can read the "
            "new flag."
        ),
        parameters=[_PROGRESS_ID_PARAM],
        request=None,
        responses={
            200: JourneyStepProgressSerializer,
            404: OpenApiResponse(
                description="No such step progress for this user.",
                examples=[OpenApiExample("Not found", value={"detail": "Not found."})],
            ),
        },
    )
    def patch(self, request, progress_id):
        try:
            progress = JourneyService.bookmark_step(request.user, progress_id)
        except JourneyStepProgress.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(JourneyStepProgressSerializer(progress).data)
