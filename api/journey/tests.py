from django.test import TestCase

from journey.exceptions import StepAlreadyCompleted, StepNotAvailable
from journey.models import Journey, JourneyStep, JourneyStepProgress, Phase
from journey.services import JourneyService
from user.models import User, Userprofile


class JourneyTestBase(TestCase):
    @staticmethod
    def make_user(email='test@example.com'):
        return User.objects.create_user(email=email, password='testpass123')

    @staticmethod
    def make_profile(user, **kwargs):
        defaults = {
            'substance': 'COCAINE',
            'usage_duration': '1-2Y',
            'goal': 'QUIT',
            'usage_times': 'AT_A_PARTY',
            'frequency': 'WEEKLY',
            'previous_attempts': 'NEVER',
        }
        defaults.update(kwargs)
        return Userprofile.objects.create(user=user, **defaults)

    @staticmethod
    def make_phase(order=1, title='Phase 1'):
        return Phase.objects.create(order=order, title=title)

    @staticmethod
    def make_step(phase=None, order=1, is_core=True, activation_rules=None):
        if phase is None:
            phase = Phase.objects.create(order=1, title='Phase 1')
        return JourneyStep.objects.create(
            phase=phase, order=order, title='Step 1',
            description='', banner_url='', assignment_type=JourneyStep.AssignmentType.JOURNAL,
            is_core=is_core, activation_rules=activation_rules,
        )


class SyncJourneyWithProfileTests(JourneyTestBase):
    def setUp(self):
        self.user = self.make_user()
        self.profile = self.make_profile(self.user)
        self.phase = self.make_phase()

    def test_creates_journey_if_not_exists(self):
        self.make_step(phase=self.phase)
        journey = JourneyService.sync_with_profile(user=self.user)
        self.assertEqual(journey.user, self.user)

    def test_returns_existing_journey(self):
        self.make_step(phase=self.phase)
        journey1 = JourneyService.sync_with_profile(user=self.user)
        journey2 = JourneyService.sync_with_profile(user=self.user)
        self.assertEqual(journey1.pk, journey2.pk)

    def test_core_steps_get_progress_record(self):
        self.make_step(phase=self.phase, is_core=True)
        journey = JourneyService.sync_with_profile(user=self.user)
        self.assertEqual(JourneyStepProgress.objects.filter(journey=journey).count(), 1)

    def test_core_steps_start_as_available(self):
        self.make_step(phase=self.phase, is_core=True)
        journey = JourneyService.sync_with_profile(user=self.user)
        progress = JourneyStepProgress.objects.get(journey=journey)
        self.assertEqual(progress.status, JourneyStepProgress.Status.AVAILABLE)

    def test_non_core_step_without_rules_is_excluded(self):
        self.make_step(phase=self.phase, is_core=False, activation_rules=None)
        journey = JourneyService.sync_with_profile(user=self.user)
        self.assertEqual(JourneyStepProgress.objects.filter(journey=journey).count(), 0)

    def test_non_core_step_with_matching_rule_is_included(self):
        rules = {'frequency': ['WEEKLY', 'DAILY']}
        self.make_step(phase=self.phase, is_core=False, activation_rules=rules)
        journey = JourneyService.sync_with_profile(user=self.user)
        self.assertEqual(JourneyStepProgress.objects.filter(journey=journey).count(), 1)

    def test_non_core_step_with_non_matching_rule_is_excluded(self):
        rules = {'frequency': 'DAILY'}
        self.make_step(phase=self.phase, is_core=False, activation_rules=rules)
        journey = JourneyService.sync_with_profile(user=self.user)
        self.assertEqual(JourneyStepProgress.objects.filter(journey=journey).count(), 0)

    def test_inactive_steps_are_excluded(self):
        step = self.make_step(phase=self.phase, is_core=True)
        step.is_active = False
        step.save()
        journey = JourneyService.sync_with_profile(user=self.user)
        self.assertEqual(JourneyStepProgress.objects.filter(journey=journey).count(), 0)

    def test_idempotent_does_not_duplicate_progress(self):
        self.make_step(phase=self.phase, is_core=True)
        JourneyService.sync_with_profile(user=self.user)
        JourneyService.sync_with_profile(user=self.user)
        self.assertEqual(JourneyStepProgress.objects.count(), 1)

    def test_reroll_adds_newly_added_steps(self):
        self.make_step(phase=self.phase, order=1, is_core=True)
        JourneyService.sync_with_profile(user=self.user)
        self.assertEqual(JourneyStepProgress.objects.count(), 1)

        self.make_step(phase=self.phase, order=2, is_core=True)
        JourneyService.sync_with_profile(user=self.user)
        self.assertEqual(JourneyStepProgress.objects.count(), 2)

    def test_reroll_preserves_existing_progress_status(self):
        step = self.make_step(phase=self.phase, is_core=True)
        journey = JourneyService.sync_with_profile(user=self.user)
        JourneyStepProgress.objects.filter(journey=journey, step=step).update(
            status=JourneyStepProgress.Status.COMPLETED
        )
        JourneyService.sync_with_profile(user=self.user)
        progress = JourneyStepProgress.objects.get(journey=journey, step=step)
        self.assertEqual(progress.status, JourneyStepProgress.Status.COMPLETED)

    def test_multiple_fields_all_must_match(self):
        rules = {'frequency': 'WEEKLY', 'goal': 'QUIT'}
        self.make_step(phase=self.phase, is_core=False, activation_rules=rules)
        journey = JourneyService.sync_with_profile(user=self.user)
        self.assertEqual(JourneyStepProgress.objects.filter(journey=journey).count(), 1)

    def test_multiple_fields_excluded_if_one_does_not_match(self):
        rules = {'frequency': 'WEEKLY', 'goal': 'USE_LESS'}
        self.make_step(phase=self.phase, is_core=False, activation_rules=rules)
        journey = JourneyService.sync_with_profile(user=self.user)
        self.assertEqual(JourneyStepProgress.objects.filter(journey=journey).count(), 0)


class StartProgressTests(JourneyTestBase):
    def setUp(self):
        self.user = self.make_user()
        self.profile = self.make_profile(self.user)
        phase = self.make_phase()
        step = self.make_step(phase=phase, is_core=True)
        JourneyService.sync_with_profile(user=self.user)
        self.progress = JourneyStepProgress.objects.get(journey__user=self.user, step=step)

    def test_transitions_to_in_progress(self):
        JourneyService.start_progress(self.user, self.progress.id)
        self.progress.refresh_from_db()
        self.assertEqual(self.progress.status, JourneyStepProgress.Status.IN_PROGRESS)

    def test_sets_started_at(self):
        self.assertIsNone(self.progress.started_at)
        JourneyService.start_progress(self.user, self.progress.id)
        self.progress.refresh_from_db()
        self.assertIsNotNone(self.progress.started_at)

    def test_returns_updated_progress(self):
        result = JourneyService.start_progress(self.user, self.progress.id)
        self.assertEqual(result.id, self.progress.id)
        self.assertEqual(result.status, JourneyStepProgress.Status.IN_PROGRESS)

    def test_raises_if_already_in_progress(self):
        JourneyService.start_progress(self.user, self.progress.id)
        with self.assertRaises(StepNotAvailable):
            JourneyService.start_progress(self.user, self.progress.id)

    def test_raises_if_unavailable(self):
        self.progress.status = JourneyStepProgress.Status.UNAVAILABLE
        self.progress.save()
        with self.assertRaises(StepNotAvailable):
            JourneyService.start_progress(self.user, self.progress.id)

    def test_raises_if_completed(self):
        self.progress.status = JourneyStepProgress.Status.COMPLETED
        self.progress.save()
        with self.assertRaises(StepNotAvailable):
            JourneyService.start_progress(self.user, self.progress.id)

    def test_raises_if_progress_belongs_to_other_user(self):
        other_user = self.make_user(email='other@example.com')
        self.make_profile(other_user)
        with self.assertRaises(JourneyStepProgress.DoesNotExist):
            JourneyService.start_progress(other_user, self.progress.id)


class CompleteProgressTests(JourneyTestBase):
    def setUp(self):
        self.user = self.make_user()
        self.profile = self.make_profile(self.user)
        self.phase = self.make_phase()
        self.step = self.make_step(phase=self.phase, order=1, is_core=True)
        JourneyService.sync_with_profile(user=self.user)
        self.progress = JourneyStepProgress.objects.get(journey__user=self.user, step=self.step)

    def test_transitions_to_completed(self):
        JourneyService.complete_progress(self.user, self.progress.id, response_data=None)
        self.progress.refresh_from_db()
        self.assertEqual(self.progress.status, JourneyStepProgress.Status.COMPLETED)

    def test_sets_completed_at(self):
        self.assertIsNone(self.progress.completed_at)
        JourneyService.complete_progress(self.user, self.progress.id, response_data=None)
        self.progress.refresh_from_db()
        self.assertIsNotNone(self.progress.completed_at)

    def test_stores_response_data(self):
        response_data = {'rating': 4, 'notes': 'good'}
        JourneyService.complete_progress(self.user, self.progress.id, response_data=response_data)
        self.progress.refresh_from_db()
        self.assertEqual(self.progress.response_data, response_data)

    def test_awards_coins(self):
        initial_coins = self.profile.coins
        JourneyService.complete_progress(self.user, self.progress.id, response_data=None)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.coins, initial_coins + 50)

    def test_activates_next_unavailable_step(self):
        step2 = self.make_step(phase=self.phase, order=2, is_core=True)
        JourneyService.sync_with_profile(user=self.user)
        step2_progress = JourneyStepProgress.objects.get(journey__user=self.user, step=step2)
        self.assertEqual(step2_progress.status, JourneyStepProgress.Status.UNAVAILABLE)

        JourneyService.complete_progress(self.user, self.progress.id, response_data=None)

        step2_progress.refresh_from_db()
        self.assertEqual(step2_progress.status, JourneyStepProgress.Status.AVAILABLE)

    def test_returns_journey(self):
        result = JourneyService.complete_progress(self.user, self.progress.id, response_data=None)
        self.assertIsInstance(result, Journey)

    def test_raises_if_already_completed(self):
        self.progress.status = JourneyStepProgress.Status.COMPLETED
        self.progress.save()
        with self.assertRaises(StepAlreadyCompleted):
            JourneyService.complete_progress(self.user, self.progress.id, response_data=None)

    def test_raises_if_unavailable(self):
        self.progress.status = JourneyStepProgress.Status.UNAVAILABLE
        self.progress.save()
        with self.assertRaises(StepNotAvailable):
            JourneyService.complete_progress(self.user, self.progress.id, response_data=None)

    def test_raises_if_progress_belongs_to_other_user(self):
        other_user = self.make_user(email='other@example.com')
        self.make_profile(other_user)
        with self.assertRaises(JourneyStepProgress.DoesNotExist):
            JourneyService.complete_progress(other_user, self.progress.id, response_data=None)

    def test_does_not_award_coins_on_failure(self):
        self.progress.status = JourneyStepProgress.Status.COMPLETED
        self.progress.save()
        initial_coins = self.profile.coins
        with self.assertRaises(StepAlreadyCompleted):
            JourneyService.complete_progress(self.user, self.progress.id, response_data=None)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.coins, initial_coins)
