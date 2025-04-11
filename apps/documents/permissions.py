from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Allow if user is admin or staff
        if request.user.is_staff or hasattr(request.user, 'is_admin') and request.user.is_admin:
            return True

        # Write permissions are only allowed to the owner
        return obj.owner == request.user


class IsOwnerAdminOrShared(permissions.BasePermission):
    """
    Custom permission to allow owners, admins, and shared users to access an object.
    """

    def has_object_permission(self, request, view, obj):
        # Allow if user is admin or staff
        if request.user.is_staff or hasattr(request.user, 'is_admin') and request.user.is_admin:
            return True

        # Allow if user is owner
        if obj.owner == request.user:
            return True

        # Allow if object is public
        if obj.is_public:
            return True

        # Allow if user is in shared_users
        if hasattr(obj, 'shared_users') and request.user in obj.shared_users.all():
            # Only allow read operations for shared users
            if request.method in permissions.SAFE_METHODS:
                return True

        return False