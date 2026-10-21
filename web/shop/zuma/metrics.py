import os

from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.http import HttpResponse
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, CollectorRegistry, generate_latest, multiprocess
from prometheus_client.core import GaugeMetricFamily

from ep1101.models import Category, Order, Product


class ShopCollector:
    """Бизнес-метрики магазина, считаются из БД в момент запроса Prometheus"""

    def collect(self):
        yield GaugeMetricFamily('shop_users', 'Количество зарегистрированных пользователей', value=User.objects.count())
        yield GaugeMetricFamily('shop_categories', 'Количество категорий', value=Category.objects.count())

        products = Product.objects.aggregate(count=Count('id'), stock=Sum('stock'))
        yield GaugeMetricFamily('shop_products', 'Количество товаров', value=products['count'])
        yield GaugeMetricFamily('shop_products_stock', 'Суммарный остаток товаров на складе', value=products['stock'] or 0)
        yield GaugeMetricFamily(
            'shop_products_out_of_stock', 'Товары, которых нет в наличии',
            value=Product.objects.filter(stock=0).count(),
        )

        orders = GaugeMetricFamily('shop_orders', 'Количество заказов по статусам', labels=['status'])
        revenue = GaugeMetricFamily('shop_orders_amount_rub', 'Сумма заказов по статусам, руб.', labels=['status'])
        stats = {row['status']: row for row in Order.objects.values('status').annotate(count=Count('id'), amount=Sum('total_amount'))}
        for status, _ in Order.STATUS_CHOICES:
            row = stats.get(status, {})
            orders.add_metric([status], row.get('count', 0))
            revenue.add_metric([status], float(row.get('amount') or 0))
        yield orders
        yield revenue


def metrics_view(request):
    """Страница /metrics в формате Prometheus.

    Gunicorn запускает несколько воркеров, поэтому метрики django-prometheus
    собираются из общего каталога PROMETHEUS_MULTIPROC_DIR, а не из памяти одного процесса.
    """
    registry = CollectorRegistry()
    if 'PROMETHEUS_MULTIPROC_DIR' in os.environ:
        multiprocess.MultiProcessCollector(registry)
    else:
        registry.register(REGISTRY)
    registry.register(ShopCollector())
    return HttpResponse(generate_latest(registry), content_type=CONTENT_TYPE_LATEST)
