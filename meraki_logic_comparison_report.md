# Meraki Script Logic Comparison Report

## Overview
This report compares the logic between the old file-based scripts (`meraki_mx.py` + `nightly_enriched.py`) and the new database script (`nightly_meraki_enriched_db.py`) to ensure all functionality is preserved.

## Critical Missing Functions

### 1. `get_organization_uplink_statuses()` - **MISSING IN NEW SCRIPT**
- **Old Script**: Lines 203-217 in `meraki_mx.py`
- **New Script**: Referenced on line 412 but NOT DEFINED
- **Impact**: CRITICAL - Script will fail when trying to collect uplink data
- **Fix Required**: Add this function to the new script

## Logic Differences

### 1. Provider Mapping Differences

#### Old Scripts Provider Mapping (Complete)
The old scripts have extensive provider mappings:
- `meraki_mx.py`: Lines 71-101 - PROVIDER_KEYWORDS (30 entries)
- `nightly_enriched.py`: Lines 29-132 - provider_mapping (103 entries)

#### New Script Provider Mapping (Incomplete)
- Lines 91-121 - PROVIDER_MAPPING (30 entries)
- Lines 124-135 - PROVIDER_KEYWORDS (10 entries)
- **Missing ~60+ provider mappings from the enriched script**

### 2. Speed Formatting Logic Differences

#### Old Enriched Script (Lines 185-203)
```python
def reformat_speed(speed, provider):
    # Override speed for specific providers
    if provider in ["Inseego", "VZW Cell", "Digi", ""]:
        return "Cell"
    if provider == "Starlink":
        return "Satellite"
    # ... complex speed parsing logic
```

#### New Script (Lines 341-353)
```python
def reformat_speed(speed, provider):
    if provider and provider.lower() == "starlink":
        return "Satellite"
    # Missing "Cell" logic for Inseego, VZW Cell, Digi
    # Missing TBD/Unknown handling
```

### 3. Provider Normalization Logic

#### Old Enriched Script (Lines 146-167)
- Complex normalization with special handling for Digi, Starlink, Inseego
- VZW/Verizon normalization based on `is_dsr` flag
- Extensive regex cleaning

#### New Script (Lines 323-339)
- Simplified normalization
- Missing the `is_dsr` parameter and logic
- Missing special provider handling

### 4. Raw Notes Parsing Differences

#### Old Enriched Script (Lines 204-242)
- Supports specific format: `WAN 1\nProvider\nSpeed\nWAN 2\nProvider\nSpeed`
- Fallback to regex parsing
- Returns `is_dsr` flags for WAN1/WAN2

#### New Script (Lines 226-280)
- Only has regex parsing
- Missing the specific format handling
- Does not return `is_dsr` flags

### 5. Tag Filtering Logic

#### Old Scripts
- Both properly handle tag filtering
- Excludes: hub, lab, voice

#### New Script
- Has EXCLUDE_TAGS defined but uses it differently
- Line 586: Uses `any(tag.lower() in EXCLUDE_TAGS for tag in device_tags)`
- Should be consistent with old script logic

### 6. Circuit Role Assignment

#### Old Enriched Script
- Lines 429, 462: Uses `Circuit Purpose` from DSR tracking data
- Properly capitalizes the role

#### New Script
- Lines 627, 640: Gets circuit_purpose from tracking data
- Correctly implements this logic ✓

### 7. Provider Comparison Logic

#### Old Meraki Script (Lines 180-193)
- Uses fuzzy matching with 80% threshold
- Normalizes and compares canonical providers

#### New Script
- Lines 472-473: Simplified comparison, not using fuzzy logic
- Missing the sophisticated comparison from old script

### 8. WAN Provider Selection Logic

#### Old Enriched Script (Lines 373-380)
- Prioritizes provider_label when provider_comparison is "No match"
- Falls back to provider from ARIN lookup

#### New Script
- Missing this prioritization logic
- Always uses ARIN provider if available

### 9. IP Address Range Checks

#### Both Scripts
- Correctly check Verizon range (166.80.0.0/16) ✓
- Use KNOWN_IPS mapping ✓
- Skip private IPs ✓

### 10. Database Schema Differences

#### New Script Tables
- `meraki_live_data` - Stores raw Meraki data
- `enriched_circuits` - Stores enriched data
- Missing some fields from JSON structure (e.g., `providers_flipped`)

## Missing Features in New Script

1. **IP Cache Persistence**: Old script saves/loads IP cache from file
2. **Missing Data Log**: Old script tracks failed IP lookups
3. **Backup Creation**: Old enriched script creates backups before updates
4. **Change Tracking**: Old script tracks and reports number of changes
5. **Duplicate Detection**: Old script handles duplicate networks
6. **Network Deletion**: Old script removes networks no longer in Meraki

## Data Transformation Issues

1. **Device Tags Storage**
   - Old: Stored as array in JSON
   - New: Stored as JSON string in database (line 512)
   - Need to ensure consistent handling

2. **Cost Formatting**
   - Old: normalize_cost function ensures $X.XX format
   - New: Simple string formatting, may not handle edge cases

3. **Confirmation Status**
   - Old: Tracks which WAN interfaces were confirmed from DSR
   - New: Implements this correctly ✓

## Recommendations

### Critical Fixes Required
1. **Add missing `get_organization_uplink_statuses()` function**
2. **Add all missing provider mappings from enriched script**
3. **Fix speed formatting logic to handle Cell/Satellite correctly**
4. **Implement proper provider normalization with `is_dsr` logic**
5. **Add specific format parsing for raw notes**
6. **Implement fuzzy provider comparison logic**

### Important Fixes
1. Add IP cache persistence
2. Implement backup/rollback mechanism
3. Add change tracking and reporting
4. Handle network deletion/deactivation
5. Add missing data logging

### Nice to Have
1. Add duplicate network detection
2. Implement comprehensive error handling
3. Add validation for data transformations
4. Create detailed logging for debugging

## Summary

The new database script is missing critical functionality that will cause it to fail (missing function) and produce different results than the old scripts (missing provider mappings, simplified logic). The core data flow is preserved, but many edge cases and data quality features have been lost in the migration.

**Recommendation**: Do not deploy the new script until all critical and important fixes are implemented to ensure data continuity and quality.