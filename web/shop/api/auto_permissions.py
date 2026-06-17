from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.db import connection


# Конфигурация прав
PERMISSIONS_CONFIG = {
    'Customers': {
        'view': ['category', 'product', 'cart', 'order'],
        'add': ['cart', 'order'],
        'change': ['cart', 'order'],
        'delete': ['cart', 'order'],
        'exclude': ['view_all_carts', 'view_all_orders']
    },
    'Staff': {
        'view': ['category', 'product', 'cart', 'order'],
        'add': ['category', 'product', 'cart', 'order'],
        'change': ['category', 'product', 'cart', 'order'],
        'delete': ['category', 'product', 'cart', 'order'],
        'include': ['view_all_carts', 'view_all_orders']
    },
    'Admins': {
        'all': True
    }
}


def get_available_permissions():
    """Получить все доступные права в виде словаря {codename: permission}"""
    return {
        perm.codename: perm
        for perm in Permission.objects.all()
    }


def create_extra_permissions():
    """Создание дополнительных прав, которых нет в стандартных"""
    extra_permissions = [
        ('view_all_carts', 'Cart', 'Can view all carts'),
        ('view_all_orders', 'Order', 'Can view all orders'),
    ]

    for codename, model_name, name in extra_permissions:
        try:
            Model = apps.get_model('ep1101', model_name)
            content_type = ContentType.objects.get_for_model(Model)

            permission, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': name}
            )
            if created:
                print(f'Created extra permission: {codename}')
        except LookupError:
            print(f'Warning: Model {model_name} not found in ep1101')
            continue


def apply_permissions():
    """Применить настройки прав ко всем группам"""
    # Проверяем, что таблицы существуют
    if not connection.introspection.table_names():
        print('Database not ready, skipping permissions setup')
        return

    try:
        # Проверяем, существует ли таблица auth_group
        if 'auth_group' not in connection.introspection.table_names():
            print('Auth tables not ready, skipping permissions setup')
            return
    except Exception:
        print('Database not ready, skipping permissions setup')
        return

    print('Applying permissions...')

    # Сначала создаем все стандартные права Django
    from django.contrib.auth.management import create_permissions
    for app_config in apps.get_app_configs():
        create_permissions(app_config, verbosity=0)

    # Создаем дополнительные права
    create_extra_permissions()

    # Получаем все существующие права
    all_perms = get_available_permissions()

    # Обновляем группы
    for role_name, config in PERMISSIONS_CONFIG.items():
        group, created = Group.objects.get_or_create(name=role_name)
        if created:
            print(f'Created group: {role_name}')

        # Если all: True - даем все права
        if config.get('all', False):
            group.permissions.add(*Permission.objects.all())
            print(f'  {role_name}: All permissions')
            continue

        # Собираем права для роли
        perms_to_add = []

        # Стандартные действия (view, add, change, delete)
        for action in ['view', 'add', 'change', 'delete']:
            if action in config:
                for model_name in config[action]:
                    codename = f'{action}_{model_name}'
                    if codename in all_perms:
                        perms_to_add.append(all_perms[codename])

        # Добавляем дополнительные права (include)
        if 'include' in config:
            for codename in config['include']:
                if codename in all_perms:
                    perms_to_add.append(all_perms[codename])

        # Удаляем исключенные права (exclude)
        if 'exclude' in config:
            perms_to_add = [p for p in perms_to_add if p.codename not in config['exclude']]

        # Обновляем права группы
        if perms_to_add:
            group.permissions.clear()
            group.permissions.add(*perms_to_add)
            print(f'  {role_name}: {len(perms_to_add)} permissions assigned')
        else:
            group.permissions.clear()
            print(f'  {role_name}: No permissions assigned')

    print('Permissions applied successfully!')


@receiver(post_migrate)
def auto_sync_permissions(sender, **kwargs):
    """Автоматическая синхронизация после миграций"""
    if sender.name == 'api' or kwargs.get('app_config', None) == 'api':
        apply_permissions()
