# VLAN Migration Integration Guide

This guide explains how to integrate the VLAN migration functionality into the DSR Circuits application.

## Files Created

### 1. Web Interface
- `/usr/local/bin/Main/templates/vlan_migration.html` - Main web interface
- `/usr/local/bin/templates/vlan_migration_help.html` - Help documentation page

### 2. Backend Components
- `/usr/local/bin/Main/vlan_migration_api.py` - API endpoints for migration operations
- `/usr/local/bin/Main/vlan_migration_routes.py` - Flask routes for web pages
- `/usr/local/bin/Main/vlan_migration_models.py` - Database models for tracking

### 3. Existing Migration Scripts
- `/usr/local/bin/Main/vlan_migration_complete.py` - Core migration script
- `/usr/local/bin/Main/detailed_rule_comparison.py` - Validation script
- `/usr/local/bin/Main/neo07_54_rule_template_20250710_105817.json` - Firewall template

## Integration Steps

### Step 1: Add Database Tables

Run the following SQL to create the necessary tables:

```sql
-- VLAN Migration History
CREATE TABLE IF NOT EXISTS vlan_migration_history (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(50) UNIQUE NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    networks_total INTEGER NOT NULL,
    networks_completed INTEGER DEFAULT 0,
    networks_failed INTEGER DEFAULT 0,
    status VARCHAR(20) NOT NULL,
    initiated_by VARCHAR(100),
    notes TEXT
);

-- VLAN Migration Logs
CREATE TABLE IF NOT EXISTS vlan_migration_logs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(50) NOT NULL REFERENCES vlan_migration_history(job_id),
    timestamp TIMESTAMP NOT NULL,
    phase VARCHAR(20),
    network VARCHAR(100),
    message TEXT
);

-- VLAN Migration Network Details
CREATE TABLE IF NOT EXISTS vlan_migration_network_details (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(50) NOT NULL REFERENCES vlan_migration_history(job_id),
    network_id VARCHAR(50) NOT NULL,
    network_name VARCHAR(100),
    migration_status VARCHAR(20),
    backup_file VARCHAR(200),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    firewall_rules_before INTEGER,
    firewall_rules_after INTEGER,
    validation_status VARCHAR(20),
    validation_details TEXT,
    error_message TEXT
);

-- VLAN Migration Templates
CREATE TABLE IF NOT EXISTS vlan_migration_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    firewall_template_file VARCHAR(200),
    vlan_mappings TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes
CREATE INDEX idx_vlan_migration_history_status ON vlan_migration_history(status);
CREATE INDEX idx_vlan_migration_history_start_time ON vlan_migration_history(start_time DESC);
CREATE INDEX idx_vlan_migration_logs_job_id ON vlan_migration_logs(job_id);
CREATE INDEX idx_vlan_migration_network_details_job_id ON vlan_migration_network_details(job_id);
CREATE INDEX idx_vlan_migration_network_details_network_id ON vlan_migration_network_details(network_id);
```

### Step 2: Update models.py

Add the VLAN migration models to your existing `/usr/local/bin/Main/models.py` file:

```python
# Add these imports at the top
from datetime import datetime

# Add these model classes
class VlanMigrationHistory(db.Model):
    """Track VLAN migration jobs"""
    __tablename__ = 'vlan_migration_history'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String(50), unique=True, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    networks_total = Column(Integer, nullable=False)
    networks_completed = Column(Integer, default=0)
    networks_failed = Column(Integer, default=0)
    status = Column(String(20), nullable=False)
    initiated_by = Column(String(100))
    notes = Column(Text)
    
    # Relationships
    logs = relationship('VlanMigrationLog', backref='job', lazy='dynamic')
    network_details = relationship('VlanMigrationNetworkDetail', backref='job', lazy='dynamic')

class VlanMigrationLog(db.Model):
    """Store migration console logs"""
    __tablename__ = 'vlan_migration_logs'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String(50), ForeignKey('vlan_migration_history.job_id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    phase = Column(String(20))
    network = Column(String(100))
    message = Column(Text)

class VlanMigrationNetworkDetail(db.Model):
    """Track individual network migration details"""
    __tablename__ = 'vlan_migration_network_details'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String(50), ForeignKey('vlan_migration_history.job_id'), nullable=False)
    network_id = Column(String(50), nullable=False)
    network_name = Column(String(100))
    migration_status = Column(String(20))
    backup_file = Column(String(200))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    firewall_rules_before = Column(Integer)
    firewall_rules_after = Column(Integer)
    validation_status = Column(String(20))
    validation_details = Column(Text)
    error_message = Column(Text)

class VlanMigrationTemplate(db.Model):
    """Store VLAN migration templates"""
    __tablename__ = 'vlan_migration_templates'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    firewall_template_file = Column(String(200))
    vlan_mappings = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    is_active = Column(Boolean, default=True)
```

### Step 3: Update dsrcircuits.py

Add the VLAN migration blueprints to your main Flask application:

```python
# Add this import at the top
from vlan_migration_routes import register_vlan_migration_blueprints

# In the create_app() function or main application setup, add:
register_vlan_migration_blueprints(app)
```

### Step 4: Update Navigation

Add the VLAN migration link to your home page or navigation menu. In your home.html template, add:

```html
<!-- In the Network Operations section -->
<div class="col-md-4 mb-3">
    <div class="card h-100">
        <div class="card-body">
            <h5 class="card-title">
                <i class="fas fa-exchange-alt text-primary"></i> VLAN Migration
            </h5>
            <p class="card-text">Migrate store networks to new VLAN standards</p>
            <a href="/vlan-migration" class="btn btn-primary btn-sm">
                <i class="fas fa-arrow-right"></i> Open Tool
            </a>
        </div>
    </div>
</div>
```

### Step 5: Copy Template to Correct Location

The Flask application expects templates in `/usr/local/bin/templates/`, so copy the main template:

```bash
cp /usr/local/bin/Main/templates/vlan_migration.html /usr/local/bin/templates/
```

### Step 6: Test the Integration

1. Restart the DSR Circuits service:
   ```bash
   sudo systemctl restart meraki-dsrcircuits.service
   ```

2. Navigate to: `http://neamsatcor1ld01.trtc.com:5052/vlan-migration`

3. Test the functionality:
   - Network discovery
   - Migration execution
   - Real-time console output
   - Validation results

## API Endpoints

The following API endpoints are available:

- `GET /api/networks-for-migration` - Get networks eligible for migration
- `POST /api/vlan-migration/start` - Start migration process
- `GET /api/vlan-migration/status/<job_id>` - Get migration status
- `POST /api/vlan-migration/validate` - Validate specific networks
- `GET /api/vlan-migration/history` - Get migration history
- `POST /api/vlan-migration/rollback` - Rollback a migration

## Security Considerations

1. **Authentication**: The routes should be protected with login_required decorators
2. **Permissions**: Only network engineers should have access to migration tools
3. **Logging**: All migrations are logged to the database for audit trails
4. **Backups**: Every migration creates a complete backup before starting

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all Python paths are correct and modules are in the right location
2. **Database Errors**: Make sure all tables are created before running
3. **API Key Issues**: Verify the Meraki API key is loaded from `/usr/local/bin/meraki.env`
4. **Template Not Found**: Ensure templates are copied to `/usr/local/bin/templates/`

### Debug Mode

To run in debug mode, temporarily modify the migration script call:

```python
# In vlan_migration_api.py, add --dry-run flag
cmd = [
    'python3',
    '/usr/local/bin/Main/vlan_migration_complete.py',
    '--network-id', network_id,
    '--dry-run'  # Add this for testing
]
```

## Next Steps

1. Add role-based access control
2. Implement batch scheduling for off-hours migrations
3. Add email notifications for completed migrations
4. Create migration reports and analytics
5. Add pre-migration health checks

## Support

For issues or questions:
- Check logs in `/var/log/meraki-dsrcircuits.log`
- Review migration reports in `/usr/local/bin/Main/complete_vlan_migration_report_*.txt`
- Contact the Network Operations Team

---

**Created:** July 10, 2025  
**Version:** 1.0  
**Status:** Ready for Integration