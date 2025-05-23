from app import app, db
from models import *
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_date_format_in_routes():
    """
    Find and replace all PostgreSQL-incompatible date formatting in routes.py
    """
    file_path = 'routes.py'
    
    try:
        # Read the file
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Replace date formats
        modified_content = content.replace(
            "item.created_date.strftime('%Y-%m-%d')", 
            "item.created_date.isoformat().split('T')[0]"
        )
        
        modified_content = modified_content.replace(
            "checked.checked_at.strftime('%Y-%m-%d')", 
            "checked.checked_at.isoformat().split('T')[0]"
        )
        
        modified_content = modified_content.replace(
            "message.created_at.strftime('%Y-%m-%d %H:%M:%S')",
            "message.created_at.isoformat().replace('T', ' ').split('.')[0]"
        )
        
        # Write the file back
        with open(file_path, 'w') as file:
            file.write(modified_content)
        
        logger.info(f"Successfully updated date formats in {file_path}")
        
    except Exception as e:
        logger.error(f"Error updating {file_path}: {str(e)}")

def fix_date_format_in_admin_routes():
    """
    Find and replace all PostgreSQL-incompatible date formatting in admin_routes.py
    """
    file_path = 'admin_routes.py'
    
    try:
        # Read the file
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Replace date formats in admin_routes.py
        modified_content = content.replace(
            "db.func.strftime('%Y-%m', FundTransaction.created_at).label('month')",
            "db.func.to_char(FundTransaction.created_at, 'YYYY-MM').label('month')"
        )
        
        modified_content = modified_content.replace(
            "message.created_at.strftime('%Y-%m-%d %H:%M:%S')",
            "message.created_at.isoformat().replace('T', ' ').split('.')[0]"
        )
        
        # Write the file back
        with open(file_path, 'w') as file:
            file.write(modified_content)
        
        logger.info(f"Successfully updated date formats in {file_path}")
        
    except Exception as e:
        logger.error(f"Error updating {file_path}: {str(e)}")

def fix_date_format_in_utils():
    """
    Find and replace all PostgreSQL-incompatible date formatting in utils.py
    """
    file_path = 'utils.py'
    
    try:
        # Read the file
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Replace date formats in utils.py
        modified_content = content.replace(
            "start_date.strftime('%Y-%m-%d')",
            "start_date.isoformat().split('T')[0]"
        )
        
        modified_content = modified_content.replace(
            "end_date.strftime('%Y-%m-%d')",
            "end_date.isoformat().split('T')[0]"
        )
        
        modified_content = modified_content.replace(
            "datetime.utcnow().strftime('%Y-%m-%d')",
            "datetime.utcnow().isoformat().split('T')[0]"
        )
        
        modified_content = modified_content.replace(
            "datetime.utcnow().strftime('%Y%m%d%H%M')",
            "datetime.utcnow().isoformat().replace('-', '').replace('T', '').replace(':', '')[:12]"
        )
        
        modified_content = modified_content.replace(
            "t.created_at.strftime('%Y-%m-%d %H:%M')",
            "t.created_at.isoformat().replace('T', ' ').split('.')[0]"
        )
        
        # Write the file back
        with open(file_path, 'w') as file:
            file.write(modified_content)
        
        logger.info(f"Successfully updated date formats in {file_path}")
        
    except Exception as e:
        logger.error(f"Error updating {file_path}: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting PostgreSQL compatibility fixes")
    fix_date_format_in_routes()
    fix_date_format_in_admin_routes()
    fix_date_format_in_utils()
    logger.info("Completed PostgreSQL compatibility fixes")