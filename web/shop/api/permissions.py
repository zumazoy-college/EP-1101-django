from rest_framework.permissions import BasePermission, DjangoModelPermissions
from rest_framework.permissions import SAFE_METHODS


class DjangoModelPermissionsWithRead(DjangoModelPermissions):
    """Расширение DjangoModelPermissions для поддержки GET запросов"""
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


class CategoryPermissions(DjangoModelPermissionsWithRead):
    """Права для категорий"""
    pass


class ProductPermissions(DjangoModelPermissionsWithRead):
    """Права для товаров"""
    pass


class OrderPermissions(DjangoModelPermissionsWithRead):
    """Права для заказов с дополнительной логикой"""

    def has_permission(self, request, view):
        if view.action == 'my':
            return request.user.is_authenticated
        return super().has_permission(request, view)

    def has_object_permission(self, request, view, obj):
        if request.user.has_perm('ep1101.view_all_orders') or request.user.is_staff:
            return True

        # Владелец заказа может просматривать свой заказ
        if request.method in SAFE_METHODS and obj.user == request.user:
            return True

        # Владелец заказа может отменить заказ
        if request.method == 'POST' and view.action == 'cancel' and obj.user == request.user:
            return True

        return super().has_object_permission(request, view, obj)


class CartPermissions(BasePermission):
    """Права для корзины"""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if request.user.has_perm('ep1101.view_all_carts'):
            return True
        return obj.user == request.user


class IsStaffOrAdmin(BasePermission):
    """Доступ только для стаффа и администраторов"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
