from datetime import datetime
from app.models.menu import MenuItem
from app.models.order import Order, OrderItem
from app.models.cart import Cart
from app import db


# ─────────────────────────────────────────────
#  HELPER — fetch all available menu items
# ─────────────────────────────────────────────
def get_available_items():
    return MenuItem.query.filter_by(is_available=True).all()


# ─────────────────────────────────────────────
#  1. TIME-BASED RECOMMENDATIONS
#     Morning  → breakfast/coffee items
#     Evening  → meals/snacks
#     All day  → always included
# ─────────────────────────────────────────────
def get_time_based_recommendations(limit=4):
    hour = datetime.now().hour

    if 5 <= hour < 12:
        time_slot = 'morning'
    elif 12 <= hour < 17:
        time_slot = 'all'
    else:
        time_slot = 'evening'

    items = MenuItem.query.filter(
        MenuItem.is_available == True,
        MenuItem.time_of_day.in_([time_slot, 'all'])
    ).limit(limit).all()

    return items


# ─────────────────────────────────────────────
#  2. POPULAR ITEMS (most ordered globally)
# ─────────────────────────────────────────────
def get_popular_items(limit=4):
    # Join OrderItem with MenuItem, sum quantities, sort descending
    results = db.session.query(
        MenuItem,
        db.func.sum(OrderItem.quantity).label('total_ordered')
    ).join(
        OrderItem, MenuItem.id == OrderItem.menu_item_id
    ).filter(
        MenuItem.is_available == True
    ).group_by(
        MenuItem.id
    ).order_by(
        db.text('total_ordered DESC')
    ).limit(limit).all()

    # If no orders yet, return random available items
    if not results:
        return MenuItem.query.filter_by(is_available=True).limit(limit).all()

    return [r[0] for r in results]


# ─────────────────────────────────────────────
#  3. PERSONALIZED — based on past orders
#     Recommends items from categories the
#     customer has ordered from before
# ─────────────────────────────────────────────
def get_personalized_recommendations(user_id, limit=4):
    # Get categories the user has ordered from
    past_orders = db.session.query(
        MenuItem.category_id
    ).join(
        OrderItem, MenuItem.id == OrderItem.menu_item_id
    ).join(
        Order, Order.id == OrderItem.order_id
    ).filter(
        Order.user_id == user_id
    ).distinct().all()

    if not past_orders:
        # New customer — return popular items instead
        return get_popular_items(limit)

    category_ids = [row[0] for row in past_orders]

    # Get items from those categories not recently ordered
    recently_ordered_ids = db.session.query(
        OrderItem.menu_item_id
    ).join(
        Order, Order.id == OrderItem.order_id
    ).filter(
        Order.user_id == user_id
    ).all()

    recent_ids = [r[0] for r in recently_ordered_ids]

    # Suggest items from same categories but not recently ordered
    items = MenuItem.query.filter(
        MenuItem.is_available   == True,
        MenuItem.category_id.in_(category_ids),
        ~MenuItem.id.in_(recent_ids)
    ).limit(limit).all()

    # If all items already ordered, suggest popular ones
    if not items:
        items = get_popular_items(limit)

    return items


# ─────────────────────────────────────────────
#  4. BUDGET-BASED RECOMMENDATIONS
#     Filter items within the customer's budget
# ─────────────────────────────────────────────
def get_budget_recommendations(budget, limit=4):
    items = MenuItem.query.filter(
        MenuItem.is_available == True,
        MenuItem.price        <= budget
    ).order_by(
        MenuItem.price.desc()   # Best value within budget
    ).limit(limit).all()

    return items


# ─────────────────────────────────────────────
#  5. SMART COMBO SUGGESTIONS
#     Pair a drink with a snack/meal
#     that fits within a combined budget
# ─────────────────────────────────────────────
def get_combo_suggestions(limit=3):
    # Get combo category items
    combos = MenuItem.query.join(
        MenuItem.category
    ).filter(
        MenuItem.is_available == True,
        db.text("categories.name LIKE '%Combo%'")
    ).limit(limit).all()

    if combos:
        return combos

    # Fallback: manually build drink + snack pairs
    from app.models.menu import Category

    drink_cat = Category.query.filter(
        Category.name.ilike('%drink%')
    ).first() or Category.query.filter(
        Category.name.ilike('%coffee%')
    ).first()

    snack_cat = Category.query.filter(
        Category.name.ilike('%snack%')
    ).first()

    suggestions = []

    if drink_cat:
        drink = MenuItem.query.filter_by(
            category_id  = drink_cat.id,
            is_available = True
        ).first()
        if drink:
            suggestions.append(drink)

    if snack_cat:
        snack = MenuItem.query.filter_by(
            category_id  = snack_cat.id,
            is_available = True
        ).first()
        if snack:
            suggestions.append(snack)

    return suggestions


# ─────────────────────────────────────────────
#  6. PERSONALISED OFFERS
#     Give discount hint to loyal customers
#     (those with 3+ orders)
# ─────────────────────────────────────────────
def get_personalized_offer(user_id):
    order_count = Order.query.filter_by(user_id=user_id).count()

    if order_count == 0:
        return {
            'type'   : 'welcome',
            'message': '🎉 Welcome! Enjoy exploring our menu.',
            'discount': 0
        }
    elif order_count < 3:
        return {
            'type'   : 'new',
            'message': f'You have placed {order_count} order(s). '
                       f'Place {3 - order_count} more to unlock a loyalty offer!',
            'discount': 0
        }
    elif order_count < 10:
        return {
            'type'   : 'loyal',
            'message': f'🌟 Loyal customer! You have {order_count} orders. '
                        'Show this to the counter for a free cookie! 🍪',
            'discount': 10
        }
    else:
        return {
            'type'   : 'vip',
            'message': f'👑 VIP Customer! {order_count} orders and counting. '
                        'You get 15% off on your next order!',
            'discount': 15
        }


# ─────────────────────────────────────────────
#  MASTER FUNCTION
#  Returns all recommendations in one call
# ─────────────────────────────────────────────
def get_all_recommendations(user_id, budget=None):
    recommendations = {
        'time_based'   : get_time_based_recommendations(limit=4),
        'popular'      : get_popular_items(limit=4),
        'personalized' : get_personalized_recommendations(user_id, limit=4),
        'combos'       : get_combo_suggestions(limit=3),
        'offer'        : get_personalized_offer(user_id),
        'budget'       : []
    }

    if budget:
        recommendations['budget'] = get_budget_recommendations(budget, limit=4)

    return recommendations