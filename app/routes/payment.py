from flask import (Blueprint, render_template, redirect,
                   url_for, flash, request, jsonify, current_app)
from flask_login import login_required, current_user
from app import db
from app.models.cart import Cart
from app.models.order import Order, OrderItem
from app.models.menu import MenuItem
from app.utils.invoice import generate_invoice
import razorpay

payment = Blueprint('payment', __name__)


# ---------- CHECKOUT PAGE ----------
@payment.route('/checkout')
@login_required
def checkout():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()

    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('customer.menu'))

    subtotal = sum(
        item.menu_item.price * item.quantity
        for item in cart_items
    )
    tax   = round(subtotal * 0.05, 2)
    total = round(subtotal + tax, 2)

    razorpay_key = current_app.config.get('RAZORPAY_KEY_ID', '')

    return render_template('payment/checkout.html',
                           cart_items   = cart_items,
                           subtotal     = subtotal,
                           tax          = tax,
                           total        = total,
                           razorpay_key = razorpay_key)


# ---------- CASH ORDER ----------
@payment.route('/place-order/cash', methods=['POST'])
@login_required
def place_order_cash():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()

    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('customer.menu'))

    subtotal = sum(
        item.menu_item.price * item.quantity
        for item in cart_items
    )
    tax   = round(subtotal * 0.05, 2)
    total = round(subtotal + tax, 2)

    order = Order(
        user_id        = current_user.id,
        total_amount   = total,
        payment_method = 'cash',
        payment_status = 'pending',
        order_status   = 'placed'
    )
    db.session.add(order)
    db.session.flush()

    for cart_item in cart_items:
        oi = OrderItem(
            order_id     = order.id,
            menu_item_id = cart_item.menu_item_id,
            quantity     = cart_item.quantity,
            price        = cart_item.menu_item.price
        )
        db.session.add(oi)

    Cart.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()

    flash(f'Order #{order.id} placed! Pay at counter.', 'success')
    return redirect(url_for('payment.order_success',
                            order_id=order.id))


# ---------- CREATE RAZORPAY ORDER ----------
@payment.route('/create-razorpay-order', methods=['POST'])
@login_required
def create_razorpay_order():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()

    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400

    subtotal = sum(
        item.menu_item.price * item.quantity
        for item in cart_items
    )
    tax   = round(subtotal * 0.05, 2)
    total = round(subtotal + tax, 2)

    key_id     = current_app.config.get('RAZORPAY_KEY_ID')
    key_secret = current_app.config.get('RAZORPAY_KEY_SECRET')

    if not key_id or not key_secret:
        return jsonify({
            'error': 'Payment not configured'
        }), 500

    try:
        client = razorpay.Client(auth=(key_id, key_secret))

        rzp_order = client.order.create({
            'amount'         : int(total * 100),  # paise mein
            'currency'       : 'INR',
            'payment_capture': 1
        })

        return jsonify({
            'order_id': rzp_order['id'],
            'amount'  : int(total * 100),
            'currency': 'INR',
            'name'    : current_user.name,
            'email'   : current_user.email,
            'mobile'  : current_user.mobile
        })

    except Exception as e:
        print(f'Razorpay Error: {e}')
        return jsonify({'error': str(e)}), 500


# ---------- VERIFY PAYMENT ----------
@payment.route('/verify-payment', methods=['POST'])
@login_required
def verify_payment():
    data = request.get_json()

    razorpay_order_id   = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature  = data.get('razorpay_signature')

    key_id     = current_app.config.get('RAZORPAY_KEY_ID')
    key_secret = current_app.config.get('RAZORPAY_KEY_SECRET')

    try:
        client = razorpay.Client(auth=(key_id, key_secret))

        # Signature verify karo
        client.utility.verify_payment_signature({
            'razorpay_order_id'  : razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature' : razorpay_signature
        })

        # Payment verified — order banao
        cart_items = Cart.query.filter_by(
            user_id=current_user.id
        ).all()

        subtotal = sum(
            i.menu_item.price * i.quantity
            for i in cart_items
        )
        tax   = round(subtotal * 0.05, 2)
        total = round(subtotal + tax, 2)

        order = Order(
            user_id        = current_user.id,
            total_amount   = total,
            payment_method = 'online',
            payment_status = 'paid',
            order_status   = 'placed',
            razorpay_id    = razorpay_payment_id
        )
        db.session.add(order)
        db.session.flush()

        for cart_item in cart_items:
            oi = OrderItem(
                order_id     = order.id,
                menu_item_id = cart_item.menu_item_id,
                quantity     = cart_item.quantity,
                price        = cart_item.menu_item.price
            )
            db.session.add(oi)

        Cart.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()

        return jsonify({
            'success' : True,
            'order_id': order.id
        })

    except Exception as e:
        print(f'Verification Error: {e}')
        return jsonify({
            'success': False,
            'error'  : str(e)
        }), 400


# ---------- ORDER SUCCESS ----------
@payment.route('/success/<int:order_id>')
@login_required
def order_success(order_id):
    order = Order.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('customer.home'))

    return render_template('payment/success.html', order=order)


# ---------- DOWNLOAD INVOICE ----------
@payment.route('/invoice/<int:order_id>')
@login_required
def download_invoice(order_id):
    order = Order.query.get_or_404(order_id)

    if (order.user_id != current_user.id and
            current_user.role != 'admin'):
        flash('Unauthorized.', 'danger')
        return redirect(url_for('customer.home'))

    return generate_invoice(order)