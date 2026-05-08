from app.models.menu import MenuItem, Category
from app.models.order import Order
from datetime import datetime


# ─────────────────────────────────────────────
#  KNOWLEDGE BASE — cafe information
# ─────────────────────────────────────────────
CAFE_INFO = {
    'name'    : 'CafeBliss',
    'timings' : '8:00 AM to 10:00 PM, all days',
    'location': 'Main Street, City Center',
    'phone'   : '+91 99999 99999',
    'email'   : 'support@cafebliss.com',
    'wifi'    : 'Yes, free WiFi available',
    'parking' : 'Yes, parking available nearby',
}


# ─────────────────────────────────────────────
#  KEYWORD MATCHER
#  Checks if any keyword exists in user message
# ─────────────────────────────────────────────
def contains(message, keywords):
    message = message.lower()
    return any(word in message for word in keywords)


# ─────────────────────────────────────────────
#  MAIN CHATBOT FUNCTION
#  Takes user message + optional user_id
#  Returns a response string
# ─────────────────────────────────────────────
def get_chatbot_response(message, user_id=None):
    message = message.strip()

    if not message:
        return "Please type a message so I can help you! 😊"

    msg = message.lower()

    # ── Greetings ──
    if contains(msg, ['hi', 'hello', 'hey', 'good morning',
                      'good evening', 'good afternoon', 'namaste']):
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        return (f"{greeting}! 👋 Welcome to CafeBliss! "
                f"I'm your AI assistant. How can I help you today?\n\n"
                f"You can ask me about:\n"
                f"• Our menu items 🍽️\n"
                f"• Cafe timings ⏰\n"
                f"• Your orders 📋\n"
                f"• Payments 💳\n"
                f"• Recommendations 🤖")

    # ── Timings ──
    if contains(msg, ['time', 'timing', 'open', 'close',
                      'hours', 'when', 'schedule']):
        return (f"⏰ CafeBliss is open:\n"
                f"**{CAFE_INFO['timings']}**\n\n"
                f"We are open 7 days a week including weekends "
                f"and holidays! ☕")

    # ── Location ──
    if contains(msg, ['location', 'address', 'where', 'direction',
                      'find', 'place', 'situated']):
        return (f"📍 We are located at:\n"
                f"**{CAFE_INFO['location']}**\n\n"
                f"🚗 Parking is available nearby.\n"
                f"📞 Call us: {CAFE_INFO['phone']}")

    # ── Contact ──
    if contains(msg, ['contact', 'phone', 'call', 'number',
                      'email', 'reach', 'support']):
        return (f"📞 Phone: {CAFE_INFO['phone']}\n"
                f"📧 Email: {CAFE_INFO['email']}\n\n"
                f"Our support team is available during cafe hours. "
                f"We typically reply within 1 hour! 😊")

    # ── WiFi ──
    if contains(msg, ['wifi', 'wi-fi', 'internet', 'network', 'password']):
        return ("📶 Yes! Free WiFi is available at CafeBliss.\n\n"
                "Ask our staff for the WiFi password when you visit. "
                "Enjoy browsing while sipping your coffee! ☕")

    # ── Menu — general ──
    if contains(msg, ['menu', 'items', 'food', 'eat',
                      'drink', 'available', 'serve', 'offer']):
        try:
            categories = Category.query.all()
            if categories:
                cat_names = ', '.join([c.name for c in categories])
                total     = MenuItem.query.filter_by(is_available=True).count()
                return (f"🍽️ We have {total} delicious items across "
                        f"these categories:\n\n"
                        f"**{cat_names}**\n\n"
                        f"Visit our Menu page to see all items, "
                        f"filter by category, and add to cart! 🛒")
            else:
                return ("🍽️ Our menu is being updated. "
                        "Please check back soon!")
        except:
            return ("🍽️ We serve a wide variety of food and drinks. "
                    "Please visit our Menu page to explore! 😊")

    # ── Specific item search ──
    if contains(msg, ['price', 'cost', 'how much', 'rate',
                      'cheap', 'expensive']):
        try:
            # Try to find a specific item name in the message
            items = MenuItem.query.filter_by(is_available=True).all()
            found = []
            for item in items:
                if item.name.lower() in msg:
                    found.append(f"• {item.name}: ₹{item.price}")

            if found:
                return ("💰 Here are the prices:\n\n" +
                        '\n'.join(found))
            else:
                # Give price range
                prices = [i.price for i in items]
                if prices:
                    return (f"💰 Our items range from "
                            f"₹{min(prices):.0f} to ₹{max(prices):.0f}.\n\n"
                            f"Visit the Menu page to see individual prices! 😊")
                return "Please visit our Menu page for pricing details."
        except:
            return "Please visit our Menu page for pricing details. 😊"

    # ── Veg / Non-veg ──
    if contains(msg, ['veg', 'vegetarian', 'non veg', 'nonveg',
                      'chicken', 'meat', 'paneer']):
        try:
            veg_count    = MenuItem.query.filter_by(
                is_available=True, is_veg=True).count()
            nonveg_count = MenuItem.query.filter_by(
                is_available=True, is_veg=False).count()
            return (f"🌿 We have **{veg_count} vegetarian** items and "
                    f"**{nonveg_count} non-vegetarian** items.\n\n"
                    f"You can filter by type on our Menu page! 😊")
        except:
            return ("We have both veg and non-veg options. "
                    "Check our Menu page for details! 🌿🍖")

    # ── Order status ──
    if contains(msg, ['order', 'status', 'my order',
                      'where is', 'track', 'placed']):
        if user_id:
            try:
                last_order = Order.query.filter_by(
                    user_id=user_id
                ).order_by(Order.created_at.desc()).first()

                if last_order:
                    return (f"📋 Your last order #{last_order.id}:\n\n"
                            f"• Status: **{last_order.order_status.title()}**\n"
                            f"• Amount: ₹{last_order.total_amount}\n"
                            f"• Payment: {last_order.payment_status.title()}\n"
                            f"• Date: "
                            f"{last_order.created_at.strftime('%d %b, %I:%M %p')}\n\n"
                            f"Visit My Orders page to see all orders! 📦")
                else:
                    return ("You haven't placed any orders yet! 😊\n\n"
                            "Browse our Menu and place your first order. "
                            "We'd love to serve you! ☕")
            except:
                return ("Please visit the My Orders page "
                        "to check your order status. 📋")
        else:
            return ("Please login to check your order status. 🔐\n\n"
                    "After logging in, visit My Orders page "
                    "or ask me again!")

    # ── Payment ──
    if contains(msg, ['pay', 'payment', 'cash', 'online',
                      'razorpay', 'upi', 'card', 'refund']):
        return ("💳 We accept the following payment methods:\n\n"
                "• 💵 **Cash** — Pay at the counter\n"
                "• 💳 **Online** — Razorpay (UPI, Cards, Net Banking)\n\n"
                "For refunds, please contact us at "
                f"{CAFE_INFO['email']} 😊")

    # ── Recommendations ──
    if contains(msg, ['recommend', 'suggest', 'best', 'popular',
                      'favourite', 'top', 'special', 'try']):
        return ("🤖 Great question! Our AI can give you personalised "
                "food recommendations based on:\n\n"
                "• ⏰ Time of day\n"
                "• 🔥 Most popular items\n"
                "• 💡 Your past orders\n"
                "• 💰 Your budget\n\n"
                "Click **AI Picks** in the navbar to get "
                "your personalised suggestions! 😊")

    # ── Combo / Offers ──
    if contains(msg, ['combo', 'offer', 'deal', 'discount',
                      'coupon', 'save', 'bundle']):
        try:
            from app.models.menu import Category
            combo_cat = Category.query.filter(
                Category.name.ilike('%combo%')
            ).first()
            if combo_cat:
                combos = MenuItem.query.filter_by(
                    category_id  = combo_cat.id,
                    is_available = True
                ).all()
                if combos:
                    combo_list = '\n'.join(
                        [f"• {c.name}: ₹{c.price}" for c in combos]
                    )
                    return (f"🎯 Our current combo deals:\n\n"
                            f"{combo_list}\n\n"
                            f"Great value for money! 😊")
            return ("🎯 We have special combo deals available!\n\n"
                    "Check the **Combos** category on our Menu page "
                    "for the best deals! 💰")
        except:
            return ("Check our Menu page for current combo deals! 🎯")

    # ── Delivery ──
    if contains(msg, ['deliver', 'delivery', 'home delivery',
                      'takeaway', 'take away', 'parcel', 'zomato',
                      'swiggy']):
        return ("🛵 Currently we offer:\n\n"
                "• 🏪 **Dine-in** at our cafe\n"
                "• 📦 **Takeaway** — order online and pick up\n\n"
                "Home delivery coming soon! Stay tuned. 😊\n"
                f"For large orders call: {CAFE_INFO['phone']}")

    # ── Table booking ──
    if contains(msg, ['book', 'table', 'reserve', 'reservation',
                      'seat', 'booking']):
        return (f"📅 For table reservations please:\n\n"
                f"📞 Call us: {CAFE_INFO['phone']}\n"
                f"📧 Email: {CAFE_INFO['email']}\n\n"
                f"We recommend booking in advance for "
                f"weekends and evenings! 😊")

    # ── Thanks ──
    if contains(msg, ['thank', 'thanks', 'thankyou', 'great',
                      'awesome', 'perfect', 'helpful']):
        return ("You're welcome! 😊☕\n\n"
                "We're always happy to help. "
                "Enjoy your experience at CafeBliss!\n"
                "Is there anything else I can help you with?")

    # ── Bye ──
    if contains(msg, ['bye', 'goodbye', 'see you', 'cya',
                      'take care', 'later']):
        return ("Goodbye! 👋 Thank you for visiting CafeBliss.\n\n"
                "We hope to serve you soon! "
                "Have a wonderful day! ☕🌟")

    # ── Default fallback ──
    return (f"I'm not sure I understood that. 🤔\n\n"
            f"I can help you with:\n"
            f"• Menu & prices 🍽️\n"
            f"• Cafe timings & location ⏰📍\n"
            f"• Your order status 📋\n"
            f"• Payment options 💳\n"
            f"• Recommendations 🤖\n"
            f"• Combos & offers 🎯\n\n"
            f"Please try asking something from the list above, "
            f"or contact us at {CAFE_INFO['email']} 😊")