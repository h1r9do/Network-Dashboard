# Fixing the Nightly DSR Pull Process

## Current Issues with Nightly Process

1. **Relies on fingerprints that may not exist**
   - Uses `ON CONFLICT (fingerprint)` 
   - If fingerprint is NULL, creates duplicates

2. **No validation before insert**
   - Doesn't check for existing records by site_id
   - Doesn't validate data integrity

3. **Fingerprint generation issues**
   - Not all records have fingerprints
   - No enforcement of fingerprint requirement

## Required Fixes

### 1. Update the UPSERT Logic

The current logic uses only fingerprint for conflict detection. It should use multiple columns:

```sql
-- Current (PROBLEMATIC):
ON CONFLICT (fingerprint) DO UPDATE SET ...

-- Should be:
ON CONFLICT (site_name, circuit_purpose) DO UPDATE SET ...
-- OR
ON CONFLICT (site_id) DO UPDATE SET ...
```

### 2. Add Pre-Import Validation

Before importing, the script should:
```python
# Check for existing records without fingerprints
existing_without_fp = db.session.query(Circuit).filter(
    Circuit.fingerprint == None
).count()

if existing_without_fp > 0:
    logger.warning(f"Found {existing_without_fp} circuits without fingerprints")
    # Fix them before proceeding
```

### 3. Ensure Fingerprints Always Exist

```python
# In the import loop:
fingerprint = create_fingerprint(row)
if not fingerprint or fingerprint == "||":
    logger.error(f"Invalid fingerprint for row: {row}")
    continue  # Skip this record
```

### 4. Add Database Constraints

```sql
-- Add these constraints:
ALTER TABLE circuits 
ADD CONSTRAINT check_fingerprint_not_null 
CHECK (fingerprint IS NOT NULL);

ALTER TABLE circuits
ADD CONSTRAINT unique_site_id 
UNIQUE (site_id);
```

## Recommended Changes to update_circuits_from_tracking_with_override.py

### Change 1: Fix the UPSERT to use site_name + circuit_purpose

```python
# Change line 189-200 from:
circuit_upsert_sql = """
INSERT INTO circuits (...) VALUES %s
ON CONFLICT (fingerprint) DO UPDATE SET ...
"""

# To:
circuit_upsert_sql = """
INSERT INTO circuits (...) VALUES %s
ON CONFLICT (site_name, circuit_purpose) DO UPDATE SET ...
"""
```

### Change 2: Add fingerprint validation

```python
# Add after line 118:
if not fingerprint or fingerprint == "||" or fingerprint.count('|') != 2:
    logger.error(f"Invalid fingerprint generated for site {row.get('site_name')}")
    continue
```

### Change 3: Pre-process existing records

```python
# Add before the main import loop:
# Ensure all existing records have fingerprints
cursor.execute("""
    UPDATE circuits 
    SET fingerprint = site_name || '|' || site_id || '|' || circuit_purpose
    WHERE fingerprint IS NULL OR fingerprint = ''
""")
conn.commit()
logger.info("Updated fingerprints for existing records")
```

## Complete Fix Process

1. **Run the duplicate fix script first**
   ```bash
   python3 /root/fix_duplicate_circuits.py
   ```

2. **Update the nightly script** with the changes above

3. **Add database constraints**
   ```sql
   ALTER TABLE circuits DROP CONSTRAINT IF EXISTS circuits_fingerprint_unique;
   ALTER TABLE circuits ADD CONSTRAINT circuits_unique_site_purpose UNIQUE (site_name, circuit_purpose);
   ```

4. **Test the nightly process**
   ```bash
   # Run manually to test
   python3 /usr/local/bin/nightly_dsr_pull_db_with_override.py
   ```

## Alternative Solution: Rewrite the Update Function

If modifying the existing script is too risky, create a new version that:
1. Uses site_id as the primary identifier
2. Always generates fingerprints
3. Validates before inserting
4. Logs all changes

## Monitoring

Add checks to detect duplicates after each nightly run:
```python
# Add to end of nightly script:
duplicate_check = db.session.query(
    Circuit.site_id,
    func.count(Circuit.id)
).group_by(
    Circuit.site_id
).having(
    func.count(Circuit.id) > 1
).count()

if duplicate_check > 0:
    logger.error(f"WARNING: Found {duplicate_check} duplicate site_ids after import!")
```

## Summary

The current nightly process will continue creating duplicates until we:
1. Fix the conflict detection (use site_name + circuit_purpose, not just fingerprint)
2. Ensure all records have valid fingerprints
3. Add proper constraints to the database
4. Add validation and monitoring

Simply removing the existing duplicates is not enough - we must fix the process that creates them.