from django.contrib import admin
from django.urls import path
from core import views

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
]
