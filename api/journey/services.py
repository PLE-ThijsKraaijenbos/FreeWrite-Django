from .models import Journey, JourneyStep, JourneyStepProgress


class JourneyService:
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