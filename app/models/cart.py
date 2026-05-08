from app import db
from datetime import datetime

class Cart(db.Model):
    __tablename__ = 'cart'

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    menu_item_id= db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    quantity    = db.Column(db.Integer, nullable=False, default=1)
    added_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    menu_item   = db.relationship('MenuItem', backref='cart_items')

    def __repr__(self):
        return f'<Cart user={self.user_id} item={self.menu_item_id}>'