from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView


class WhoAmI(APIView):
    """
    Ask for who am I
    """
    permission_classes = (permissions.AllowAny, )

    def get(self, request):
        if not request.user.is_authenticated:
            response = {}
        else:
            response = {
                'userId': request.user.id,
                'userName': request.user.username,
                'userEmail': request.user.email,
                'isSuperUser': request.user.is_superuser
            }
        return Response(response)
