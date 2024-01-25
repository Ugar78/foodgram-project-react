from rest_framework import permissions


# class IsAdmin(permissions.BasePermission):
#     """Права доступа администратор."""
#     def has_permission(self, request, view):
#         return (
#             request.user.is_authenticated
#             and request.user.is_admin
#         )


class IsAuthorOrAdmin(permissions.IsAuthenticatedOrReadOnly):
    """Права доступа администратор, модератор, автор."""
    # def has_permission(self, request, view):
    #     return (
    #         request.user.is_authenticated
    #         or request.method in permissions.SAFE_METHODS
    #     )
    message = 'Доступ запрещен!'

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_superuser
            or obj.author == request.user
        )


# class IsAdminOrReadOnly(permissions.BasePermission):
#     """Права доступа на изменения администратор."""
#     def has_permission(self, request, view):
#         return (
#             request.method in permissions.SAFE_METHODS
#             or request.user.is_authenticated
#             and request.user.is_admin
#         )