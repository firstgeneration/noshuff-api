from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from spotipy.exceptions import SpotifyException

User = get_user_model()

@patch('spotipy.Spotify')
class SpotifyPlaylistAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create(
            spotify_id='test_user_id',
            email='test@example.com',
            spotify_access_token='test_access_token'
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse('spotify_user_playlists')

        # First page of results
        self.user_playlists_response_page_1 = {
            "href": "https://api.spotify.com/v1/users/spotify_spain/playlists",
            "items": [{
                "collaborative": False,
                "description": "First page playlist",
                "external_urls": {
                    "spotify": "http://open.spotify.com/user/spotify_spain/playlist/2oCEWyyAPbZp9xhVSxZavx"
                },
                "href": "https://api.spotify.com/v1/users/spotify_spain/playlists/2oCEWyyAPbZp9xhVSxZavx",
                "id": "2oCEWyyAPbZp9xhVSxZavx",
                "images": [{
                    "height": 640,
                    "url": "https://mosaic.scdn.co/640/page1-image",
                    "width": 640
                }],
                "name": "First Test Playlist",
                "owner": {
                    "display_name": "Spotify Spain",
                    "external_urls": {
                        "spotify": "http://open.spotify.com/user/spotify_spain"
                    },
                    "href": "https://api.spotify.com/v1/users/spotify_spain",
                    "id": "test_user_id",
                    "type": "user",
                    "uri": "spotify:user:spotify_spain"
                },
                "tracks": {
                    "href": "https://api.spotify.com/v1/users/spotify_spain/playlists/2oCEWyyAPbZp9xhVSxZavx/tracks",
                    "total": 5
                },
            }],
            "limit": 50,
            "next": "https://api.spotify.com/v1/users/spotify_spain/playlists?offset=50",
            "offset": 0,
            "previous": None,
            "total": 75
        }

        # Second page of results
        self.user_playlists_response_page_2 = {
            "href": "https://api.spotify.com/v1/users/spotify_spain/playlists",
            "items": [{
                "collaborative": False,
                "description": "Second page playlist",
                "external_urls": {
                    "spotify": "http://open.spotify.com/user/spotify_spain/playlist/3oCEWyyAPbZp9xhVSxZavx"
                },
                "href": "https://api.spotify.com/v1/users/spotify_spain/playlists/3oCEWyyAPbZp9xhVSxZavx",
                "id": "3oCEWyyAPbZp9xhVSxZavx",
                "images": [{
                    "height": 640,
                    "url": "https://mosaic.scdn.co/640/page2-image",
                    "width": 640
                }],
                "name": "Second Test Playlist",
                "owner": {
                    "display_name": "Spotify Spain",
                    "external_urls": {
                        "spotify": "http://open.spotify.com/user/spotify_spain"
                    },
                    "href": "https://api.spotify.com/v1/users/spotify_spain",
                    "id": "test_user_id",
                    "type": "user",
                    "uri": "spotify:user:spotify_spain"
                },
                "tracks": {
                    "href": "https://api.spotify.com/v1/users/spotify_spain/playlists/3oCEWyyAPbZp9xhVSxZavx/tracks",
                    "total": 10
                },
            }],
            "limit": 50,
            "next": None,
            "offset": 50,
            "previous": "https://api.spotify.com/v1/users/spotify_spain/playlists?offset=0",
            "total": 75
        }

    def test_successful_single_page(self, mock_spotify):
        """Test successful retrieval of a single page of playlists"""
        # Modify first page response to have no next page
        single_page_response = self.user_playlists_response_page_1.copy()
        single_page_response['next'] = None
        
        mock_instance = MagicMock()
        mock_instance.current_user_playlists.return_value = single_page_response
        mock_spotify.return_value = mock_instance

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        playlist = response.data[0]
        self.assertEqual(playlist['id'], '2oCEWyyAPbZp9xhVSxZavx')
        self.assertEqual(playlist['name'], 'First Test Playlist')
        self.assertEqual(playlist['description'], 'First page playlist')
        self.assertEqual(playlist['image_url'], 'https://mosaic.scdn.co/640/page1-image')
        self.assertEqual(playlist['track_count'], 5)

    def test_playlist_pagination(self, mock_spotify):
        """Test retrieval of multiple pages of playlists"""
        mock_instance = MagicMock()
        
        def mock_current_user_playlists(limit=50, offset=0):
            if offset == 0:
                return self.user_playlists_response_page_1
            elif offset == 50:
                return self.user_playlists_response_page_2
            else:
                raise Exception(f"Unexpected offset: {offset}")
                
        mock_instance.current_user_playlists.side_effect = mock_current_user_playlists
        mock_spotify.return_value = mock_instance

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        playlist_ids = [playlist['id'] for playlist in response.data]
        self.assertIn('2oCEWyyAPbZp9xhVSxZavx', playlist_ids)
        self.assertIn('3oCEWyyAPbZp9xhVSxZavx', playlist_ids)
        
        mock_instance.current_user_playlists.assert_any_call(limit=50, offset=0)
        mock_instance.current_user_playlists.assert_any_call(limit=50, offset=50)
        
        self.assertEqual(mock_instance.current_user_playlists.call_count, 2)

    def test_playlist_filtering(self, mock_spotify):
        """Test filtering of collaborative and non-owned playlists"""
        mixed_playlists_response = self.user_playlists_response_page_1.copy()
        mixed_playlists_response['items'] = [
            # User's own playlist (should be included)
            self.user_playlists_response_page_1['items'][0],
            # Collaborative playlist (should be filtered out)
            {
                **self.user_playlists_response_page_1['items'][0],
                'id': 'collaborative_playlist',
                'collaborative': True,
                'name': 'Collaborative Playlist'
            },
            # Other user's playlist (should be filtered out)
            {
                **self.user_playlists_response_page_1['items'][0],
                'id': 'other_user_playlist',
                'name': 'Other User Playlist',
                'owner': {
                    'id': 'other_user_id',
                    'display_name': 'Other User'
                }
            }
        ]
        mixed_playlists_response['next'] = None

        mock_instance = MagicMock()
        mock_instance.current_user_playlists.return_value = mixed_playlists_response
        mock_spotify.return_value = mock_instance

        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], '2oCEWyyAPbZp9xhVSxZavx')

    def test_missing_images(self, mock_spotify):
        """Test handling of playlists with no images"""
        no_images_response = self.user_playlists_response_page_1.copy()
        no_images_response['items'][0]['images'] = []
        no_images_response['next'] = None
        
        mock_instance = MagicMock()
        mock_instance.current_user_playlists.return_value = no_images_response
        mock_spotify.return_value = mock_instance

        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIsNone(response.data[0]['image_url'])

    def test_spotify_error(self, mock_spotify):
        """Test handling of Spotify API errors"""
        mock_instance = MagicMock()
        mock_instance.current_user_playlists.side_effect = SpotifyException(
            http_status=401,
            code=-1,
            msg="Invalid access token",
            reason="The access token expired"
        )
        mock_spotify.return_value = mock_instance

        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_authentication_required(self, mock_spotify):
        """Test that the endpoint requires authentication"""
        client = APIClient()
        response = client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
