from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from core.tests.factories.user_factory import UserFactory


class UserAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
    
    def test_get_current_user(self):
        current_user = UserFactory()

        self.client.force_authenticate(user=current_user)

        response = self.client.get(reverse('current_user'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

