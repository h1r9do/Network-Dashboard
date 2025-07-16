"""
MAIN APPLICATION ENTRY POINT
============================

Purpose:
    - Main Flask application entry point and configuration
    - Registers all modular blueprints
    - Handles app-wide configuration and initialization

Pages Served:
    - Coordinates all pages through registered blueprints
    - No direct page serving

Dependencies:
    - dsrcircuits.py (main circuits page and Meraki integration)
    - status.py (dashboard and circuit orders pages)
    - historical.py (change log and historical analysis)
    - inventory.py (inventory summary and details pages)
    - reports.py (daily circuit enablement reports)
    - utils.py (shared utilities and data processing functions)

Templates Used:
    - None directly (delegates to blueprints)

API Endpoints:
    - None directly (delegates to blueprints)

Key Functions:
    - App initialization and configuration
    - Blueprint registration
    - Global error handling
    - Shared static/template folder configuration

File Structure:
    main.py              <- This file (entry point)
    dsrcircuits.py       <- Main circuits page + Meraki integration
    status.py            <- Dashboard and circuit orders
    historical.py        <- Historical data and change logs
    inventory.py         <- Inventory management
    reports.py           <- Daily circuit enablement reports
    utils.py             <- Shared utilities and data processing
    templates/           <- All HTML templates
    static/              <- Static assets (CSS, JS, images)
"""

from flask import Flask
import os
import sys

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all blueprint modules
from dsrcircuits import dsrcircuits_bp
from status import status_bp
from historical import historical_bp
from inventory import inventory_bp
from reports import reports_bp

def create_app():
    """
    Create and configure the Flask application
    
    Returns:
        Flask app instance with all blueprints registered
    """
    # Initialize Flask app with shared template and static folders
    app = Flask(__name__, 
                template_folder="/usr/local/bin/templates", 
                static_folder="/usr/local/bin/static")
    
    # App configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Register all blueprints
    app.register_blueprint(dsrcircuits_bp)
    app.register_blueprint(status_bp)
    app.register_blueprint(historical_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(reports_bp)  # NEW: Circuit enablement reports
    
    # Global error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return "Page not found", 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return "Internal server error", 500
    
    return app

# Create app instance
app = create_app()

if __name__ == "__main__":
    print("🚀 Starting DSR Circuits Flask App")
    print("📂 Template Directory: /usr/local/bin/templates")
    print("📂 Static Directory: /usr/local/bin/static")
    
    # Print data directory status
    from utils import DATA_DIR, TRACKING_DATA_DIR
    print(f"📂 Data Directory: {DATA_DIR}")
    print(f"📂 Tracking Directory: {TRACKING_DATA_DIR}")
    
    if not os.path.exists(DATA_DIR):
        print(f"⚠️  Warning: Data directory {DATA_DIR} does not exist")
    if not os.path.exists(TRACKING_DATA_DIR):
        print(f"⚠️  Warning: Tracking directory {TRACKING_DATA_DIR} does not exist")
    
    # Check Meraki functions availability
    from utils import MERAKI_FUNCTIONS_AVAILABLE
    print(f"🔧 Meraki Functions Available: {MERAKI_FUNCTIONS_AVAILABLE}")
    
    print("📈 Circuit Enablement Reports: Available")
    
    app.run(host="0.0.0.0", port=5052, debug=False)