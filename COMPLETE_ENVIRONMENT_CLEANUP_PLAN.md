# Complete Environment Cleanup and Dev Setup Plan

## Current Situation Summary

### What's Wrong:
1. **Flask serves from**: `/usr/local/bin/templates/` and `/usr/local/bin/static/`
2. **Development happens in**: `/usr/local/bin/Main/templates/` and `/usr/local/bin/Main/static/`
3. **Manual copying required**: Every change needs to be copied from Main to root directories
4. **File clutter**: 316 Python files in Main, only ~30 are production
5. **No dev environment**: Testing happens in production

### Current Workflow (BAD):
```
Edit: /usr/local/bin/Main/templates/dsrcircuits.html
Copy: sudo cp /usr/local/bin/Main/templates/dsrcircuits.html /usr/local/bin/templates/
Restart: sudo systemctl restart meraki-dsrcircuits
```

## Phase 1: Fix Template/Static Paths (PRIORITY 1)

### Step 1.1: Backup Current State
```bash
# Create backup of current working state
sudo tar -czf /tmp/dsrcircuits_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
    /usr/local/bin/Main \
    /usr/local/bin/templates \
    /usr/local/bin/static \
    /etc/systemd/system/meraki-dsrcircuits.service

# Document current state
echo "Backup created at: /tmp/dsrcircuits_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
```

### Step 1.2: Update Flask Configuration
```bash
# Edit /usr/local/bin/Main/dsrcircuits.py
# Change from:
app = Flask(__name__, 
            template_folder='/usr/local/bin/templates',
            static_folder='/usr/local/bin/static')

# To:
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
```

This uses relative paths, so with WorkingDirectory=/usr/local/bin/Main, Flask will use:
- `/usr/local/bin/Main/templates/`
- `/usr/local/bin/Main/static/`

### Step 1.3: Test Configuration Change
```bash
# Restart service
sudo systemctl restart meraki-dsrcircuits

# Test all pages load correctly
curl -s http://localhost:5052/dsrcircuits | grep "<title>"
curl -s http://localhost:5052/dsrdashboard | grep "<title>"
curl -s http://localhost:5052/inventory | grep "<title>"

# Check logs for errors
sudo journalctl -u meraki-dsrcircuits -n 50
```

### Step 1.4: Remove Old Directories (After Confirming Working)
```bash
# Archive old directories first
sudo mv /usr/local/bin/templates /tmp/old_templates_$(date +%Y%m%d)
sudo mv /usr/local/bin/static /tmp/old_static_$(date +%Y%m%d)

# Can delete after 1 week if no issues
```

## Phase 2: Clean Production Directory Structure

### Step 2.1: Create Organization Directories
```bash
cd /usr/local/bin/Main

# Create organized structure
sudo mkdir -p archive/backups
sudo mkdir -p archive/old_versions
sudo mkdir -p dev_tools/analysis
sudo mkdir -p dev_tools/testing
sudo mkdir -p dev_tools/utilities
sudo mkdir -p dev_tools/migrations
sudo mkdir -p documentation
```

### Step 2.2: Move Non-Production Files
```bash
# Move test scripts
sudo mv test_*.py dev_tools/testing/
sudo mv *_test.py dev_tools/testing/

# Move analysis scripts
sudo mv analyze_*.py dev_tools/analysis/
sudo mv check_*.py dev_tools/analysis/
sudo mv find_*.py dev_tools/analysis/
sudo mv compare_*.py dev_tools/analysis/

# Move utility scripts
sudo mv fix_*.py dev_tools/utilities/
sudo mv update_*.py dev_tools/utilities/
sudo mv create_*.py dev_tools/utilities/
sudo mv generate_*.py dev_tools/utilities/
sudo mv apply_*.py dev_tools/utilities/

# Move backup files
sudo mv *.bak archive/backups/
sudo mv *.backup archive/backups/
sudo mv *_backup_* archive/backups/
sudo mv *.broken archive/backups/

# Move old versions
sudo mv *_old.py archive/old_versions/
sudo mv *_original.py archive/old_versions/
sudo mv *.orig archive/old_versions/

# Move documentation
sudo mv *.md documentation/
sudo mv *.txt documentation/
```

### Step 2.3: Verify Production Files
```bash
# List remaining Python files (should be ~30 production files)
ls -la *.py | wc -l

# Production files that should remain:
# - dsrcircuits.py (main app)
# - config.py, models.py, utils.py, credential_manager.py
# - All blueprint files (16 modules)
# - Any other active production modules
```

### Step 2.4: Final Production Structure
```
/usr/local/bin/Main/
├── dsrcircuits.py              # Main Flask app
├── config.py                   # Configuration
├── models.py                   # Database models
├── utils.py                    # Utilities
├── credential_manager.py       # Credentials
├── [blueprint modules]         # ~16 production blueprints
├── templates/                  # HTML templates (Flask uses this)
│   └── *.html                  # All templates
├── static/                     # Static files (Flask uses this)
│   ├── css/
│   ├── js/
│   └── images/
├── nightly/                    # Scheduled scripts
│   └── nightly_*.py
├── dev_tools/                  # Development scripts (not in production)
│   ├── analysis/
│   ├── testing/
│   ├── utilities/
│   └── migrations/
├── archive/                    # Old files
│   ├── backups/
│   └── old_versions/
└── documentation/              # All .md and .txt files
```

## Phase 3: Create Development Environment

### Step 3.1: Create Dev Directory Structure
```bash
# Create base Dev directory
sudo mkdir -p /usr/local/bin/Dev
cd /usr/local/bin/Dev

# Copy only production files
sudo cp /usr/local/bin/Main/dsrcircuits.py .
sudo cp /usr/local/bin/Main/config.py .
sudo cp /usr/local/bin/Main/models.py .
sudo cp /usr/local/bin/Main/utils.py .
sudo cp /usr/local/bin/Main/credential_manager.py .

# Copy all blueprint modules
sudo cp /usr/local/bin/Main/dsrcircuits_blueprint.py .
sudo cp /usr/local/bin/Main/status.py .
sudo cp /usr/local/bin/Main/inventory.py .
# ... (copy all 16 blueprint modules)

# Copy directories
sudo cp -r /usr/local/bin/Main/templates .
sudo cp -r /usr/local/bin/Main/static .
sudo mkdir -p nightly
sudo cp -r /usr/local/bin/Main/nightly/* nightly/

# Create dev-specific directories
sudo mkdir -p logs
sudo mkdir -p scripts
```

### Step 3.2: Configure Dev Environment
```bash
# Edit /usr/local/bin/Dev/config.py
# Change database to dev:
SQLALCHEMY_DATABASE_URI = 'postgresql://user:pass@localhost/dsrcircuits_dev'

# Edit /usr/local/bin/Dev/dsrcircuits.py
# Change port:
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5053, debug=True)  # Dev on 5053

# Add DEV indicator to base template
# Edit /usr/local/bin/Dev/templates/base.html or similar
# Add "[DEV]" to title or header
```

### Step 3.3: Create Database Sync Script
```python
# /usr/local/bin/Dev/scripts/sync_prod_to_dev.py
#!/usr/bin/env python3
"""
Sync production database to development
"""
import subprocess
import sys
from datetime import datetime

def sync_database():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print(f"Starting database sync at {timestamp}")
    
    # Dump production database
    dump_cmd = [
        'pg_dump',
        '-h', 'localhost',
        '-U', 'postgres',
        '-d', 'dsrcircuits_prod',
        '-f', f'/tmp/prod_dump_{timestamp}.sql'
    ]
    
    print("Dumping production database...")
    subprocess.run(dump_cmd, check=True)
    
    # Drop and recreate dev database
    print("Recreating development database...")
    subprocess.run(['psql', '-U', 'postgres', '-c', 'DROP DATABASE IF EXISTS dsrcircuits_dev;'])
    subprocess.run(['psql', '-U', 'postgres', '-c', 'CREATE DATABASE dsrcircuits_dev;'])
    
    # Restore to dev
    restore_cmd = [
        'psql',
        '-h', 'localhost',
        '-U', 'postgres',
        '-d', 'dsrcircuits_dev',
        '-f', f'/tmp/prod_dump_{timestamp}.sql'
    ]
    
    print("Restoring to development database...")
    subprocess.run(restore_cmd, check=True)
    
    print("Database sync complete!")
    
    # Clean up
    subprocess.run(['rm', f'/tmp/prod_dump_{timestamp}.sql'])

if __name__ == '__main__':
    sync_database()
```

### Step 3.4: Create Dev Service (Optional)
```bash
# Create /etc/systemd/system/meraki-dsrcircuits-dev.service
[Unit]
Description=DSR Circuits Flask Application (Development)
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/usr/local/bin/Dev
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="FLASK_ENV=development"
ExecStart=/bin/python3 /usr/local/bin/Dev/dsrcircuits.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Phase 4: Testing and Validation

### Step 4.1: Test Production After Changes
```bash
# Check all pages load
for page in dsrcircuits dsrdashboard inventory reports new-stores performance; do
    echo "Testing /$page..."
    curl -s http://localhost:5052/$page | grep -q "<title>" && echo "✓ OK" || echo "✗ FAILED"
done

# Check static files load
curl -I http://localhost:5052/static/favicon.ico
```

### Step 4.2: Test Dev Environment
```bash
# Start dev server
cd /usr/local/bin/Dev
python3 dsrcircuits.py

# In another terminal, test dev pages
curl -s http://localhost:5053/dsrcircuits | grep "<title>"
```

## Phase 5: Documentation and Training

### Step 5.1: Create Usage Documentation
```markdown
# /usr/local/bin/README.md

## Production Environment
- Location: /usr/local/bin/Main/
- Port: 5052
- Templates: /usr/local/bin/Main/templates/
- Static: /usr/local/bin/Main/static/
- Service: meraki-dsrcircuits

## Development Environment  
- Location: /usr/local/bin/Dev/
- Port: 5053
- Templates: /usr/local/bin/Dev/templates/
- Static: /usr/local/bin/Dev/static/
- Database: dsrcircuits_dev

## Workflow
1. Make changes in Dev environment
2. Test thoroughly
3. Copy changes to Main when ready
4. No more copying between /usr/local/bin/templates!
```

## Rollback Plan

If anything goes wrong:

```bash
# Restore from backup
cd /
sudo tar -xzf /tmp/dsrcircuits_backup_[timestamp].tar.gz

# Restart service
sudo systemctl restart meraki-dsrcircuits

# Verify working
curl http://localhost:5052/dsrcircuits
```

## Success Criteria

After completion:
- [ ] Flask serves templates from Main/templates/ directly
- [ ] No more manual copying between directories
- [ ] Dev environment runs on port 5053
- [ ] Production files clearly separated from dev scripts
- [ ] Both environments can run simultaneously
- [ ] Database sync script works
- [ ] All pages load correctly in both environments
- [ ] Documentation is clear for future developers

## Timeline

- **Phase 1**: 30 minutes (Fix template paths)
- **Phase 2**: 1 hour (Clean directory structure)
- **Phase 3**: 1 hour (Create dev environment)
- **Phase 4**: 30 minutes (Testing)
- **Phase 5**: 30 minutes (Documentation)

**Total**: ~3.5 hours

## Benefits After Completion

1. **No more confusion**: Templates served from where they're edited
2. **Clean structure**: Easy to see what's production vs development
3. **Safe testing**: Dev environment isolated from production
4. **Easier deployment**: Clear separation of concerns
5. **Better workflow**: No manual file copying needed