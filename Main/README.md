# DSR Circuits - Network Infrastructure Management System

## Overview
Comprehensive circuit tracking, monitoring, and inventory management system for Discount Tire network infrastructure. Built with Flask, PostgreSQL, and Meraki API integration.

## System Status
- **Environment**: Production (`/usr/local/bin/Main/`)
- **Database**: PostgreSQL with 4,171+ circuit records
- **Networks**: 1,411+ Meraki networks tracked
- **API Performance Monitoring**: ✅ Active (24 endpoints monitored hourly)
- **Last Updated**: July 4, 2025

## Quick Access
**Primary URL**: `http://neamsatcor1ld01.trtc.com:5052/home`

## Web Application Documentation

### 📖 Complete Page Documentation
**Web-Accessible Documentation:**
- View this README online: `http://neamsatcor1ld01.trtc.com:5052/readme`
- Individual documentation files: `http://neamsatcor1ld01.trtc.com:5052/docs/[filename].md`

**Available Documentation Files (accessible via /docs/):**

Each page includes comprehensive documentation with:
- Complete button and functionality details
- User workflows and scenarios
- Technical implementation details
- API endpoints and data sources

### 🏠 Primary Navigation Pages
- **Home Page** ([View Online](http://neamsatcor1ld01.trtc.com:5052/docs/HOME_PAGE.md)) - Main navigation hub with all system access points
- **DSR Dashboard** ([View Online](http://neamsatcor1ld01.trtc.com:5052/docs/DSR_DASHBOARD.md)) - Real-time circuit status tracking and assignment management
- **New Stores Management** ([View Online](http://neamsatcor1ld01.trtc.com:5052/docs/NEW_STORES.md)) - Store construction and circuit planning

### 📊 Reporting & Analytics
- **Circuit Enablement Report** - Multi-tab performance analytics with team attribution
- **Historical Data** - Circuit change tracking and audit trails
- **Circuit Orders** - Order management and procurement tracking

### 🔧 Network Operations
- **Inventory Summary** - Device tracking and EOL monitoring (13,000+ total devices across 60+ models)
- **Non-Meraki Inventory Collection** - 🚧 **Work in Progress** - SNMP-based inventory collection for traditional network devices ([Details](inventory.md))
- **Switch Port Visibility** - Real-time port monitoring and client tracking
- **Subnet Analysis** ([View Online](http://neamsatcor1ld01.trtc.com:5052/docs/SUBNET_ANALYSIS.md)) - Network subnet visualization and VLAN analysis
- **Firewall Management** - Security rule administration with template system
- **Tag Management** - Device tagging and organization

### 🎯 System Administration
- **System Health Monitor** - Infrastructure monitoring and diagnostics
- **Performance Monitoring** - System performance tracking and optimization

## Key Features

### Circuit Management
- **Real-time Status Tracking**: Live circuit status with assignment management
- **Record Number Integration**: DSR Global record_number correlation for accurate tracking
- **Assignment Management**: SCTASK and team member assignment tracking
- **Automated Workflows**: Integration with ServiceNow and Meraki systems

### Store Construction Management
- **Target Opening Date (TOD) Tracking**: Complete store construction lifecycle management
- **Excel Bulk Upload**: Streamlined data import with validation
- **Auto-Record Number Generation**: Unique DSR-format record number creation
- **Meraki Auto-Detection**: Automatic cleanup when stores become operational

### Network Device Management
- **Live Inventory Tracking**: Real-time device status and configuration monitoring
- **End-of-Life Management**: Automated EOL detection and replacement planning
- **Port Visibility**: Switch port client monitoring and identification
- **Firewall Rule Management**: Template-based security rule deployment

### Performance Analytics
- **Daily Enablement Tracking**: Circuit enablement trends and team performance
- **Team Attribution**: Individual team member performance tracking
- **Historical Analysis**: Long-term trend analysis and reporting
- **Export Capabilities**: Excel, PDF, and CSV export functionality

## Technical Architecture

### Core Technology Stack
- **Backend**: Python Flask with SQLAlchemy ORM
- **Database**: PostgreSQL with optimized indexing
- **Caching**: Application-level caching (Redis not currently configured)
- **Frontend**: HTML5, CSS3, JavaScript with Chart.js
- **API Integration**: Meraki Dashboard API, DSR Global CSV imports

### Database Schema
- **circuits**: Primary circuit data (4,171+ records)
- **circuit_assignments**: Assignment tracking and SCTASK correlation
- **meraki_inventory**: Network device tracking (13,109+ devices)
- **new_stores**: Construction project management
- **circuit_history**: Change tracking and audit trails

### Integration Points
- **DSR Global**: Daily CSV imports with record_number synchronization
- **Meraki API**: Real-time device data and configuration management
- **ServiceNow**: SCTASK ticket correlation and assignment tracking
- **Git Repository**: Version control and deployment automation

## Recent Enhancements (July 2025)

### Non-Meraki Network Device Inventory (Work in Progress)
- **SNMP Collection System**: Successfully collected inventory from 345 devices (90.3% success rate)
- **Parallel Processing**: 5-worker system processed 382 devices in 44.8 minutes
- **Credential Management**: Working credentials documented (DTC4nmgt v2c, multiple SNMPv3 users)
- **Data Volume**: 849,832 inventory lines collected from network infrastructure
- **Failed Device Tracking**: Excel report with 37 failed devices documented by location/type
- **Implementation Details**: See [inventory.md](inventory.md) for complete technical documentation

### Record Number Implementation
- **Tracking Strategy**: DSR Global record_numbers used as reference identifiers (NOT primary keys)
- **Cross-System Correlation**: Enhanced tracking between DSR Global, database, and ServiceNow
- **Auto-Generation**: Unique record number creation for manually created circuits
- **Data Integrity**: Prevention of duplicate tracking and lost assignment data

### Assignment Data Improvements
- **Enhanced Correlation**: Site-based assignment tracking with record_number reference
- **Data Merging**: Priority-based merging from circuit_assignments table
- **Site-Based Counting**: Fixed duplicate counting issues (14→10 unique sites)
- **Complete Attribution**: All missing assignment data now displays correctly

### Performance Optimizations
- **Database Indexing**: Optimized queries on site_id and record_number
- **Caching Strategy**: Redis-backed response caching with 30-second refresh
- **Query Optimization**: Efficient data retrieval with minimal database load
- **Real-time Updates**: JavaScript polling for live data synchronization

## Development & Deployment

### Service Configuration
- **SystemD Service**: `meraki-dsrcircuits.service`
- **Working Directory**: `/usr/local/bin/Main`
- **Port**: 5052 (Flask application, direct access)
- **Environment**: Production with debug disabled

### Maintenance Schedule (Crontab)
```bash
# DSR CSV import with manual override protection
0 0 * * * /usr/bin/python3 /usr/local/bin/Main/nightly/nightly_dsr_pull_db_with_override.py >> /var/log/dsr-pull-db.log 2>&1

# Meraki device collection
0 1 * * * /usr/bin/python3 /usr/local/bin/Main/nightly/nightly_meraki_db.py >> /var/log/meraki-mx-db.log 2>&1

# Full inventory scan
0 2 * * * /usr/bin/python3 /usr/local/bin/Main/nightly/nightly_inventory_db.py >> /var/log/nightly-inventory-db.log 2>&1

# Data enrichment/matching
0 3 * * * /usr/bin/python3 /usr/local/bin/Main/nightly/nightly_enriched_db.py >> /var/log/nightly-enriched-db.log 2>&1

# Process enablement tracking in database (4 AM)
0 4 * * * /usr/bin/python3 /usr/local/bin/Main/nightly/nightly_enablement_db.py >> /var/log/nightly-enablement-db.log 2>&1

# Circuit change history
30 4 * * * /usr/bin/python3 /usr/local/bin/Main/nightly/nightly_circuit_history.py >> /var/log/circuit-history.log 2>&1

# Hourly API performance monitoring (ACTIVE - 24 endpoints)
0 * * * * /usr/bin/python3 /usr/local/bin/Main/nightly/hourly_api_performance.py >> /var/log/api-performance.log 2>&1
```

## Support & Documentation

### Complete Documentation Suite

#### Web Interface Documentation
[Home Page Guide](http://neamsatcor1ld01.trtc.com:5052/docs/HOME_PAGE.md)

[DSR Dashboard Guide](http://neamsatcor1ld01.trtc.com:5052/docs/DSR_DASHBOARD.md)

[New Stores Management Guide](http://neamsatcor1ld01.trtc.com:5052/docs/NEW_STORES.md)

[Circuit Enablement Report Guide](http://neamsatcor1ld01.trtc.com:5052/docs/CIRCUIT_ENABLEMENT_REPORT.md)

[Historical Data Guide](http://neamsatcor1ld01.trtc.com:5052/docs/DSR_HISTORICAL.md)

[Circuit Orders Guide](http://neamsatcor1ld01.trtc.com:5052/docs/CIRCUIT_ORDERS.md)

[Inventory Summary Guide](http://neamsatcor1ld01.trtc.com:5052/docs/INVENTORY_SUMMARY.md)

[Switch Port Visibility Guide](http://neamsatcor1ld01.trtc.com:5052/docs/SWITCH_VISIBILITY.md)

[Subnet Analysis Guide](http://neamsatcor1ld01.trtc.com:5052/docs/SUBNET_ANALYSIS.md)

[Firewall Management Guide](http://neamsatcor1ld01.trtc.com:5052/docs/FIREWALL_MANAGEMENT.md)

[Tag Management Guide](http://neamsatcor1ld01.trtc.com:5052/docs/TAG_MANAGEMENT.md)

[System Health Monitor Guide](http://neamsatcor1ld01.trtc.com:5052/docs/SYSTEM_HEALTH.md)

[Performance Monitoring Guide](http://neamsatcor1ld01.trtc.com:5052/docs/PERFORMANCE_MONITORING.md)

#### Technical Documentation
[Nightly Scripts Documentation](http://neamsatcor1ld01.trtc.com:5052/docs/NIGHTLY_SCRIPTS.md)

[Flask Scripts Documentation](http://neamsatcor1ld01.trtc.com:5052/docs/FLASK_SCRIPTS.md)

[Primary Key Analysis](http://neamsatcor1ld01.trtc.com:5052/docs/PRIMARY_KEY_ANALYSIS.md)

#### Additional Resources
[Main README](http://neamsatcor1ld01.trtc.com:5052/readme)

[README Line-by-Line Verification](http://neamsatcor1ld01.trtc.com:5052/docs/README_LINE_BY_LINE_VERIFICATION.md)

[URL Validation Report](http://neamsatcor1ld01.trtc.com:5052/docs/URL_VALIDATION_REPORT.md)

[Documentation Access Guide](http://neamsatcor1ld01.trtc.com:5052/docs/DOCUMENTATION_ACCESS_GUIDE.md)

### Getting Started
1. **Access System**: Navigate to `http://neamsatcor1ld01.trtc.com:5052/home`
2. **Choose Your Role**: Select appropriate navigation based on your responsibilities
3. **Review Documentation**: Consult page-specific documentation for detailed workflows
4. **Contact Support**: Reference documentation or contact system administrators

---
*Last Updated: July 4, 2025*  
*Production Environment - 4,171+ circuits tracked across 1,411+ networks*  
*Enhanced with API performance monitoring (24 endpoints) and comprehensive documentation*