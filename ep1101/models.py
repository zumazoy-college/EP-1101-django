from django.db import models
from django.core.validators import MinValueValidator


class Category(models.Model):
    """Категория товаров"""
    name = models.CharField('Название', max_length=100)
    description = models.TextField('Описание', blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    """Товар"""
    name = models.CharField('Название', max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория', related_name='products')
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.PositiveIntegerField('Количество на складе', default=0)
    description = models.TextField('Описание', blank=True)
    image = models.ImageField('Изображение', upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return f"{self.name} - {self.price}₽"


class Cart(models.Model):
    """Корзина"""
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    def __str__(self):
        return f"Корзина #{self.id}"

    def total_price(self):
        """Общая стоимость корзины"""
        return sum(item.total_price() for item in self.items.all())


class CartItem(models.Model):
    """Позиция в корзине"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, verbose_name='Корзина', related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    quantity = models.PositiveIntegerField('Количество', default=1, validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = 'Позиция корзины'
        verbose_name_plural = 'Позиции корзины'
        unique_together = ['cart', 'product']

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    def total_price(self):
        """Стоимость позиции"""
        return self.product.price * self.quantity


class Order(models.Model):
    """Заказ"""
    STATUS_CHOICES = [
        ('pending', 'В обработке'),
        ('confirmed', 'Подтвержден'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]

    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField('Общая сумма', max_digits=10, decimal_places=2, default=0)

    # Информация о покупателе
    customer_name = models.CharField('Имя покупателя', max_length=200)
    phone = models.CharField('Телефон', max_length=20)
    email = models.EmailField('Email', blank=True)
    shipping_address = models.TextField('Адрес доставки')

    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f"Заказ #{self.id} - {self.customer_name}"


class OrderItem(models.Model):
    """Позиция заказа"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name='Заказ', related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    quantity = models.PositiveIntegerField('Количество')
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

