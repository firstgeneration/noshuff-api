from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse
from spotipy import Spotify, SpotifyOAuth
from django.conf import settings
from django.urls import reverse
import requests
import json
from core.models import User
from core.spotipy_utils import (
    get_noshuff_user_fields,
    get_spotify_user_playlists,
    get_spotify_playlist,
)
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from urllib.parse import urlencode
from core.serializers import (
    UserSerializer,
    SpotifyPlaylistSummarySerializer,
    SpotifyPlaylistDetailSerializer,
)
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.pagination import PageNumberPagination


@api_view(['GET'])
def spotify_pre_auth(request):
    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIPY_CLIENT_ID,
        client_secret=settings.SPOTIPY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIPY_REDIRECT_URI,
        scope=settings.SPOTIPY_SCOPE
    )
    auth_url = sp_oauth.get_authorize_url()

    return redirect(auth_url)

@api_view(['GET'])
def spotify_post_auth_callback(request):
    sp_oauth = SpotifyOAuth(
        client_id=settings.SPOTIPY_CLIENT_ID,
        client_secret=settings.SPOTIPY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIPY_REDIRECT_URI,
        scope=settings.SPOTIFY_SCOPE
    )
    try:
        token_data = sp_oauth.get_access_token(request.GET['code'])
    except:
        return Response(
            {'detail': 'Invalid token'},
            status=status.HTTP_400_BAD_REQUEST
        )

    sp = Spotify(auth=token_data["access_token"])
    spotify_user = sp.current_user()
    noshuff_user_fields = get_noshuff_user_fields(spotify_user, token_data)
    noshuff_user, _ = User.objects.update_or_create(
        spotify_id=noshuff_user_fields['spotify_id'],
        defaults=noshuff_user_fields
    )

    noshuff_refresh_token = RefreshToken.for_user(noshuff_user)
    noshuff_access_token = str(noshuff_refresh_token.access_token)

    params = urlencode({'access_token': noshuff_access_token})

    # TODO: Use settings.NOSHUFF_FE_REDIRECT_URI when FE is ready
    redirect_url = f"{reverse("frontend_placeholder_redirect")}?{params}"

    response = HttpResponseRedirect(redirect_url)
    response.set_cookie(
        key='refresh_token',
        value=noshuff_refresh_token,
        httponly=True,
        secure=True,
        samesite='Strict', # TODO: Adjust this when FE is ready
        max_age=86400 * 30
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    refresh_token = request.COOKIES.get('refresh_token')
    if not refresh_token:
        return Response(
            {'detail': 'Refresh token not provided.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except TokenError:
        return Response(
            {'detail': 'Invalid token'},
            status=status.HTTP_400_BAD_REQUEST
        )

    request.user.spotify_access_token = None
    request.user.spotify_refresh_token = None
    request.user.save()

    response = Response(
        {'detail': 'Successfully logged out'},
        status=status.HTTP_200_OK
    )
    response.set_cookie(
        'refresh_token',
        value='',
        max_age=0,
        path='/',
        httponly=True,
        secure=True,
        samesite='Lax'
    )

    return response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    serializer = UserSerializer(request.user)

    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def spotify_user_playlists_summary(request):
    current_user = request.user
    playlists = get_spotify_user_playlists(current_user)
    serializer = SpotifyPlaylistSummarySerializer(playlists, many=True)

    return Response(serializer.data)

class SpotifyPageNumberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def spotify_user_playlist_detail(request, spotify_playlist_id: str):
    try:
        spotify_client = request.user.get_spotify_client()

        paginator = SpotifyPageNumberPagination()

        try:
            page = int(request.query_params.get('page', 1))
            if page < 1:
                return Response(
                    {'error': 'Page number must be greater than 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {'error': 'Invalid page number'},
                status=status.HTTP_400_BAD_REQUEST
            )

        page_size = paginator.get_page_size(request)

        playlist_data = get_spotify_playlist(
            spotify_client,
            spotify_playlist_id,
            page=page,
            page_size=page_size
        )

        # Serialize the data
        serializer = SpotifyPlaylistDetailSerializer(playlist_data)
        
        # Construct paginated response manually
        return Response({
            'count': playlist_data['total_tracks'],
            'next': f'{request.build_absolute_uri()}?page={page + 1}&page_size={page_size}' 
                   if (page * page_size) < playlist_data['total_tracks'] else None,
            'previous': f'{request.build_absolute_uri()}?page={page - 1}&page_size={page_size}' 
                       if page > 1 else None,
            'results': serializer.data
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
