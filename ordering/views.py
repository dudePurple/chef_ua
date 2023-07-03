import os
import stripe
from django.http import HttpRequest
from django.shortcuts import render, redirect
from dotenv import load_dotenv

from .models import Product, Order, OrderItem

load_dotenv()
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')
BASE_URL = os.getenv('BASE_URL', 'http://127.0.0.1:8000')


def product_list(request: HttpRequest):
    """
    :param request: object that contains metadata about the request
    :return: renders product_list page, if there is pending request, shows it general details
    """
    products = Product.objects.all()
    order_id = request.session.get('order_id')
    order = Order.objects.get(pk=order_id) if order_id else None
    quantities = {}
    if order:
        order_items = order.orderitem_set.all()
        quantities = {item.product_id: item.quantity for item in order_items}

    for product in products:
        product.quantity = quantities.get(product.pk)

    return render(request, 'orders/product_list.html', {'products': products, 'order': order})


def add_or_update_order_item(request: HttpRequest, product_id: int):
    """
    Handles:
    1) Creation of order when its first order item added
    2) Addition of order items, update of their quantity, their removal (when new item quantity is set to 0)
    3) Deletion of order (and its removal from browser session) if it has no remaining order items
    :param request: object that contains metadata about the request
    :param product_id: id of the product to be added to the order
    :return: redirects user to products list page (with short info about his or her current order)
    """
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 0))
        product = Product.objects.get(pk=product_id)

        # Check if an order ID is already present in the session
        # After each successful or cancelled order session order is cleared
        order_id = request.session.get('order_id')

        # If no order ID exists in the session, create new and bind it to session
        # It allows to show relevant order for each user and not to pass it in every request
        if not order_id:
            order = Order.objects.create()
            request.session['order_id'] = order.id
        else:
            order = Order.objects.get(pk=order_id)

        try:
            order_item = OrderItem.objects.get(order=order, product=product)
        except OrderItem.DoesNotExist:
            order_item = None

        if order_item and quantity:
            order_item.quantity = quantity
            order_item.save()
        elif order_item:
            order_item.delete()
            if not order.orderitem_set.all():
                order.delete()
                request.session.update({'order_id': None})
        else:
            OrderItem.objects.create(order=order, product=product, quantity=quantity)

    return redirect('product_list')


def order_details(request: HttpRequest, order_id: int):
    """
    :param request: object that contains metadata about the request
    :param order_id: id of the current user's order
    :return: renders current user's order details with option to change order or pay for it
    """
    order = Order.objects.get(pk=order_id)
    return render(request, 'orders/order_details.html', {'order': order})


def process_payment(request: HttpRequest):
    """
    When user clicks on Pay Now button:
    1) order status is changed to active
    2) Stripe checkout Session is created
    :param request: object that contains metadata about the request
    :return: redirects user to stripe payment page
    """
    order_id = request.session.get('order_id')
    if not stripe.api_key:
        return redirect(f'{BASE_URL}/order_details/{order_id}')

    order = Order.objects.get(pk=order_id)
    order.status = 'active'
    order.save()
    session = stripe.checkout.Session.create(
        success_url=f'{BASE_URL}/successful_payment',  # url to which user is redirected after successful payment
        cancel_url=f'{BASE_URL}/cancelled_payment',  # url to which user is redirected after cancelled payment
        line_items=[
            {
                'price_data': {
                    'unit_amount': int(order.total * 100),
                    'currency': 'USD',
                    'product': stripe.Product.create(name=f'Order {order_id}').id
                },
                'quantity': 1
            },
        ],
        mode='payment',
    )
    return redirect(session.url)


def successful_payment(request: HttpRequest):
    """
    Current order's status is updated to completed
    :param request: object that contains metadata about the request
    :return: renders page notifying user about successful payment with option to make another order
    """
    order_id = request.session.get('order_id')
    Order.objects.filter(pk=order_id).update(status='completed')
    request.session.update({'order_id': None})
    return render(request, 'orders/successful_payment.html', {'order_id': order_id})


def cancelled_payment(request: HttpRequest):
    """
    :param request: object that contains metadata about the request
    :return: renders page notifying user about cancelled payment with option to make new order
    """
    order_id = request.session.get('order_id')
    request.session.update({'order_id': None})
    return render(request, 'orders/cancelled_payment.html', {'order_id': order_id})
