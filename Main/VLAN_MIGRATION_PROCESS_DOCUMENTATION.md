# VLAN Migration Process - Complete Documentation

**Date:** July 10, 2025  
**Version:** 1.0 (Production Ready)  
**Status:** ✅ FULLY TESTED AND VALIDATED

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Migration Process Steps](#migration-process-steps)
4. [Scripts and Files](#scripts-and-files)
5. [Validation Process](#validation-process)
6. [Troubleshooting](#troubleshooting)
7. [Technical Details](#technical-details)

---

## Overview

This document provides the complete, step-by-step process for migrating store networks from legacy VLAN numbering to the new corporate standard. The process has been tested and validated to produce exact matches with NEO 07's configuration.

### VLAN Number Mapping
| Legacy VLAN | New VLAN | Purpose | IP Change Required |
|-------------|----------|---------|-------------------|
| 1 | 100 | Data | No |
| 101 | 200 | Voice | No |
| 801 | 400 | IoT | Yes (172.13.0.1/30 → 172.16.40.1/24) |
| 201 | 410 | Credit Card | No |
| 800 | 800 | Guest | Yes (172.13.0.1/30 → 172.16.80.1/24) |
| 300 | 300 | AP Mgmt → Net Mgmt | No (name change only) |
| 301 | 301 | Scanner | No |
| 803 | 803 | IoT Wireless | No |
| 900 | 900 | Management | No |

---

## Prerequisites

### Required Files
1. **Migration Script:** `vlan_migration_complete.py`
2. **NEO 07 Template:** `neo07_54_rule_template_20250710_105817.json` (54 rules, no default rule)
3. **Environment File:** `/usr/local/bin/meraki.env` (contains API key)
4. **Python Dependencies:** requests, dotenv

### Network Requirements
- Target network must be accessible via Meraki API
- Network ID must be known (e.g., L_3790904986339115852 for TST 01)
- Maintenance window scheduled (migration takes ~2-3 minutes)

---

## Migration Process Steps

### Step 1: Pre-Migration Backup (Optional but Recommended)

```bash
# Create production-ready backup for quick restoration if needed
python3 create_production_ready_backup.py --network-id <NETWORK_ID>
```

This creates a complete backup of:
- All VLANs with current configuration
- Firewall rules (with legacy VLAN references)
- MX port configurations
- Switch port configurations
- Group policies

### Step 2: Run the Migration

```bash
# Run the complete VLAN migration
python3 vlan_migration_complete.py --network-id <NETWORK_ID>
```

**For automated/scripted runs:**
```bash
# Skip confirmation prompt
SKIP_CONFIRMATION=1 python3 vlan_migration_complete.py --network-id <NETWORK_ID>
```

### Step 3: Migration Process (Automatic)

The script performs these actions automatically:

1. **Complete Backup** (0:00-0:10)
   - Saves all current configurations
   - Creates timestamped backup file

2. **Clear VLAN References** (0:10-0:30)
   - Removes all firewall rules
   - Creates temporary VLANs (996, 997, 998, 999)
   - Moves all switch ports to temporary VLANs
   - Updates MX ports to temporary VLANs

3. **Migrate VLANs** (0:30-1:30)
   - Deletes old VLANs (1, 101, 201, 801)
   - Creates new VLANs (100, 200, 410, 400)
   - Updates IP configurations for VLANs 400 and 800
   - Preserves all VLAN settings (DHCP, DNS, etc.)

4. **Restore Configurations** (1:30-2:30)
   - Updates all switch ports to new VLAN IDs
   - Updates MX ports to new VLAN IDs
   - Applies NEO 07 firewall template (54 rules)
   - Deletes temporary VLANs

5. **Generate Report** (2:30-2:40)
   - Creates detailed migration report
   - Logs all actions taken

### Step 4: Validate Migration

```bash
# Run detailed comparison against NEO 07
python3 detailed_rule_comparison.py
```

Expected output:
- TST 01: 55 rules
- NEO 07: 55 rules
- Match percentage: 100.0%

---

## Scripts and Files

### Primary Migration Script
**File:** `vlan_migration_complete.py`  
**Purpose:** Main migration script that handles the complete VLAN migration process  
**Key Features:**
- Automatic backup before migration
- Zero-downtime migration using temporary VLANs
- Firewall rule migration with NEO 07 template
- Comprehensive error handling and logging

### NEO 07 Firewall Template
**File:** `neo07_54_rule_template_20250710_105817.json`  
**Purpose:** Clean firewall template with 54 rules (Meraki auto-adds default rule)  
**Key Features:**
- All policy object references resolved to IP ranges
- Uses new VLAN numbers (100, 200, 400, 410)
- No duplicate default rules

### Supporting Scripts

1. **Backup/Restore Scripts:**
   - `create_production_ready_backup.py` - Creates complete network backup
   - `restore_tst01_production_ready.py` - Quick restore from backup
   - `wipe_tst01.py` - Clears configuration for testing

2. **Validation Scripts:**
   - `detailed_rule_comparison.py` - Line-by-line firewall rule comparison
   - `compare_post_migration_to_neo07.py` - Complete configuration comparison
   - `check_tst01_current_rules.py` - Quick rule count check

3. **Template Creation:**
   - `create_clean_neo07_template.py` - Creates template with resolved policy objects
   - `create_54_rule_template.py` - Removes default rule for clean application

---

## Validation Process

### 1. Rule Count Validation
```bash
python3 check_tst01_current_rules.py
```
- Should show exactly 55 rules
- Should have only one "Default rule" entry

### 2. Detailed Rule Comparison
```bash
python3 detailed_rule_comparison.py
```
- Should show 100% match rate
- All 55 rules should match between sites

### 3. VLAN Verification
Check that all VLANs use new numbering:
- VLAN 100 (Data) - replaced VLAN 1
- VLAN 200 (Voice) - replaced VLAN 101
- VLAN 400 (IoT) - replaced VLAN 801
- VLAN 410 (Credit Card) - replaced VLAN 201

### 4. IP Configuration Verification
Verify IP changes were applied:
- VLAN 400: 172.16.40.1/24
- VLAN 800: 172.16.80.1/24

---

## Troubleshooting

### Issue: Extra Default Rule (56 rules instead of 55)
**Cause:** Using template with default rule included  
**Solution:** Use `neo07_54_rule_template_20250710_105817.json` which has no default rule

### Issue: Policy Object Errors
**Cause:** NEO 07 template contains unresolved GRP() or OBJ() references  
**Solution:** Use clean template with all policy objects resolved to IP ranges

### Issue: MX Port Configuration Errors
**Error:** "You must enable the port before applying any change to it"  
**Cause:** Trying to configure disabled ports  
**Solution:** Script already handles this by checking port enabled status

### Issue: Migration Fails Mid-Process
**Recovery Steps:**
1. Check backup file was created
2. Use restore script to return to pre-migration state
3. Review error logs
4. Address specific issue
5. Retry migration

---

## Technical Details

### Migration Flow Diagram
```
Start
  ↓
Take Complete Backup
  ↓
Clear Firewall Rules
  ↓
Create Temporary VLANs (996-999)
  ↓
Move All Ports to Temp VLANs
  ↓
Delete Old VLANs (1, 101, 201, 801)
  ↓
Create New VLANs (100, 200, 410, 400)
  ↓
Update IP Configs (400, 800)
  ↓
Move All Ports to New VLANs
  ↓
Apply NEO 07 Firewall Template (54 rules)
  ↓
Delete Temporary VLANs
  ↓
Generate Report
  ↓
Complete (55 rules total - Meraki adds default)
```

### API Endpoints Used
- `/networks/{id}/appliance/vlans` - VLAN management
- `/networks/{id}/appliance/firewall/l3FirewallRules` - Firewall rules
- `/devices/{serial}/switch/ports/{port}` - Switch port configuration
- `/networks/{id}/appliance/ports/{port}` - MX port configuration
- `/networks/{id}/groupPolicies` - Group policy backup

### Time Requirements
- **Backup Phase:** ~10 seconds
- **Reference Clearing:** ~20 seconds
- **VLAN Migration:** ~60 seconds
- **Configuration Restore:** ~60 seconds
- **Cleanup:** ~10 seconds
- **Total Time:** ~2-3 minutes

### Rollback Process
If migration needs to be reversed:
```bash
# Option 1: Use production-ready backup
python3 restore_tst01_production_ready.py

# Option 2: Use migration backup (created automatically)
python3 restore_from_backup.py --backup-file complete_vlan_backup_<NETWORK_ID>_<TIMESTAMP>.json
```

---

## Best Practices

1. **Always Test First:** Run migration on test network (TST 01) before production
2. **Schedule Maintenance Window:** Migration takes 2-3 minutes of network reconfiguration
3. **Create Backup:** Use production-ready backup script before migration
4. **Validate Results:** Always run comparison scripts after migration
5. **Document Changes:** Keep migration reports for audit trail

## Support Files Location

All files should be placed in: `/usr/local/bin/Main/`

Key files:
- `vlan_migration_complete.py` - Main migration script
- `neo07_54_rule_template_20250710_105817.json` - Firewall template
- `detailed_rule_comparison.py` - Validation script
- All backup/restore scripts

---

**Last Updated:** July 10, 2025  
**Validated On:** TST 01 → 100% match with NEO 07  
**Author:** Migration process developed and tested via Claude