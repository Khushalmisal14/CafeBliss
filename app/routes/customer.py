from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from app import db
from app.ai.chatbot import get_chatbot_response
from app.ai.recommender import get_all_recommendations
from app.models.menu import MenuItem, Category
from app.models.cart import Cart
from app.models.order import Order, OrderItem

customer = Blueprint('customer', __name__)


# ---------- HOME ----------
@customer.route('/')
def home():
    # Get featured items (first 6 available items)
    featured_items = MenuItem.query.filter_by(is_available=True).limit(6).all()

    # Get all categories
    categories = Category.query.all()

    return render_template('customer/home.html',
                           featured_items=featured_items,
                           categories=categories)


# ---------- MENU ----------
@customer.route('/menu')
def menu():
    category_id = request.args.get('category', type=int)
    search      = request.args.get('search', '').strip()

    # Base query — only available items
    query = MenuItem.query.filter_by(is_available=True)

    # Filter by category if selected
    if category_id:
        query = query.filter_by(category_id=category_id)

    # Filter by search term
    if search:
        query = query.filter(MenuItem.name.ilike(f'%{search}%'))

    items      = query.all()
    categories = Category.query.all()

    return render_template('customer/menu.html',
                           items=items,
                           categories=categories,
                           selected_category=category_id,
                           search=search)


# ---------- CART ----------
@customer.route('/cart')
@login_required
def cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()

    total = sum(item.menu_item.price * item.quantity for item in cart_items)

    return render_template('customer/cart.html',
                           cart_items=cart_items,
                           total=total)


# ---------- ADD TO CART ----------
@customer.route('/cart/add/<int:item_id>', methods=['POST'])
@login_required
def add_to_cart(item_id):
    menu_item = MenuItem.query.get_or_404(item_id)

    # Check if item already in cart
    existing = Cart.query.filter_by(
        user_id=current_user.id,
        menu_item_id=item_id
    ).first()

    if existing:
        existing.quantity += 1
    else:
        cart_item = Cart(
            user_id      = current_user.id,
            menu_item_id = item_id,
            quantity     = 1
        )
        db.session.add(cart_item)

    db.session.commit()
    flash(f'{menu_item.name} added to cart!', 'success')
    return redirect(url_for('customer.menu'))


# ---------- REMOVE FROM CART ----------
@customer.route('/cart/remove/<int:cart_id>')
@login_required
def remove_from_cart(cart_id):
    cart_item = Cart.query.get_or_404(cart_id)

    if cart_item.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('customer.cart'))

    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart.', 'info')
    return redirect(url_for('customer.cart'))


# ---------- UPDATE CART QUANTITY ----------
@customer.route('/cart/update/<int:cart_id>', methods=['POST'])
@login_required
def update_cart(cart_id):
    cart_item = Cart.query.get_or_404(cart_id)
    quantity  = int(request.form.get('quantity', 1))

    if cart_item.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('customer.cart'))

    if quantity < 1:
        db.session.delete(cart_item)
    else:
        cart_item.quantity = quantity

    db.session.commit()
    return redirect(url_for('customer.cart'))


# ---------- ORDER HISTORY ----------
@customer.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(
        user_id=current_user.id
    ).order_by(Order.created_at.desc()).all()

    return render_template('customer/orders.html', orders=user_orders)


# ---------- ORDER DETAIL ----------
@customer.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('customer.orders'))

    return render_template('customer/order_detail.html', order=order)

# ---------- AI RECOMMENDATIONS ----------
@customer.route('/recommendations')
@login_required
def recommendations():
    budget = request.args.get('budget', type=float)
    recs   = get_all_recommendations(current_user.id, budget=budget)

    return render_template('customer/recommendations.html',
                           recs   = recs,
                           budget = budget)

# ---------- CHATBOT ----------
@customer.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    response = None
    user_message = None

    if request.method == 'POST':
        user_message = request.form.get('message', '').strip()
        user_id = current_user.id if current_user.is_authenticated else None
        response = get_chatbot_response(user_message, user_id)

    return render_template('customer/chatbot.html',
                           response=response,
                           user_message=user_message)


# ---------- CHATBOT API (for live chat widget) ----------
@customer.route('/chatbot/api', methods=['POST'])
def chatbot_api():
    from flask import jsonify
    data = request.get_json()
    message = data.get('message', '').strip()
    user_id = current_user.id if current_user.is_authenticated else None
    response = get_chatbot_response(message, user_id)
    return jsonify({'response': response})

# ---------- PROFILE ----------
@customer.route('/profile')
@login_required
def profile():
    total_orders = Order.query.filter_by(user_id=current_user.id).count()
    total_spent  = db.session.query(
                     db.func.sum(Order.total_amount)
                   ).filter_by(
                     user_id=current_user.id,
                     payment_status='paid'
                   ).scalar() or 0

    return render_template('customer/profile.html',
                           total_orders = total_orders,
                           total_spent  = total_spent)