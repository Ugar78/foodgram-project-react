from rest_framework import permissions


class IsAuthorOrAdmin(permissions.IsAuthenticatedOrReadOnly):
    """Права доступа администратор, автор."""
    message = 'Доступ запрещен!'

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_superuser
            or obj.author == request.user
        )
