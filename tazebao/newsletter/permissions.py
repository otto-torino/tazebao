from rest_framework import permissions


class IsClient(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if(request.user.is_authenticated):
            return request.user == obj.client.user
        return False
