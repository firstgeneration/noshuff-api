from django.shortcuts import render, redirect
from spotipy import Spotify, SpotifyOAuth
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponse


def spotify_pre_auth(request):
    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIPY_CLIENT_ID,
        client_secret=settings.SPOTIPY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIPY_REDIRECT_URI,
        scope="user-library-read"
    )

    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

def spotify_post_auth_callback(request):
    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIPY_CLIENT_ID,
        client_secret=settings.SPOTIPY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIPY_REDIRECT_URI,
    )

    code = request.GET.get('code')
    token_info = sp_oauth.get_access_token(code)

    print('token_info', token_info)

    return redirect(reverse("frontend_placeholder_redirect"))

# TODO: Remove this when frontend is built
def frontend_placeholder_redirect(request):
    html = f"""
    <html>
    <head><title>Spotify User Profile</title></head>
    <body>
        <h1>Welcome to NoShuff</h1>
    </body>
    </html>
    """

    return HttpResponse(html)
