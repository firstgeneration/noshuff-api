from django.contrib import admin
from django.urls import path
from core import views
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.conf import settings


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Authentication
    path('api/v1/auth', views.spotify_pre_auth, name='spotify_pre_auth'),
    path('api/v1/post_auth', views.spotify_post_auth_callback, name='spotify_post_auth_callback'),
    # TODO: Remove this when frontend is built
    path(
        'frontend-placeholder-redirect',
        views.frontend_placeholder_redirect,
        name='frontend_placeholder_redirect'
    ),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/auth/logout/', views.logout_view, name='logout'),

    # Noshuff Resources
    path('api/v1/current_user', views.current_user, name='current_user'),

    # Spotify Resources
    path(
        'api/v1/spotify_user_playlists',
        views.spotify_user_playlists_summary,
        name='spotify_user_playlists_summary'
    ),
    path(
        'api/v1/spotify_user_playlists/<str:spotify_playlist_id>',
        views.spotify_user_playlist_detail,
        name='spotify-user-playlist-detail'
    ),
]

# OpenAPI
if settings.ENABLE_API_DOCS:
    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
        path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    ]
