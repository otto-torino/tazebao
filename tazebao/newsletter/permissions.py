from rest_framework import permissions


class IsClient(permissions.BasePermission):

    def __init__(self, field_name=None):
        self.field_name = field_name

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if(request.user.is_authenticated):
            if self.field_name:
                return request.user == getattr(obj, self.field_name).client.user
            else:
                return request.user == obj.client.user
        return False
