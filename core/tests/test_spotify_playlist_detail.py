from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch, ANY
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class SpotifyUserPlaylistDetailTests(APITestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create(
            email='test@example.com',
            spotify_id='test_spotify_id',
            spotify_display_name='Test User',
            spotify_access_token='test_access_token',
            spotify_access_token_expires_at=timezone.now() + timedelta(hours=1),
            spotify_refresh_token='test_refresh_token'
        )
        
        self.playlist_id = 'playlist123'
        self.url = reverse('spotify-user-playlist-detail', kwargs={'spotify_playlist_id': self.playlist_id})
        
        # Mock Spotify API response data
        self.mock_playlist_data = {
            'id': self.playlist_id,
            'name': 'Test Playlist',
            'description': 'A test playlist',
            'images': [{'url': 'http://example.com/image.jpg'}],
            'owner': {'display_name': 'Test User'},
            'followers': {'total': 100},
            'total_tracks': 50,
            'tracks': [
                {
                    'id': 'track1',
                    'name': 'Test Track',
                    'duration_ms': 300000,
                    'album': {
                        'name': 'Test Album',
                        'images': [{'url': 'http://example.com/album.jpg'}]
                    },
                    'artists': [{'name': 'Test Artist'}]
                }
            ]
        }

    def test_authentication_required(self):
        """Test that authentication is required to access the endpoint"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('core.views.get_spotify_playlist')
    def test_successful_playlist_fetch(self, mock_get_spotify_playlist):
        """Test successful playlist fetch with valid authentication and data"""
        # Setup mock
        mock_get_spotify_playlist.return_value = self.mock_playlist_data

        # Authenticate user
        self.client.force_authenticate(user=self.user)

        # Make request
        response = self.client.get(self.url)

        # Use ANY for the Spotify client argument
        mock_get_spotify_playlist.assert_called_once_with(
            ANY,  # This replaces the specific Spotify client instance
            self.playlist_id,
            page=1,
            page_size=20
        )

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results']['id'], self.playlist_id)
        self.assertEqual(response.data['results']['name'], 'Test Playlist')
        self.assertEqual(response.data['count'], 50)
        self.assertEqual(len(response.data['results']['tracks']), 1)
        
        # Check pagination links
        self.assertIn('page=2', response.data['next'])
        self.assertIsNone(response.data['previous'])

        # Verify track data
        track = response.data['results']['tracks'][0]
        self.assertEqual(track['name'], 'Test Track')
        self.assertEqual(track['artists'], ['Test Artist'])
        self.assertEqual(track['album'], 'Test Album')
        self.assertEqual(track['album_image_url'], 'http://example.com/album.jpg')


    @patch('core.views.get_spotify_playlist')
    def test_pagination(self, mock_get_spotify_playlist):
        """Test pagination parameters and response structure"""
        # Setup mock
        mock_get_spotify_playlist.return_value = self.mock_playlist_data

        # Authenticate user
        self.client.force_authenticate(user=self.user)

        # Test with custom page size
        response = self.client.get(f'{self.url}?page=2&page_size=10')

        # Verify get_spotify_playlist was called with correct pagination parameters
        mock_get_spotify_playlist.assert_called_once_with(
            ANY,  # Use ANY instead of the specific Spotify client instance
            self.playlist_id,
            page=2,
            page_size=10
        )

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('page=3', response.data['next'])
        self.assertIn('page=1', response.data['previous'])
        self.assertIn('page_size=10', response.data['next'])

    def test_invalid_page_number(self):
        """Test handling of invalid page number"""
        # Authenticate user
        self.client.force_authenticate(user=self.user)

        # Test with invalid page parameter
        response = self.client.get(f'{self.url}?page=invalid')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Invalid page number')

    @patch('core.views.get_spotify_playlist')
    def test_spotify_client_error(self, mock_get_spotify_playlist):
        """Test handling of Spotify API errors"""
        # Setup mock to raise an exception
        mock_get_spotify_playlist.side_effect = Exception('Spotify API Error')

        # Authenticate user
        self.client.force_authenticate(user=self.user)

        # Make request
        response = self.client.get(self.url)

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['error'], 'Spotify API Error')

    @patch('core.views.get_spotify_playlist')
    def test_max_page_size_limit(self, mock_get_spotify_playlist):
        """Test that page size is limited to max_page_size"""
        # Setup mock
        mock_get_spotify_playlist.return_value = self.mock_playlist_data

        # Authenticate user
        self.client.force_authenticate(user=self.user)

        # Test with page size larger than max_page_size
        response = self.client.get(f'{self.url}?page_size=200')

        # Verify get_spotify_playlist was called with limited page size
        mock_get_spotify_playlist.assert_called_once_with(
            ANY,  # Use ANY instead of the specific Spotify client instance
            self.playlist_id,
            page=1,
            page_size=100  # Should be limited to max_page_size
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('core.views.get_spotify_playlist')
    def test_empty_playlist(self, mock_get_spotify_playlist):
        """Test handling of an empty playlist"""
        # Modify mock data for empty playlist
        empty_playlist = self.mock_playlist_data.copy()
        empty_playlist['tracks'] = []
        empty_playlist['total_tracks'] = 0
        mock_get_spotify_playlist.return_value = empty_playlist

        # Authenticate user
        self.client.force_authenticate(user=self.user)

        # Make request
        response = self.client.get(self.url)

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(len(response.data['results']['tracks']), 0)
        self.assertIsNone(response.data['next'])
        self.assertIsNone(response.data['previous'])

    @patch('core.views.get_spotify_playlist')
    def test_last_page_pagination(self, mock_get_spotify_playlist):
        """Test pagination when requesting the last page"""
        # Setup mock data with known number of tracks
        last_page_data = self.mock_playlist_data.copy()
        last_page_data['total_tracks'] = 25  # Total tracks
        mock_get_spotify_playlist.return_value = last_page_data

        # Authenticate user
        self.client.force_authenticate(user=self.user)

        # Request the last page (assuming page_size=20, last page would be 2)
        response = self.client.get(f'{self.url}?page=2&page_size=20')

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['next'])  # No next page
        self.assertIn('page=1', response.data['previous'])  # Previous page exists

    @patch('core.views.get_spotify_playlist')
    def test_zero_page_number(self, mock_get_spotify_playlist):
        """Test handling of zero page number"""
        # Authenticate user
        self.client.force_authenticate(user=self.user)

        # Test with page=0
        response = self.client.get(f'{self.url}?page=0')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Page number must be greater than 0')
