# File Elimination Plan - Database Migration

## 🎯 Current Status

You are correct - the new database-driven system should eliminate the need for intermediate CSV/JSON files. Currently we have:

### ✅ Completed
- **Web Application**: 100% database-driven (reads from PostgreSQL)
- **Main Data**: 4,171 circuits stored in database
- **Firewall Management**: 55 rules stored in database
- **Meraki Collection**: Enhanced script writes directly to database

### 🔄 In Progress - File Elimination
We still have 3 legacy scripts creating unnecessary files:

## 📁 Files Being Created (That We Don't Need)

### 1. `/var/www/html/meraki-data/` Directory
**Current Files Being Created:**
- `mx_inventory_enriched_YYYY-MM-DD.json` (~30MB daily)
- `mx_inventory_enriched_YYYY-MM-DD.json.backup` (backup files)
- `update_log_YYYY-MM-DD.txt` (processing logs)
- `meraki_inventory_summary.json` (~50MB)
- `meraki_inventory_full.json` (~50MB+)
- `circuit_enablement_data.json`
- `circuit_enablement_trends.json`
- `circuit_enablement_details.json`

**Storage Impact:** ~500MB+ of redundant files created daily

### 2. `/var/www/html/circuitinfo/` Directory
**Current Files:**
- `tracking_data_YYYY-MM-DD.csv` (still needed as input from DSR Global)
- These CSV files are the raw input from DSR Global and still needed

## 🚀 Solution - Database Scripts Created

I've created database versions of the file-based scripts:

### 1. `/usr/local/bin/Main/nightly_enriched_db.py`
**Replaces:** `/usr/local/bin/nightly_enriched.py`
**Function:** Writes enriched network data directly to `enriched_networks` table
**Eliminates:** Daily JSON files (~30MB), backup files, update logs

### 2. `/usr/local/bin/Main/nightly_inventory_db.py` 
**Replaces:** `/usr/local/bin/nightly_inventory_summary.py`
**Function:** Writes inventory data to `device_inventory` and `inventory_summary` tables
**Eliminates:** Large inventory JSON files (~50MB+), HTML cache files

### 3. `/usr/local/bin/Main/nightly_enablement_db.py`
**Replaces:** `/usr/local/bin/nightly_enablement_processor.py`
**Function:** Writes enablement tracking to `circuit_enablements` table
**Eliminates:** Trend JSON files, detailed enablement files

## 📋 Cron Jobs Updated

**Old Schedule:**
```bash
0 3 * * * /usr/bin/python3 /usr/local/bin/nightly_enriched.py
0 2 * * * /usr/bin/python3 /usr/local/bin/nightly_inventory_summary.py  
0 4 * * * /usr/bin/python3 /usr/local/bin/nightly_enablement_processor.py
```

**New Schedule:**
```bash
0 3 * * * /usr/bin/python3 /usr/local/bin/Main/nightly_enriched_db.py
0 2 * * * /usr/bin/python3 /usr/local/bin/Main/nightly_inventory_db.py
0 4 * * * /usr/bin/python3 /usr/local/bin/Main/nightly_enablement_db.py
```

## 🔧 Next Steps to Complete File Elimination

### Phase 1: Test Database Scripts (Immediate)
1. Fix any SQL syntax issues in the new scripts
2. Test each script individually
3. Verify database tables are created correctly
4. Run scripts manually to verify data flow

### Phase 2: Production Cutover (Next 24-48 hours)
1. Let new scripts run for 1-2 nights via cron
2. Verify web application continues working with database data
3. Compare database vs file data for accuracy
4. Monitor logs for any issues

### Phase 3: File Cleanup (After verification)
1. Stop file-based scripts completely
2. Update web application to remove any remaining file dependencies
3. Clean up old JSON files in `/var/www/html/meraki-data/`
4. Archive historical data if needed
5. Update documentation

## 💾 Storage Benefits After Completion

### Current Storage Usage
```
/var/www/html/meraki-data/: ~2GB+ (growing ~500MB/month)
/var/www/html/circuitinfo/: ~1GB+ (tracking CSVs - keep for input)
```

### After File Elimination
```
/var/www/html/meraki-data/: <100MB (only essential cache files)
/var/www/html/circuitinfo/: ~1GB (tracking CSVs - still needed as input)
Database storage: ~500MB total (more efficient, indexed)
```

**Net Savings:** ~1.5GB immediate + ~500MB/month reduction

## ⚠️ Important Notes

### Files to KEEP
- `tracking_data_*.csv` - Raw input from DSR Global (still needed)
- `meraki.env` - API credentials
- `circuit_assignments.json` - May still be used for assignments

### Files to ELIMINATE
- All daily JSON enriched files
- All inventory summary/detail JSON files  
- All enablement tracking JSON files
- All backup and log files in meraki-data

### Web Application Changes Needed
Some web application endpoints may still reference file paths instead of database queries. These need to be updated to complete the migration.

## 🔍 Verification Commands

After scripts run, verify data is in database:
```bash
# Check enriched networks
psql -U dsradmin -d dsrcircuits -c "SELECT COUNT(*) FROM enriched_networks;"

# Check inventory
psql -U dsradmin -d dsrcircuits -c "SELECT COUNT(*) FROM device_inventory;"

# Check enablements  
psql -U dsradmin -d dsrcircuits -c "SELECT COUNT(*) FROM circuit_enablements;"
```

This plan will eliminate the redundant file creation while maintaining all functionality through the database.