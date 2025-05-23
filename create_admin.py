from app import app, db
from models import User

with app.app_context():
    # Check if admin already exists
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print("Admin user already exists!")
    else:
        # Create the admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            full_name='Admin User',
            is_admin=True,
            role_id=1,
            is_active=True,
            balance=1000.0  # Give admin some balance
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")