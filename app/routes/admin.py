from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.menu import MenuItem, Category
from app.models.order import Order, OrderItem
from app.models.user import User
from functools import wraps
import os
from werkzeug.utils import secure_filename
from flask import current_app

admin = Blueprint('admin', __name__)


# ---------- ADMIN ONLY DECORATOR ----------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


# ---------- DASHBOARD ----------
@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    from datetime import datetime, timedelta

    # Stats
    total_orders    = Order.query.count()
    total_revenue   = db.session.query(
                        db.func.sum(Order.total_amount)
                      ).filter_by(payment_status='paid').scalar() or 0
    total_customers = User.query.filter_by(role='customer').count()
    total_items     = MenuItem.query.count()

    # Recent orders
    recent_orders   = Order.query.order_by(
                        Order.created_at.desc()
                      ).limit(10).all()

    # Popular items
    popular_items   = db.session.query(
                        MenuItem.name,
                        db.func.sum(OrderItem.quantity).label('total_sold')
                      ).join(OrderItem, MenuItem.id == OrderItem.menu_item_id
                      ).group_by(MenuItem.id
                      ).order_by(db.text('total_sold DESC')
                      ).limit(5).all()

    # Daily revenue last 7 days
    seven_days_ago  = datetime.utcnow() - timedelta(days=7)
    daily_revenue   = db.session.query(
                        db.func.date(Order.created_at).label('date'),
                        db.func.sum(Order.total_amount).label('revenue')
                      ).filter(Order.created_at >= seven_days_ago
                      ).group_by(db.func.date(Order.created_at)
                      ).all()

    return render_template('admin/dashboard.html',
                           total_orders    = total_orders,
                           total_revenue   = total_revenue,
                           total_customers = total_customers,
                           total_items     = total_items,
                           recent_orders   = recent_orders,
                           popular_items   = popular_items,
                           daily_revenue   = daily_revenue,
                           now             = datetime.now(),
                           enumerate       = enumerate)

# ---------- ALL ORDERS ----------
@admin.route('/orders')
@login_required
@admin_required
def all_orders():
    status = request.args.get('status', '')
    query  = Order.query.order_by(Order.created_at.desc())
    if status:
        query = query.filter_by(order_status=status)
    orders = query.all()
    return render_template('admin/orders.html', orders=orders, status=status)


# ---------- UPDATE ORDER STATUS ----------
@admin.route('/orders/<int:order_id>/update', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_id):
    order  = Order.query.get_or_404(order_id)
    status = request.form.get('status')

    valid  = ['placed', 'preparing', 'ready', 'delivered']
    if status in valid:
        order.order_status = status
        db.session.commit()
        flash(f'Order #{order_id} status updated to {status}.', 'success')
    else:
        flash('Invalid status.', 'danger')

    return redirect(url_for('admin.all_orders'))


# ---------- MENU ITEMS LIST ----------
@admin.route('/menu')
@login_required
@admin_required
def menu_list():
    items      = MenuItem.query.order_by(MenuItem.created_at.desc()).all()
    categories = Category.query.all()
    return render_template('admin/menu_list.html',
                           items=items, categories=categories)


# ---------- ADD MENU ITEM ----------
@admin.route('/menu/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_menu_item():
    categories = Category.query.all()

    if request.method == 'POST':
        name        = request.form.get('name').strip()
        description = request.form.get('description').strip()
        price       = float(request.form.get('price'))
        category_id = int(request.form.get('category_id'))
        is_veg      = request.form.get('is_veg') == 'true'
        time_of_day = request.form.get('time_of_day')
        is_available= request.form.get('is_available') == 'true'

        # Handle image upload
        image_name = 'default_food.jpg'
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                filename   = secure_filename(file.filename)
                image_name = filename
                file.save(os.path.join(
                    current_app.config['UPLOAD_FOLDER'], filename
                ))

        item = MenuItem(
            name        = name,
            description = description,
            price       = price,
            category_id = category_id,
            is_veg      = is_veg,
            time_of_day = time_of_day,
            is_available= is_available,
            image       = image_name
        )
        db.session.add(item)
        db.session.commit()
        flash(f'"{name}" added to menu!', 'success')
        return redirect(url_for('admin.menu_list'))

    return render_template('admin/add_menu_item.html', categories=categories)


# ---------- EDIT MENU ITEM ----------
@admin.route('/menu/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_menu_item(item_id):
    item       = MenuItem.query.get_or_404(item_id)
    categories = Category.query.all()

    if request.method == 'POST':
        item.name        = request.form.get('name').strip()
        item.description = request.form.get('description').strip()
        item.price       = float(request.form.get('price'))
        item.category_id = int(request.form.get('category_id'))
        item.is_veg      = request.form.get('is_veg') == 'true'
        item.time_of_day = request.form.get('time_of_day')
        item.is_available= request.form.get('is_available') == 'true'

        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                filename   = secure_filename(file.filename)
                item.image = filename
                file.save(os.path.join(
                    current_app.config['UPLOAD_FOLDER'], filename
                ))

        db.session.commit()
        flash(f'"{item.name}" updated successfully!', 'success')
        return redirect(url_for('admin.menu_list'))

    return render_template('admin/edit_menu_item.html',
                           item=item, categories=categories)


# ---------- DELETE MENU ITEM ----------
@admin.route('/menu/delete/<int:item_id>')
@login_required
@admin_required
def delete_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash(f'"{item.name}" deleted from menu.', 'info')
    return redirect(url_for('admin.menu_list'))


# ---------- MANAGE CATEGORIES ----------
@admin.route('/categories', methods=['GET', 'POST'])
@login_required
@admin_required
def categories():
    if request.method == 'POST':
        name = request.form.get('name').strip()
        if name:
            existing = Category.query.filter_by(name=name).first()
            if existing:
                flash('Category already exists.', 'warning')
            else:
                cat = Category(name=name)
                db.session.add(cat)
                db.session.commit()
                flash(f'Category "{name}" added!', 'success')
        return redirect(url_for('admin.categories'))

    all_cats = Category.query.all()
    return render_template('admin/categories.html', categories=all_cats)


# ---------- DELETE CATEGORY ----------
@admin.route('/categories/delete/<int:cat_id>')
@login_required
@admin_required
def delete_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    if cat.items:
        flash('Cannot delete category with existing items.', 'danger')
    else:
        db.session.delete(cat)
        db.session.commit()
        flash(f'Category "{cat.name}" deleted.', 'info')
    return redirect(url_for('admin.categories'))


# ---------- ALL CUSTOMERS ----------
@admin.route('/customers')
@login_required
@admin_required
def customers():
    all_users = User.query.filter_by(role='customer').all()
    return render_template('admin/customers.html', customers=all_users)