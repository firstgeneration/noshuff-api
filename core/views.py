from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse
from spotipy import Spotify, SpotifyOAuth
from django.conf import settings
from django.urls import reverse
import requests
import json
from .models import User
from .spotipy_utils import get_noshuff_user_fields
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from urllib.parse import urlencode
from core.serializers import UserSerializer


@api_view(['GET'])
def spotify_pre_auth(request):
    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIPY_CLIENT_ID,
        client_secret=settings.SPOTIPY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIPY_REDIRECT_URI,
        scope="user-library-read"
    )
    auth_url = sp_oauth.get_authorize_url()
    
    return redirect(auth_url)

@api_view(['GET'])
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

    noshuff_refresh_token = RefreshToken.for_user(noshuff_user)
    noshuff_access_token = str(noshuff_refresh_token.access_token)

    params = urlencode({'noshuff_access_token': noshuff_access_token})
    
    # TODO: Use settings.NOSHUFF_FE_REDIRECT_URI when FE is ready
    redirect_url = f"{reverse("frontend_placeholder_redirect")}?{params}"

    response = HttpResponseRedirect(redirect_url)
    response.set_cookie(
        key='noshuff_refresh_token',
        value=noshuff_refresh_token,
        httponly=True,
        secure=True,
        samesite='Strict' # TODO: Adjust this when FE is ready
    )

    return response

@api_view(['GET'])
def frontend_placeholder_redirect(request):
    noshuff_access_token = request.GET.get('noshuff_access_token', '')

    html = f"""
    <html>
    <head><title>Spotify User Profile</title></head>
    <body>
        <h1>Welcome to NoShuff</h1>
        <p>Auth token: {noshuff_access_token}</p>
    </body>
    </html>
    """

    return HttpResponse(html)

@api_view(['GET'])
def logout_view(request):
    refresh_token = request.COOKIES.get('refresh_token')

    if refresh_token is None:
        return Response(
            {"detail": "Refresh token not provided."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except Exception as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    response = Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
    response.delete_cookie(
        "noshuff_refresh_token",
        domain=settings.SESSION_COOKIE_DOMAIN,
        path="/"
    )

    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    serializer = UserSerializer(request.user)

    return Response(serializer.data)
