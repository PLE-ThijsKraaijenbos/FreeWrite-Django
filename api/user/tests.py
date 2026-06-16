from django.test import TestCase

from .exceptions import ProfileAlreadyExists
from .models import User, Userprofile
from .services import UserService


class CompleteProfileGuardTests(TestCase):
    def test_second_completion_raises_conflict(self):
        user = User.objects.create_user(email='a@b.com', password='password123')
        Userprofile.objects.create(user=user, name='Existing')

        # The guard runs before any writes, so this raises without touching the
        # journey/avatar side effects.
        with self.assertRaises(ProfileAlreadyExists):
            UserService.complete_profile(user=user, data={'name': 'Again'}, avatar={})

        self.assertEqual(Userprofile.objects.filter(user=user).count(), 1)
        user.refresh_from_db()
        self.assertEqual(user.profile.name, 'Existing')
