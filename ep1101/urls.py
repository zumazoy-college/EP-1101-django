from django.urls import path
from .views import *

urlpatterns = [
    # Главная
    path('', home, name='home'),

    # Категории
    path('categories/', category_list, name='category_list'),
    path('categories/create/', category_create, name='category_create'),
    path('categories/<int:category_id>/edit/', category_edit, name='category_edit'),
    path('categories/<int:category_id>/delete/', category_delete, name='category_delete'),
    path('categories/<int:category_id>/products/', category_products, name='category_products'),

    # Товары
    path('products/<int:product_id>/', product_detail, name='product_detail'),
    path('products/create/', product_create, name='product_create'),
    path('products/<int:product_id>/edit/', product_edit, name='product_edit'),
    path('products/<int:product_id>/delete/', product_delete, name='product_delete'),

    # Корзина
    path('cart/', cart_view, name='cart_view'),
    path('cart/add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', remove_from_cart, name='remove_from_cart'),

    # Заказы
    path('orders/', order_list, name='order_list'),
    path('orders/<int:order_id>/', order_detail, name='order_detail'),
    path('checkout/', checkout, name='checkout'),
    path('orders/<int:order_id>/edit/', order_edit, name='order_edit'),
    path('orders/<int:order_id>/delete/', order_delete, name='order_delete'),
]
