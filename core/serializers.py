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
