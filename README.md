# Chief Elite BD - Account Management System

A comprehensive web application for managing user accounts, digital services, and invoice generation.

## Features

- **User Management**: Registration, login, profile management
- **Service Management**: Multiple digital services (Facebook, Gmail, etc.)
- **Stock Management**: Track available items for each service
- **Admin Panel**: Complete control over users, services, and pricing
- **Invoice Generation**: Professional invoices with image download
- **Fund Management**: User balance and transaction tracking
- **Chat System**: Customer support communication

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export DATABASE_URL="your_database_url"
export SESSION_SECRET="your_secret_key"
```

3. Run the application:
```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

4. Create admin user:
```bash
python create_admin.py
```

5. Setup initial data:
```bash
python add_services.py
python add_sample_stock.py
```

## Project Structure

- `main.py` - Application entry point
- `app.py` - Flask application setup
- `models.py` - Database models
- `routes.py` - User routes
- `admin_routes.py` - Admin panel routes
- `forms.py` - WTForms definitions
- `utils.py` - Utility functions
- `templates/` - HTML templates
- `static/` - CSS, JS, images

## Key Components

### Invoice System
- Generate professional invoices for users
- Download invoices as PNG images
- Include company branding and user details

### Admin Features
- User management with role-based access
- Service and pricing management
- Stock item tracking
- Fund request processing
- Invoice generation and settings

### User Features
- Account dashboard
- Service browsing and checking
- Fund requests
- Order history
- Profile management

## Database Models

- User, Role - User management
- Service, ServiceCategory - Service organization
- StockItem, CheckedItem - Inventory tracking
- FundRequest, FundTransaction - Financial management
- Post, PostComment, PostLike - Content system
- OtherOrder, OtherOrderType - Custom orders

## Technologies Used

- **Backend**: Flask, SQLAlchemy, WTForms
- **Frontend**: Bootstrap 5, jQuery, Font Awesome
- **Database**: PostgreSQL
- **Image Generation**: html2canvas
- **Authentication**: Flask-Login

## License

Private project for Chief Elite BD