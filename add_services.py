"""
Script to add service categories and services to the database
"""
from app import app, db
from models import ServiceCategory, Service

def add_service_categories_and_services():
    """
    Add required service categories and services to the database
    """
    with app.app_context():
        # Create service categories
        social_media_cat = ServiceCategory.query.filter_by(name="Social Media").first()
        if not social_media_cat:
            social_media_cat = ServiceCategory()
            social_media_cat.name = "Social Media"
            social_media_cat.description = "Social media accounts"
            db.session.add(social_media_cat)
            db.session.commit()
            print(f"Created category: Social Media")
        
        email_cat = ServiceCategory.query.filter_by(name="Email").first()
        if not email_cat:
            email_cat = ServiceCategory()
            email_cat.name = "Email"
            email_cat.description = "Email accounts"
            db.session.add(email_cat)
            db.session.commit()
            print(f"Created category: Email")
        
        # Create services
        services = [
            # Social Media services
            {
                "name": "Facebook",
                "description": "Facebook accounts",
                "rate": 20.0,
                "validity": "Lifetime",
                "category": social_media_cat
            },
            {
                "name": "LinkedIn",
                "description": "LinkedIn premium accounts",
                "rate": 30.0,
                "validity": "30 days",
                "category": social_media_cat
            },
            
            # Email services
            {
                "name": "Gmail",
                "description": "Gmail accounts",
                "rate": 15.0,
                "validity": "Lifetime",
                "category": email_cat
            },
            {
                "name": "Outlook",
                "description": "Outlook email accounts",
                "rate": 12.0,
                "validity": "Lifetime",
                "category": email_cat
            },
            {
                "name": "Webmail",
                "description": "Webmail accounts",
                "rate": 10.0,
                "validity": "Lifetime",
                "category": email_cat
            },
            {
                "name": "Edu Mail",
                "description": "Educational email accounts",
                "rate": 25.0,
                "validity": "1 year",
                "category": email_cat
            }
        ]
        
        for service_data in services:
            service = Service.query.filter_by(name=service_data["name"]).first()
            if not service:
                service = Service()
                service.name = service_data["name"]
                service.description = service_data["description"]
                service.rate = service_data["rate"]
                service.validity = service_data["validity"]
                service.category_id = service_data["category"].id
                db.session.add(service)
                print(f"Created service: {service_data['name']}")
            else:
                print(f"Service already exists: {service_data['name']}")
        
        db.session.commit()
        print("Service categories and services added successfully!")

if __name__ == "__main__":
    add_service_categories_and_services()