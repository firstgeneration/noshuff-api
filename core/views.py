from django.shortcuts import render, redirect
from spotipy import Spotify, SpotifyOAuth
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponse
import requests
import json
from .models import User
from .spotipy_utils import get_noshuff_user_fields


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
    token_data = sp_oauth.get_access_token(request.GET['code'])
    sp = Spotify(auth=token_data["access_token"])
    spotify_user = sp.current_user()

    noshuff_user_fields = get_noshuff_user_fields(spotify_user, token_data)
    noshuff_user = User.objects.filter(
        spotify_id=noshuff_user_fields['spotify_id']
    ).first()

    if not noshuff_user:
        noshuff_user = User.objects.create(**noshuff_user_fields)
    else:
        for field, val in noshuff_user_fields.items():
            setattr(noshuff_user, field, val)
        noshuff_user.save()

    query_params = "token=token"
    # response_data = {'noshuff_access_token': generate_noshuff_access_token()}
    # query_params = urllib.parse.urlencode(response_data, doseq=False)

    return redirect(f'{reverse("frontend_placeholder_redirect")}?{query_params}')
    # return redirect(settings.NOSHUFF_FE_REDIRECT_URI + '?' + query_params)

# TODO: Remove this when frontend is built
def frontend_placeholder_redirect(request):
    token = request.GET.get('token', '')

    html = f"""
    <html>
    <head><title>Spotify User Profile</title></head>
    <body>
        <h1>Welcome to NoShuff</h1>
        <p>Auth token: {token}</p>
    </body>
    </html>
    """

    return HttpResponse(html)

