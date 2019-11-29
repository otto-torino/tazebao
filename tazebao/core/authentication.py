from rest_framework_jwt.authentication import JSONWebTokenAuthentication


class JSONWebTokenQuerystringAuthentication(JSONWebTokenAuthentication):
    """
    Clients could authenticate by passing the token key in the "querystring"
    bearer=eyJhbGciOiAiSFMyNTYiLCAidHlwIj
    """

    def get_jwt_value(self, request):
        auth = request.GET.get('bearer')

        if not auth:
            return None

        return auth
