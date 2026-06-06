from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwner(BasePermission):
    """Allow access only when the object's created_by matches the request user."""

    message = "You do not have permission to access this object."

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(obj, "created_by_id", None) == request.user.pk


class IsActive(BasePermission):
    """Deny access to users whose is_active flag is False."""

    message = "Your account has been deactivated."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
        )


class IsAdminOrReadOnly(BasePermission):
    """Grant full access to admin (is_staff) users; read-only for everyone else."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)
