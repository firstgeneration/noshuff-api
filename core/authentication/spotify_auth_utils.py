import urllib
from django.conf import settings
from random import Random
import spotipy
from core.models import User


def generate_spotify_auth_url():
    state = int(Random().random() * 10000000000000000)
    scope = 'user-read-private user-read-email'
    url = 'https://accounts.spotify.com/authorize?'
    data = {'client_id': settings.SPOTIFY_CLIENT_ID,
            'redirect_uri': settings.SPOTIFY_REDIRECT_URI,
            'response_type': 'code',
            'scope': scope,
            'state': state}
    query_params = urllib.parse.urlencode(data, doseq=False)

    return url + query_params

class UserTokenCache(spotipy.CacheHandler):

    def get_cached_token(self):
        current_user = None # Fill me in
        token_info = {
            'expires_at': current_user.expires_at,
            'access_token': current_user.access_token,
            'expires_in': current_user.expires_in,
            'scope': current_user.scope,
            'refresh_token': current_user.refresh_token,
        }

        return token_info

    def save_token_to_cache(self, token_info):
        spotify_access_token = token_info['access_token']
        spotify_scope = token_info['scope']
        spotify_access_token_expires_in = token_info['expires_in']
        spotify_refresh_token = token_info['refresh_token']

        sp = spotipy.Spotify(
            auth=spotify_access_token,
            requests_session=True,
            client_credentials_manager=None,
            oauth_manager=None,
            auth_manager=None,
            proxies=None,
            requests_timeout=5,
            status_forcelist=None,
            retries=3,
            status_retries=3,
            backoff_factor=0.3,
            language=None
        )

        spotify_user_data = sp.current_user()

        spotify_id = spotify_user_data.get('id')
        spotify_email = spotify_user_data.get('email')
        spotify_display_name = spotify_user_data.get('display_name')

        try:
            spotify_avatar_url = spotify_user_data['images'][0]['url']
        except:
            spotify_avatar_url = ''

        noshuff_user = User.objects.filter(spotify_id=spotify_id).first()
        # Check for inactive so no db failure
        if not noshuff_user:
            noshuff_user = User.objects.create(
                spotify_id=spotify_id,
                spotify_access_token=spotify_access_token,
                spotify_refresh_token=spotify_refresh_token,
                spotify_display_name=spotify_display_name,
                spotify_email=spotify_email,
                spotify_avatar_url=spotify_avatar_url)
        else:
            changed = False
            user_data = {
                'spotify_access_token': spotify_access_token,
                'spotify_refresh_token': spotify_refresh_token,
                'spotify_display_name': spotify_display_name,
                'spotify_email': spotify_email,
                'spotify_avatar_url': spotify_avatar_url,
                'spotify_scope': spotify_scope,
            }

            for attr, val in user_data.items():
                if getattr(noshuff_user, attr) != val:
                    changed = True
                    setattr(noshuff_user, attr, val)

            if changed:
                noshuff_user.save()

        return None
