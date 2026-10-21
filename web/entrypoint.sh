#!/bin/sh
while ! nc -z $DB_HOST_PGSQL $DB_PORT_PGSQL; do
    sleep 1
done

echo "start migration"
uv run python manage.py migrate --noinput
echo "Migration completed"

echo "start collecting staticfiles"
uv run python manage.py collectstatic --noinput
echo "Collecting staticfiles completed"

echo "start creating superuser"
uv run python manage.py shell << END
from django.contrib.auth import get_user_model
import os
User = get_user_model()

username = os.getenv('DJANGO_SUPERUSER_USERNAME')
email = os.getenv('DJANGO_SUPERUSER_EMAIL')
password = os.getenv('DJANGO_SUPERUSER_PASSWORD')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f'Superuser {username} created')
else:
    print(f'Superuser {username} already exists')
END

echo "Superuser check completed"

# Каталог метрик воркеров лежит в volume: счётчики переживают перезапуск контейнера.
# Live-gauge принадлежат процессам прошлого запуска, поэтому их удаляем.
mkdir -p "$PROMETHEUS_MULTIPROC_DIR"
rm -f "$PROMETHEUS_MULTIPROC_DIR"/gauge_live*.db

echo "starting gunicorn"
exec uv run gunicorn zuma.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --access-logfile - \
    --error-logfile -