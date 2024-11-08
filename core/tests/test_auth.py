from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from core.tests.factories.user_factory import UserFactory


class LogoutViewTest(APITestCase):
    def setUp(self):
        self.user = UserFactory()

        self.client = APIClient()
        self.url = reverse('logout')
        self.client.force_authenticate(user=self.user)

        self.refresh = RefreshToken.for_user(self.user)
        self.client.cookies['refresh_token'] = str(self.refresh)
        self.client.cookies['refresh_token'].httponly = True

        self.user.spotify_access_token = 'spotify-test-access'
        self.user.spotify_refresh_token = 'spotify-test-refresh'
        self.user.save()

    def test_logout_success(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'Successfully logged out')

        # Check that refresh token was blacklisted
        self.assertTrue(
            BlacklistedToken.objects.filter(
                token__token=str(self.refresh)
            ).exists()
        )

        # Check that Spotify tokens were cleared
        self.user.refresh_from_db()
        self.assertIsNone(self.user.spotify_access_token)
        self.assertIsNone(self.user.spotify_refresh_token)

        # Check that JWT Refresh token was cleared
        refresh_cookie = response.cookies.get('refresh_token')
        self.assertIsNotNone(refresh_cookie)
        self.assertEqual(refresh_cookie.value, '')
        self.assertTrue(refresh_cookie['httponly'])

    def test_logout_without_refresh_token_cookie(self):
        self.client.cookies.pop('refresh_token', None)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Refresh token not provided.")
