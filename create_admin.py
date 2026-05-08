from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    # Check if admin already exists
    admin = User.query.filter_by(email='admin@cafebliss.com').first()
    if not admin:
        admin = User(
            name        = 'CafeBliss Admin',
            email       = 'admin@cafebliss.com',
            mobile      = '9999999999',
            role        = 'admin',
            is_verified = True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('✅ Admin created successfully!')
        print('Email: admin@cafebliss.com')
        print('Password: admin123')
    else:
        print('Admin already exists.')