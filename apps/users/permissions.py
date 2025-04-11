from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """
    Custom permission to only allow admin users access.
    """
    def has_permission(self, request, view):
        return request.user and (request.user.is_admin or request.user.is_superuser)

class IsManager(permissions.BasePermission):
    """
    Custom permission to only allow managers access.
    """
    def has_permission(self, request, view):
        return request.user and (request.user.is_manager or request.user.is_admin or request.user.is_superuser)

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object or admins to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions are only allowed to the owner or admin
        return obj.id == request.user.id or request.user.is_admin or request.user.is_superuser