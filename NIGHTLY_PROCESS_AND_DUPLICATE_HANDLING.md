# DSR Circuits - Nightly Process and Duplicate Handling Documentation

## Overview
This document explains the nightly data synchronization processes and how the system handles duplicate records.

## Current Issue: Migration Duplicates
During the server migration on July 2, 2025, duplicate circuit records were created for:
- INI 06 -B (2 records)
- MSG 01- B (2 records)
- TXD 76- B (2 records)

These duplicates have identical site_name, site_id, and circuit_purpose values, which should not occur.

## Nightly Process Schedule

### 00:00 - DSR Data Pull (`nightly_dsr_pull_db_with_override.py`)
**Purpose:** Download and sync circuit data from DSR Global Portal

**Process:**
1. Downloads CSV from DSR Global Portal
2. Parses circuit data
3. Uses UPSERT logic: `INSERT ... ON CONFLICT (site_name, circuit_purpose) DO UPDATE`
4. Skips circuits with `manual_override = TRUE`
5. Updates existing records based on site_name + circuit_purpose combination

**Duplicate Prevention:**
- Database constraint: `UNIQUE(site_name, circuit_purpose)`
- UPSERT prevents duplicate inserts
- Manual override protection

### 01:00 - Meraki Enrichment (`nightly_meraki_enriched_db.py`)
**Purpose:** Collect device data and enrich circuit information

**Process:**
1. Fetches device inventory from Meraki API
2. Parses device notes for provider/speed
3. Performs ARIN RDAP lookups
4. Updates `meraki_inventory` and `enriched_circuits` tables

**Duplicate Prevention:**
- Primary key on network_name
- Updates existing records rather than inserting

### 01:30 - Switch Port Visibility (`nightly_switch_visibility_db.py`)
**Purpose:** Track switch port client connections

**Process:**
1. Collects switch port data
2. Updates `switch_port_clients` table

### 04:00 - Enablement Tracking (`nightly_enablement_db.py`)
**Purpose:** Track circuits changing from "Ready for Enablement" to "Enabled"

**Process:**
1. Compares current state with previous day
2. Records enablements in `daily_enablements`
3. Updates summary statistics

### 04:30 - Circuit History (`nightly_circuit_history.py`)
**Purpose:** Maintain audit trail of all circuit changes

**Process:**
1. Detects changes in circuit data
2. Records changes to `circuit_history` table
3. Runs duplicate cleanup to remove empty records

## Database Constraints

### Current Constraints
```sql
-- Circuits table
UNIQUE(site_name, circuit_purpose)  -- Prevents duplicates per site/purpose
```

### Missing Constraints (Should be Added)
```sql
-- Should also have:
UNIQUE(site_id)  -- Site ID should be unique across all records
```

## Root Cause Analysis

### Why Duplicates Exist
1. **Migration Issue:** During July 2 migration, data was imported multiple times
2. **Missing Constraint:** No unique constraint on site_id allows duplicate Site IDs
3. **Timing:** 
   - Original records: Created June 25, 2025
   - Duplicates: Created July 2, 2025 during migration

### Why Dashboard Shows 14 Instead of 11
- Database contains 14 circuit records with "Ready for Enablement"
- 11 unique site IDs + 3 duplicates = 14 total records
- Dashboard counts records, not unique sites

## Recommended Fixes

### Immediate Actions
1. **Remove Duplicate Records:**
   ```sql
   -- Keep older records, delete newer duplicates
   DELETE FROM circuits 
   WHERE id IN (36262, 36602, 37368)  -- July 2 duplicates
   AND site_id IN ('INI 06 -B', 'MSG 01- B', 'TXD 76- B');
   ```

2. **Add Unique Constraint:**
   ```sql
   ALTER TABLE circuits 
   ADD CONSTRAINT unique_site_id UNIQUE(site_id);
   ```

### Dashboard Fix (Already Implemented)
- Modified `/api/dashboard-data` to count unique site_ids
- Shows correct count of 11 unique sites

### Preventive Measures
1. **Enhance DSR Pull Logic:**
   - Check for existing site_id before insert
   - Log warnings for potential duplicates

2. **Add Data Validation:**
   - Pre-import validation script
   - Post-import duplicate check

3. **Migration Best Practices:**
   - Use transactional imports
   - Validate data integrity after migration
   - Create rollback points

## Manual Override Feature

Circuits can be protected from automatic updates:
- Set `manual_override = TRUE`
- DSR pull will skip these circuits
- Preserves custom data (provider, speed, cost)

## Data Flow Summary

```
DSR CSV → Circuits Table → Enriched Circuits → Web Display
           ↓                    ↑
      Manual Override      Meraki Data
```

## Monitoring and Alerts

### Current Monitoring
- Circuit history tracks all changes
- Manual review of enablement reports

### Recommended Additions
- Daily duplicate check script
- Alert on constraint violations
- Migration validation checklist

## Conclusion

The duplicate issue stems from the July 2 migration process. While the nightly processes have duplicate prevention mechanisms, the migration bypassed these safeguards. Adding a unique constraint on site_id and cleaning up the existing duplicates will resolve the issue and prevent future occurrences.