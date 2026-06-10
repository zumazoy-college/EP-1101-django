from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Product, Category, Cart, CartItem, Order, OrderItem
from .forms import ProductForm, CategoryForm, OrderForm


def home(request):
    """Главная страница - список товаров"""
    products = Product.objects.filter(stock__gt=0)
    categories = Category.objects.all()
    return render(request, 'shop/home.html', {
        'products': products,
        'categories': categories
    })


def category_list(request):
    """Список категорий"""
    categories = Category.objects.all()
    return render(request, 'shop/category_list.html', {'categories': categories})


def category_create(request):
    """Создание категории"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Категория успешно создана')
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'shop/category_form.html', {'form': form, 'title': 'Создать категорию'})


def category_edit(request, category_id):
    """Редактирование категории"""
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Категория успешно обновлена')
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'shop/category_form.html', {'form': form, 'title': 'Редактировать категорию'})


def category_delete(request, category_id):
    """Удаление категории"""
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Категория "{category_name}" удалена')
        return redirect('category_list')
    return render(request, 'shop/category_confirm_delete.html', {'category': category})


def category_products(request, category_id):
    """Товары по категории"""
    category = get_object_or_404(Category, id=category_id)
    products = category.products.filter(stock__gt=0)
    return render(request, 'shop/category_products.html', {'category': category, 'products': products})


def product_detail(request, product_id):
    """Детальная страница товара"""
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'shop/product_detail.html', {'product': product})


def product_create(request):
    """Создание товара"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Товар успешно добавлен')
            return redirect('home')
    else:
        form = ProductForm()
    return render(request, 'shop/product_form.html', {'form': form, 'title': 'Добавить товар'})


def product_edit(request, product_id):
    """Редактирование товара"""
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Товар успешно обновлен')
            return redirect('product_detail', product_id=product.id)
    else:
        form = ProductForm(instance=product)
    return render(request, 'shop/product_form.html', {'form': form, 'title': 'Редактировать товар'})


def product_delete(request, product_id):
    """Удаление товара"""
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Товар "{product_name}" удален')
        return redirect('home')
    return render(request, 'shop/product_confirm_delete.html', {'product': product})


def add_to_cart(request, product_id):
    """Добавление товара в корзину"""
    product = get_object_or_404(Product, id=product_id)
    cart_id = request.session.get('cart_id')
    if cart_id:
        try:
            cart = Cart.objects.get(id=cart_id)
        except Cart.DoesNotExist:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
    else:
        cart = Cart.objects.create()
        request.session['cart_id'] = cart.id

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:
        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f'Количество товара "{product.name}" увеличено')
    else:
        messages.success(request, f'Товар "{product.name}" добавлен в корзину')

    return redirect('cart_view')


def cart_view(request):
    """Просмотр корзины"""
    cart_id = request.session.get('cart_id')
    if cart_id:
        try:
            cart = Cart.objects.get(id=cart_id)
        except Cart.DoesNotExist:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
    else:
        cart = Cart.objects.create()
        request.session['cart_id'] = cart.id

    return render(request, 'shop/cart.html', {'cart': cart})


def update_cart_item(request, item_id):
    """Обновление количества товара в корзине"""
    cart_id = request.session.get('cart_id')
    if cart_id:
        cart_item = get_object_or_404(CartItem, id=item_id, cart_id=cart_id)

        if request.method == 'POST':
            quantity = int(request.POST.get('quantity', 1))
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()

    return redirect('cart_view')


def remove_from_cart(request, item_id):
    """Удаление товара из корзины"""
    cart_id = request.session.get('cart_id')
    if cart_id:
        cart_item = get_object_or_404(CartItem, id=item_id, cart_id=cart_id)
        product_name = cart_item.product.name
        cart_item.delete()
        messages.success(request, f'Товар "{product_name}" удален из корзины')

    return redirect('cart_view')


def order_list(request):
    """Список заказов"""
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'shop/order_list.html', {'orders': orders})


def order_detail(request, order_id):
    """Детали заказа"""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'shop/order_detail.html', {'order': order})


def checkout(request):
    """Оформление заказа (создание)"""
    cart_id = request.session.get('cart_id')
    if not cart_id:
        messages.warning(request, 'Корзина пуста')
        return redirect('cart_view')

    try:
        cart = Cart.objects.get(id=cart_id)
    except Cart.DoesNotExist:
        messages.warning(request, 'Корзина пуста')
        return redirect('cart_view')

    if cart.items.count() == 0:
        messages.warning(request, 'Корзина пуста')
        return redirect('cart_view')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = Order.objects.create(
                customer_name=form.cleaned_data['customer_name'],
                shipping_address=form.cleaned_data['shipping_address'],
                phone=form.cleaned_data['phone'],
                email=form.cleaned_data['email'],
                total_amount=cart.total_price()
            )

            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price
                )
                # Уменьшаем количество товара на складе
                cart_item.product.stock -= cart_item.quantity
                cart_item.product.save()

            # Очищаем корзину
            cart.items.all().delete()
            # Удаляем сессию корзины
            del request.session['cart_id']

            messages.success(request, f'Заказ #{order.id} успешно оформлен!')
            return redirect('order_list')
    else:
        form = OrderForm()

    return render(request, 'shop/checkout.html', {'cart': cart, 'form': form})


def order_edit(request, order_id):
    """Редактирование заказа"""
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f'Заказ #{order.id} успешно обновлен')
            return redirect('order_detail', order_id=order.id)
    else:
        form = OrderForm(instance=order)
    return render(request, 'shop/order_form.html',
                  {'form': form, 'title': f'Редактировать заказ #{order.id}', 'order': order})


def order_delete(request, order_id):
    """Удаление заказа"""
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        order_id_del = order.id
        order.delete()
        messages.success(request, f'Заказ #{order_id_del} удален')
        return redirect('order_list')
    return render(request, 'shop/order_confirm_delete.html', {'order': order})

