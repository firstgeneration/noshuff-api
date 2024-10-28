from core.models import User
from rest_framework import serializers

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

class PlaylistSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    image_url = serializers.SerializerMethodField()
    track_count = serializers.IntegerField(source="tracks.total")

    def get_image_url(self, playlist):
        # Get the first image URL if available
        images = playlist.get("images", [])
        return images[0]["url"] if images else None
