# Nightly Script Analysis Summary

## Critical Finding

**The `nightly_enriched_db.py` script WILL overwrite all 870 fixes made today because it uses `TRUNCATE TABLE enriched_circuits` and rebuilds from scratch every night.**

## Nightly Scripts That Run

### 1. nightly_dsr_pull_db_with_override.py
- Downloads fresh DSR tracking data from DSR Global portal
- Updates the `circuits` table
- **RESPECTS manual_override flag** - won't overwrite manually managed circuits

### 2. update_circuits_from_tracking_with_override.py
- Updates circuits from CSV file
- **Key protection**: `WHERE record_number = %s AND manual_override IS NOT TRUE`
- Only updates when data actually changes
- **This protects the circuits table but NOT enriched_circuits**

### 3. nightly_enriched_db.py (THE PROBLEM)
- **Line 477**: `cursor.execute("TRUNCATE TABLE enriched_circuits")`
- Completely wipes and rebuilds the enriched_circuits table
- Does have good logic for:
  - DSR priority when IP matches
  - Provider normalization (handles CenturyLink variations)
  - Fuzzy matching for providers
- **But still overwrites everything nightly**

### 4. Other nightly scripts
- nightly_meraki_db.py - Updates Meraki inventory
- nightly_circuit_history.py - Tracks changes
- nightly_enablement_db.py - Tracks enablements
- **None of these affect enriched_circuits**

## The Solution

I've created a modified version: `nightly_enriched_db_with_preservation.py` that:

1. **Does NOT truncate the table**
2. **Preserves DSR data when ARIN matches**
3. **Only updates records that actually changed**
4. **Maintains a preservation count**

Key logic added:
```python
# For WAN1: If current provider is DSR and ARIN matches, preserve it
if (current_record.get('wan1_confirmed') and 
    current_record.get('wan1_provider') and 
    wan1_arin and
    providers_match_for_sync(current_record.get('wan1_provider'), wan1_arin)):
    # Preserve existing DSR data
```

## Immediate Actions Needed

1. **TONIGHT**: Either disable the nightly script or replace it with the preservation version
2. **TOMORROW**: Test the modified script thoroughly
3. **LONG TERM**: Add a `manual_override` column to enriched_circuits similar to circuits table

## What Will Happen If We Do Nothing

Tonight at the scheduled run time:
1. nightly_enriched_db.py will run
2. It will TRUNCATE enriched_circuits
3. All 870 sites we fixed will revert to mismatched providers
4. Cost calculations will break again for sites like AZP 21

## Recommendation

Replace `/usr/local/bin/Main/nightly/nightly_enriched_db.py` with the preservation version before tonight's run to save the 870 fixes.