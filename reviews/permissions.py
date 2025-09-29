from datetime import timedelta
from django.utils import timezone
from rest_framework import permissions


class IsOwnerOrAdminWithTimeWindow(permissions.BasePermission):
    EDIT_WINDOW = timedelta(minutes=15)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        if not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        if obj.user_id == user.id:
            return False
        return timezone.now() <= (obj.create_at + self.EDIT_WINDOW)
