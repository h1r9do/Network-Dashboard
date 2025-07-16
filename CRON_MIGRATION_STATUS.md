# DSR Circuits Cron Job Migration Status

## Current Status: INCOMPLETE MIGRATION ⚠️

As of June 26, 2025, the system is still running legacy file-based scripts instead of the database-integrated versions.

## Current Cron Jobs (PRODUCTION)

| Time | Script | Type | Status | Log File |
|------|--------|------|--------|----------|
| 00:00 | `/usr/local/bin/dsr-pull.py` | Legacy File-Based | ⚠️ Should Replace | `/var/log/dsr-pull.log` |
| 01:00 | `/usr/local/bin/Main/nightly_meraki_db.py` | Database Integrated | ✅ Correct | `/var/log/merakimx.log` |
| 02:00 | `/usr/local/bin/nightly_inventory_summary.py` | Legacy File-Based | ⚠️ Should Replace | None |
| 03:00 | `/usr/local/bin/nightly_enriched.py` | Legacy File-Based | ⚠️ Should Replace | None |
| 04:00 | `/usr/local/bin/nightly_enablement_processor.py` | Legacy File-Based | ⚠️ Should Replace | `/var/log/enablement-processor.log` |
| 04:30 | `/usr/local/bin/Main/nightly_circuit_history.py` | Database Integrated | ✅ Correct | `/var/log/circuit-history.log` |
| 05:00 | `/usr/local/bin/Main/update_enablement_json.py` | Legacy File-Based | ⚠️ Should Remove | `/var/log/update-enablement.log` |
| */5 min | `/usr/local/bin/git_autocommit.sh` | Utility | ✅ Keep | None |

## Required Database-Integrated Cron Jobs

| Time | Script | Type | Purpose | Log File |
|------|--------|------|---------|----------|
| 00:00 | `/usr/local/bin/Main/nightly_dsr_pull_db_with_override.py` | Database + Override | Download DSR data, respect manual overrides | `/var/log/dsr-pull-db.log` |
| 01:00 | `/usr/local/bin/Main/nightly_meraki_db.py` | Database | Collect Meraki inventory & firewall rules | `/var/log/meraki-mx-db.log` |
| 02:00 | `/usr/local/bin/Main/nightly_inventory_db.py` | Database | Generate inventory summaries | `/var/log/nightly-inventory-db.log` |
| 03:00 | `/usr/local/bin/Main/nightly_enriched_db.py` | Database | Enrich circuit data | `/var/log/nightly-enriched-db.log` |
| 04:00 | `/usr/local/bin/Main/nightly_enablement_db.py` | Database | Process enablement tracking | `/var/log/nightly-enablement-db.log` |
| 04:30 | `/usr/local/bin/Main/nightly_circuit_history.py` | Database | Track circuit changes | `/var/log/circuit-history.log` |
| */5 min | `/usr/local/bin/git_autocommit.sh` | Utility | Git auto-commit | None |

## Migration Commands

To update the crontab with database-integrated scripts:

```bash
# Edit crontab
crontab -e

# Remove these legacy entries:
0 0 * * * /usr/bin/python3 /usr/local/bin/dsr-pull.py >> /var/log/dsr-pull.log 2>&1
0 2 * * * /usr/bin/python3 /usr/local/bin/nightly_inventory_summary.py
0 3 * * * /usr/bin/python3 /usr/local/bin/nightly_enriched.py
0 4 * * * /usr/bin/python3 /usr/local/bin/nightly_enablement_processor.py >> /var/log/enablement-processor.log 2>&1
0 5 * * * /usr/bin/python3 /usr/local/bin/Main/update_enablement_json.py >> /var/log/update-enablement.log 2>&1

# Add these database entries:
0 0 * * * /usr/bin/python3 /usr/local/bin/Main/nightly_dsr_pull_db_with_override.py >> /var/log/dsr-pull-db.log 2>&1
0 2 * * * /usr/bin/python3 /usr/local/bin/Main/nightly_inventory_db.py >> /var/log/nightly-inventory-db.log 2>&1
0 3 * * * /usr/bin/python3 /usr/local/bin/Main/nightly_enriched_db.py >> /var/log/nightly-enriched-db.log 2>&1
0 4 * * * /usr/bin/python3 /usr/local/bin/Main/nightly_enablement_db.py >> /var/log/nightly-enablement-db.log 2>&1
```

## Benefits of Migration

1. **Performance**: Database queries are 100x faster than file operations
2. **Storage**: Eliminates ~500MB/month of JSON file creation
3. **Real-time**: Web interface queries database directly
4. **Manual Override**: New DSR pull respects manually managed circuits
5. **Data Integrity**: ACID compliance with PostgreSQL

## Current Issues

- Still creating unnecessary JSON files daily
- File-based scripts running in parallel with database operations
- Redundant processing and storage waste
- `update_enablement_json.py` is completely unnecessary with database integration

## Action Required

**URGENT**: Update production crontab to use database-integrated scripts to:
- Stop creating redundant JSON files
- Improve system performance
- Reduce storage usage
- Enable manual override protection