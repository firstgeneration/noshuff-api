from django.utils import timezone
from datetime import timedelta

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
