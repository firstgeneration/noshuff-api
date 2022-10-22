from django.shortcuts import redirect
from core.authentication.spotify_auth_utils import generate_spotify_auth_url, UserTokenCache
from spotipy.oauth2 import SpotifyOAuth
from django.conf import settings
from core.models import User


def pre_auth(request):
    return redirect(generate_spotify_auth_url())

def post_auth(request):
    code_data = request.GET

    error = code_data.get('error')
    if error:
        return redirect(f'{settings.NOSHUFF_FE_REDIRECT_URI}?error={error}')

    code = code_data['code']

    auth_handler = SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_SECRET_KEY,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        state=None, # Does this even matter?
        scope='user-read-private user-read-email',
        cache_path=None,
        username=None,
        proxies=None,
        show_dialog=False,
        requests_session=False,
        requests_timeout=None,
        open_browser=False,
        cache_handler=UserTokenCache()
    )

    token_info = auth_handler.get_access_token(code=code, as_dict=True, check_cache=False)
    user = User.objects.get(spotify_access_token=token_info['access_token'])

    breakpoint()

    # Create a noshuff auth token for this user

    # Redirect to Frontend here with a data payload
    # to store noshuff_token and other relevant info
