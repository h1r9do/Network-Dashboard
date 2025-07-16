# Discount Tire Network Management System - Comprehensive Circuit Management

## ✅ PRODUCTION SYSTEM - DATABASE INTEGRATED

**This IS the CURRENT PRODUCTION SYSTEM** running with full PostgreSQL database integration.

**Migration Status:** Successfully completed on June 25, 2025

**System Version:** 2.0.0-production-database

**Access URLs:**
- **Production System:** http://10.0.145.130:5052 (Direct Flask access)
- **Home Page:** http://10.0.145.130:5052/home (Central navigation hub with card-based UI)
- **Main Circuits:** http://10.0.145.130:5052/dsrcircuits (Primary circuits management)
- **Dashboard:** http://10.0.145.130:5052/dsrdashboard (Status overview)
- **Performance:** http://10.0.145.130:5052/performance (API monitoring dashboard)
- **System Health:** http://10.0.145.130:5052/system-health (Comprehensive server monitoring)
- **Nginx Proxy:** Port 8080 (Currently inactive - nginx service stopped)

**Service Management:**
```bash
systemctl status dsrcircuits.service    # Check service status
systemctl restart dsrcircuits.service   # Restart service
journalctl -u dsrcircuits.service -f    # View live logs
```

**Related Services:**
- **AWX (Ansible):** http://10.0.145.130:30483 (Username: admin, Password: admin)
- **Git Repository:** http://10.0.145.130:3000/mbambic/usr-local-bin
- **Nginx:** Currently stopped (was on port 8080)

## 🔧 Key System Documentation

### Circuit Processing Logic
**All circuit processing logic is documented in** `/usr/local/bin/Main/circuit_logic.md`

This comprehensive documentation covers:
- **Step 1**: Raw notes parsing from Meraki devices (regex patterns, text splitting)
- **Step 2**: Provider normalization (VZG→VZW Cell, prefix removal, fuzzy matching)
- **Step 3**: ARIN provider lookups via RDAP API
- **Step 4**: Provider comparison logic (Match vs No match)
- **Step 5**: Final enrichment hierarchy (DSR > Notes > ARIN)

### Key Business Rules
- **Enabled Circuits Only**: Process only circuits with status='enabled'
- **VZG/VZW Normalization**: All VZG variants become "VZW Cell" (removes IMEI suffixes)
- **DSR Priority**: Enabled DSR data overrides notes/ARIN when available
- **Comparison Logic**: When notes don't match ARIN, trust the notes
- **Private IP Handling**: Private IPs return "Private IP" for ARIN lookups

### Example: CAL 17
```
Raw Notes: "WAN1 NOT DSR Frontier Fiber 500.0M x 500.0M ... WAN2 VZG IMEI: 356405432462415"
Processing:
  Step 1: Parse → wan1="NOT DSR Frontier Fiber", wan2="VZG IMEI: 356405432462415"
  Step 2: Normalize → wan1="Frontier Fiber", wan2="VZW Cell"
  Step 3: ARIN → wan1="Frontier Communications", wan2="Private IP"
  Step 4: Compare → wan1="Match", wan2="No match"
  Step 5: Final → wan1="Frontier Communications", wan2="VZW Cell"
```

**This logic is implemented in**: `nightly_meraki_db.py`, recovery scripts, and modal processing.

**Source Scripts**: Based on original `/usr/local/bin/meraki_mx.py` + `/usr/local/bin/nightly_enriched.py`
- **PostgreSQL:** Database server (localhost:5432)
- **Redis:** Cache layer (localhost:6379)

**Database Schema:**
- **Type:** PostgreSQL
- **Name:** dsrcircuits
- **User:** dsradmin
- **Connection:** Via SQLAlchemy ORM with connection pooling
- **Tables (13 primary):**
  - `circuits` - Main circuit data (4,171+ records, includes notes field)
  - `circuit_history` - Change tracking (649+ historical records)
  - `daily_summaries` - Enablement summaries and metrics
  - `provider_mappings` - Provider name normalization
  - `circuit_assignments` - SCTASK and personnel attribution
  - `firewall_rules` - L3 firewall rules (55 rules from NEO 07 template)
  - `new_stores` - Store tracking with Target Opening Dates (TOD)
  - `meraki_inventory` - Device inventory (1,300+ devices)
  - `enriched_circuits` - Enhanced circuit data with Meraki integration
  - `inventory_summary` - Device model summaries with EOL/EOS dates
  - `performance_metrics` - API endpoint performance monitoring
  - `performance_summary` - Historical performance aggregates
  - `switch_port_clients` - Switch port visibility data (18,500+ active ports)

---

## 📋 System Overview

This is the comprehensive circuit management system for Discount Tire that combines automated data collection, processing, and web-based reporting. The system integrates data from:

- **DSR Global Portal:** Circuit tracking data (CSV imports)
- **Meraki API:** Device inventory and network configuration
- **ARIN RDAP:** IP provider identification
- **ServiceNow:** SCTASK assignment integration
- **Manual Entry:** New store construction tracking

**Database Integration:** All pages now serve data from PostgreSQL database with 100x faster queries, real-time capabilities, and ACID compliance.

## 🌐 All Web Pages & Functionality

### Main Navigation (Card-Based UI)
**Home Page:** `/home`
- Central navigation hub with dynamic status cards
- Real-time system health monitoring
- Live circuit statistics and metrics
- Links to all major system sections

### Circuit Management Pages
1. **Main Circuits (`/dsrcircuits`)** - Primary interface
   - Interactive circuit table with advanced filtering
   - Confirm/Edit workflow for circuit data validation
   - Push to Meraki functionality for device configuration
   - Export capabilities (Excel, CSV, PDF)
   - Real-time status updates and confirmation tracking

2. **Status Dashboard (`/dsrdashboard`)** - Overview page
   - Circuit status categorization and counts
   - Action items and pending tasks
   - Recent activity summaries
   - Performance metrics

3. **Circuit Orders (`/circuit-orders`)** - In-flight tracking
   - Active circuit orders and provisioning status
   - Timeline tracking and milestone monitoring
   - Assignment and ownership tracking

4. **Historical Analysis (`/dsrhistorical`)** - Change tracking
   - 649+ historical changes tracked since April 2025
   - Change detection and comparison tools
   - Trend analysis and reporting

### Inventory Management
5. **Inventory Summary (`/inventory-summary`)** - Device overview
   - Device model counts and summaries
   - End-of-Life (EOL) and End-of-Support (EOS) tracking
   - Excel export with EOL analysis

6. **Inventory Details (`/inventory-details`)** - Device specifics
   - Detailed device inventory with full specs
   - Network associations and device status
   - Search and filtering capabilities

### Reporting & Analytics
7. **Enablement Reports (`/circuit-enablement-report`)** - Metrics
   - Daily, weekly, monthly enablement statistics
   - Tracks ALL circuits changing TO "Enabled" status (not just from "Ready")
   - Team attribution based on assigned_to field
   - Export capabilities for management reporting
   - NEW: Enablement Details tab shows individual circuits with real previous status
   - **📚 Full Documentation**: See [ENABLEMENT_TRACKING_DOCUMENTATION.md](./ENABLEMENT_TRACKING_DOCUMENTATION.md)

8. **Performance Dashboard (`/performance`)** - System monitoring
   - Real-time API endpoint performance metrics
   - Response time trends and error rate tracking
   - 14 monitored endpoints with hourly data collection
   - Automatic anomaly detection

9. **System Health (`/system-health`)** - Server monitoring
   - Comprehensive server statistics and system information
   - RHEL version, hostname, uptime, kernel details
   - CPU usage, memory utilization, disk space monitoring
   - Network interfaces with IP addresses and status
   - Database connectivity and PostgreSQL status
   - System services status (dsrcircuits, postgresql, nginx, etc.)
   - Top processes by CPU usage
   - Health score calculation with automated alerts
   - Auto-refresh every 30 seconds with PDF export
   - AWX/Ansible monitoring: K3s cluster status, pod health, web interface accessibility
   - Git/Gitea monitoring: Repository accessibility, service status, version information

### Switch Port Visibility
10. **Switch Port Visibility (`/switch-visibility`)** - Real-time port monitoring
   - View connected devices across all switches and ports
   - MAC address manufacturer identification using OUI database
   - Real-time refresh capability per store or per switch
   - Comprehensive filtering: Store, Switch, Port, Hostname, IP, MAC, VLAN, Manufacturer
   - DataTables integration for sorting and searching
   - Export to Excel and PDF functionality
   - Nightly data collection from Meraki API (1:30 AM)
   - Automatic stale data cleanup (30+ days)
   - ~18,500+ active ports across 1,350+ switches

### New Store Management
11. **New Stores (`/new-stores`)** - Construction tracking
   - Target Opening Date (TOD) tracking and management
   - TOD Report Excel upload with duplicate handling
   - Manual entry as "Enter New TOD Store"
   - Circuit management with manual override protection
   - Status progression tracking (01-Planning through 05-Live)
   - Provider and speed configuration with Starlink auto-detection
   - **Free-form notes field for each circuit**
     - Type notes directly in the table
     - Auto-saves when you click away (no save button needed)
     - Notes persist until circuit is enabled or cancelled
     - Automatically cleared during nightly DSR pull on circuit completion
   - **📚 Full Documentation**: See [NEW_STORES_TOD_DOCUMENTATION.md](./NEW_STORES_TOD_DOCUMENTATION.md)

### Network Security
12. **Firewall Management (`/firewall`)** - L3 rule management
    - Template-based firewall rule deployment
    - NEO 07 template with 55 pre-configured rules
    - Rule editing and validation
    - Bulk deployment to multiple networks

## 🔧 System Architecture

### Application Stack
```
┌─────────────────────────────────────────┐
│    Direct Flask Access (Port 5052)      │
│         Production Interface             │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│    Flask Application Framework           │
│      dsrcircuits_integrated.py          │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│  Application Blueprints:                 │
│  • dsrcircuits.py (main circuits)       │
│  • status.py (dashboard & analytics)    │
│  • historical.py (change tracking)      │
│  • inventory.py (device management)     │
│  • reports.py (enablement reporting)    │
│  • new_stores.py (construction track)   │
│  • performance.py (system monitoring)   │
│  • tags.py (device tagging)             │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│        Database Layer                    │
│  • PostgreSQL (dsrcircuits database)   │
│  • SQLAlchemy ORM with models.py       │
│  • Redis caching layer                 │
│  • Connection pooling & optimization    │
└─────────────────────────────────────────┘
```

### Key Components
- **dsrcircuits_integrated.py** - Main application entry point
- **models.py** - SQLAlchemy database models and relationships
- **config.py** - Database configuration and environment settings
- **utils.py** - Shared utilities and Meraki integration
- **Templates** - Jinja2 HTML templates with responsive design

## 🚦 Current System State (June 27, 2025)

### Active Services & Status

| Service | Status | Port | Purpose | Command |
|---------|--------|------|---------|---------| 
| dsrcircuits.service | ✅ Active | 5052 | Main Flask application | `systemctl status dsrcircuits.service` |
| postgresql | ✅ Active | 5432 | Database server | `systemctl status postgresql` |
| redis | ✅ Active | 6379 | Cache layer | `systemctl status redis` |
| crond | ✅ Active | - | Scheduled tasks | `systemctl status crond` |
| nginx | ❌ Stopped | 8080 | Reverse proxy (inactive) | `systemctl status nginx` |
| gitea | ✅ Active | 3000 | Git repository | Access: http://10.46.0.3:3000 |
| k3s/AWX | ✅ Active | 30483 | Ansible automation | Access: http://10.46.0.3:30483 |

### Database Health Check
```bash
# Test database connection
curl http://localhost:5052/api/health | jq .

# Expected response:
{
  "status": "healthy",
  "database": "healthy", 
  "cache": "healthy",
  "version": "2.0.0-production-database",
  "timestamp": "2025-06-27T03:47:29.123456"
}
```

### Port Configuration Summary

| Port | Service | Status | Access | Notes |
|------|---------|--------|-----------|-------|
| 80 | k3s Traefik | Active | LoadBalancer | Kubernetes cluster traffic |
| 3000 | Gitea | Active | http://10.46.0.3:3000 | Git repository server |
| 5052 | DSR Circuits | Active | http://10.46.0.3:5052 | **Direct production access** |
| 5432 | PostgreSQL | Active | localhost only | Database server |
| 6379 | Redis | Active | localhost only | Cache server |
| 8080 | Nginx | Stopped | (was reverse proxy) | Currently inactive |
| 30483 | AWX | Active | http://10.46.0.3:30483 | Ansible automation |

## 📅 Automated Cron Jobs

### Production Database-Integrated Schedule

**Current Status:** ✅ All database scripts deployed and active

**Currently Active Schedule:**

| Time | Script | Purpose | Log File | Status |
|------|--------|---------|----------|--------|
| 00:00 | `nightly_dsr_pull_db_with_override.py` | Download DSR data with manual override protection | `/var/log/dsr-pull-db.log` | ✅ Active |
| 01:00 | `nightly_meraki_enriched_db.py` | Combined Meraki collection and enrichment | `/var/log/nightly-meraki-enriched-db.log` | ✅ Active |
| 03:00 | `nightly_inventory_db.py` | Generate inventory summaries | `/var/log/nightly-inventory-db.log` | ✅ Active |
| 01:30 | `nightly_switch_visibility_db.py` | Collect switch port client data | `/var/log/switch-visibility-db.log` | ⏳ Ready |
| 04:00 | `nightly_enablement_db.py` | Track Ready→Enabled transitions by Site ID | `/var/log/nightly-enablement-db.log` | ✅ Active |
| 04:30 | `nightly_circuit_history.py` | Track circuit changes | `/var/log/circuit-history.log` | ✅ Active |
| Hourly | `performance_monitor.py` | API performance monitoring | `/var/log/performance-monitor.log` | ✅ Active |
| */5 min | `git_autocommit.sh` | Auto-commit changes | N/A | ✅ Active |

### Complete Active Cron Configuration
```bash
# Database-integrated nightly scripts (CURRENTLY ACTIVE)
0 0 * * * /usr/bin/python3 /usr/local/bin/Main/nightly_dsr_pull_db_with_override.py >> /var/log/dsr-pull-db.log 2>&1
0 1 * * * /usr/bin/python3 /usr/local/bin/Main/nightly_meraki_enriched_db.py >> /var/log/nightly-meraki-enriched-db.log 2>&1
30 1 * * * /usr/bin/python3 /usr/local/bin/Main/nightly_switch_visibility_db.py >> /var/log/switch-visibility-db.log 2>&1
0 3 * * * /usr/bin/python3 /usr/local/bin/Main/nightly_inventory_db.py >> /var/log/nightly-inventory-db.log 2>&1
0 4 * * * /usr/bin/python3 /usr/local/bin/Main/nightly_enablement_db.py >> /var/log/nightly-enablement-db.log 2>&1
30 4 * * * /usr/bin/python3 /usr/local/bin/Main/nightly_circuit_history.py >> /var/log/circuit-history.log 2>&1

# System monitoring (CURRENTLY ACTIVE)
0 * * * * /usr/bin/python3 /usr/local/bin/Main/performance_monitor.py >> /var/log/performance-monitor.log 2>&1
*/5 * * * * /usr/local/bin/git_autocommit.sh
```

**Note:** The system uses a combined `nightly_meraki_enriched_db.py` script that handles both Meraki collection and data enrichment in a single optimized process.

### Database Scripts Status
- **All database scripts:** ✅ Deployed and running nightly
- **File elimination:** ✅ Complete - no more JSON/CSV file creation (~500MB/month saved)
- **Backup scripts:** Available as `*.bak-file-based` files for rollback if needed
- **Script optimization:** Combined Meraki collection and enrichment for better performance

## 🗄️ Database Schema & Models

### Primary Tables

#### 1. `circuits` Table (4,171+ records)
**Primary circuit data from DSR Global**
```sql
-- Key columns:
site_name VARCHAR(100) NOT NULL  -- Indexed
circuit_purpose VARCHAR(50)      -- Primary/Secondary
status VARCHAR(100)              -- Enabled/In Progress/etc
provider_name VARCHAR(100)       -- Circuit provider
billing_monthly_cost NUMERIC(10,2)
date_record_updated TIMESTAMP
assigned_to VARCHAR(100)         -- Personnel assignment
sctask VARCHAR(50)               -- ServiceNow task ID
manual_override BOOLEAN          -- Prevents DSR overwrites
```

#### 2. `circuit_history` Table (649+ records)
**Change tracking and historical analysis**
```sql
site_name VARCHAR(100)
change_type VARCHAR(50)  -- status/provider/speed/cost
old_value TEXT
new_value TEXT
change_date TIMESTAMP
detected_by VARCHAR(50)
```

#### 3. `daily_summaries` Table
**Enablement metrics and reporting**
```sql
summary_date DATE PRIMARY KEY
total_circuits INTEGER
today_enabled INTEGER
week_enabled INTEGER
month_enabled INTEGER
average_per_day DECIMAL(5,2)
```

#### 4. `firewall_rules` Table (55+ rules)
**L3 firewall rule templates**
```sql
network_name VARCHAR(100)  -- Template source
rule_number INTEGER
name VARCHAR(200)
protocol VARCHAR(20)
src_cidr VARCHAR(50)
src_port VARCHAR(50)
dest_cidr VARCHAR(50)
dest_port VARCHAR(50)
policy VARCHAR(20)  -- allow/deny
```

#### 5. `new_stores` Table
**New store construction tracking**
```sql
store_number VARCHAR(20)
region VARCHAR(50)
status VARCHAR(20)     -- 01-Planning, 02-Acquired, etc
tod DATE               -- Target Opening Date
address TEXT
created_date TIMESTAMP
```

### Performance Tables

#### 6. `performance_metrics` Table
**API endpoint monitoring (28 metrics/hour)**
```sql
endpoint VARCHAR(200)
method VARCHAR(10)
response_time_ms FLOAT
response_size_bytes INTEGER
status_code INTEGER
timestamp TIMESTAMP
```

#### 7. `switch_port_clients` Table
**Switch port visibility data (18,500+ active ports)**
```sql
store_name VARCHAR(100)          -- Store/network name
switch_name VARCHAR(100)         -- Switch device name
switch_serial VARCHAR(50)        -- Switch serial number
port_id VARCHAR(50)              -- Port identifier
hostname VARCHAR(200)            -- Connected device hostname
ip_address VARCHAR(50)           -- Device IP address
mac_address VARCHAR(50)          -- Device MAC address
vlan INTEGER                     -- VLAN assignment
manufacturer VARCHAR(100)        -- MAC OUI manufacturer
description TEXT                 -- Additional notes
last_seen TIMESTAMP              -- Last detection time
-- Unique constraint on (switch_serial, port_id, mac_address)
```

### Supporting Tables
- `provider_mappings` - Provider name normalization
- `circuit_assignments` - SCTASK and personnel tracking
- `meraki_inventory` - Device inventory (1,300+ devices)
- `enriched_circuits` - Enhanced circuit data with Meraki integration
- `inventory_summary` - Device model summaries with EOL/EOS

## 🔌 API Endpoints

### Core System APIs

#### Health & Monitoring
- `GET /api/health` - System health check
- `GET /api/stats/quick` - Quick system statistics
- `GET /performance` - Performance monitoring dashboard

#### Circuit Management
- `GET /api/circuits/search` - Circuit search with filters
  - Parameters: `status`, `provider`, `assigned_to`, `sctask`
- `POST /confirm/<site_name>` - Get circuit confirmation data
- `POST /confirm/<site_name>/submit` - Submit confirmed circuit data
- `POST /push_to_meraki` - Push confirmed circuits to Meraki

#### Dashboard & Analytics
- `GET /api/dashboard-data` - Dashboard statistics (160ms avg)
- `GET /api/inflight-data` - In-flight circuit orders (17ms avg)
- `POST /api/circuit-changelog` - Historical changes (41ms avg)
  - Body: `{"timePeriod": "last_week"}`

#### Inventory Management
- `GET /api/inventory-summary` - Device summaries (8ms avg)
- `GET /api/inventory-details` - Detailed inventory (12ms avg)
- `GET /api/networks` - List Meraki networks (16ms avg)

#### Reporting
- `GET /api/daily-enablement-data` - Enablement metrics (7ms avg)

#### New Stores Management
- `GET /api/new-stores` - All new stores (7ms avg)
- `POST /api/new-stores/manual` - Add stores manually
- `POST /api/new-stores/upload` - Upload Excel file
- `PUT /api/new-stores/<id>` - Update store
- `DELETE /api/new-stores/<id>` - Remove store
- `GET /api/new-store-circuits-with-tod` - Circuits with TOD (13ms avg)

#### Firewall Management
- `GET /api/firewall/rules/<network>` - Get firewall rules
- `POST /api/firewall/rules/<network>` - Update firewall rules

#### Switch Port Visibility
- `GET /api/switch-port-clients` - Get all switch port client data
  - Returns: Filtered list with store/switch hierarchy
- `POST /api/switch-port-clients/refresh-store/<store>` - Refresh all switches in a store
  - Returns: Updated client count and processing status
- `POST /api/switch-port-clients/refresh-switch/<serial>` - Refresh a specific switch
  - Returns: Updated client count for the switch
- `GET /api/switch-port-clients/export` - Export data to Excel
  - Returns: Excel file download with all visible data

*Note: Average response times from performance monitoring*

## 📊 Performance Metrics

### Database Performance Improvements
| Operation | File-Based | Database | Improvement |
|-----------|------------|----------|-------------|
| Circuit queries | 5000ms | 50ms | **100x faster** |
| Dashboard loading | 5000ms | 200ms | **25x faster** |
| Historical analysis | 30000ms | 2000ms | **15x faster** |
| Search operations | 2000ms | 20ms | **100x faster** |
| Data consistency | Manual | ACID | **Automatic** |

### Current API Performance (Hourly Monitoring)
- **Average response time:** 24.46ms across 14 endpoints
- **Data throughput:** 1.2MB average per monitoring cycle
- **Error rate:** 0% (all endpoints healthy)
- **Monitoring coverage:** 28 metrics collected per hour
- **Performance tracking:** 90-day data retention

### System Resource Usage
- **Database size:** ~50MB (circuits, history, summaries)
- **Memory usage:** ~200MB (Flask + SQLAlchemy + Redis)
- **CPU usage:** <5% during normal operations
- **Storage savings:** ~500MB/month (eliminated JSON/CSV file creation)

## 🔧 Key System Files

### Application Core
```
/usr/local/bin/Main/
├── dsrcircuits_integrated.py    # Main Flask application
├── config.py                     # Database & app configuration
├── models.py                     # SQLAlchemy database models
└── utils.py                      # Shared utilities & Meraki integration
```

### Blueprint Modules
```
├── dsrcircuits.py               # Main circuits management
├── status.py                    # Dashboard & status overview
├── historical.py                # Change tracking & analysis
├── inventory.py                 # Device inventory management
├── reports.py                   # Enablement reporting
├── new_stores.py                # New store construction tracking
├── performance.py               # System performance monitoring
└── tags.py                      # Device tagging system
```

### Database Scripts (Ready for Cron Deployment)
```
├── nightly_dsr_pull_db_with_override.py     # DSR data import with protection
├── nightly_meraki_db.py                     # Meraki inventory & firewall collection
├── nightly_inventory_db.py                  # Inventory processing
├── nightly_enriched_db.py                   # Data enrichment
├── nightly_enablement_db.py                 # Enablement tracking
├── nightly_circuit_history.py               # Change detection
└── performance_monitor.py                   # API performance monitoring ✅
```

### Templates & UI
```
/usr/local/bin/templates/
├── home.html                    # Central navigation hub
├── dsrcircuits.html             # Main circuits interface
├── dsrdashboard.html            # Status dashboard
├── new_stores.html              # New store management
├── performance_dashboard.html   # Performance monitoring
├── meraki_firewall.html         # Firewall management
└── [additional templates...]
```

### Service Configuration
```
/etc/systemd/system/dsrcircuits.service     # Systemd service definition
/usr/local/bin/meraki.env                   # Environment variables
```

### Backup Files (Rollback Capability)
```
/usr/local/bin/Main/
├── *.py.bak-file-based          # File-based system backups
├── MIGRATION_ROLLBACK_PLAN.md   # Rollback procedures
└── /usr/local/bin/backups/      # Data backups
```

## 🚨 Critical Operations

### Emergency Service Recovery
```bash
# Check service status
systemctl status dsrcircuits.service

# View recent logs
journalctl -u dsrcircuits.service --since "1 hour ago"

# Test in foreground (if service fails)
systemctl stop dsrcircuits.service
cd /usr/local/bin/Main
python3 dsrcircuits_integrated.py
# If working, Ctrl+C and restart service
systemctl start dsrcircuits.service
```

### Database Connection Test
```bash
# Test database connectivity
psql -U dsradmin -d dsrcircuits -h localhost -c "SELECT COUNT(*) FROM circuits;"

# Test application health
curl http://localhost:5052/api/health | jq .
```

### Manual Override Management
```sql
-- Check circuits with manual override protection
SELECT site_name, circuit_purpose, manual_override_date, manual_override_by
FROM circuits 
WHERE manual_override = TRUE
ORDER BY manual_override_date DESC;

-- Remove manual override (allow DSR updates)
UPDATE circuits 
SET manual_override = FALSE, manual_override_date = NULL, manual_override_by = NULL
WHERE site_name = 'SITE_NAME';
```

### Performance Monitoring
```bash
# Check API performance manually
python3 /usr/local/bin/Main/performance_monitor.py

# View performance logs
tail -f /var/log/performance-monitor.log

# Access performance dashboard
curl http://localhost:5052/performance
```

## 📈 Monitoring & Logging

### Log Files
| Service | Log Location | Purpose | Rotation |
|---------|-------------|---------|----------|
| DSR Circuits | `journalctl -u dsrcircuits.service` | Application logs | systemd |
| Performance | `/var/log/performance-monitor.log` | API metrics | Manual |
| DSR Pull | `/var/log/dsr-pull-db.log` | Data import | Daily |
| Meraki | `/var/log/meraki-mx-db.log` | Inventory collection | Daily |
| Inventory | `/var/log/nightly-inventory-db.log` | Processing | Daily |
| Enrichment | `/var/log/nightly-enriched-db.log` | Data enhancement | Daily |
| Enablement | `/var/log/nightly-enablement-db.log` | Metrics | Daily |
| History | `/var/log/circuit-history.log` | Change tracking | Daily |

### Monitoring Endpoints
- **Health Check:** `curl http://localhost:5052/api/health`
- **Quick Stats:** `curl http://localhost:5052/api/stats/quick`
- **Performance Dashboard:** http://localhost:5052/performance

### Key Metrics to Monitor
1. **Circuit Count:** Should maintain ~4,171 records
2. **Database Health:** PostgreSQL connectivity
3. **API Response Times:** <100ms for most endpoints
4. **Service Uptime:** dsrcircuits.service should always be active
5. **Cron Job Execution:** Check log files for nightly script completion

## 🔄 System Maintenance

### Daily Checks
1. Service status: `systemctl status dsrcircuits.service`
2. Database health: `curl http://localhost:5052/api/health`
3. Recent logs: `journalctl -u dsrcircuits.service --since yesterday`
4. Performance metrics: Check `/performance` dashboard

### Weekly Tasks
1. Review performance trends
2. Check manual override circuits
3. Verify cron job execution
4. Monitor database growth

### Monthly Tasks
1. Review enablement reports
2. Analyze historical changes
3. Update firewall templates if needed
4. Check for system updates

---

## 🔒 Security & Access

### Authentication
- **System Access:** SSH key-based authentication
- **Database:** Local PostgreSQL with dedicated user
- **Git Repository:** http://10.46.0.3:3000/mbambic/usr-local-bin
- **AWX Access:** admin/admin (reset as needed)

### Data Protection
- **Database Backups:** Automated PostgreSQL backups
- **Code Versioning:** Git repository with auto-commits
- **Manual Override Protection:** Prevents accidental data overwrites
- **Error Logging:** Comprehensive error tracking and alerting

---

## 📞 Support & Documentation

### Quick Reference
- **Main Application:** http://10.46.0.3:5052
- **Service Command:** `systemctl restart dsrcircuits.service`
- **Database:** `psql -U dsradmin -d dsrcircuits`
- **Logs:** `journalctl -u dsrcircuits.service -f`

### Additional Documentation
- **AI Context:** `/usr/local/bin/Main/CLAUDE.md`
- **Database Schema:** `/usr/local/bin/Main/DATABASE_SCHEMA_DOCUMENTATION.md`
- **Modal System:** `/usr/local/bin/Main/MODAL_COMPLETE_DOCUMENTATION.md`
- **Enablement Tracking:** `/usr/local/bin/Main/ENABLEMENT_TRACKING_DOCUMENTATION.md`
- **New Stores TOD:** `/usr/local/bin/Main/NEW_STORES_TOD_DOCUMENTATION.md`
- **Rollback Plan:** `/usr/local/bin/Main/MIGRATION_ROLLBACK_PLAN.md`
- **Git Repository:** http://10.46.0.3:3000/mbambic/usr-local-bin

### Common Issues & Solutions
1. **Service won't start:** Check database connectivity and port availability
2. **Database connection errors:** Verify PostgreSQL service and credentials
3. **Performance issues:** Check Redis cache and database indexes
4. **Missing data:** Verify cron jobs are running and check log files
5. **Modal shows literal \n:** Run `python3 /usr/local/bin/Main/fix_all_notes_and_arin.py`
6. **ARIN data incorrect:** Same fix script updates ARIN providers from live data
7. **Database column errors:** See `/usr/local/bin/Main/DATABASE_SCHEMA_DOCUMENTATION.md` for correct column names per table

### Modal Display Issues
If the Confirm modal shows notes with literal `\n` characters or incorrect ARIN data:
1. **Quick Fix:** Run `python3 /usr/local/bin/Main/fix_all_notes_and_arin.py`
2. **Clear Cache:** Press Ctrl+F5 in your browser
3. **Documentation:** See `/usr/local/bin/Main/MODAL_COMPLETE_DOCUMENTATION.md`

### Enablement Tracking Troubleshooting
If enablement counts seem incorrect:
1. **Check the average:** Should be ~0.7 per day, NOT 18+
2. **Verify the logic:** Only counts "Ready for Enablement" → "Enabled" transitions
3. **Check attribution:** Empty assigned_to shows as "Unknown"
4. **Verify tables:** Use `daily_enablements` NOT `circuit_enablements`
5. **Check logs:** `grep "Ready->Enabled" /var/log/nightly-enablement-db.log`
6. **Reference:** See `/usr/local/bin/Main/enablement_restoration_notes.md`

---

## 📋 Recent Updates

### June 30, 2025 - Comprehensive EOL Tracking
- **Comprehensive EOL Tracking System:** Complete overhaul of End-of-Life tracking
  - Downloads and parses ALL 164 PDFs from Meraki EOL page
  - Scrapes HTML tables for complete date information
  - Merges both sources for comprehensive coverage
  - 505 models now have EOL data (up from ~200)
  - MS120 family correctly shows: EOS March 28, 2025, EOL March 28, 2030
  - Stores all data in `meraki_eol_enhanced` database table
  - Updated `nightly_inventory_db.py` to use enhanced database
  - Created `/var/www/html/meraki-data/EOL/` with all EOL PDFs
  - Runs nightly at 1:15 AM via cron

### June 27, 2025 - Notes Feature and System Health
- **Notes Column:** Added to new-stores page with auto-save on blur
  - Notes persist until circuit is enabled or cancelled
  - Added `notes` field to circuits table (TEXT type)
  - Auto-clear notes on circuit completion
- **System Health Monitoring:** New comprehensive server monitoring page at `/system-health`
  - CPU, memory, disk, network, and database monitoring
  - Real-time updates with toggleable auto-refresh
  - Health score calculation and PDF export

---

**System Status:** ✅ Production Ready - Database Integrated  
**Last Updated:** June 30, 2025  
**Next Review:** Monitor enhanced EOL tracking performance