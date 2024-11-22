import unittest
from unittest.mock import Mock
import requests
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from core.spotipy_utils import get_spotify_playlist

class SpotifyClientCredentialsMock(SpotifyClientCredentials):
    def __init__(self, client_id=None, client_secret=None, proxies=None, requests_timeout=None):
        super().__init__(
            client_id=client_id or 'mock_client_id',
            client_secret=client_secret or 'mock_client_secret',
            proxies=proxies,
            requests_timeout=requests_timeout
        )
        self.token_info = {'access_token': 'mock_access_token'}
        self._session = requests.Session()

    def get_access_token(self, as_dict=True):
        return self.token_info if as_dict else self.token_info['access_token']

class TestSpotifyClient(Spotify):
    def __init__(self):
        super().__init__(client_credentials_manager=SpotifyClientCredentialsMock())

class TestGetSpotifyPlaylist(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.spotify_client = TestSpotifyClient()
        
        # Mock playlist response
        self.mock_playlist_response = {
            "id": "test_playlist_id",
            "name": "Test Playlist",
            "description": "Test Description",
            "images": [
                {
                    "height": 640,
                    "url": "https://example.com/playlist.jpg",
                    "width": 640
                }
            ],
            "owner": {
                "display_name": "Test User"
            },
            "followers": {
                "total": 100
            }
        }

        # Mock tracks response
        self.mock_tracks_response = {
            "items": [
                {
                    "track": {
                        "id": "track1",
                        "name": "Track 1",
                        "duration_ms": 180000,
                        "album": {
                            "name": "Album 1",
                            "images": [
                                {
                                    "height": 640,
                                    "url": "https://example.com/album1.jpg",
                                    "width": 640
                                }
                            ]
                        },
                        "artists": [
                            {"name": "Artist 1"},
                            {"name": "Artist 2"}
                        ]
                    }
                }
            ],
            "total": 50
        }

    def test_basic_playlist_fetch(self):
        """Test basic playlist fetch with default pagination"""
        # Setup mocks
        self.spotify_client.playlist = Mock(return_value=self.mock_playlist_response)
        self.spotify_client.playlist_tracks = Mock(return_value=self.mock_tracks_response)
        
        # Call function
        result = get_spotify_playlist(self.spotify_client, 'test_playlist_id')
        
        # Verify correct API calls
        self.spotify_client.playlist.assert_called_once_with(
            'test_playlist_id',
            fields='id,name,description,images,owner.display_name,followers.total'
        )
        
        self.spotify_client.playlist_tracks.assert_called_once_with(
            'test_playlist_id',
            offset=0,
            limit=20,
            additional_types=['track'],
            fields='items(track(id,name,duration_ms,album(name,images),artists(name))),total'
        )
        
        # Verify playlist data
        self.assertEqual(result['id'], 'test_playlist_id')
        self.assertEqual(result['name'], 'Test Playlist')
        self.assertEqual(result['description'], 'Test Description')
        self.assertEqual(result['total_tracks'], 50)
        
        # Verify track data
        self.assertEqual(len(result['tracks']), 1)
        track = result['tracks'][0]
        self.assertEqual(track['id'], 'track1')
        self.assertEqual(track['name'], 'Track 1')
        self.assertEqual(track['duration_ms'], 180000)
        self.assertEqual(track['album']['name'], 'Album 1')
        self.assertEqual(track['album']['images'][0]['url'], 'https://example.com/album1.jpg')
        self.assertEqual(track['artists'], [
            {"name": "Artist 1"},
            {"name": "Artist 2"}
        ])

    def test_empty_playlist(self):
        """Test handling of empty playlist"""
        self.spotify_client.playlist = Mock(return_value=self.mock_playlist_response)
        empty_response = {"items": [], "total": 0}
        self.spotify_client.playlist_tracks = Mock(return_value=empty_response)
        
        result = get_spotify_playlist(self.spotify_client, 'test_playlist_id')
        
        self.assertEqual(result['total_tracks'], 0)
        self.assertEqual(len(result['tracks']), 0)

    def test_missing_images(self):
        """Test handling of missing images in response"""
        self.spotify_client.playlist = Mock(return_value=self.mock_playlist_response)
        
        # Modify tracks response to have no images
        no_images_response = {
            "items": [
                {
                    "track": {
                        "id": "track1",
                        "name": "Track 1",
                        "duration_ms": 180000,
                        "album": {
                            "name": "Album 1",
                            "images": []
                        },
                        "artists": [{"name": "Artist 1"}]
                    }
                }
            ],
            "total": 1
        }
        self.spotify_client.playlist_tracks = Mock(return_value=no_images_response)
        
        result = get_spotify_playlist(self.spotify_client, 'test_playlist_id')
        
        track = result['tracks'][0]
        self.assertEqual(track['album']['images'], [])
        self.assertEqual(track['artists'], [{"name": "Artist 1"}])

    def test_pagination(self):
        """Test playlist fetch with custom pagination"""
        self.spotify_client.playlist = Mock(return_value=self.mock_playlist_response)
        self.spotify_client.playlist_tracks = Mock(return_value=self.mock_tracks_response)
        
        # Test second page with 10 items per page
        result = get_spotify_playlist(self.spotify_client, 'test_playlist_id', page=2, page_size=10)
        
        # Verify correct offset calculation
        self.spotify_client.playlist_tracks.assert_called_once_with(
            'test_playlist_id',
            offset=10,  # (page-1) * page_size
            limit=10,
            additional_types=['track'],
            fields='items(track(id,name,duration_ms,album(name,images),artists(name))),total'
        )
        
        self.assertEqual(result['total_tracks'], 50)