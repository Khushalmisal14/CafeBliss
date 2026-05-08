from app import create_app, db
from app.models.menu import Category, MenuItem

app = create_app()

with app.app_context():
    # Create categories
    categories = ['Coffee & Drinks', 'Snacks', 'Meals', 'Desserts', 'Combos']
    cat_objects = {}

    for name in categories:
        existing = Category.query.filter_by(name=name).first()
        if not existing:
            cat = Category(name=name)
            db.session.add(cat)
            db.session.flush()
            cat_objects[name] = cat
        else:
            cat_objects[name] = existing

    db.session.commit()

    # Create menu items
    items = [
        {'name': 'Cappuccino',      'price': 120, 'category': 'Coffee & Drinks',
         'desc': 'Rich espresso with steamed milk foam', 'veg': True,  'time': 'morning'},
        {'name': 'Cold Coffee',     'price': 100, 'category': 'Coffee & Drinks',
         'desc': 'Chilled blended coffee delight',       'veg': True,  'time': 'all'},
        {'name': 'Masala Chai',     'price': 40,  'category': 'Coffee & Drinks',
         'desc': 'Traditional spiced Indian tea',        'veg': True,  'time': 'morning'},
        {'name': 'Veg Sandwich',    'price': 80,  'category': 'Snacks',
         'desc': 'Grilled sandwich with fresh veggies',  'veg': True,  'time': 'all'},
        {'name': 'Chicken Burger',  'price': 150, 'category': 'Snacks',
         'desc': 'Juicy chicken patty burger',           'veg': False, 'time': 'all'},
        {'name': 'Paneer Wrap',     'price': 120, 'category': 'Snacks',
         'desc': 'Spicy paneer in a soft wrap',          'veg': True,  'time': 'all'},
        {'name': 'Veg Fried Rice',  'price': 140, 'category': 'Meals',
         'desc': 'Wok-tossed rice with vegetables',      'veg': True,  'time': 'evening'},
        {'name': 'Chicken Biryani', 'price': 200, 'category': 'Meals',
         'desc': 'Fragrant basmati rice with chicken',   'veg': False, 'time': 'evening'},
        {'name': 'Brownie',         'price': 90,  'category': 'Desserts',
         'desc': 'Warm chocolate brownie with ice cream','veg': True,  'time': 'all'},
        {'name': 'Cheesecake',      'price': 130, 'category': 'Desserts',
         'desc': 'Classic New York style cheesecake',    'veg': True,  'time': 'all'},
        {'name': 'Coffee + Snack Combo', 'price': 180, 'category': 'Combos',
         'desc': 'Cold coffee + veg sandwich deal',      'veg': True,  'time': 'all'},
        {'name': 'Meal Deal',       'price': 280, 'category': 'Combos',
         'desc': 'Fried rice + drink + dessert',         'veg': True,  'time': 'evening'},
    ]

    for item_data in items:
        existing = MenuItem.query.filter_by(name=item_data['name']).first()
        if not existing:
            item = MenuItem(
                name        = item_data['name'],
                price       = item_data['price'],
                description = item_data['desc'],
                category_id = cat_objects[item_data['category']].id,
                is_veg      = item_data['veg'],
                time_of_day = item_data['time'],
                is_available= True
            )
            db.session.add(item)

    db.session.commit()
    print('✅ Sample data added successfully!')