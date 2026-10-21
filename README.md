# Техномаркет — интернет-магазин на Django

Учебный проект интернет-магазина: каталог товаров по категориям, корзина, оформление и просмотр заказов, личный кабинет и REST API.

**Стек:** Django 6, Django REST Framework, PostgreSQL 18, gunicorn, nginx, Docker Compose, uv.

## Запуск

```bash
# 1. Переменные окружения
cp .env.example .env

# 2. Общая сеть с мониторингом (один раз)
docker network create MS

# 3. Сборка и запуск
docker compose up -d --build
```

При старте контейнер `web` сам применяет миграции, собирает статику и создаёт суперпользователя из `.env` (`DJANGO_SUPERUSER_*`).

## Адреса

| Адрес | Что там |
| --- | --- |
| <http://localhost/> | сайт магазина |
| <http://localhost/admin/> | админка Django |
| <http://localhost/api/> | REST API |
| <http://localhost/api/docs/> | Swagger-документация API |

## Сервисы

- `db` — PostgreSQL, данные хранятся в volume `postgres_data`;
- `web` — Django + gunicorn (4 воркера) на порту 8000 внутри сети;
- `nginx` — порт 80, отдаёт статику и медиа, проксирует запросы в `web`.

## Метрики Prometheus

Приложение отдаёт метрики на `/metrics` (через [django-prometheus](https://github.com/korfuri/django-prometheus)):

- `django_*` — запросы, HTTP-статусы, время ответа, запросы к БД;
- `shop_*` — пользователи, товары, остатки, заказы и их суммы по статусам (`web/shop/zuma/metrics.py`).

Снаружи страница закрыта в nginx. Prometheus забирает её напрямую из сети `MS` по адресу `django-shop:8000/metrics`. Счётчики хранятся в volume `prometheus_multiproc` и не сбрасываются при перезапуске.

## Полезные команды

```bash
docker compose logs -f web                                  # логи приложения
docker compose exec web uv run python manage.py shell       # Django shell
docker compose exec db psql -U store_user -d store          # консоль БД
```
