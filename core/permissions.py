from rest_framework.permissions import BasePermission

class IsClienteOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.role == 'cliente' or request.user.is_superuser)

class IsVendedor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'vendedor'

class IsBodeguero(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'bodeguero'

class IsContador(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'contador'
