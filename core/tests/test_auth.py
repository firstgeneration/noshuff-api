from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from core.tests.factories.user_factory import UserFactory
from unittest.mock import patch, MagicMock
from urllib.parse import parse_qs, urlparse
from core.models import User


class SpotifyCallbackViewTests(APITestCase):
    def setUp(self):
        self.callback_url = reverse('spotify_post_auth_callback')

        # Sample Spotify user data
        self.spotify_user_data = {
            'id': 'spotify_test_id',
            'display_name': 'Test User',
            'email': 'test@example.com',
            'images': [{'url': 'https://example.com/avatar.jpg'}],
            'country': 'US',
            'followers': {'total': 42},
            'href': 'https://api.spotify.com/v1/users/test',
            'product': 'premium',
            'uri': 'spotify:user:test'
        }

        # Sample token data
        self.token_data = {
            'access_token': 'spotify_test_access_token',
            'refresh_token': 'spotify_test_refresh_token',
            'expires_in': 3600
        }

    @patch('core.views.SpotifyOAuth')
    @patch('core.views.Spotify')
    def test_successful_callback_new_user(self, mock_spotify, mock_spotify_oauth):
        """Test successful callback flow for a new user"""
        # Configure mocks
        mock_oauth_instance = MagicMock()
        mock_oauth_instance.get_access_token.return_value = self.token_data
        mock_spotify_oauth.return_value = mock_oauth_instance

        mock_spotify_instance = MagicMock()
        mock_spotify_instance.current_user.return_value = self.spotify_user_data
        mock_spotify.return_value = mock_spotify_instance

        # Make request
        response = self.client.get(f'{self.callback_url}?code=test_code')

        # Assert response
        self.assertEqual(response.status_code, 302)

        # Verify user creation
        user = User.objects.get(spotify_id='spotify_test_id')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.spotify_display_name, 'Test User')

        # Verify cookie
        self.assertIn('refresh_token', response.cookies)
        refresh_cookie = response.cookies['refresh_token']
        self.assertTrue(refresh_cookie['httponly'])
        self.assertTrue(refresh_cookie['secure'])
        self.assertEqual(refresh_cookie['samesite'], 'Strict')

        # Verify redirect and access token
        redirect_url = urlparse(response.url)
        query_params = parse_qs(redirect_url.query)
        self.assertIn('access_token', query_params)

        # Verify the access token is valid
        access_token = query_params['access_token'][0]
        self.assertTrue(len(access_token) > 0)

    @patch('core.views.SpotifyOAuth')
    @patch('core.views.Spotify')
    def test_successful_callback_existing_user(self, mock_spotify, mock_spotify_oauth):
        """Test successful callback flow for an existing user"""
        # Create existing user
        existing_user = User.objects.create(
            spotify_id='spotify_test_id',
            email='old@example.com',
            spotify_display_name='Old Name'
        )

        # Configure mocks
        mock_oauth_instance = MagicMock()
        mock_oauth_instance.get_access_token.return_value = self.token_data
        mock_spotify_oauth.return_value = mock_oauth_instance

        mock_spotify_instance = MagicMock()
        mock_spotify_instance.current_user.return_value = self.spotify_user_data
        mock_spotify.return_value = mock_spotify_instance

        # Make request
        response = self.client.get(f'{self.callback_url}?code=test_code')

        # Assert response
        self.assertEqual(response.status_code, 302)

        # Verify user update
        updated_user = User.objects.get(spotify_id='spotify_test_id')
        self.assertEqual(updated_user.id, existing_user.id)  # Same user
        self.assertEqual(updated_user.email, 'test@example.com')  # Updated email
        self.assertEqual(updated_user.spotify_display_name, 'Test User')  # Updated name

    @patch('core.views.SpotifyOAuth')
    def test_invalid_code(self, mock_spotify_oauth):
        """Test callback with invalid authorization code"""
        mock_oauth_instance = MagicMock()
        mock_oauth_instance.get_access_token.side_effect = Exception('Invalid code')
        mock_spotify_oauth.return_value = mock_oauth_instance

        response = self.client.get(f'{self.callback_url}?code=invalid_code')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.count(), 0)

    def test_missing_code(self):
        """Test callback without authorization code"""
        response = self.client.get(self.callback_url)
        self.assertEqual(response.status_code, 400)


class LogoutViewTest(APITestCase):
    def setUp(self):
        self.user = UserFactory()

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
