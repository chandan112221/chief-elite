"""
Script to remove all existing services and categories
"""
from app import app, db
from models import ServiceCategory, Service, StockItem

def remove_all_services():
    """
    Remove all services, categories, and stock items from the database
    """
    with app.app_context():
        # First remove all stock items
        try:
            stock_count = StockItem.query.count()
            print(f"Deleting {stock_count} stock items...")
            StockItem.query.delete()
            db.session.commit()
            print("All stock items deleted successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting stock items: {str(e)}")
        
        # Then remove all services
        try:
            service_count = Service.query.count()
            print(f"Deleting {service_count} services...")
            Service.query.delete()
            db.session.commit()
            print("All services deleted successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting services: {str(e)}")
        
        # Finally remove all categories
        try:
            category_count = ServiceCategory.query.count()
            print(f"Deleting {category_count} service categories...")
            ServiceCategory.query.delete()
            db.session.commit()
            print("All service categories deleted successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting service categories: {str(e)}")
        
        print("Database cleanup complete.")

if __name__ == "__main__":
    remove_all_services()