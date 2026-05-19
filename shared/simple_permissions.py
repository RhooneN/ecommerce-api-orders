# shared/simple_permissions.py
        
  # products/permissions.py
from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    """
    Allows access only to users with is_admin=True in JWT.
    """
    def has_permission(self, request, view):
        print("USER:", request.user)
        print("AUTH:", request.auth)
        print("HEADERS:", request.META.get('HTTP_AUTHORIZATION'))

        return bool(
            request.user 
            and getattr(request.user, "is_admin", False) is True
        )
        
class IsAdminOrReadOnly(BasePermission):
    """
    Allows access only to users with is_admin=True in JWT.
    """
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return bool(
            request.user 
            and getattr(request.user, "is_admin", False) is True
        )
class IsAuth(BasePermission):
    """
    Allows access only to authenticated users (with user_id and username).
    """
    
    def has_permission(self, request, view):
        print("USER:", dir(request))
        print("USER:", request.user)
        print("AUTH:", request.auth)
        print("HEADERS:", request.META.get('HTTP_AUTHORIZATION'))

        return bool(
            request.user 
            and getattr(request.user, "user_id", None) 
        )


class IsAuthenticatedOrReadOnly(BasePermission):
    """Allow read access to anyone, write access to authenticated users"""
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return getattr(request, 'user_id', None) is not None
