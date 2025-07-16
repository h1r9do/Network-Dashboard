"""
Flask routes for VLAN Migration web interface
Integrates with DSR Circuits main application
"""

from flask import Blueprint, render_template, request, jsonify, session
# from flask_login import login_required  # Commented out - not using authentication yet
import sys
sys.path.append('/usr/local/bin/Main')

# Import the API blueprint
from vlan_migration_api import vlan_migration_bp

# Create routes blueprint
vlan_migration_routes = Blueprint('vlan_migration_routes', __name__)

@vlan_migration_routes.route('/vlan-migration')
def vlan_migration():
    """Main VLAN migration page"""
    return render_template('vlan_migration.html')

@vlan_migration_routes.route('/vlan-migration/help')
def vlan_migration_help():
    """Help documentation page"""
    return render_template('vlan_migration_help.html')

# Integration function for dsrcircuits.py
def register_vlan_migration_blueprints(app):
    """Register VLAN migration blueprints with main Flask app"""
    # Register the routes
    app.register_blueprint(vlan_migration_routes)
    
    # Register the API endpoints
    app.register_blueprint(vlan_migration_bp)
    
    print("✓ VLAN Migration module registered")

# Add to navigation menu
VLAN_MIGRATION_NAV_ITEM = {
    'name': 'VLAN Migration',
    'url': '/vlan-migration',
    'icon': 'fa-exchange-alt',
    'description': 'Migrate store networks to new VLAN standards',
    'category': 'network_operations',
    'roles': ['admin', 'network_engineer']
}