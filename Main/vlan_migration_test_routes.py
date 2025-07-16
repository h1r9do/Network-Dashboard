"""
Flask routes for VLAN Migration Test interface
"""

from flask import Blueprint, render_template

# Import the test API blueprint
from vlan_migration_test_api import vlan_migration_test_bp

# Create routes blueprint
vlan_migration_test_routes = Blueprint('vlan_migration_test_routes', __name__)

@vlan_migration_test_routes.route('/vlan-migration-test')
def vlan_migration_test():
    """Test page for TST 01 VLAN migration"""
    return render_template('vlan_migration_test.html')