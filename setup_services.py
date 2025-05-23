"""
Script to set up required service categories and services for the stock system
"""
from app import app, db
from models import ServiceCategory, Service

def setup_required_services():
    """
    Set up the required service categories and services
    """
    print("Setting up required services for stock system...")
    
    # Create service categories if they don't exist
    # We're using just one category for simplicity
    social_media_category = ServiceCategory.query.filter_by(name="Social Media").first()
    if not social_media_category:
        social_media_category = ServiceCategory(name="Social Media", description="Social media related services")
        db.session.add(social_media_category)
        print("Created 'Social Media' category")
    
    # Create services if they don't exist
    # Define our required services
    required_services = [
        {
            "name": "Facebook",
            "description": "Facebook accounts",
            "category": social_media_category,
            "rate": 100.0,
            "validity": "Lifetime"
        },
        {
            "name": "Gmail",
            "description": "Gmail accounts",
            "category": social_media_category,
            "rate": 120.0,
            "validity": "Lifetime"
        },
        {
            "name": "LinkedIn",
            "description": "LinkedIn accounts",
            "category": social_media_category,
            "rate": 150.0,
            "validity": "Lifetime"
        },
        {
            "name": "Webmail",
            "description": "Webmail accounts",
            "category": social_media_category,
            "rate": 90.0,
            "validity": "Lifetime"
        },
        {
            "name": "Edu Mail",
            "description": "Educational email accounts",
            "category": social_media_category,
            "rate": 180.0,
            "validity": "Lifetime"
        },
        {
            "name": "Outlook",
            "description": "Outlook email accounts",
            "category": social_media_category,
            "rate": 130.0,
            "validity": "Lifetime"
        }
    ]
    
    # Create services if they don't exist
    for service_data in required_services:
        service = Service.query.filter_by(name=service_data["name"]).first()
        if not service:
            service = Service(
                name=service_data["name"],
                description=service_data["description"],
                rate=service_data["rate"],
                validity=service_data["validity"],
                category_id=service_data["category"].id
            )
            db.session.add(service)
            print(f"Created '{service_data['name']}' service")
    
    # Add price list items for different types
    from models import PriceList
    
    # Define price list items
    price_items = [
        # Facebook
        {"service": "Facebook", "type": "New", "rate": 100.0},
        {"service": "Facebook", "type": "Old", "rate": 150.0},
        
        # Gmail
        {"service": "Gmail", "type": "One Time", "rate": 120.0},
        {"service": "Gmail", "type": "Old", "rate": 180.0},
        
        # LinkedIn
        {"service": "LinkedIn", "type": "One Time", "rate": 150.0},
        {"service": "LinkedIn", "type": "Old", "rate": 200.0},
        
        # Webmail
        {"service": "Webmail", "type": "Standard", "rate": 90.0},
        
        # Edu Mail
        {"service": "Edu Mail", "type": "Standard", "rate": 180.0},
        
        # Outlook
        {"service": "Outlook", "type": "One Time", "rate": 130.0},
        {"service": "Outlook", "type": "Old", "rate": 190.0}
    ]
    
    # Add price list items if they don't exist
    for item_data in price_items:
        existing_item = PriceList.query.filter_by(
            service=item_data["service"],
            type=item_data["type"]
        ).first()
        
        if not existing_item:
            price_item = PriceList(
                service=item_data["service"],
                type=item_data["type"],
                rate=item_data["rate"]
            )
            db.session.add(price_item)
            print(f"Created price item: {item_data['service']} - {item_data['type']}")
    
    # Commit all changes
    db.session.commit()
    print("Service setup completed!")

if __name__ == "__main__":
    with app.app_context():
        setup_required_services()