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

        to_create = []
        for step in steps:
            if step.id in existing_step_ids:
                continue

            if step.is_core or JourneyService._evaluate_activation_rules(step.activation_rules, profile):
                to_create.append(JourneyStepProgress(
                    journey=journey,
                    step=step,
                    status=JourneyStepProgress.Status.AVAILABLE,
                ))

        JourneyStepProgress.objects.bulk_create(to_create)

        return journey