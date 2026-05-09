from flask import Flask, render_template 
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from config import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Connect extensions to app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # Where to redirect if user is not logged in
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please login to access this page.'
    login_manager.login_message_category = 'warning'

    # Register blueprints (route groups)
    from app.routes.auth import auth
    from app.routes.customer import customer
    from app.routes.admin import admin
    from app.routes.payment import payment

    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(customer, url_prefix='/')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(payment, url_prefix='/payment')

    # Custom error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('404.html'), 500

    # Create all database tables
    with app.app_context():
        from app.models import User, Category, MenuItem, Order, OrderItem, Cart
        db.create_all()

    return app