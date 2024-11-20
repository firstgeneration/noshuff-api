from django.utils import timezone
from datetime import timedelta
import spotipy
from spotipy.exceptions import SpotifyException
from typing import Dict, Any, List
from spotipy import Spotify


def get_avatar_url(images_list):
    try:
        avatar_url = images_list[0]['url']
    except:
        avatar_url = ''

    return avatar_url

def get_spotify_access_token_expires_at(token_data):
    return timezone.now() + timedelta(seconds=token_data['expires_in'])

def get_noshuff_user_fields(spotify_user, token_data):

    return {
        'spotify_id': spotify_user['id'],
        'spotify_display_name': spotify_user['display_name'],
        'email': spotify_user['email'],
        'spotify_avatar_url': get_avatar_url(spotify_user['images']),
        'spotify_country': spotify_user['country'],
        'spotify_follower_count': spotify_user['followers']['total'],
        'spotify_account_href': spotify_user['href'],
        'spotify_product': spotify_user['product'],
        'spotify_account_uri': spotify_user['uri'],
        'spotify_access_token': token_data["access_token"],
        'spotify_refresh_token': token_data["refresh_token"],
        'spotify_access_token_expires_at': get_spotify_access_token_expires_at(token_data),
    }

def get_spotify_user_playlists(
    user,
    only_owned_by_user=True,
    only_non_collaborative=True
):
    spotify = spotipy.Spotify(auth=user.spotify_access_token)
    playlists = []
    limit = 50
    offset = 0
    try:
        while True:
            playlists_data = spotify.current_user_playlists(limit=limit, offset=offset)
            items = playlists_data.get('items', [])

            for playlist in items:
                is_owned_by_user = playlist['owner']['id'] == user.spotify_id
                is_collaborative = playlist['collaborative']

                if only_owned_by_user and not is_owned_by_user:
                    continue
                if only_non_collaborative and is_collaborative:
                    continue

                playlists.append(playlist)

            if playlists_data['next'] is None:
                break

            offset += limit

        return playlists
    except SpotifyException as e:
        print(f"Error fetching playlists: {e}")
        return None


def get_spotify_playlist(
        spotify_client,
        playlist_id: str,
        page: int = 1,
        page_size: int = 20
    ):
    """
    Fetch a Spotify playlist's tracks with pagination, excluding podcast episodes.
    
    Args:
        spotify_client: Authenticated Spotipy client instance
        playlist_id (str): Spotify playlist ID
        page (int): Page number (1-based)
        page_size (int): Number of items per page
    
    Returns:
        tuple: (playlist_data, tracks_list) where playlist_data is the raw Spotipy response 
        and tracks_list is the list of track objects for the current page
    """
    # Calculate offset based on page number (convert to 0-based)
    offset = (page - 1) * page_size
    
    # Get full playlist data
    playlist_data = spotify_client.playlist(
        playlist_id,
        fields='id,name,description,images,owner.display_name,followers.total'
    )
    
    # Get tracks for the current page
    tracks_response = spotify_client.playlist_tracks(
        playlist_id,
        offset=offset,
        limit=page_size,
        additional_types=['track'],
        fields='items(track(id,name,duration_ms,album(name,images),artists(name))),total'
    )

    # Add total_tracks to playlist_data
    playlist_data['total_tracks'] = tracks_response['total']

    # Add tracks to playlist_data
    playlist_data['tracks'] = [
        item['track'] for item in tracks_response['items']
        if item.get('track')
    ]

    return playlist_data