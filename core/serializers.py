from core.models import User
from rest_framework import serializers
from typing import Dict, Any, List

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'uuid',
            'spotify_id',
            'spotify_display_name',
            'spotify_avatar_url',
            'personal_blurb',
            # 'post_count',
            # 'followers_count',
            # 'following_count',
        ]
        read_only_fields = [
            'uuid',
            'spotify_id',
            'spotify_display_name',
            'spotify_avatar_url',
        ]

class SpotifyPlaylistSummarySerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    image_url = serializers.SerializerMethodField()
    track_count = serializers.IntegerField(source="tracks.total")

    def get_image_url(self, playlist):
        # Get the first image URL if available
        images = playlist.get("images", [])
        return images[0]["url"] if images else None


class SpotifyTrackSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    duration_ms = serializers.IntegerField()
    artists = serializers.SerializerMethodField()
    album = serializers.CharField(source='album.name')
    album_image_url = serializers.SerializerMethodField()

    def get_artists(self, obj):
        return [artist['name'] for artist in obj['artists']]
    
    def get_album_image_url(self, obj):
        images = obj['album']['images']
        return images[0]['url'] if images else None


class SpotifyPlaylistDetailSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    followers = serializers.IntegerField(source='followers.total')
    total_tracks = serializers.IntegerField()
    image_url = serializers.SerializerMethodField()
    tracks = SpotifyTrackSerializer(many=True)

    def get_image_url(self, obj):
        images = obj.get('images', [])
        return images[0]['url'] if images else None
