# DSR Circuits Production File Analysis

## Date: July 13, 2025

## Executive Summary

This document analyzes the production Flask application setup for DSR Circuits to identify which files are actually used in production versus development/test files.

## Main Application File

**Production Entry Point:** `/usr/local/bin/Main/dsrcircuits.py`

### Template Configuration
```python
app = Flask(__name__, 
            template_folder='/usr/local/bin/templates',
            static_folder='/usr/local/bin/static')
```

**Important Note:** The Flask app is configured to use `/usr/local/bin/templates` (NOT `/usr/local/bin/Main/templates`) for templates.

## Imported Python Modules (Production Dependencies)

From dsrcircuits.py imports:

### Core System Files
1. `config.py` - Configuration and Redis connection
2. `models.py` - Database models (Circuit, CircuitHistory, DailySummary, ProviderMapping, CircuitAssignment)

### Blueprint Modules (All Registered in Production)
1. `dsrcircuits_blueprint.py` - Main DSR circuits functionality
2. `dsrcircuits_beta_combined.py` - Beta features
3. `status.py` - Status tracking
4. `historical.py` - Historical data views
5. `inventory.py` - Inventory management
6. `reports.py` - Reporting functionality
7. `new_stores.py` - New store management
8. `performance.py` - Performance monitoring
9. `tags.py` - Tag management
10. `system_health.py` - System health monitoring
11. `subnets_blueprint.py` - Subnet management
12. `eol_routes.py` - End-of-life tracking
13. `switch_visibility.py` - Switch port visibility
14. `dsrcircuits_test.py` - Test features
15. `dsrcircuits_dev.py` - Development features
16. `inventory_working.py` - Working inventory features

### Optional Modules (Try/Except Import)
1. `vlan_migration_routes.py` - VLAN migration UI routes
2. `vlan_migration_api.py` - VLAN migration API
3. `vlan_migration_test_routes.py` - VLAN test UI routes
4. `vlan_migration_test_api.py` - VLAN test API

## Template Files Analysis

### Templates Directory Mismatch Issue
- Flask configured to use: `/usr/local/bin/templates`
- Actual Main templates in: `/usr/local/bin/Main/templates`

This means there are TWO template directories, and Flask is using the one outside Main/.

### Templates Referenced in dsrcircuits.py
1. `meraki_firewall.html` - Firewall dashboard
2. `home.html` - Home page
3. `documentation.html` - Documentation viewer
4. `documentation_index.html` - Documentation index

### All Templates Used in Production (from render_template() calls)

**From Core dsrcircuits.py:**
1. `meraki_firewall.html` - Firewall management dashboard
2. `home.html` - Main home page
3. `documentation.html` - Documentation viewer
4. `documentation_index.html` - Documentation index

**From Blueprint Modules:**

**dsrcircuits_blueprint.py:**
5. `index.html` - Index page
6. `dsrcircuits.html` - Main DSR circuits page
7. `dsrallcircuits.html` - All circuits view

**dsrcircuits_beta_combined.py:**
8. `dsrcircuits_beta_no_roles.html` - Beta features without roles

**status.py:**
9. `dsrdashboard.html` - Status dashboard
10. `circuit_orders.html` - Circuit orders page

**inventory.py:**
11. `inventory_summary_tabs.html` - Inventory summary with tabs
12. `inventory_details.html` - Inventory details view
13. `ssh_inventory.html` - SSH inventory page
14. `collected_inventory.html` - Collected inventory view
15. `inventory_final_4tabs.html` - Final inventory with 4 tabs

**reports.py:**
16. `circuit_enablement_report.html` - Circuit enablement reporting

**new_stores.py:**
17. `new_stores_tabbed.html` - New stores tabbed interface

**performance.py:**
18. `performance_dashboard.html` - Performance monitoring dashboard

**system_health.py:**
19. `system_health.html` - System health monitoring

**subnets_blueprint.py:**
20. `subnets.html` - Subnet management

**eol_routes.py:**
21. `eol_dashboard.html` - End-of-life dashboard

**switch_visibility.py:**
22. `switch_visibility.html` - Switch port visibility

**tags.py:**
23. `tags.html` - Tag management

**historical.py:**
24. `dsrhistorical.html` - Historical data view

**dsrcircuits_test.py:**
25. `dsrcircuits_test.html` - Test version of circuits page
26. `provider_matching_test.html` - Provider matching test
27. `test_site_circuits.html` - Test site circuits view

**dsrcircuits_dev.py:**
- Uses existing `dsrcircuits.html` template

**vlan_migration_routes.py (optional):**
28. `vlan_migration.html` - VLAN migration interface
29. `vlan_migration_help.html` - VLAN migration help

**vlan_migration_test_routes.py (optional):**
30. `vlan_migration_test.html` - VLAN migration test interface

## Static Files

**Flask Configuration:**
- Configured to use: `/usr/local/bin/static`
- Contains: favicon.ico, dsr-badge.svg, jQuery libraries, tracking styles

**Main/static Directory:**
- Also exists at: `/usr/local/bin/Main/static`
- Minimal content (favicon.ico, empty libs/tracking directories)

## Nightly/Scheduled Scripts

### Production Nightly Scripts (in /usr/local/bin/Main/nightly/)
1. **hourly_api_performance.py** - API performance monitoring (hourly)
2. **nightly_circuit_history.py** - Circuit history tracking
3. **nightly_dsr_pull_db_with_override.py** - DSR data pull with override capability
4. **nightly_enablement_db.py** - Circuit enablement tracking
5. **nightly_enriched_db.py** - Enriched circuit data processing
6. **nightly_inventory_db.py** - Inventory database updates
7. **nightly_meraki_db.py** - Meraki data synchronization
8. **nightly_meraki_enriched_merged.py** - Merged Meraki enriched data
9. **update_circuits_from_tracking_with_override.py** - Circuit tracking updates

### Known Scheduled Scripts (from production_cron_entry.txt)
- **nightly_inventory_web_format_update.py** - Runs at 2:30 AM daily

## Development vs Production File Classification

### Production Files (Core System)
**Main Application:**
- dsrcircuits.py (main Flask app)
- config.py (configuration)
- models.py (database models)
- utils.py (utilities)
- credential_manager.py (credential management)

**Blueprint Modules (All in Production):**
- All 16 blueprint files listed above

**Database/Model Files:**
- vlan_migration_models.py
- vlan_migration_db.py

### Development/Test Files (Not in Production)
**Test Scripts:**
- All files with "test" in name
- dsrcircuits_test.py (despite being imported, it's a test module)
- dsrcircuits_dev.py (development features)
- inventory_working.py (work in progress)

**Utility/Migration Scripts:**
- Files starting with: analyze_, check_, fix_, migrate_, create_, extract_, export_, import_, setup_, verify_, download_, generate_, update_, apply_, restore_, deploy_, prepare_, populate_, normalize_, deduplicate_, consolidate_, enhance_, process_, search_, clean_, wipe_, copy_, find_, align_, add_, bulk_, monitor_, compare_, complete_

**Backup Files:**
- All .backup, .bak, .broken files
- Files in backup directories

## Directory Structure Issues

### Template Directory Mismatch
**Critical Issue:** Flask is configured to use `/usr/local/bin/templates` but most development appears to happen in `/usr/local/bin/Main/templates`. This could lead to:
1. Templates not being found in production
2. Updates to Main/templates not reflecting in production
3. Confusion about which template is actually being used

### Potential Solutions:
1. Update Flask configuration to use `/usr/local/bin/Main/templates`
2. OR move all templates to `/usr/local/bin/templates`
3. OR create symbolic links between directories

### Static Directory Similar Issue
- Flask uses: `/usr/local/bin/static`
- Development static files in: `/usr/local/bin/Main/static`

## Running Process Analysis
From `ps aux` output:
- Main app running: `/bin/python3 /usr/local/bin/Main/dsrcircuits.py`
- Process started at 12:13 (recently restarted)
- Running as root with PID 179041
- Active PostgreSQL connections indicate the app is operational

## Summary

### Production Components:
1. **Core Flask App:** dsrcircuits.py + 16 blueprint modules
2. **Templates:** 30 HTML templates (location mismatch issue)
3. **Static Files:** jQuery, CSS, favicon (location mismatch issue)
4. **Nightly Scripts:** 9 production scheduled scripts
5. **Database:** PostgreSQL with SQLAlchemy models

### Key Issues to Address:
1. Template directory mismatch between Flask config and actual location
2. Static directory mismatch
3. Large number of development/test scripts mixed with production code
4. Need for better separation of production vs development environments

### Recommendations:
1. Fix template/static directory configuration
2. Move development scripts to a separate directory
3. Create clear production deployment documentation
4. Consider using environment variables for path configuration

## File Statistics

### Total File Counts:
- **Python files in Main:** 316 total
- **Templates in /usr/local/bin/templates:** 62 files
- **Templates in /usr/local/bin/Main/templates:** 53 files
- **Backup/test Python files:** 63 files

### Production vs Development Breakdown:
- **Production Python modules:** ~25-30 core files
- **Development/utility scripts:** ~250+ files
- **Production templates:** 30 actively used
- **Template backups/variants:** ~30+ unused files

### File Organization Issues:
1. Over 80% of Python files are development/utility scripts
2. Template duplication between two directories
3. Many backup files mixed with production code
4. No clear separation between production and development environments

