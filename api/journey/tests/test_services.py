from django.test import TestCase

from journey.models import Journey, JourneyStepProgress, Phase, JourneyStep
from journey.exceptions import JourneyAlreadyExists, StepAlreadyCompleted
from journey.services import create_journey, complete_journey_step, toggle_bookmark
from user.models import User


def make_user(email='test@example.com'):
    return User.objects.create_user(email=email, password='testpass123')


def make_step(phase=None, order=1, is_core=True):
    if phase is None:
        phase = Phase.objects.create(order=1, title='Phase 1')
    return JourneyStep.objects.create(
        phase=phase, order=order, title='Step 1',
        description='', banner_url='', assignment_type='journal', is_core=is_core,
    )


class CreateJourneyTests(TestCase):
    def setUp(self):
        self.user = make_user()
        make_step()

    def test_creates_journey_and_step_progress(self):
        journey = create_journey(user=self.user)
        self.assertEqual(journey.user, self.user)
        self.assertEqual(JourneyStepProgress.objects.filter(journey=journey).count(), 1)

    def test_core_steps_start_as_available(self):
        journey = create_journey(user=self.user)
        progress = JourneyStepProgress.objects.get(journey=journey)
        self.assertEqual(progress.status, JourneyStepProgress.Status.AVAILABLE)

    def test_non_core_steps_start_as_unavailable(self):
        phase = Phase.objects.create(order=2, title='Phase 2')
        make_step(phase=phase, order=2, is_core=False)
        journey = create_journey(user=self.user)
        non_core = JourneyStepProgress.objects.filter(
            journey=journey, status=JourneyStepProgress.Status.UNAVAILABLE
        )
        self.assertEqual(non_core.count(), 1)

    def test_raises_if_journey_already_exists(self):
        create_journey(user=self.user)
        with self.assertRaises(JourneyAlreadyExists):
            create_journey(user=self.user)


class CompleteJourneyStepTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.step = make_step()
        self.journey = Journey.objects.create(user=self.user)
        self.progress = JourneyStepProgress.objects.create(
            journey=self.journey,
            step=self.step,
            status=JourneyStepProgress.Status.AVAILABLE,
        )

    def test_marks_step_completed(self):
        progress = complete_journey_step(journey=self.journey, step=self.step)
        self.assertEqual(progress.status, JourneyStepProgress.Status.COMPLETED)
        self.assertIsNotNone(progress.completed_at)

    def test_saves_response_data(self):
        data = {'answer': 'some journal text'}
        progress = complete_journey_step(journey=self.journey, step=self.step, response_data=data)
        self.assertEqual(progress.response_data, data)

    def test_raises_if_already_completed(self):
        complete_journey_step(journey=self.journey, step=self.step)
        with self.assertRaises(StepAlreadyCompleted):
            complete_journey_step(journey=self.journey, step=self.step)


class ToggleBookmarkTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.step = make_step()
        self.journey = Journey.objects.create(user=self.user)
        JourneyStepProgress.objects.create(journey=self.journey, step=self.step)

    def test_sets_bookmark(self):
        progress = toggle_bookmark(journey=self.journey, step=self.step)
        self.assertTrue(progress.bookmarked)

    def test_unsets_bookmark(self):
        toggle_bookmark(journey=self.journey, step=self.step)
        progress = toggle_bookmark(journey=self.journey, step=self.step)
        self.assertFalse(progress.bookmarked)
