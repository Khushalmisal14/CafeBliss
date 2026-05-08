from app import db
from datetime import datetime

class Order(db.Model):
    __tablename__ = 'orders'

    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_amount   = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), default='cash')  # 'cash' or 'online'
    payment_status = db.Column(db.String(20), default='pending')  # 'pending', 'paid', 'failed'
    order_status   = db.Column(db.String(20), default='placed')  # 'placed', 'preparing', 'ready', 'delivered'
    razorpay_id    = db.Column(db.String(100), nullable=True)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    items          = db.relationship('OrderItem', backref='order', lazy=True)

    def __repr__(self):
        return f'<Order {self.id} - {self.order_status}>'


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id          = db.Column(db.Integer, primary_key=True)
    order_id    = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    menu_item_id= db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    quantity    = db.Column(db.Integer, nullable=False, default=1)
    price       = db.Column(db.Float, nullable=False)

    # Relationship
    menu_item   = db.relationship('MenuItem', backref='order_items')

    def __repr__(self):
        return f'<OrderItem {self.menu_item_id} x{self.quantity}>'