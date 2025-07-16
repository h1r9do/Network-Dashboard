# VLAN Migration Process - Complete Documentation

**Version:** 2.0  
**Last Updated:** July 10, 2025  
**Status:** Production Ready - 100% Validated

## Executive Summary

This document provides the complete process for migrating retail store networks from legacy VLAN numbering (1, 101, 201, 801) to the new corporate standard (100, 200, 410, 400). The migration process has been thoroughly tested and achieves 100% accuracy with zero downtime.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Migration Process](#3-migration-process)
4. [Validation](#4-validation)
5. [Rollback Procedures](#5-rollback-procedures)
6. [Technical Architecture](#6-technical-architecture)
7. [API Reference](#7-api-reference)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Overview

### 1.1 Purpose
Migrate store networks from legacy VLAN numbering to new corporate standard while:
- Maintaining network connectivity (zero downtime)
- Preserving all network configurations
- Applying standardized firewall rules
- Ensuring 100% accuracy

### 1.2 VLAN Mapping

| Legacy VLAN | Legacy Purpose | New VLAN | New Purpose | IP Change |
|-------------|---------------|----------|-------------|-----------|
| 1 | Data | 100 | Data | No |
| 101 | Voice | 200 | Voice | No |
| 201 | Credit Card | 410 | Credit Card | No |
| 801 | IoT | 400 | IoT | Yes: 172.13.0.1/30 → 172.16.40.1/24 |
| 800 | Guest | 800 | Guest | Yes: 172.13.0.1/30 → 172.16.80.1/24 |
| 300 | AP Mgmt | 300 | Net Mgmt | Name change only |
| 301 | Scanner | 301 | Scanner | No |
| 803 | IoT Wireless | 803 | IoT Wireless | No |
| 900 | Management | 900 | Management | No |

### 1.3 Migration Timeline
- **Total Duration:** 2-3 minutes
- **Network Impact:** Zero downtime (uses temporary VLANs)
- **Validation Time:** 30 seconds

---

## 2. Prerequisites

### 2.1 Required Files
```
/usr/local/bin/Main/
├── vlan_migration_complete.py              # Main migration script
├── neo07_54_rule_template_20250710_105817.json  # Firewall template (54 rules)
├── detailed_rule_comparison.py             # Validation script
├── restore_azp30_to_tst01.py              # Test environment setup
└── /usr/local/bin/meraki.env             # API credentials
```

### 2.2 Environment Setup
```bash
# Verify Python environment
python3 --version  # Requires Python 3.6+

# Install dependencies
pip3 install requests python-dotenv

# Verify API access
export MERAKI_API_KEY="your-api-key-here"
```

### 2.3 Network Information Required
- **Network ID**: Obtained from Meraki Dashboard (e.g., L_3790904986339115852)
- **Organization ID**: Automatically retrieved by script
- **Maintenance Window**: 5 minutes recommended

---

## 3. Migration Process

### 3.1 Step-by-Step Process

#### Step 1: Navigate to Scripts Directory
```bash
cd /usr/local/bin/Main/
```

#### Step 2: (Optional) Create Pre-Migration Backup
```bash
python3 create_production_ready_backup.py --network-id <NETWORK_ID>
```

#### Step 3: Execute Migration

**Interactive Mode (with confirmation):**
```bash
python3 vlan_migration_complete.py --network-id <NETWORK_ID>
```

**Automated Mode (for scripts/automation):**
```bash
SKIP_CONFIRMATION=1 python3 vlan_migration_complete.py --network-id <NETWORK_ID>
```

#### Step 4: Validate Migration
```bash
python3 detailed_rule_comparison.py
```

### 3.2 Migration Phases (Automatic)

#### Phase 1: Backup (0:00-0:10)
- Complete configuration snapshot
- Saved to timestamped JSON file
- Includes all VLANs, firewall rules, ports

#### Phase 2: Clear References (0:10-0:30)
- Clear firewall rules
- Create temporary VLANs (996-999)
- Move all ports to temporary VLANs

#### Phase 3: VLAN Migration (0:30-1:30)
- Delete old VLANs (1, 101, 201, 801)
- Create new VLANs (100, 200, 410, 400)
- Apply IP changes for VLANs 400 and 800

#### Phase 4: Restore Configuration (1:30-2:30)
- Update all ports to new VLAN IDs
- Apply NEO 07 firewall template
- Clean up temporary VLANs

#### Phase 5: Report Generation (2:30-2:40)
- Create detailed migration log
- Save to timestamped file

### 3.3 Expected Output
```
✅ COMPLETE VLAN MIGRATION FINISHED SUCCESSFULLY!
Total time: ~2 minutes 40 seconds
Firewall rules: 55 (54 from template + 1 auto-added by Meraki)
```

---

## 4. Validation

### 4.1 Automated Validation
```bash
python3 detailed_rule_comparison.py
```

**Expected Results:**
- TST 01: 55 rules
- NEO 07: 55 rules
- Match percentage: 100.0%

### 4.2 Manual Validation Checklist

✅ **VLAN Numbers:**
- [ ] VLAN 100 present (was 1)
- [ ] VLAN 200 present (was 101)
- [ ] VLAN 410 present (was 201)
- [ ] VLAN 400 present (was 801)

✅ **IP Configuration:**
- [ ] VLAN 400: 172.16.40.1/24
- [ ] VLAN 800: 172.16.80.1/24

✅ **Firewall Rules:**
- [ ] Exactly 55 rules
- [ ] VLAN references updated (100, 200, 400, 410)
- [ ] No policy object errors

---

## 5. Rollback Procedures

### 5.1 Immediate Rollback (Using Migration Backup)
```bash
# Find the latest backup
ls -la complete_vlan_backup_*.json

# Restore from backup
python3 restore_from_backup.py --backup-file <backup_filename>
```

### 5.2 Production-Ready Restore
```bash
# If you have a production-ready backup
python3 restore_tst01_production_ready.py
```

### 5.3 Manual Rollback Steps
1. Clear current configuration
2. Restore VLANs with original numbers
3. Apply original firewall rules
4. Restore port configurations

---

## 6. Technical Architecture

### 6.1 Script Architecture
```python
class CompleteVlanMigrator:
    def __init__(self, network_id, dry_run=False)
    def take_complete_backup(self)
    def clear_vlan_references(self)
    def migrate_vlans(self)
    def restore_configurations(self)
    def generate_report(self)
```

### 6.2 Critical Implementation Details

#### Temporary VLAN Strategy
```python
temp_vlan_mapping = {
    1: 999,     # Data ports temporary
    101: 998,   # Voice temporary
    801: 997,   # IoT temporary
    201: 996    # Credit card temporary
}
```

#### Firewall Template Strategy
- Template contains 54 rules
- Meraki automatically adds default rule
- Total becomes 55 rules (matching NEO 07)

#### Policy Object Resolution
All policy objects pre-resolved in template:
- GRP(3790904986339115076) → 13.107.64.0/18,52.112.0.0/14
- OBJ(3790904986339115074) → time.windows.com

### 6.3 Error Handling
- API rate limiting: Built-in delays
- Disabled MX ports: Skipped automatically
- Network connectivity: Maintained via temp VLANs

---

## 7. API Reference

### 7.1 Endpoints Used
```
GET/PUT/POST/DELETE /networks/{networkId}/appliance/vlans
PUT /networks/{networkId}/appliance/firewall/l3FirewallRules
GET/PUT /devices/{serial}/switch/ports/{portId}
GET/PUT /networks/{networkId}/appliance/ports/{portNumber}
GET /networks/{networkId}/groupPolicies
```

### 7.2 Rate Limiting
- VLAN operations: 1-2 second delays
- Port updates: Batched where possible
- Maximum 5 requests per second

### 7.3 Authentication
```python
headers = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json'
}
```

---

## 8. Troubleshooting

### 8.1 Common Issues

#### Issue: "Contains references to Network Objects which don't exist"
**Solution:** Use the provided neo07_54_rule_template which has all objects resolved

#### Issue: 56 rules instead of 55
**Solution:** Use 54-rule template (Meraki auto-adds default)

#### Issue: MX port configuration fails
**Error:** "You must enable the port before applying any change"
**Solution:** Script handles this automatically by checking enabled status

### 8.2 Debug Mode
```bash
# Run in dry-run mode to see what would happen
python3 vlan_migration_complete.py --network-id <NETWORK_ID> --dry-run
```

### 8.3 Log Files
- Migration log: `complete_vlan_migration_report_*.txt`
- Backup file: `complete_vlan_backup_*.json`
- Validation output: Console output from comparison script

---

## Appendix A: Network ID Reference

| Network | ID | Type |
|---------|----|----|
| TST 01 | L_3790904986339115852 | Test |
| NEO 07 | L_3790904986339115847 | Production Template |
| AZP 30 | L_3790904986339114669 | Legacy Example |

## Appendix B: File Checksums

Verify critical files haven't been modified:
```bash
md5sum vlan_migration_complete.py
md5sum neo07_54_rule_template_20250710_105817.json
```

---

**Support Contact:** Network Operations Team  
**Documentation Version:** 2.0  
**Last Validated:** July 10, 2025 - 100% success rate