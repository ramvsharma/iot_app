from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions

from user.exceptions import MissingTokenException
from user.jwt_utils import decode_jwt_token
from user.models import CustomUser


class JsonTokenAuthentication(authentication.BaseAuthentication):
    PUBLIC_URLS = [
        '/auth/login/',
    ]

    def authenticate(self, request):
        if request.path in self.PUBLIC_URLS:
            return None
        api_token = request.META.get('HTTP_TOKEN')
        if not api_token:
            raise exceptions.AuthenticationFailed('missing token')
        user_data = decode_jwt_token(api_token)
        if user_data is None:
            raise exceptions.AuthenticationFailed('Invalid token')

        user = CustomUser.objects.get(user_id=user_data['user_id'])
        return user, api_token
