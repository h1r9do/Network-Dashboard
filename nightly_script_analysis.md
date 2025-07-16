# Nightly Script Analysis Report

## Date: July 10, 2025

### Executive Summary

After analyzing the nightly scripts, I've identified that the `nightly_enriched_db.py` script **WILL OVERWRITE** the fixes made today because it:

1. **Truncates the entire enriched_circuits table** (line 477)
2. **Rebuilds from scratch** every night
3. **Does not preserve manual updates**

### Critical Findings

#### 1. nightly_enriched_db.py Behavior

**The Good:**
- DOES prioritize DSR data when IP addresses match
- DOES handle provider normalization (should handle CenturyLink variations)
- DOES copy DSR provider/speed when DSR circuits are found

**The Bad:**
- Uses `TRUNCATE TABLE enriched_circuits` - completely wipes the table
- No mechanism to preserve manual updates or fixes
- Will overwrite the 870 sites we fixed today

#### 2. DSR Circuit Update Script

The `update_circuits_from_tracking_with_override.py` script:
- Respects `manual_override` flag (line 187: `WHERE record_number = %s AND manual_override IS NOT TRUE`)
- Only updates when data actually changes
- This is good but only protects the circuits table, not enriched_circuits

### The Real Issue

The enriched_circuits table is rebuilt from scratch every night by:
1. Reading all MX devices from meraki_inventory
2. Parsing device notes for provider/speed info
3. Matching against DSR circuits by IP or provider name
4. Writing fresh data to enriched_circuits

**This means our 870 fixes will be lost tonight unless we modify the script.**

### Recommended Solution

We need to modify `nightly_enriched_db.py` to:

1. **Option A: Incremental Updates**
   - Instead of TRUNCATE, only update records that have changed
   - Add logic to check if DSR data matches ARIN before updating
   - Preserve existing good data

2. **Option B: Add Override Flag**
   - Add a `manual_override` column to enriched_circuits
   - Skip updating records with this flag set
   - Similar to how circuits table works

3. **Option C: Smart Sync Logic**
   - When DSR provider matches ARIN provider, always use DSR data
   - Only update enriched_circuits when:
     - IP addresses change
     - DSR circuit data changes
     - New sites are added

### Immediate Action Required

To preserve today's fixes, we must either:
1. Disable the nightly_enriched_db.py script temporarily
2. Modify it before tonight's run
3. Add the sync logic from sync_dsr_to_enriched_with_arin_check.py to the nightly script

### Provider Matching Logic

The script already has good provider normalization that should handle:
- "CenturyLink" vs "CenturyLink/Embarq" 
- "Cox Business" vs "Cox Communications"
- "AT&T" variations

But it's still doing a full table rebuild which will lose our fixes.

### Other Nightly Scripts

- `nightly_dsr_pull_db_with_override.py` - Downloads fresh DSR data
- `update_circuits_from_tracking_with_override.py` - Updates circuits table (respects overrides)
- `nightly_meraki_db.py` - Updates Meraki inventory
- `nightly_circuit_history.py` - Tracks circuit changes
- `nightly_enablement_db.py` - Tracks enablements

None of these directly affect enriched_circuits except for nightly_enriched_db.py.

### Conclusion

**The enriched_circuits table WILL be overwritten tonight** unless we take action. The script needs to be modified to preserve the DSR-ARIN matched updates we made today.