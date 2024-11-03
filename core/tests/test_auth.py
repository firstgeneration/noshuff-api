from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from core.tests.factories.user_factory import UserFactory
from django.http import SimpleCookie

class LogoutViewTest(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('logout')        
        self.refresh = RefreshToken.for_user(self.user)
        self.client.cookies = SimpleCookie()
        self.client.cookies['noshuff_refresh_token'] = str(self.refresh)
        self.client.cookies['noshuff_refresh_token']['httponly'] = True

    def test_successful_logout(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertTrue(BlacklistedToken.objects.filter(
            token__token=str(self.refresh)
        ).exists())

        refresh_cookie = response.cookies.get('noshuff_refresh_token')
        self.assertIsNotNone(refresh_cookie)
        self.assertEqual(refresh_cookie.value, '')
        self.assertTrue(refresh_cookie['httponly'])

    def test_logout_without_refresh_token_cookie(self):
        self.client.cookies.pop('noshuff_refresh_token', None)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Refresh token not provided.")
