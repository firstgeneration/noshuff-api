import factory
from factory import Faker, LazyAttribute
from core.models import User

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = Faker('email')
    spotify_id = Faker('uuid4')
    spotify_display_name = Faker('name')
    spotify_avatar_url = Faker('image_url')
    spotify_access_token = Faker('sha256')
    spotify_access_token_expires_at = Faker('future_datetime')
    spotify_refresh_token = Faker('sha256')
    spotify_country = Faker('country_code')
    spotify_follower_count = Faker('random_int', min=0, max=10000)
    spotify_account_href = LazyAttribute(lambda obj: f'https://api.spotify.com/v1/users/{obj.spotify_id}'),
    spotify_account_uri = LazyAttribute(lambda obj: f'spotify:user:{obj.spotify_id}')
    spotify_product = Faker('random_element', elements=['free', 'premium', 'family'])
    personal_blurb = Faker('paragraph', nb_sentences=3)
