from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenObtainSlidingSerializer
from rest_framework_simplejwt.views import TokenObtainSlidingView, TokenRefreshSlidingView


class JSONWebTokenQuerystringAuthentication(JWTAuthentication):
    """
    Clients could authenticate by passing the token key in the "querystring"
    bearer=eyJhbGciOiAiSFMyNTYiLCAidHlwIj
    """

    def authenticate(self, request):
        raw_token = request.GET.get('bearer')
        if not raw_token:
            return None
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token


class TokenObtainSerializer(TokenObtainSlidingSerializer):
    """Keeps the username and email claims that django-rest-framework-jwt put in the payload."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.get_username()
        token['email'] = user.email
        return token


class LegacyErrorsMixin:
    """django-rest-framework-jwt answered 400 {"non_field_errors": [...]} on bad credentials
    or invalid tokens; the web and desktop apps rely on it."""

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except (exceptions.AuthenticationFailed, InvalidToken, TokenError) as e:
            detail = getattr(e, 'detail', None)
            if isinstance(detail, dict):
                detail = detail.get('detail', str(e))
            return Response({'non_field_errors': [str(detail or e)]}, status=status.HTTP_400_BAD_REQUEST)


class ObtainTokenView(LegacyErrorsMixin, TokenObtainSlidingView):
    serializer_class = TokenObtainSerializer


class RefreshTokenView(LegacyErrorsMixin, TokenRefreshSlidingView):
    pass
