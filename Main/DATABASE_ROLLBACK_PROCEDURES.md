# Database Rollback Procedures - DSR Circuits System

## Overview
This document provides step-by-step procedures for rolling back database changes in the DSR Circuits system, specifically for production table backups created during the circuit change detection implementation.

## Current Backup Files (July 11, 2025)

### Production Table Backups
- **meraki_inventory**: `/tmp/meraki_inventory_backup_20250711_204705.sql` (461KB)
- **enriched_circuits**: `/tmp/enriched_circuits_backup_20250711_204710.sql` (220KB)
- **Full database**: `/tmp/test_db_backup_with_changes_20250711_203317.sql` (66MB)

### Backup Creation Details
- **Date Created**: July 11, 2025 at 8:47 PM
- **Pre-rollback State**: Clean production data after DSR pull and manual corrections
- **Tables Backed Up**: Production tables before circuit change detection testing
- **Backup Method**: `pg_dump` with `--no-owner --no-privileges` flags

## Rollback Procedures

### 1. Emergency Full Database Rollback

**When to use**: Complete system failure or data corruption across multiple tables

```bash
# Stop all services
sudo systemctl stop meraki-dsrcircuits.service

# Create emergency backup of current state
sudo -u postgres pg_dump -h localhost -p 5432 -U dsruser -d dsrcircuits \
  --no-owner --no-privileges > /tmp/emergency_backup_$(date +%Y%m%d_%H%M%S).sql

# Drop and recreate database (DESTRUCTIVE)
sudo -u postgres dropdb dsrcircuits
sudo -u postgres createdb dsrcircuits -O dsruser

# Restore from backup
sudo -u postgres psql -h localhost -p 5432 -U dsruser -d dsrcircuits \
  < /tmp/test_db_backup_with_changes_20250711_203317.sql

# Restart services
sudo systemctl start meraki-dsrcircuits.service
```

### 2. Selective Table Rollback - meraki_inventory

**When to use**: Issues with Meraki device data or inventory corruption

```bash
# Create backup of current state
sudo -u postgres pg_dump -h localhost -p 5432 -U dsruser -d dsrcircuits \
  -t meraki_inventory --no-owner --no-privileges \
  > /tmp/meraki_inventory_current_$(date +%Y%m%d_%H%M%S).sql

# Drop and recreate table
sudo -u postgres psql -h localhost -p 5432 -U dsruser -d dsrcircuits -c \
  "DROP TABLE IF EXISTS meraki_inventory CASCADE;"

# Restore from backup
sudo -u postgres psql -h localhost -p 5432 -U dsruser -d dsrcircuits \
  < /tmp/meraki_inventory_backup_20250711_204705.sql

# Verify restoration
psql -U dsruser -d dsrcircuits -c "SELECT COUNT(*) FROM meraki_inventory;"
```

### 3. Selective Table Rollback - enriched_circuits

**When to use**: Issues with circuit enrichment data or change detection logic

```bash
# Create backup of current state
sudo -u postgres pg_dump -h localhost -p 5432 -U dsruser -d dsrcircuits \
  -t enriched_circuits --no-owner --no-privileges \
  > /tmp/enriched_circuits_current_$(date +%Y%m%d_%H%M%S).sql

# Drop and recreate table
sudo -u postgres psql -h localhost -p 5432 -U dsruser -d dsrcircuits -c \
  "DROP TABLE IF EXISTS enriched_circuits CASCADE;"

# Restore from backup
sudo -u postgres psql -h localhost -p 5432 -U dsruser -d dsrcircuits \
  < /tmp/enriched_circuits_backup_20250711_204710.sql

# Verify restoration
psql -U dsruser -d dsrcircuits -c "SELECT COUNT(*) FROM enriched_circuits;"
```

### 4. Cron Job Rollback

**When to use**: Need to revert to separate nightly scripts

```bash
# Backup current cron
sudo crontab -l > /tmp/cron_backup_$(date +%Y%m%d_%H%M%S).txt

# Create rollback cron configuration
cat > /tmp/rollback_cron.txt << 'EOF'
0 0 * * * /usr/bin/python3 /usr/local/bin/Main/nightly/nightly_dsr_pull_db_with_override.py >> /var/log/dsr-pull-db.log 2>&1
# DSR CSV import with manual override protection
# SEPARATED Meraki and enrichment scripts (ROLLBACK MODE)
0 1 * * * /usr/bin/python3 /usr/local/bin/Main/nightly/nightly_meraki_db.py >> /var/log/meraki-mx-db.log 2>&1
0 3 * * * /usr/bin/python3 /usr/local/bin/Main/nightly/nightly_enriched_db.py >> /var/log/nightly-enriched-db.log 2>&1
# Full inventory scan
0 2 * * * /usr/bin/python3 /usr/local/bin/Main/nightly/nightly_inventory_db.py >> /var/log/nightly-inventory-db.log 2>&1
# Process enablement tracking in database (4 AM)
0 4 * * * /usr/bin/python3 /usr/local/bin/Main/nightly/nightly_enablement_db.py >> /var/log/nightly-enablement-db.log 2>&1
# Circuit change history
30 4 * * * /usr/bin/python3 /usr/local/bin/Main/nightly/nightly_circuit_history.py >> /var/log/circuit-history.log 2>&1
# Hourly API performance monitoring (ACTIVE - 24 endpoints)
0 * * * * /usr/bin/python3 /usr/local/bin/Main/nightly/hourly_api_performance.py >> /var/log/api-performance.log 2>&1
*/5 * * * * /usr/local/bin/git_autocommit.sh
# Complete inventory processing pipeline (runs after SNMP collection)
30 2 * * * /usr/bin/python3 /usr/local/bin/Main/nightly_inventory_web_format_update.py >> /var/log/nightly-inventory-pipeline.log 2>&1
# SNMP inventory collection using encrypted credentials
0 2 * * * /usr/bin/python3 /usr/local/bin/Main/nightly_snmp_inventory_collection.py >> /var/log/nightly-snmp-collection.log 2>&1
EOF

# Install rollback cron
sudo crontab /tmp/rollback_cron.txt
```

## Verification Procedures

### Post-Rollback Verification Checklist

1. **Database Connectivity**
   ```bash
   psql -U dsruser -d dsrcircuits -c "SELECT 1;"
   ```

2. **Table Counts**
   ```bash
   psql -U dsruser -d dsrcircuits -c "
   SELECT 'meraki_inventory' as table_name, COUNT(*) as record_count FROM meraki_inventory
   UNION ALL
   SELECT 'enriched_circuits' as table_name, COUNT(*) as record_count FROM enriched_circuits
   UNION ALL  
   SELECT 'circuits' as table_name, COUNT(*) as record_count FROM circuits;"
   ```

3. **Key Data Integrity**
   ```bash
   # Check IAD 05 test site
   psql -U dsruser -d dsrcircuits -c "
   SELECT 'circuits' as source, site_id, provider_name, details_service_speed 
   FROM circuits WHERE site_id = 'IAD 05'
   UNION ALL
   SELECT 'enriched' as source, network_name, wan1_provider, wan1_speed 
   FROM enriched_circuits WHERE network_name = 'IAD 05';"
   ```

4. **Web Application**
   ```bash
   curl -s http://localhost:5052/health | grep -q "OK" && echo "Web app healthy" || echo "Web app issues"
   ```

5. **Service Status**
   ```bash
   sudo systemctl status meraki-dsrcircuits.service
   ```

## Expected Post-Rollback State

### meraki_inventory Table
- **Expected Records**: ~1,300 devices
- **Key Fields**: network_name, device_serial, wan1_ip, wan2_ip, wan1_provider, wan2_provider

### enriched_circuits Table  
- **Expected Records**: ~1,320 circuits
- **Key Fields**: network_name, wan1_provider, wan2_provider, wan1_confirmed, wan2_confirmed

### circuits Table (should remain unchanged)
- **Expected Records**: ~1,950 circuits
- **Key Fields**: site_id, provider_name, details_service_speed, status

## Emergency Contacts

### System Information
- **Server**: 10.0.145.130 (Production)
- **Database**: PostgreSQL dsrcircuits
- **Application**: Flask on port 5052
- **Service**: meraki-dsrcircuits.service

### File Locations
- **Backup Files**: `/tmp/*backup*20250711*.sql`
- **Application**: `/usr/local/bin/Main/`
- **Logs**: `/var/log/meraki-*`
- **Cron**: `sudo crontab -l`

## Notes

### Critical Reminders
- **Always create backup before rollback**: Current state backup before any restoration
- **Verify service status**: Check that meraki-dsrcircuits.service starts after rollback
- **Test web interface**: Ensure the web application loads and displays data correctly
- **Monitor logs**: Check `/var/log/meraki-enriched-merged.log` for any errors
- **Validate cron jobs**: Ensure nightly processing continues to work

### Backup Retention
- **Production backups**: Keep for 30 days minimum
- **Emergency backups**: Keep for 7 days minimum  
- **Archive location**: Consider moving to `/var/backups/` for long-term storage

---

**Document Created**: July 11, 2025  
**Last Updated**: July 11, 2025  
**System**: DSR Circuits - 10.0.145.130  
**Purpose**: Circuit Change Detection Implementation Rollback Procedures