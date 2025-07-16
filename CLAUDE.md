# DSR Circuits - Comprehensive Circuit Management System

## ⚠️ MIGRATION NOTICE - JULY 2, 2025
**This server (10.46.0.3) has been MIGRATED to new server (10.0.145.130)**
- **Original Server:** 10.46.0.3 - **SHUTDOWN** after migration
- **New Production Server:** 10.0.145.130 - **ACTIVE**
- **Migration Date:** July 2, 2025
- **Migration Documentation:** [MIGRATION_TO_REMOTE_SERVER_20250702.md](http://10.0.145.130:8080/docs/MIGRATION_TO_REMOTE_SERVER_20250702.md)

## Project Overview

**Project Name:** DSR Circuits - Database-Integrated Circuit Management System  
**Organization:** Discount Tire  
**Status:** **MIGRATED** to 10.0.145.130  
**Previous Location:** `neamsatcor1ld01.trtc.com` (10.46.0.3) - **SHUTDOWN**  
**New Location:** `neamsatcor1ld01.trtc.com` (10.0.145.130) - **PRODUCTION**  

## System Architecture Summary

### Production Environment (MIGRATED)
- **Previous Location:** `/usr/local/bin/Main/` on 10.46.0.3 - **INACTIVE**
- **New Location:** `/usr/local/bin/` on 10.0.145.130 - **ACTIVE**
- **System:** PostgreSQL database-integrated
- **Status:** Production (Migration Complete July 2, 2025)
- **Data Pipeline:** DSR Global → PostgreSQL → Enhanced web interface

## Key System Information

### Infrastructure (NEW SERVER)
- **Platform:** Production server environment
- **External Access:** Port 5052 (direct Flask access)
- **Database:** PostgreSQL with optimized schema (migrated)
- **Web Framework:** Flask with SQLAlchemy
- **Server:** 10.0.145.130

### Data Sources (MIGRATED)
1. **DSR Global Portal:** Circuit tracking data (CSV)
2. **Meraki API:** Device inventory and network data
   - Uplink status endpoint for IP addresses
   - Device notes for provider/speed labels
3. **ARIN RDAP:** IP provider identification
   - Real-time ISP lookups via RDAP API
   - Caching mechanism to reduce API calls
   - Special handling for IP ranges (166.80.0.0/16)
4. **ServiceNow:** SCTASK assignment integration

### Migration Status
- **Circuits Table:** 7,026+ records  (100% migrated)
- **Meraki Inventory:** 1,300+ devices  (Complete migration)
- **Netdisco Integration:** 29 models, 132 devices (Traditional network infrastructure)
- **Enriched Circuits:** Full database integration migrated
- **Inventory Summary:** Combined Meraki + Netdisco unified view

## Current Development Context

### Migration Activities (July 2, 2025)
1. **Complete System Migration:** All files and database migrated to 10.0.145.130 ✅
2. **TOD Store Management:** Enhanced new stores features migrated ✅
3. **Database Integration:** All 33 tables with full data migrated ✅
4. **Enhanced Scripts:** 200+ Python scripts migrated ✅
5. **Documentation:** All .md files and documentation migrated ✅

### Active Processes (NEW SERVER)
- **Database Integration:** All processing via PostgreSQL on new server
- **TOD Management:** Target Opening Date tracking system
- **Enhanced Features:** System health monitoring, performance tracking
- **File Structure:** Adapted to new server's direct `/usr/local/bin/` structure

## Project Structure (PRODUCTION REORGANIZATION - JULY 3, 2025)

```
DSR Circuits Project (CLEAN PRODUCTION STRUCTURE)
   Production Server (10.0.145.130) - ACTIVE
      /usr/local/bin/Main/ - CLEAN PRODUCTION DIRECTORY
         dsrcircuits.py (main Flask app)
         models.py, config.py (core components)
         new_stores.py, eol_routes.py (supporting modules)
         templates/ (all HTML templates)
         static/ (CSS, JS, images)
         nightly/ (all nightly scripts)
            nightly_dsr_pull_db_with_override.py
            nightly_enablement_db.py
            nightly_meraki_db.py
            nightly_inventory_db.py
            nightly_enriched_db.py
            nightly_circuit_history.py
            update_circuits_from_tracking_with_override.py
      /usr/local/bin/ - Development/test scripts
         All other 200+ development scripts
      PostgreSQL database
      Service: meraki-dsrcircuits.service (points to Main/)
```

## Migration Documentation

### Complete Migration Record
- **Migration Log:** [MIGRATION_TO_REMOTE_SERVER_20250702.md](http://10.0.145.130:8080/docs/MIGRATION_TO_REMOTE_SERVER_20250702.md)
- **Files Transferred:** 314MB complete system archive
- **Database Export:** 25MB with all 33 tables
- **Documentation:** All .md files including updated CLAUDE.md

### New Server Structure
- **Main App:** `/usr/local/bin/dsrcircuits.py` (renamed from dsrcircuits_integrated.py)
- **Templates:** `/usr/local/bin/templates/`
- **Scripts:** All in `/usr/local/bin/` (no Main/ subdirectory)
- **Service:** Uses existing meraki-dsrcircuits.service

## Technical Notes (MIGRATED SYSTEM)

### Database Schema (MIGRATED)
- **Primary Tables:** circuits, circuit_history, new_stores, meraki_inventory, firewall_rules, circuit_assignments, provider_mappings, daily_summaries, firewall_deployment_log, rdap_cache, enriched_circuits, enrichment_change_tracking
- **Performance:** Indexed queries, connection pooling, ACID compliance
- **Records:** 7,026+ circuits with complete history
- **New Server:** PostgreSQL on 10.0.145.130

### Enhanced Features (MIGRATED)
- **TOD Store Management:** Target Opening Date tracking with enhanced UI
- **Excel Upload:** Smart duplicate handling (updates existing vs creating duplicates)
- **System Health Monitoring:** Comprehensive server monitoring
- **Performance Tracking:** API endpoint performance monitoring
- **Switch Port Visibility:** Enterprise-scale port monitoring
- **Database Integration:** All processing via PostgreSQL

### Application Stack (NEW SERVER)
```
┌─────────────────────────────────────────┐
│    Flask Application (Port 5052)        │
│           dsrcircuits.py                 │
├─────────────────────────────────────────┤
│  Enhanced Features (Migrated):          │
│  - new_stores.py (TOD management)       │
│  - system_health.py (monitoring)        │
│  - switch_visibility.py (port tracking) │
│  - performance.py (API monitoring)      │
├─────────────────────────────────────────┤
│  Database Models (models.py):           │
│  - Circuit, CircuitHistory              │
│  - NewStores (TOD tracking)             │
│  - All 33 migrated tables               │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│     PostgreSQL Database (Migrated)      │
│         7,026+ circuits                  │
│         33 tables with full data        │
└─────────────────────────────────────────┘
```

## Contact & Support (UPDATED)

**Primary System:** `10.0.145.130:5052` (NEW)  
**Previous System:** `10.46.0.3` (SHUTDOWN)  
**Migration Date:** July 2, 2025  
**Documentation:** 
- Migration Log: [MIGRATION_TO_REMOTE_SERVER_20250702.md](http://10.0.145.130:8080/docs/MIGRATION_TO_REMOTE_SERVER_20250702.md)
- System Docs: [README.md](http://10.0.145.130:8080/docs/README.md) (migrated)
- Full Context: [CLAUDE.md](http://10.0.145.130:8080/docs/CLAUDE.md) (this file, updated for new server)

## Post-Migration Status

### ✅ Completed
- All files transferred (314MB archive)
- Database migrated (25MB, 7,026+ circuits)
- Enhanced features available (TOD management, monitoring)
- Documentation updated for new server structure
- API Performance Monitoring: ✅ ACTIVE (24 endpoints monitored hourly)
- Performance optimization fixes completed (dsrcircuits, system health)

### ✅ Recent Fixes (July 4, 2025)
- Fixed dsrcircuits_blueprint module import error
- Restored API performance monitoring functionality
- Hourly performance collection working (24 endpoints across 9 categories)
- Performance monitoring page displaying real-time metrics
- System health endpoints optimized (2500ms → <200ms)
- DSR Circuits page optimized (2200ms → 148ms)

---

**Last Updated:** July 4, 2025 (Performance Monitoring Restored)  
**Migration Status:** Complete - All systems operational  
**Production Server:** 10.0.145.130  
**API Monitoring:** 24 endpoints tracked hourly with real-time performance metrics

## ✅ RECENT SYSTEM UPDATES (July 6, 2025)

### Circuit Enablement Report - ALL ISSUES RESOLVED ✅
**Location**: `/circuit-enablement-report`  
**Status**: ✅ **FULLY OPERATIONAL** - All tabs synchronized

#### Fixed Issues (July 6, 2025):
1. **Date Range Synchronization** ✅
   - All tabs now show consistent April 29, 2025 → Current Date
   - Tab 3 (Team Attribution) fixed to match Tab 1 date range
   - Automatic daily extension (April 29 → Today, grows daily)

2. **July 6th Display Issue** ✅ 
   - Fixed timezone conversion in `formatDate()` JavaScript function
   - Applied to all charts: Tab 1, Tab 3 (Team Attribution), Tab 4
   - Charts now properly display current day and future dates

3. **Tab Count Consistency** ✅
   - Tab 4 switched from old JSON files to database API
   - All tabs now show 41 total enablements consistently
   - Database-driven APIs across all tabs

4. **Tab 4 Date Header Formatting** ✅
   - Fixed CSS specificity conflicts in date header styling
   - Date group headers now display properly with dark blue background
   - Table grouping by date working correctly

5. **JavaScript Error Resolution** ✅
   - Fixed `loadTrend` function parameter handling
   - Page loads without console errors
   - All interactive features working

#### Current Performance Metrics:
- **Total Enablements**: 41 circuits (April 29 - July 6)
- **Date Range**: 69 days of data
- **Average**: 0.6 enablements per day
- **Peak Day**: May 30 (12 enablements)
- **Team Attribution**: 100% "Unknown" (ready for assignment data)

#### Technical Architecture:
```
CSV Data → nightly_enablement_db.py → PostgreSQL → Web APIs → Charts
```

**APIs (All Database-Integrated):**
- `/api/daily-enablement-data` - Tab 1 (complete date series)
- `/api/closure-attribution-data` - Tab 3 (team attribution) 
- `/api/enablement-details-list` - Tab 4 (detailed records)
- `/api/ready-queue-data` - Tab 2 (queue tracking)

**Chart Configuration (Standardized):**
```javascript
x: {
    type: 'category',
    ticks: { autoSkip: false, maxTicksLimit: 30 }
}
```

### Database Schema Updates
- **daily_enablements**: 41 records with team attribution
- **circuit_assignments**: 8 manual assignments (Taren Andrickson)
- **enablement_summary**: Pre-aggregated daily counts
- **Attribution Logic**: Manual assignments override CSV data

### Documentation Updates (July 6, 2025)
- ✅ **ENABLEMENT_TRACKING_LOGIC.md**: Complete rewrite with all fixes
- ✅ **CIRCUIT_ENABLEMENT_REPORT.md**: Updated with current architecture  
- ✅ **CLAUDE.md**: This section (current system status)



## Evening System Updates (July 6, 2025)

### ✅ Final Critical Fixes Completed

#### Circuit Enablement Report - Complete Resolution
**Issues Resolved (Evening Session):**

1. **July 7th Date Issue** ✅ FIXED
   - **Problem**: End date showing 2025-07-07 instead of 2025-07-06
   - **Cause**: JavaScript timezone conversion creating future date
   - **Solution**: Timezone-safe date calculation with explicit parsing
   - **Result**: Date field correctly shows today's date dynamically

2. **Tab 3 Timezone Shifting** ✅ FIXED  
   - **Problem**: Date labels showing "Jul 05" instead of "Jul 06"
   - **Cause**: `formatDate()` function timezone conversion shifting dates backward
   - **Solution**: Explicit date parsing without timezone conversion
   - **Result**: All date labels correctly match their date values

3. **Tab 4 CSS Formatting** ✅ FIXED
   - **Problem**: Date header styling broken, text not visible
   - **Cause**: CSS specificity conflict after debug system addition
   - **Solution**: Enhanced CSS selectors with `!important` overrides
   - **Result**: Date headers properly display with dark blue background

4. **Permanent Debug System** ✅ IMPLEMENTED
   - **Feature**: Comprehensive debugging for ongoing troubleshooting
   - **Coverage**: All tabs, date parameters, timezone validation
   - **Benefits**: Real-time issue detection and validation
   - **Status**: Active and monitoring system health

5. **Default Mode Optimization** ✅ UPDATED
   - **Change**: Default mode set to "All Available Data" 
   - **Benefit**: Loads complete dataset by default
   - **Smart Defaults**: Custom range pre-populated with dynamic dates
   - **Growth**: Automatically extends daily (July 6 → July 7 → July 8...)

### Technical Implementation Details

#### Timezone-Safe Date Handling
```javascript
// Prevents timezone conversion issues
const today = new Date();
const todayStr = today.getFullYear() + '-' + 
               String(today.getMonth() + 1).padStart(2, '0') + '-' + 
               String(today.getDate()).padStart(2, '0');

// Explicit date parsing prevents shifts
function formatDate(dateStr) {
    const parts = dateStr.split('-');
    const year = parseInt(parts[0]);
    const month = parseInt(parts[1]) - 1;
    const day = parseInt(parts[2]);
    const date = new Date(year, month, day);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}
```

#### Permanent Debug System  
```javascript
// Always-on debugging functions
logDebugHeader(tabName)     // Timestamped debug headers
logDateRange(params)        // Date parameter validation  
logDataSummary(data, type)  // Data analysis and validation
```

#### CSS Specificity Fixes
```css
.details-table .date-header {
    background: #34495e !important;
    color: white !important;
    font-weight: bold !important;
    text-align: center !important;
}
```

### Validation Results (July 6, 2025 - Evening)
- ✅ **All Tabs**: Show correct date ranges (April 29 → July 6)
- ✅ **July 6th Display**: Properly shows on all charts and tables
- ✅ **July 7th Prevention**: No future dates displayed
- ✅ **Debug System**: Active monitoring with comprehensive logging
- ✅ **Default Mode**: "All Available Data" loads complete dataset
- ✅ **Dynamic Dates**: Will automatically show July 7th tomorrow

### Files Updated (Evening)
- **Template**: `/usr/local/bin/templates/circuit_enablement_report.html` (primary)
- **Backup**: `/usr/local/bin/Main/templates/circuit_enablement_report.html` (secondary)
- **Documentation**: All .md files updated with final fixes
- **Service**: meraki-dsrcircuits.service restarted with latest changes

---

---



## System Updates (July 7, 2025)

### ✅ Circuit Enablement Report - Site ID Column Enhancement

#### Tab 4 Enhancement - Site ID Column Added
**Purpose**: Better circuit identification, especially for secondary circuits  
**Implementation**:
- Added Site ID column between Site Name and Circuit Purpose columns
- Shows circuit identifier that distinguishes primary vs secondary circuits
- Secondary circuits display with "-B" suffix (e.g., "LAS 03 -B")
- Primary circuits show matching Site ID and Site Name (e.g., "LAS 03")

#### Column Structure Update
**Tab 4 Column Order**:
1. Date - When the circuit was enabled
2. Site Name - Store name/location  
3. **Site ID** - Circuit identifier (NEW)
4. Circuit Purpose - Primary or Secondary
5. Provider - ISP/Carrier name
6. Previous Status - Status before enablement
7. Current Status - Should always be "Enabled"
8. Assigned To - Person who enabled the circuit
9. SCTASK - ServiceNow task number

#### Technical Details
- **Data Source**: Site ID populated from DSR tracking CSV data
- **Format Examples**:
  - Primary: "LAS 03" (matches site name)
  - Secondary: "LAS 03 -B", "TXD 76 -B", "NMA 05-B- B"
- **Benefits**: Clear identification of specific circuits at locations with multiple connections

### ✅ DSR Dashboard Enhancements

#### JavaScript Loading Fix (July 7, 2025)
**Issue**: Dashboard stuck on "Loading circuit data..." message
**Root Cause**: 
- JavaScript syntax error - extra closing brace on line 744
- Template location mismatch: Flask uses `/usr/local/bin/templates/` not `/usr/local/bin/Main/templates/`
**Resolution**:
- Fixed syntax error in `dsrdashboard.html`
- Copied corrected template to proper Flask template directory
- Added comprehensive debugging system for future troubleshooting

#### SCTASK Field Dual-Mode Implementation
**Feature**: SCTASK fields are now both editable AND clickable  
**Implementation**:
- Empty fields show input boxes for immediate entry
- Filled fields display as ServiceNow links with edit button (✏️)
- Edit mode provides save (✓) and cancel (✗) buttons
- Keyboard shortcuts: Enter to save, Escape to cancel
- Auto-saves maintain link functionality

#### Database Debug Console System
**Feature**: Comprehensive database vs page content debugging  
**Commands Available**:
- `debugDashboard.status()` - Show debug system status
- `debugDashboard.ready()` - Analyze Ready for Turn Up data
- `debugDashboard.compare()` - Compare table vs database
- `debugDashboard.timing()` - Show API call timing
- `debugDashboard.test()` - Run comprehensive system tests (NEW)
**Benefits**: Real-time verification of database consistency

### Documentation Updates
- **ENABLEMENT_TRACKING_LOGIC.md**: Added Tab 4 column structure documentation
- **CIRCUIT_ENABLEMENT_REPORT.md**: Updated with Site ID column details
- **CLAUDE.md**: This section documenting July 7 enhancements

---

**Last Updated:** July 7, 2025  
**Circuit Enablement Status:** ✅ **ALL ISSUES RESOLVED**  
**System Health:** ✅ **FULLY OPERATIONAL**  
**API Performance Monitoring:** ✅ **ACTIVE** (24 endpoints tracked hourly)
