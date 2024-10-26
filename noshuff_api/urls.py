from django.contrib import admin
from django.urls import path
from core import views
from rest_framework_simplejwt.views import TokenRefreshView

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
]
