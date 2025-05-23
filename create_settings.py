from app import app, db
from models import WebsiteSetting

with app.app_context():
    # Check if settings already exist
    setting = WebsiteSetting.query.first()
    if setting:
        print("Website settings already exist!")
    else:
        # Create default settings
        setting = WebsiteSetting(
            site_name='Chief Elite BD',
            logo_url='logo.svg',
            primary_color='#007bff',
            secondary_color='#6c757d',
            contact_phone='01856659780',
            contact_email='admin@example.com',
            admin_notice='Welcome to Chief Elite BD!',
            minimum_fund=20.0
        )
        db.session.add(setting)
        db.session.commit()
        print("Website settings created successfully!")