from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, permission_required
from .models import Product, Category, Cart, CartItem, Order, OrderItem
from .forms import ProductForm, CategoryForm, OrderForm, UserRegisterForm


def home(request):
    """Главная страница - список товаров"""
    products = Product.objects.filter(stock__gt=0)
    categories = Category.objects.all()
    return render(request, 'shop/home.html', {
        'products': products,
        'categories': categories
    })


def register(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'shop/register.html', {'form': form})


@login_required
def profile(request):
    """Профиль пользователя"""
    return render(request, 'shop/profile.html')


@login_required
def my_orders(request):
    """Список заказов текущего пользователя"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/my_orders.html', {'orders': orders})


# Категории - проверка прав
@permission_required('ep1101.view_category', raise_exception=True)
def category_list(request):
    """Список категорий"""
    categories = Category.objects.all()
    return render(request, 'shop/category_list.html', {'categories': categories})


@permission_required('ep1101.add_category', raise_exception=True)
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


@permission_required('ep1101.change_category', raise_exception=True)
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


@permission_required('ep1101.delete_category', raise_exception=True)
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
    """Товары по категории (доступно всем)"""
    category = get_object_or_404(Category, id=category_id)
    products = category.products.filter(stock__gt=0)
    return render(request, 'shop/category_products.html', {'category': category, 'products': products})


def product_detail(request, product_id):
    """Детальная страница товара (доступно всем)"""
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'shop/product_detail.html', {'product': product})


@permission_required('ep1101.add_product', raise_exception=True)
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


@permission_required('ep1101.change_product', raise_exception=True)
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


@permission_required('ep1101.delete_product', raise_exception=True)
def product_delete(request, product_id):
    """Удаление товара"""
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Товар "{product_name}" удален')
        return redirect('home')
    return render(request, 'shop/product_confirm_delete.html', {'product': product})


@login_required
def add_to_cart(request, product_id):
    """Добавление товара в корзину"""
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:
        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f'Количество товара "{product.name}" увеличено')
    else:
        messages.success(request, f'Товар "{product.name}" добавлен в корзину')

    return redirect('cart_view')


@login_required
def cart_view(request):
    """Просмотр корзины"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'shop/cart.html', {'cart': cart})


@login_required
def update_cart_item(request, item_id):
    """Обновление количества товара в корзине"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if 0 < quantity <= cart_item.product.stock:
            cart_item.quantity = quantity
            cart_item.save()
        elif quantity <= 0:
            cart_item.delete()

    return redirect('cart_view')


@login_required
def remove_from_cart(request, item_id):
    """Удаление товара из корзины"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f'Товар "{product_name}" удален из корзины')
    return redirect('cart_view')


@login_required
def clear_cart(request):
    """Очистка корзины"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart.items.all().delete()
    messages.success(request, 'Корзина очищена')
    return redirect('cart_view')


@login_required
def increment_cart_item(request, item_id):
    """Увеличить количество товара на 1"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if cart_item.quantity + 1 <= cart_item.product.stock:
        cart_item.quantity += 1
        cart_item.save()
    else:
        messages.warning(request, f'Недостаточно товара на складе (в наличии: {cart_item.product.stock})')
    return redirect('cart_view')


@login_required
def decrement_cart_item(request, item_id):
    """Уменьшить количество товара на 1"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart_view')


@permission_required('ep1101.view_order', raise_exception=True)
def order_list(request):
    """Список заказов (только для админов/менеджеров)"""
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'shop/order_list.html', {'orders': orders})


def order_detail(request, order_id):
    """Детали заказа (админ видит все, обычный пользователь только свои)"""
    order = get_object_or_404(Order, id=order_id)
    if not (request.user.is_superuser or request.user.has_perm('ep1101.view_order') or order.user == request.user):
        return render(request, 'shop/access_denied.html', {'message': 'У вас нет доступа к этому заказу'}, status=403)
    return render(request, 'shop/order_detail.html', {'order': order})


@login_required
def checkout(request):
    """Оформление заказа"""
    cart, created = Cart.objects.get_or_create(user=request.user)

    if cart.items.count() == 0:
        messages.warning(request, 'Корзина пуста')
        return redirect('cart_view')

    # Проверка наличия всех товаров в достаточном количестве
    insufficient_stock = []
    for cart_item in cart.items.all():
        if cart_item.quantity > cart_item.product.stock:
            insufficient_stock.append({
                'name': cart_item.product.name,
                'requested': cart_item.quantity,
                'available': cart_item.product.stock
            })

    if insufficient_stock:
        for item in insufficient_stock:
            messages.error(request,
                           f'Товар "{item["name"]}" в количестве {item["requested"]} шт. недоступен. '
                           f'Доступно: {item["available"]} шт.')
        return redirect('cart_view')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Дополнительная проверка перед созданием заказа
            for cart_item in cart.items.all():
                if cart_item.quantity > cart_item.product.stock:
                    messages.error(request,
                                   f'К сожалению, товар "{cart_item.product.name}" закончился или его количество изменилось. '
                                   f'Пожалуйста, обновите корзину.')
                    return redirect('cart_view')

            order = Order.objects.create(
                user=request.user,
                customer_name=form.cleaned_data['customer_name'],
                shipping_address=form.cleaned_data['shipping_address'],
                phone=form.cleaned_data['phone'],
                email=form.cleaned_data['email'],
                total_amount=cart.total_price()
            )

            for cart_item in cart.items.all():
                # Проверка перед списанием
                if cart_item.quantity > cart_item.product.stock:
                    order.delete()  # Отменяем заказ
                    messages.error(request,
                                   f'Ошибка: товар "{cart_item.product.name}" закончился. Заказ отменен.')
                    return redirect('cart_view')

                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price
                )
                # Уменьшаем количество товара на складе
                cart_item.product.stock -= cart_item.quantity
                cart_item.product.save()

            cart.items.all().delete()

            messages.success(request, f'Заказ #{order.id} успешно оформлен!')
            return redirect('my_orders')
    else:
        form = OrderForm()

    return render(request, 'shop/checkout.html', {'cart': cart, 'form': form})


@permission_required('ep1101.change_order', raise_exception=True)
def order_edit(request, order_id):
    """Редактирование заказа"""
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            if 'status' in request.POST:
                order.status = request.POST['status']
            order.save()
            messages.success(request, f'Заказ #{order.id} успешно обновлен')
            return redirect('order_detail', order_id=order.id)
    else:
        form = OrderForm(instance=order)
    return render(request, 'shop/order_form.html',
                  {'form': form, 'title': f'Редактировать заказ #{order.id}', 'order': order})


@permission_required('ep1101.delete_order', raise_exception=True)
def order_delete(request, order_id):
    """Удаление заказа"""
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        order_id_del = order.id
        order.delete()
        messages.success(request, f'Заказ #{order_id_del} удален')
        return redirect('order_list')
    return render(request, 'shop/order_confirm_delete.html', {'order': order})

