# Duplicate Circuits Issue Report - July 3, 2025

## Executive Summary
The DSR Circuits database contains approximately 2,800-3,000 duplicate circuit records created during the July 2, 2025 migration. This has resulted in incorrect counts throughout the system.

## Issue Details

### Current State
- **Total circuits:** 7,027 (should be ~4,000)
- **Enabled circuits:** 3,652 (should be ~1,800-2,000)  
- **Circuits with duplicates:** 2,813 site_ids
- **Duplicate (site_name, circuit_purpose) combinations:** 2,686

### Root Cause
The duplicate issue stems from a fingerprint mismatch during migration:

1. **Original records (June 25):** 4,172 circuits imported WITHOUT fingerprints
2. **Migration records (July 2):** 2,855 circuits created WITH fingerprints
3. **Nightly updates:** Use `ON CONFLICT (fingerprint)` which can't match NULL fingerprints

### Why This Happened
```sql
-- The nightly update uses:
INSERT INTO circuits (...) VALUES (...)
ON CONFLICT (fingerprint) DO UPDATE SET ...

-- But original records have fingerprint = NULL
-- So instead of updating, it creates new records
```

## Examples of Duplicates

### Worst Offenders
- "AMERICA'S TIRE CO" + Primary: 228 duplicates
- "AMERICAS TIRE CO" + Primary: 100 duplicates
- Individual sites like AZN 04: 14 duplicates

### Specific Examples (Ready for Enablement)
- INI 06 -B: 2 identical records
- MSG 01- B: 2 identical records
- TXD 76- B: 2 identical records

## Impact

### User-Facing Issues
1. Dashboard shows 14 "Ready for Turn Up" instead of 11
2. "All Circuits" shows 3,425 enabled (way too high)
3. Reports show inflated numbers
4. Potential billing/cost calculation errors

### Data Integrity Issues
1. Violates unique constraint on (site_name, circuit_purpose)
2. History tracking may be split across duplicate records
3. Manual overrides may not work correctly

## Solution

### Immediate Fix
Run the fix script: `/root/fix_duplicate_circuits.py`

This script will:
1. Add fingerprints to all records missing them
2. Identify duplicates (keeping oldest record)
3. Delete duplicate records
4. Verify the fix

### Expected Results After Fix
- Total circuits: ~4,000
- Enabled circuits: ~1,800-2,000
- No duplicate fingerprints
- Correct dashboard counts

## Prevention

### Database Constraints
```sql
-- Current constraints:
UNIQUE (fingerprint)
UNIQUE (fingerprint, last_csv_file)

-- Should also have:
UNIQUE (site_id)  -- Prevent duplicate site IDs
CHECK (fingerprint IS NOT NULL)  -- Require fingerprints
```

### Migration Best Practices
1. Always generate fingerprints during import
2. Use transactional imports
3. Validate record counts before/after
4. Run duplicate checks post-migration

### Nightly Process Improvements
1. Add pre-import validation
2. Log duplicate detection
3. Alert on unusual record count changes
4. Consider using site_id as additional conflict key

## Timeline

- **June 25, 2025:** Original 4,172 circuits imported (no fingerprints)
- **July 2, 2025 11:15:** Migration creates 2,855 duplicates (with fingerprints)
- **July 2-3, 2025:** Nightly updates can't match records, may create more duplicates
- **July 3, 2025:** Issue discovered and documented

## Recommendations

### Immediate Actions
1. Run the fix script to remove duplicates
2. Add NOT NULL constraint to fingerprint column
3. Update nightly process to handle NULL fingerprints

### Long-term Improvements
1. Add monitoring for duplicate detection
2. Implement data quality checks
3. Create migration validation checklist
4. Consider using UUID primary keys

## Commands for Verification

```bash
# Check current state
python3 /root/check_all_duplicates.py

# Run the fix
python3 /root/fix_duplicate_circuits.py

# Verify the fix
psql -U postgres -d dsrcircuits -c "SELECT COUNT(*) FROM circuits;"
psql -U postgres -d dsrcircuits -c "SELECT COUNT(DISTINCT site_id) FROM circuits;"
```

## Conclusion

This duplicate issue was caused by a fingerprint mismatch between original data and migrated data. The nightly update process couldn't match records without fingerprints, leading to duplicate creation instead of updates. The fix involves adding fingerprints to all records and removing duplicates, which should restore the database to its correct state.