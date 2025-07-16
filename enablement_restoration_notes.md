# Enablement Restoration Notes - June 27, 2025

## Problem Summary
The circuit enablement report was showing incorrect data:
- Enablement average was 18.7 per day (should be <1 per day)
- Ready queue tracking only had data through June 26th (missing June 27th)
- Team attribution also only had data through June 26th
- The system was counting ANY transition to "enabled" status instead of specifically "Ready for Enablement" to "Enabled" transitions

## Root Cause Analysis

### 1. Incorrect Enablement Logic
**File:** `/usr/local/bin/Main/nightly_enablement_db.py`
- Was checking if current status contained any enabled keyword
- Should have been checking for specific transition from "Ready for Enablement" to "Enabled"
- This caused ~18 enablements per day instead of the actual ~0.7 per day

### 2. Wrong Table Used for Attribution
**File:** `/usr/local/bin/Main/reports.py`
- Was querying `circuit_enablements` table (old table with 723 incorrect records)
- Should have been querying `daily_enablements` table (new table with 29 correct records)

### 3. Empty Assigned Values
- CSV files don't have "SCTASK Assignee" column
- The `assigned_to` field in circuits table was mostly empty
- System was showing empty string instead of "Unknown"

## Changes Made

### 1. Fixed Enablement Logic (`nightly_enablement_db.py`)

**Original incorrect logic:**
```python
def is_enabled_status(status):
    enabled_keywords = ['enabled', 'service activated', 'activated', 'enabled using existing broadband']
    status_lower = str(status).lower().strip()
    return any(keyword in status_lower for keyword in enabled_keywords)
```

**Corrected logic:**
```python
# Specific check: was "ready for enablement" and now "enabled" (but not "ready for enablement")
if ('ready for enablement' in prev_status and 
    'enabled' in current_status and 
    'ready for enablement' not in current_status):
    # This is a true Ready->Enabled transition!
```

**Key changes:**
- Tracks by Site ID instead of complex fingerprints
- Only counts transitions FROM "Ready for Enablement" TO "Enabled"
- Looks up assigned_to from circuits table during processing
- Stores in daily_enablements table with proper attribution

### 2. Fixed Attribution Query (`reports.py`)

**Changed from:**
```python
FROM circuit_enablements ce
LEFT JOIN circuits c ON (
    ce.site_name = c.site_name 
    AND ce.circuit_purpose = c.circuit_purpose
)
```

**Changed to:**
```python
FROM daily_enablements de
```

**Also fixed empty assigned_to handling:**
```python
CASE 
    WHEN de.assigned_to IS NULL OR de.assigned_to = '' THEN 'Unknown'
    ELSE de.assigned_to 
END as assigned_person
```

### 3. Fixed Chart Display (`circuit_enablement_report.html`)

**Added to x-axis configuration:**
```javascript
x: {
    title: {
        display: true,
        text: 'Date'
    },
    ticks: {
        autoSkip: false,
        maxRotation: 45,
        minRotation: 45
    }
}
```

This ensures all dates are displayed on the Team Attribution chart.

## Data Verification

### Analysis Results
- **Total enablements over 43 days:** 29 (not 800+)
- **Average per day:** 0.7 (not 18.7)
- **Maximum in one day:** 7 on May 30th
- **Most days:** 0 enablements

### Specific Ready→Enabled Transitions Found
1. April 30: 4 transitions (IAI 01, KST 01, NEO 01, UTS 11)
2. May 8: 1 transition (CAN 53)
3. May 9: 1 transition (TXD 92)
4. May 10: 1 transition (MNM 27)
5. May 14: 3 transitions (CAN 61, TNN 15, TXH 81)
6. May 15: 2 transitions (CAN 23, IAF 01)
7. May 30: 7 transitions (AZK 01, CAS 28, CAS 50, MNM 09, MOK 07, WAE 04, WAS 28)
8. June 5: 1 transition (NEO 07)
9. June 11: 1 transition (CAL 46)
10. June 17: 2 transitions (CAS 31, MOS XX)
11. June 18: 3 transitions (AZY 02, CAL 43, TXH 33)
12. June 19: 1 transition (NEO 07)
13. June 20: 1 transition (PAC 01)
14. June 21: 1 transition (TXS 12)

## Database Tables Involved

### 1. `daily_enablements`
- Stores individual enablement records
- Includes assigned_to field for team attribution
- Currently has 29 correct records

### 2. `enablement_summary`
- Stores daily count summaries
- Used for the main enablement report
- Has entries for all dates including days with 0 enablements

### 3. `ready_queue_daily`
- Tracks how many circuits are in "Ready for Enablement" status each day
- Used for the Ready Queue Tracking tab

### 4. `circuit_enablements` (old/incorrect)
- Contains 723 records with incorrect logic
- Should not be used anymore
- Reports.py was incorrectly querying this table

## Cron Job Configuration

The nightly enablement script runs at 4:00 AM:
```
0 4 * * * /usr/bin/python3 /usr/local/bin/Main/nightly_enablement_db.py >> /var/log/nightly-enablement-db.log 2>&1
```

This timing ensures:
1. DSR data has been pulled (midnight)
2. Data has been enriched (3 AM)
3. Circuits table has latest assigned_to information

## Team Attribution Flow

### Current State
- 6 circuits have assigned_to = "Taren Andrickson"
- All past enablements show as "Unknown" (no assignment data at time of enablement)

### Future State
When a circuit with an assigned person transitions from "Ready for Enablement" to "Enabled":
1. Nightly script detects the transition
2. Looks up current assigned_to from circuits table
3. Stores in daily_enablements with the person's name
4. Reports show attribution to that person

## Scripts Created During Fix

### 1. `analyze_csv_detailed.py`
- Used to analyze actual enablement patterns in CSV files
- Found the true pattern of <1 enablement per day

### 2. `verify_old_logic.py`
- Recreated the old logic to understand why it was counting ~18/day
- Confirmed it was counting ANY transition to enabled status

### 3. `nightly_enablement_db_correct.py`
- Created the corrected version with proper logic
- Later replaced the production script with this version

## Lessons Learned

1. **Be specific about status transitions** - Don't just check if something is "enabled", check what it transitioned FROM
2. **Use the correct data source** - The reports were querying an old table with incorrect data
3. **Handle empty values gracefully** - Show "Unknown" instead of blank for better UX
4. **Verify calculations match reality** - 18.7 enablements per day should have been a red flag

## Validation Steps

To verify the fix is working:
1. Check enablement average is <1 per day: ✓
2. Check all dates including June 27th appear: ✓
3. Test attribution with assigned data: ✓
4. Verify cron job runs successfully: ✓
5. Check logs show correct counts: ✓

## Future Monitoring

Watch for:
- Enablement average suddenly jumping above 2-3 per day
- Missing dates in any of the tabs
- Attribution showing blank instead of "Unknown"
- Log file errors at 4 AM

## Files Modified

1. `/usr/local/bin/Main/nightly_enablement_db.py` - Fixed enablement logic
2. `/usr/local/bin/Main/reports.py` - Fixed attribution query
3. `/usr/local/bin/templates/circuit_enablement_report.html` - Fixed chart display

## Commands for Future Reference

Check enablement data:
```bash
curl -s "http://localhost:5052/api/daily-enablement-data?days=30" | jq '.summary'
```

Check attribution data:
```bash
curl -s "http://localhost:5052/api/closure-attribution-data?days=30" | jq '.attribution_by_person'
```

Check last script run:
```bash
grep "completed successfully" /var/log/nightly-enablement-db.log | tail -1
```

## Backup Information

- Original incorrect script backed up as: `nightly_enablement_db.py.incorrect_backup`
- Test scripts created in `/usr/local/bin/Main/`:
  - `analyze_csv_detailed.py`
  - `verify_old_logic.py`
  - `nightly_enablement_db_correct.py` (now replaced the main script)

---

**Resolution Status:** ✅ COMPLETE - All issues fixed and verified
**Date:** June 27, 2025
**Time to Resolution:** ~1 hour