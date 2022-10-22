from django.urls import path
from core.authentication import views as auth_views
# from core.post import views as post_views

urlpatterns = [
    path('api/v1/pre_auth', auth_views.pre_auth, name='pre_auth'),
    path('api/v1/post_auth', auth_views.post_auth, name='post_auth'),
    # path('playlists', post_views.get_current_user_unposted_playlists, name='playlists')
]
