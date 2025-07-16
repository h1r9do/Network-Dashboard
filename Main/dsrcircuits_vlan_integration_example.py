"""
Example code snippet showing how to integrate VLAN migration into dsrcircuits.py
Add these sections to your existing dsrcircuits.py file
"""

# ============================================
# SECTION 1: Add imports at the top of dsrcircuits.py
# ============================================

# Add these imports with your other imports
from vlan_migration_routes import register_vlan_migration_blueprints
from vlan_migration_api import vlan_migration_bp
from vlan_migration_models import (
    VlanMigrationHistory, 
    VlanMigrationLog, 
    VlanMigrationNetworkDetail,
    VlanMigrationTemplate
)

# ============================================
# SECTION 2: Register blueprints in your app initialization
# ============================================

# In your create_app() function or where you initialize Flask app:
def create_app():
    app = Flask(__name__)
    
    # ... existing app configuration ...
    
    # Register VLAN migration blueprints
    register_vlan_migration_blueprints(app)
    
    # ... rest of your app setup ...
    
    return app

# OR if you're not using app factory pattern:
# After creating your Flask app instance
app = Flask(__name__)

# ... existing configuration ...

# Register VLAN migration blueprints
from vlan_migration_routes import vlan_migration_routes
app.register_blueprint(vlan_migration_routes)
app.register_blueprint(vlan_migration_bp)

# ============================================
# SECTION 3: Add to navigation menu (if you have a centralized nav config)
# ============================================

# Add to your navigation configuration
NAVIGATION_ITEMS = {
    'network_operations': [
        # ... existing items ...
        {
            'name': 'VLAN Migration',
            'url': '/vlan-migration',
            'icon': 'fa-exchange-alt',
            'description': 'Migrate store networks to new VLAN standards',
            'roles': ['admin', 'network_engineer']
        }
    ]
}

# ============================================
# SECTION 4: Add authentication check (if using Flask-Login)
# ============================================

# In vlan_migration_routes.py, update the routes:
from flask_login import login_required

@vlan_migration_routes.route('/vlan-migration')
@login_required
def vlan_migration():
    """Main VLAN migration page"""
    return render_template('vlan_migration.html')

# ============================================
# SECTION 5: Add to your home page template
# ============================================

# In your home.html or main navigation template, add:
"""
<!-- VLAN Migration Card -->
<div class="col-md-4 mb-3">
    <div class="card h-100">
        <div class="card-body">
            <h5 class="card-title">
                <i class="fas fa-exchange-alt text-primary"></i> VLAN Migration
            </h5>
            <p class="card-text">
                Automated tool for migrating store networks from legacy VLAN 
                numbering to new corporate standards with zero downtime.
            </p>
            <ul class="list-unstyled small text-muted">
                <li><i class="fas fa-check text-success"></i> Zero downtime migration</li>
                <li><i class="fas fa-check text-success"></i> Automatic backup & rollback</li>
                <li><i class="fas fa-check text-success"></i> Real-time progress tracking</li>
                <li><i class="fas fa-check text-success"></i> 100% firewall validation</li>
            </ul>
            <a href="/vlan-migration" class="btn btn-primary btn-sm">
                <i class="fas fa-arrow-right"></i> Open Migration Tool
            </a>
        </div>
    </div>
</div>
"""

# ============================================
# SECTION 6: Database initialization
# ============================================

# If you have a database initialization script, add:
def init_vlan_migration_tables():
    """Initialize VLAN migration tables"""
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Or run the SQL directly
        db.engine.execute("""
            CREATE TABLE IF NOT EXISTS vlan_migration_history (
                -- table definition from integration guide
            );
        """)

# ============================================
# SECTION 7: Add to your requirements.txt (if needed)
# ============================================

# These should already be installed, but ensure you have:
# flask
# flask-sqlalchemy
# requests
# python-dotenv

# ============================================
# SECTION 8: Environment variables
# ============================================

# Ensure your .env file has:
# API_KEY=your-meraki-api-key
# This should already exist at /usr/local/bin/meraki.env