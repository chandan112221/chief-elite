# Chief Elite BD - Setup Instructions

## Quick Setup

1. **Install Dependencies:**
```bash
pip install flask flask-login flask-sqlalchemy flask-wtf wtforms email-validator werkzeug gunicorn psycopg2-binary sqlalchemy
```

2. **Set Environment Variables:**
```bash
export DATABASE_URL="postgresql://username:password@host:port/database"
export SESSION_SECRET="your-secret-key-here"
```

3. **Initialize Database:**
```bash
python create_admin.py       # Create admin user
python add_services.py       # Add service categories
python add_sample_stock.py   # Add sample stock items
python create_settings.py    # Create website settings
```

4. **Run Application:**
```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

## Default Admin Login
- Username: admin
- Password: admin123

## Features Ready
✅ User registration and login
✅ Admin panel with full management
✅ Service and stock management
✅ Invoice generation with image download
✅ Fund management system
✅ Chat support system
✅ Professional UI with Bootstrap 5

## File Structure
```
chief_elite_clean/
├── main.py              # Entry point
├── app.py               # Flask setup
├── models.py            # Database models
├── routes.py            # User routes
├── admin_routes.py      # Admin routes
├── forms.py             # Form definitions
├── utils.py             # Helper functions
├── templates/           # HTML templates
├── static/              # CSS, JS, images
├── create_admin.py      # Admin creation script
├── add_services.py      # Service setup script
├── add_sample_stock.py  # Stock setup script
└── create_settings.py   # Settings setup script
```

Ready to deploy! 🚀