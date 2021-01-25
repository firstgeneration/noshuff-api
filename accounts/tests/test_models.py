from django.test import TestCase
from accounts.models import User

class UserModelTest(TestCase):
    def test_user_create(self):
        """User records can be created"""
        User.objects.create(id='abcdefghij')
        user = User.objects.get(id='abcdefghij')
        self.assertEqual(user.id, 'abcdefghij')
