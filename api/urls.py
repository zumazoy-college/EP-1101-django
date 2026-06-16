from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.response import Response
from rest_framework.decorators import api_view
from drf_spectacular.utils import extend_schema
from .views import CategoryViewSet, ProductViewSet, CartViewSet, OrderViewSet, UserViewSet

router = SimpleRouter()
router.register('categories', CategoryViewSet, basename='category')
router.register('products', ProductViewSet, basename='product')
router.register('cart', CartViewSet, basename='cart')
router.register('orders', OrderViewSet, basename='order')
router.register('users', UserViewSet, basename='user')


@extend_schema(exclude=True)
@api_view(['GET'])
def api_root(request):
    """Корневой эндпоинт API"""
    return Response({
        'categories': '/api/categories/',
        'products': '/api/products/',
        'cart': '/api/cart/',
        'orders': '/api/orders/',
        'users': '/api/users/',
        'auth': '/api/auth/',
        'docs': '/api/docs/',
        'schema': '/api/schema/',
    })


urlpatterns = [
    path('', api_root, name='api-root'),
    path('', include(router.urls)),
    path('auth/token/', obtain_auth_token, name='api_token_auth'),
    path('auth/', include('rest_framework.urls')),
]
