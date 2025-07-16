# DSR Circuits - Nightly Scripts Documentation

## Overview
**Directory**: `/usr/local/bin/Main/nightly/`  
**Purpose**: Automated data collection, synchronization, and enrichment processes  
**Schedule**: Runs via cron from midnight to 4:30 AM daily  
**Database**: PostgreSQL with transactional integrity

## Critical Finding: Primary Key Architecture

### Current Implementation
**The circuits table does NOT use record_number as primary key**. Instead:
- **Primary Key**: Auto-increment integer `id`
- **Unique Constraint**: `(site_name, circuit_purpose)` combination
- **Record Number**: Stored as a regular column for reference only

### Implications
1. **Site-based tracking**: All operations key on site_name + circuit_purpose
2. **Record number usage**: Used for correlation but not as primary identifier
3. **Manual override protection**: Based on site_name matching, not record_number

## Nightly Script Execution Schedule

### Cron Schedule (from crontab)
```bash
0 0 * * * cd /usr/local/bin/Main && python3 nightly/update_circuits_from_tracking_with_override.py
0 1 * * * cd /usr/local/bin/Main && python3 nightly/nightly_meraki_db.py
0 2 * * * cd /usr/local/bin/Main && python3 nightly/nightly_all_orgs_meraki_db.py
0 3 * * * cd /usr/local/bin/Main && python3 nightly/nightly_enriched_db.py
0 4 * * * cd /usr/local/bin/Main && python3 nightly/nightly_enablement_db.py
30 4 * * * cd /usr/local/bin/Main && python3 nightly/nightly_history_db.py
```

## Script-by-Script Database Logic

### 1. DSR Data Import Script
**File**: `update_circuits_from_tracking_with_override.py`  
**Schedule**: Midnight (0 0 * * *)  
**Purpose**: Import circuit data from DSR Global CSV files

#### Database Operations
```python
# UPSERT logic with manual override protection
INSERT INTO circuits (columns...)
VALUES (values...)
ON CONFLICT (site_name, circuit_purpose) DO UPDATE SET
    column = EXCLUDED.column
WHERE circuits.manual_override = FALSE
```

#### Key Features
- **Manual Override Protection**: Skips updates if `manual_override = TRUE`
- **Fingerprint Deduplication**: Creates hash of key fields to detect changes
- **Transaction Support**: Full rollback on any error
- **Data Validation**: Extensive field validation and normalization

#### Data Fields Imported
- `site_name`, `site_id`, `record_number`
- `circuit_purpose`, `provider`, `speed`
- `status`, `sub_status`, `notes`
- `desired_cktid`, `current_cktid`
- `project_manager`, `regional_manager`
- All date fields (install, ready_for, etc.)

### 2. Meraki Device Collection
**File**: `nightly_meraki_db.py`  
**Schedule**: 1 AM (0 1 * * *)  
**Purpose**: Collect device inventory from Meraki Dashboard API

#### Database Operations
```sql
-- Check if device exists
SELECT serial FROM meraki_inventory WHERE serial = ?

-- Update existing device
UPDATE meraki_inventory SET ... WHERE serial = ?

-- Insert new device
INSERT INTO meraki_inventory (columns...) VALUES (...)
```

#### Key Features
- **ARIN RDAP Integration**: Real-time ISP lookups for WAN IPs
- **Caching Strategy**: 30-day RDAP cache to reduce API calls
- **Provider Normalization**: Standardizes ISP names
- **New Store Detection**: Auto-identifies stores not in circuits table

#### Data Collected
- Device details (serial, model, MAC, firmware)
- Network info (name, tags, notes)
- WAN IP addresses and ARIN providers
- Uplink status and configuration

### 3. Multi-Org Inventory Collection
**File**: `nightly_all_orgs_meraki_db.py`  
**Schedule**: 2 AM (0 2 * * *)  
**Purpose**: Extended inventory collection across all Meraki organizations

#### Database Operations
- Similar to single-org script but processes multiple organizations
- Handles 60+ distinct device models
- Processes 13,000+ devices across 1,400+ networks

### 4. Data Enrichment Process
**File**: `nightly_enriched_db.py`  
**Schedule**: 3 AM (0 3 * * *)  
**Purpose**: Match and enrich circuit data with Meraki device information

#### Database Operations
```sql
-- Truncate and rebuild approach
TRUNCATE TABLE enriched_circuits;

-- Insert enriched data with matching logic
INSERT INTO enriched_circuits 
SELECT ... FROM circuits c
LEFT JOIN meraki_inventory m ON (matching conditions)
```

#### Matching Algorithm (Priority Order)
1. **IP Address Match**: WAN1/WAN2 IP exact match
2. **Provider + Store Match**: Normalized provider name + store
3. **Fallback**: Circuit data only (no Meraki match)

#### Enrichment Fields Added
- Meraki serial numbers and device details
- WAN IP addresses and ARIN providers
- Uplink statuses
- Device tags and notes

### 5. Enablement Tracking
**File**: `nightly_enablement_db.py`  
**Schedule**: 4 AM (0 4 * * *)  
**Purpose**: Track circuit enablement transitions and team performance

#### Database Operations
```sql
-- Clear existing data for date range
DELETE FROM daily_enablements WHERE date >= ?

-- Insert new enablement records
INSERT INTO daily_enablements (site_id, date, enabled_by, record_number)
VALUES (?, ?, ?, ?)

-- Update summary statistics
INSERT OR REPLACE INTO enablement_summary (date, enablements_count)
```

#### Tracking Logic
- **Status Transition**: "Ready for Enablement" → "Enabled"
- **Attribution**: Links to circuit_assignments for team member
- **90-Day History**: Maintains rolling 90-day window
- **Site-based**: Uses Site ID as primary identifier

### 6. Historical Change Tracking
**File**: `nightly_history_db.py`  
**Schedule**: 4:30 AM (30 4 * * *)  
**Purpose**: Audit trail of all circuit changes

#### Database Operations
```sql
-- Insert change records
INSERT INTO circuit_history 
(circuit_id, field_name, old_value, new_value, change_date)
VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
```

#### Change Detection
- Compares current state with previous day
- Records field-level changes
- Maintains complete audit trail
- Excludes timestamp fields from comparison

## Database Schema Implications

### Primary Keys Across Tables
```sql
-- All tables use auto-increment IDs, NOT record_number
circuits: id (PRIMARY KEY), UNIQUE(site_name, circuit_purpose)
meraki_inventory: id (PRIMARY KEY), serial (UNIQUE)
enriched_circuits: id (PRIMARY KEY)
circuit_assignments: id (PRIMARY KEY)
daily_enablements: id (PRIMARY KEY)
```

### Record Number Usage
- **Storage**: Regular column in circuits table
- **Purpose**: Reference/correlation with DSR Global
- **Not Used For**: Primary key, joins, or unique constraints
- **Assignment Lookups**: May use record_number for correlation

## Data Flow Architecture

```
DSR Global CSV Files
    ↓ (Midnight)
update_circuits_from_tracking_with_override.py
    ↓
PostgreSQL circuits table
    ↓ (1-2 AM)
Meraki API → nightly_meraki_db.py
    ↓
PostgreSQL meraki_inventory table  
    ↓ (3 AM)
nightly_enriched_db.py (matching logic)
    ↓
PostgreSQL enriched_circuits table
    ↓ (4 AM)
nightly_enablement_db.py (status tracking)
    ↓
PostgreSQL daily_enablements table
```

## Error Handling & Monitoring

### Transaction Management
- All scripts use database transactions
- Automatic rollback on errors
- Commit only on successful completion

### Logging
- Logs to `/var/log/[script-name].log`
- Includes error details and stack traces
- Timestamp for each operation

### Data Validation
- Date parsing with multiple format support
- Provider name normalization
- IP address validation
- Duplicate detection and handling

## Manual Intervention Points

### Manual Override Flag
- Set via web interface or direct database update
- Prevents automated updates to specific circuits
- Preserves manually entered data
- Based on site_name, not record_number

### Data Source Indicators
- `data_source` column tracks origin
- Values: 'tracking', 'manual', 'new_stores'
- Used for filtering and reporting

## Performance Considerations

### Database Optimization
- Indexed columns: site_name, site_id, serial, record_number
- Bulk operations where possible
- Connection pooling via SQLAlchemy
- Efficient JOIN strategies

### API Rate Limiting
- Meraki API: Request throttling
- ARIN RDAP: 30-day caching
- Batch processing for efficiency

## Recommendations

### Primary Key Architecture
**Current state is actually correct** for this use case:
1. **Site-based business logic**: The unique constraint on (site_name, circuit_purpose) matches business requirements
2. **Record number flexibility**: Can change without breaking relationships
3. **Manual override protection**: Works correctly with site-based logic

### Potential Improvements
1. **Add index on record_number**: For faster assignment lookups
2. **Foreign key constraints**: Add where relationships exist
3. **Partitioning**: Consider date-based partitioning for history tables
4. **Monitoring**: Add execution time tracking and alerts

---
*Last Updated: July 3, 2025*  
*Comprehensive nightly script database logic documentation*  
*Part of DSR Circuits Documentation Suite*