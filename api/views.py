from rest_framework import viewsets, status, filters, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema, OpenApiParameter

from ep1101.models import Category, Product, Cart, CartItem, Order, OrderItem
from .serializers import (
    CategorySerializer, ProductSerializer, CartSerializer,
    CartItemSerializer, OrderSerializer, OrderCreateSerializer, UserSerializer
)
from .permissions import (
    CategoryPermissions, ProductPermissions, OrderPermissions, CartPermissions, IsStaffOrAdmin
)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class CategoryViewSet(viewsets.ModelViewSet):
    """API для работы с категориями"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [CategoryPermissions]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']


class ProductViewSet(viewsets.ModelViewSet):
    """API для работы с товарами"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [ProductPermissions]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'category__name']
    filterset_fields = ['category', 'stock']
    ordering_fields = ['name', 'price', 'stock', 'created_at']
    ordering = ['name']


class CartViewSet(viewsets.ModelViewSet):
    """API для работы с корзиной"""
    serializer_class = CartSerializer
    permission_classes = [CartPermissions]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        if hasattr(self, 'swagger_fake_view'):
            return Cart.objects.none()

        if user.is_authenticated and user.has_perm('ep1101.view_all_carts'):
            return Cart.objects.all()
        if user.is_authenticated:
            return Cart.objects.filter(user=user)
        return Cart.objects.none()

    def get_object(self):
        if hasattr(self, 'swagger_fake_view'):
            return None

        if self.request.user.is_authenticated and self.request.user.has_perm('ep1101.view_all_carts'):
            return get_object_or_404(Cart, pk=self.kwargs.get('pk'))
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def list(self, request, *args, **kwargs):
        if hasattr(self, 'swagger_fake_view'):
            return Response([])

        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        if request.user.has_perm('ep1101.view_all_carts'):
            return super().list(request, *args, **kwargs)

        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name='product_id', description='ID продукта', required=True, type=int)
        ]
    )
    @action(detail=False, methods=['post'], url_path='add/(?P<product_id>[^/.]+)',
            permission_classes=[IsAuthenticatedOrReadOnly])
    def add_item(self, request, product_id=None):
        """Добавление товара в корзину"""
        if hasattr(self, 'swagger_fake_view'):
            return Response({})

        product = get_object_or_404(Product, id=product_id)
        cart, _ = Cart.objects.get_or_create(user=request.user)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()

        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        parameters=[
            OpenApiParameter(name='item_id', description='ID позиции в корзине', required=True, type=int)
        ]
    )
    @action(detail=False, methods=['post'], url_path='item/(?P<item_id>[^/.]+)/increment',
            permission_classes=[IsAuthenticatedOrReadOnly])
    def increment_item(self, request, item_id=None):
        """Увеличение количества товара"""
        if hasattr(self, 'swagger_fake_view'):
            return Response({})

        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        if cart_item.quantity + 1 <= cart_item.product.stock:
            cart_item.quantity += 1
            cart_item.save()
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name='item_id', description='ID позиции в корзине', required=True, type=int)
        ]
    )
    @action(detail=False, methods=['post'], url_path='item/(?P<item_id>[^/.]+)/decrement',
            permission_classes=[IsAuthenticatedOrReadOnly])
    def decrement_item(self, request, item_id=None):
        """Уменьшение количества товара"""
        if hasattr(self, 'swagger_fake_view'):
            return Response({})

        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
            return Response({'message': 'Item removed from cart'}, status=status.HTTP_200_OK)
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(name='item_id', description='ID позиции в корзине', required=True, type=int)
        ]
    )
    @action(detail=False, methods=['delete'], url_path='item/(?P<item_id>[^/.]+)/remove',
            permission_classes=[IsAuthenticatedOrReadOnly])
    def remove_item(self, request, item_id=None):
        """Удаление товара из корзины"""
        if hasattr(self, 'swagger_fake_view'):
            return Response({})

        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
        return Response({'message': 'Item removed from cart'}, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(name='item_id', description='ID позиции в корзине', required=True, type=int)
        ]
    )
    @action(detail=False, methods=['put'], url_path='item/(?P<item_id>[^/.]+)',
            permission_classes=[IsAuthenticatedOrReadOnly])
    def update_item(self, request, item_id=None):
        """Обновление количества товара"""
        if hasattr(self, 'swagger_fake_view'):
            return Response({})

        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        quantity = request.data.get('quantity', cart_item.quantity)
        if quantity > 0 and quantity <= cart_item.product.stock:
            cart_item.quantity = quantity
            cart_item.save()
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)

    @action(detail=False, methods=['delete'], permission_classes=[IsAuthenticatedOrReadOnly])
    def clear(self, request):
        """Очистка корзины"""
        if hasattr(self, 'swagger_fake_view'):
            return Response({})

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        return Response({'message': 'Cart cleared successfully'}, status=status.HTTP_200_OK)


class OrderViewSet(viewsets.ModelViewSet):
    """API для работы с заказами"""
    serializer_class = OrderSerializer
    permission_classes = [OrderPermissions]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['customer_name', 'phone', 'email']
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'total_amount', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        """Возвращает все заказы для стаффа или только свои для обычного пользователя"""
        if hasattr(self, 'swagger_fake_view'):
            return Order.objects.none()

        user = self.request.user
        if not user.is_authenticated:
            return Order.objects.none()

        if user.has_perm('ep1101.view_all_orders') or user.is_staff or user.is_superuser:
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def get_object(self):
        """Получение заказа с проверкой прав"""
        if hasattr(self, 'swagger_fake_view'):
            return None

        obj = get_object_or_404(Order, pk=self.kwargs.get('pk'))
        user = self.request.user

        # Проверка прав на просмотр
        if user.has_perm('ep1101.view_all_orders') or user.is_staff or user.is_superuser:
            return obj

        # Обычный пользователь может просматривать только свои заказы
        if obj.user == user:
            return obj

        raise PermissionError('У вас нет доступа к этому заказу')

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        """Создание заказа с проверкой корзины"""
        cart, _ = Cart.objects.get_or_create(user=self.request.user)

        if cart.items.count() == 0:
            raise serializers.ValidationError({'error': 'Cart is empty'})

        # Проверка наличия товаров
        for cart_item in cart.items.all():
            if cart_item.quantity > cart_item.product.stock:
                raise serializers.ValidationError({
                    'error': f'Product "{cart_item.product.name}" is not available in requested quantity'
                })

        # Создаем заказ
        order = Order.objects.create(
            user=self.request.user,
            customer_name=serializer.validated_data['customer_name'],
            shipping_address=serializer.validated_data['shipping_address'],
            phone=serializer.validated_data['phone'],
            email=serializer.validated_data.get('email', ''),
            total_amount=cart.total_price()
        )

        # Создаем позиции заказа и обновляем склад
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            cart_item.product.stock -= cart_item.quantity
            cart_item.product.save()

        cart.items.all().delete()

        return order

    def create(self, request, *args, **kwargs):
        """Создание заказа через API"""
        if hasattr(self, 'swagger_fake_view'):
            return Response({})

        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            order = self.perform_create(serializer)
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticatedOrReadOnly])
    def cancel(self, request, pk=None):
        """Отмена заказа (только для владельца или стаффа)"""
        if hasattr(self, 'swagger_fake_view'):
            return Response({})

        order = self.get_object()

        if not (request.user == order.user or request.user.has_perm('ep1101.change_order') or request.user.is_staff):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        if order.status not in ['pending', 'confirmed']:
            return Response({'error': 'Order cannot be cancelled in current status'},
                            status=status.HTTP_400_BAD_REQUEST)

        order.status = 'cancelled'
        order.save()

        return Response({'message': f'Order #{order.id} cancelled successfully'})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticatedOrReadOnly])
    def my(self, request):
        """Получение заказов текущего пользователя"""
        if hasattr(self, 'swagger_fake_view'):
            return Response([])

        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """API для просмотра пользователей"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsStaffOrAdmin]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email']
    ordering_fields = ['username', 'date_joined']
    ordering = ['username']
