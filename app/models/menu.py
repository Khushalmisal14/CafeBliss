from app import db
from datetime import datetime

class Category(db.Model):
    __tablename__ = 'categories'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    items      = db.relationship('MenuItem', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'


class MenuItem(db.Model):
    __tablename__ = 'menu_items'

    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(150), nullable=False)
    description  = db.Column(db.Text, nullable=True)
    price        = db.Column(db.Float, nullable=False)
    image        = db.Column(db.String(200), default='default_food.jpg')
    is_available = db.Column(db.Boolean, default=True)
    is_veg       = db.Column(db.Boolean, default=True)
    time_of_day  = db.Column(db.String(20), default='all')  # 'morning', 'evening', 'all'
    category_id  = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<MenuItem {self.name}>'