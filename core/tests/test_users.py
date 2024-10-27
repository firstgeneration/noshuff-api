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

        fields = {
            'uuid',
            'spotify_id',
            'spotify_display_name',
            'spotify_avatar_url',
            'personal_blurb',
        }

        response_json = response.json()
        self.assertEqual(fields, set(response_json.keys()))

        for field in fields:
            model_value = getattr(current_user, field)
            if field == 'uuid':
                model_value = str(model_value)

            self.assertEqual(
                model_value, response_json[field]
            )

