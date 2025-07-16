# Development Environment Setup Plan

## Overview
Create a complete, isolated development environment that mirrors production but runs independently with its own database and port.

## Directory Structure
```
/usr/local/bin/Dev/
├── dsrcircuits.py (main Flask app - modified for port 5053)
├── config.py (dev-specific database connection)
├── models.py (exact copy from production)
├── templates/ (all HTML templates)
│   └── [all .html files from Main/templates/]
├── static/ (all CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
├── nightly/ (all nightly scripts - NOT scheduled)
│   └── [all scripts from Main/nightly/]
├── scripts/ (utility scripts)
│   └── sync_prod_to_dev_db.py (database sync script)
└── logs/ (dev-specific logs)
```

## Implementation Steps

### 1. Create Directory Structure
- Create `/usr/local/bin/Dev` as main dev directory
- Create subdirectories: templates, static, nightly, scripts, logs
- Set appropriate permissions

### 2. Copy Core Application Files
**From Main to Dev:**
- `dsrcircuits.py` → modify for port 5053
- `models.py` → exact copy (no changes)
- `config.py` → modify for dev database
- `utils.py` → exact copy
- `credential_manager.py` → exact copy

### 3. Copy Blueprint/Module Files
**All supporting modules:**
- `new_stores.py`
- `eol_routes.py`
- `system_health.py`
- `performance.py`
- `switch_visibility.py`
- `network_analysis_blueprint.py`
- `subnets_blueprint.py`
- `inventory.py`
- `reports.py`
- `tags.py`
- `status.py`
- `historical.py`
- `ipinfo.md`
- `subnets.md`
- `inventory.md`
- `nmis.md`

### 4. Copy Templates
**All HTML templates from Main/templates/:**
- Base templates (base.html, etc.)
- All page templates
- All modal templates
- Email templates

### 5. Copy Static Assets
**From Main/static/:**
- CSS files (all stylesheets)
- JavaScript files (all scripts)
- Images (logos, icons, etc.)
- Any other static resources

### 6. Copy Nightly Scripts (No Scheduling)
**From Main/nightly/:**
- All nightly_*.py scripts
- These will NOT be added to cron
- Can be run manually for testing

### 7. Database Setup

#### A. Create Dev Database
```sql
-- Create development database
CREATE DATABASE dsrcircuits_dev WITH TEMPLATE dsrcircuits_prod OWNER postgres;

-- Or create empty and use sync script
CREATE DATABASE dsrcircuits_dev OWNER postgres;
```

#### B. Create Database Sync Script
`/usr/local/bin/Dev/scripts/sync_prod_to_dev_db.py`
- Dumps production database
- Restores to development database
- Can be run on-demand to refresh dev data
- Includes safety checks

### 8. Configuration Changes

#### A. Dev Config File
Create `Dev/config.py`:
```python
class Config:
    # Development database
    SQLALCHEMY_DATABASE_URI = 'postgresql://user:pass@localhost/dsrcircuits_dev'
    
    # Dev-specific settings
    DEBUG = True
    TESTING = True
    
    # Same secret key as prod (or different for security)
    SECRET_KEY = 'dev-secret-key'
    
    # Dev port
    PORT = 5053
```

#### B. Flask App Modifications
In `Dev/dsrcircuits.py`:
- Change port from 5052 to 5053
- Update log file paths to use Dev/logs/
- Add "DEV" indicator to page titles/headers
- Ensure all imports use relative paths

### 9. Environment Variables
- Copy `/usr/local/bin/meraki.env` (contains API keys)
- No changes needed - same API access

### 10. Service Configuration (Optional)
Create systemd service for dev (if desired):
- `meraki-dsrcircuits-dev.service`
- Points to Dev directory
- Runs on port 5053
- Can be started/stopped independently

### 11. Testing Checklist
- [ ] Flask app starts on port 5053
- [ ] All pages load correctly
- [ ] Database connections work
- [ ] Static assets load
- [ ] All blueprints register
- [ ] API endpoints function
- [ ] Can modify without affecting prod

### 12. Documentation
Create `Dev/README.md`:
- How to start dev server
- How to sync database from prod
- Differences from production
- Testing procedures

## Benefits
1. **Complete Isolation**: Changes don't affect production
2. **Full Testing**: Test database migrations, schema changes
3. **Parallel Running**: Both prod (5052) and dev (5053) can run simultaneously
4. **Easy Refresh**: Sync script can refresh dev data anytime
5. **Safe Development**: Break things without consequences

## Usage After Setup

### Start Dev Server
```bash
cd /usr/local/bin/Dev
python3 dsrcircuits.py
# Access at http://localhost:5053
```

### Sync Database from Production
```bash
python3 /usr/local/bin/Dev/scripts/sync_prod_to_dev_db.py
```

### Run Nightly Scripts Manually
```bash
cd /usr/local/bin/Dev/nightly
python3 nightly_meraki_db.py  # Run manually for testing
```

## Security Considerations
- Dev database should have different passwords
- Consider firewall rules for port 5053
- Don't expose dev to internet without auth
- Keep API keys secure (same as prod)

## Maintenance
- Periodically sync code changes from Main to Dev
- Keep database schema in sync
- Document any dev-specific modifications

---

**Estimated Time**: 30-45 minutes for complete setup
**Disk Space**: ~500MB (including database copy)
**Requirements**: PostgreSQL, Python 3.8+, same dependencies as prod