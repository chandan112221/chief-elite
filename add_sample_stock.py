"""
Script to add sample stock items to the database for testing
"""
from app import app, db
from models import Service, StockItem
from datetime import datetime, timedelta
import random

def add_sample_stock_items():
    """
    Add sample stock items for each service
    """
    with app.app_context():
        # Get all services
        facebook = Service.query.filter_by(name="Facebook").first()
        gmail = Service.query.filter_by(name="Gmail").first()
        linkedin = Service.query.filter_by(name="LinkedIn").first()
        webmail = Service.query.filter_by(name="Webmail").first()
        edumail = Service.query.filter_by(name="Edu Mail").first()
        outlook = Service.query.filter_by(name="Outlook").first()
        
        if not facebook or not gmail or not linkedin or not webmail or not edumail or not outlook:
            print("Error: Not all required services exist in the database")
            return
        
        # Sample stock items for Facebook - New
        fb_new_items = [
            {
                "name": "John Smith",
                "mail": "johnsmith@example.com",
                "password": "password123",
                "profile_link": "https://facebook.com/johnsmith",
                "is_old": False,
                "rate": 20.00
            },
            {
                "name": "Sarah Johnson",
                "mail": "sarahj@example.com",
                "password": "securepass456",
                "profile_link": "https://facebook.com/sarahjohnson",
                "is_old": False,
                "rate": 22.50
            }
        ]
        
        # Sample stock items for Facebook - Old
        fb_old_items = [
            {
                "name": "Michael Brown",
                "mail": "mikebrown@example.com",
                "password": "brownpass789",
                "profile_link": "https://facebook.com/mikebrown",
                "two_factor": "recovery_code_12345",
                "is_old": True,
                "rate": 15.00
            }
        ]
        
        # Sample stock items for Gmail - One Time
        gmail_items = [
            {
                "mail": "testuser@gmail.com",
                "password": "gmailpass123",
                "recovery_mail": "recovery@example.com",
                "is_old": False,
                "rate": 18.00
            },
            {
                "mail": "business@gmail.com",
                "password": "businessacc456",
                "recovery_mail": "recovery2@example.com",
                "is_old": False,
                "rate": 19.50
            }
        ]
        
        # Sample stock items for Gmail - Old
        gmail_old_items = [
            {
                "mail": "oldaccount@gmail.com",
                "password": "oldpass123",
                "recovery_mail": "oldrecovery@example.com",
                "is_old": True,
                "rate": 12.00
            }
        ]
        
        # Sample stock items for LinkedIn
        linkedin_items = [
            {
                "name": "Professional User",
                "mail": "professional@example.com",
                "password": "propass123",
                "profile_link": "https://linkedin.com/in/professional",
                "is_old": False,
                "rate": 30.00
            }
        ]
        
        # Sample stock items for LinkedIn - Old
        linkedin_old_items = [
            {
                "name": "Corporate User",
                "mail": "corporate@example.com",
                "password": "corppass456",
                "profile_link": "https://linkedin.com/in/corporate",
                "two_factor": "recovery_code_67890",
                "is_old": True,
                "rate": 25.00
            }
        ]
        
        # Sample stock items for Webmail
        webmail_items = [
            {
                "mail": "user@webmail.com",
                "password": "webmailpass123",
                "rate": 10.00
            },
            {
                "mail": "staff@company.org",
                "password": "staffpass456",
                "rate": 10.50
            }
        ]
        
        # Sample stock items for Edu Mail
        edumail_items = [
            {
                "mail": "student@university.edu",
                "password": "student123",
                "rate": 25.00
            },
            {
                "mail": "professor@college.edu",
                "password": "professor456",
                "rate": 27.50
            }
        ]
        
        # Sample stock items for Outlook - One Time
        outlook_items = [
            {
                "mail": "user@outlook.com",
                "password": "outlookpass123",
                "recovery_mail": "recov1@example.com",
                "is_old": False,
                "rate": 12.00
            }
        ]
        
        # Sample stock items for Outlook - Old
        outlook_old_items = [
            {
                "mail": "olduser@outlook.com",
                "password": "oldoutlook456",
                "recovery_mail": "oldrecov@example.com",
                "is_old": True,
                "rate": 8.00
            }
        ]
        
        # Function to create stock items
        def create_stock_items(service, items_list):
            created_count = 0
            for item_data in items_list:
                item = StockItem()
                item.service_id = service.id
                
                if "name" in item_data:
                    item.name = item_data["name"]
                
                if "mail" in item_data:
                    item.mail = item_data["mail"]
                
                if "password" in item_data:
                    item.password = item_data["password"]
                
                if "profile_link" in item_data:
                    item.profile_link = item_data["profile_link"]
                
                if "recovery_mail" in item_data:
                    item.recovery_mail = item_data["recovery_mail"]
                
                if "two_factor" in item_data:
                    item.two_factor = item_data["two_factor"]
                
                item.rate = item_data.get("rate", service.rate)
                item.is_old = item_data.get("is_old", False)
                
                # Set created date for old items
                if item.is_old:
                    days_old = random.randint(30, 365)
                    item.created_date = datetime.utcnow() - timedelta(days=days_old)
                
                db.session.add(item)
                created_count += 1
            
            return created_count
        
        # Create all stock items
        counts = {
            "Facebook (New)": create_stock_items(facebook, fb_new_items),
            "Facebook (Old)": create_stock_items(facebook, fb_old_items),
            "Gmail (One Time)": create_stock_items(gmail, gmail_items),
            "Gmail (Old)": create_stock_items(gmail, gmail_old_items),
            "LinkedIn (One Time)": create_stock_items(linkedin, linkedin_items),
            "LinkedIn (Old)": create_stock_items(linkedin, linkedin_old_items),
            "Webmail": create_stock_items(webmail, webmail_items),
            "Edu Mail": create_stock_items(edumail, edumail_items),
            "Outlook (One Time)": create_stock_items(outlook, outlook_items),
            "Outlook (Old)": create_stock_items(outlook, outlook_old_items)
        }
        
        # Commit all changes
        db.session.commit()
        
        # Print results
        total = sum(counts.values())
        print(f"Added {total} sample stock items:")
        for category, count in counts.items():
            print(f"- {category}: {count} items")

if __name__ == "__main__":
    add_sample_stock_items()