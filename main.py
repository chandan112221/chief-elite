import os
import logging
from app import app, db
from routes import *
from admin_routes import *

# Configure logging
logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
