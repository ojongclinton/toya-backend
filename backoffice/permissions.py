from rest_framework.permissions import BasePermission

from .models import BackofficeAdmin


class IsBackofficeAdmin(BasePermission):
    """Allow access only to active users backed by a back-office admin row."""

    message = "Only an authenticated back-office administrator may perform this action."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated or not user.is_active:
            return False

        return BackofficeAdmin.objects.filter(pk=user.pk, user_type="admin").exists()
