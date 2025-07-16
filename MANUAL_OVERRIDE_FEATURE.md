# Manual Override Feature for Circuit Management

## Overview
The manual override feature allows manually added or edited circuits to be protected from automatic updates by the nightly DSR pull process. This ensures that circuits added through the new-stores interface maintain their custom information.

## Implementation Date
June 26, 2025

## How It Works

### 1. Database Schema Changes
Added three new columns to the `circuits` table:
- `manual_override` (BOOLEAN) - Flag indicating the circuit is protected
- `manual_override_date` (TIMESTAMP) - When the override was set
- `manual_override_by` (VARCHAR) - Who/what set the override

### 2. New Stores Interface Updates
When adding circuits through the `/new-stores` interface:
- **New circuits** are automatically marked with `manual_override = TRUE`
- **Existing circuits** can be overwritten if user confirms
- User sees existing circuit details before confirming overwrite
- All manually managed circuits are protected from DSR updates

### 3. DSR Pull Process Updates
The nightly DSR pull script now:
- Checks the `manual_override` flag before updating any circuit
- Skips circuits where `manual_override = TRUE`
- Logs all skipped circuits for audit purposes
- Still tracks these circuits in history for reference

## Usage

### Adding a New Circuit
1. Go to `/new-stores` page
2. Click "Add Circuit" button
3. Fill in circuit details
4. If circuit exists, you'll be prompted to overwrite
5. Confirm to update and protect the circuit

### Manual Override Protection
- Circuits added/edited through new-stores are automatically protected
- Protection prevents DSR pull from overwriting:
  - Provider information
  - Speed details
  - Monthly cost
  - Status
  - All other circuit fields

### Viewing Protected Circuits
To see which circuits have manual override protection:
```sql
SELECT site_name, circuit_purpose, manual_override_date, manual_override_by
FROM circuits
WHERE manual_override = TRUE
ORDER BY manual_override_date DESC;
```

## Scripts and Files

### Modified Files
1. `/usr/local/bin/Main/models.py` - Added manual_override columns
2. `/usr/local/bin/Main/new_stores.py` - Updated to handle overwrite and set flags
3. `/usr/local/bin/templates/new_stores_tabbed.html` - UI updates for overwrite confirmation

### New Scripts
1. `/usr/local/bin/Main/add_manual_override_columns.py` - Database migration script
2. `/usr/local/bin/Main/update_circuits_from_tracking_with_override.py` - Enhanced update script
3. `/usr/local/bin/Main/nightly_dsr_pull_db_with_override.py` - Enhanced nightly pull

## Cron Job Update Required
Replace the current DSR pull cron job with the enhanced version:
```bash
# Old (remove this):
0 0 * * * /usr/bin/python3 /usr/local/bin/dsr-pull.py >> /var/log/dsr-pull.log 2>&1

# New (add this):
0 0 * * * /usr/bin/python3 /usr/local/bin/Main/nightly_dsr_pull_db_with_override.py >> /var/log/dsr-pull-db.log 2>&1
```

## Rollback Procedure
If needed to rollback:
1. Remove manual_override columns:
   ```sql
   ALTER TABLE circuits 
   DROP COLUMN manual_override,
   DROP COLUMN manual_override_date,
   DROP COLUMN manual_override_by;
   ```
2. Restore original scripts from backups
3. Update cron job back to original

## Benefits
1. **Data Integrity** - Manually entered data is preserved
2. **Flexibility** - Can override DSR data when needed
3. **Audit Trail** - Tracks who/when overrides were set
4. **Selective Updates** - DSR still updates non-protected circuits

## Future Enhancements
- Add UI indicator for protected circuits
- Bulk protection management interface
- Manual override removal capability
- Protection expiration dates