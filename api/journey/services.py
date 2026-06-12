from django.db import transaction
from django.db.models import F
from django.utils import timezone

from user.models import Userprofile
from .models import Journey, JourneyStep, JourneyStepProgress
from .exceptions import StepAlreadyCompleted, StepNotAvailable

class JourneyService:
    @staticmethod
    def get_journey(user):
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
            .get(user=user)
        )

    @staticmethod
    @transaction.atomic
    def start_progress(user, progress_id):
        progress = (
            JourneyStepProgress.objects
            .select_for_update()
            .get(id=progress_id, journey__user=user)
        )

        if progress.status != JourneyStepProgress.Status.AVAILABLE:
            raise StepNotAvailable

        progress.status = JourneyStepProgress.Status.IN_PROGRESS
        progress.started_at = timezone.now()
        progress.save(update_fields=['status', 'started_at'])

        progress.refresh_from_db()
        return progress

    @staticmethod
    @transaction.atomic
    def complete_progress(user, progress_id, response_data):
        progress = (
            JourneyStepProgress.objects
            .select_for_update()
            .get(id=progress_id, journey__user=user)
        )

        if progress.status == JourneyStepProgress.Status.COMPLETED:
            raise StepAlreadyCompleted
        if progress.status == JourneyStepProgress.Status.UNAVAILABLE:
            raise StepNotAvailable

        progress.status = JourneyStepProgress.Status.COMPLETED
        progress.completed_at = timezone.now()
        progress.response_data = response_data
        progress.save(update_fields=['status', 'completed_at', 'response_data'])

        coin_reward_amount = 50

        Userprofile.objects.filter(user=user).update(coins=F('coins') + coin_reward_amount)

        JourneyService.sync_with_profile(user=user)

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

        return JourneyService.get_journey(user)

    @staticmethod
    def _evaluate_activation_rules(rules, profile):
        """
        Checks if a Userprofile matches all activation_rules.

        Rule format: flat dictionary of field: value (or list of values).
        All fields must match (AND). A list value means "any of".

        Examples:
            {"frequency": "WEEKLY"}
            {"frequency": ["WEEKLY", "DAILY"], "goal": "QUIT"}
        """
        if not rules:
            return False

        for field, value in rules.items():
            profile_value = getattr(profile, field, None)
            if isinstance(value, list):
                if profile_value not in value:
                    return False
            else:
                if profile_value != value:
                    return False

        return True

    @staticmethod
    def sync_with_profile(*, user):
        journey, _ = Journey.objects.get_or_create(user=user)
        profile = user.profile

        existing_step_ids = set(
            JourneyStepProgress.objects.filter(journey=journey).values_list('step_id', flat=True)
        )

        steps = JourneyStep.objects.filter(is_active=True).select_related('phase').order_by('phase__order', 'order')

        steps_to_add = []
        for step in steps:
            if step.id in existing_step_ids:
                continue
            if step.is_core or JourneyService._evaluate_activation_rules(step.activation_rules, profile):
                steps_to_add.append(step)

        if not steps_to_add:
            return journey

        has_active = JourneyStepProgress.objects.filter(
            journey=journey,
            status__in=[JourneyStepProgress.Status.AVAILABLE, JourneyStepProgress.Status.IN_PROGRESS],
        ).exists()

        to_create = []
        for i, step in enumerate(steps_to_add):
            status = (
                JourneyStepProgress.Status.AVAILABLE
                if i == 0 and not has_active
                else JourneyStepProgress.Status.UNAVAILABLE
            )
            to_create.append(JourneyStepProgress(journey=journey, step=step, status=status))

        JourneyStepProgress.objects.bulk_create(to_create)

        return journey

    @staticmethod
    @transaction.atomic
    def bookmark_step(user, progress_id):
        progress = (
            JourneyStepProgress.objects
            .select_for_update()
            .get(id=progress_id, journey__user=user)
        )
        progress.bookmarked = not progress.bookmarked
        progress.save(update_fields=['bookmarked'])
        return progress