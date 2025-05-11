from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrAdmin(BasePermission):
    """
    Permite editar/eliminar solo si el usuario es el creador del objeto (auctioneer o user)
    o si es administrador. Cualquiera puede leer (GET, HEAD, OPTIONS).
    """
    def has_object_permission(self, request, view, obj):
        # Lectura para todos
        if request.method in SAFE_METHODS:
            return True

        # Si el objeto tiene atributo 'auctioneer'
        if hasattr(obj, 'auctioneer'):
            return obj.auctioneer == request.user or request.user.is_staff

        # Si el objeto tiene atributo 'user'
        if hasattr(obj, 'user'):
            return obj.user == request.user or request.user.is_staff

        # Por defecto, denegar
        return False