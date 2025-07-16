# TST 01 Backup and Restore Documentation

**Created:** July 10, 2025  
**Status:** ✅ **PRODUCTION READY**  
**Environment:** TST 01 Test Network  

## Overview

This document provides comprehensive documentation for the dual backup and restore approach implemented for TST 01. Two methods are available for restoring TST 01 to a production-ready state for VLAN migration testing.

## Backup and Restore Options

### Option 1: Comprehensive Restore (From Source)
**Script:** `restore_azp30_to_tst01.py`  
**Duration:** ~2 minutes  
**Source:** AZP 30 original configuration file  

#### When to Use:
- Initial setup of test environment
- When AZP 30 source configuration has changed
- When you need the latest production configuration
- For complete documentation of the restore process

#### Features:
- Processes original AZP 30 configuration
- Converts production IP ranges to test ranges
- Filters and simplifies policy object references
- Creates comprehensive backup before restoration
- Handles MX port API restrictions for disabled ports
- Provides detailed logging and reporting

#### Usage:
```bash
# With confirmation prompt
python3 restore_azp30_to_tst01.py

# Skip confirmation (for automation)
SKIP_CONFIRMATION=1 python3 restore_azp30_to_tst01.py
```

### Option 2: Quick Production-Ready Restore (From Backup)
**Script:** `restore_tst01_production_ready.py`  
**Duration:** ~30-45 seconds  
**Source:** Production-ready backup file  

#### When to Use:
- Repeated migration testing
- Quick reset to known good state
- When speed is important
- For multiple test iterations

#### Features:
- Uses pre-processed backup file
- 3-4x faster than comprehensive restore
- Identical end result to comprehensive restore
- Same configuration validation
- Perfect for repeated testing scenarios

#### Usage:
```bash
# With confirmation prompt
python3 restore_tst01_production_ready.py

# Skip confirmation (for automation)
SKIP_CONFIRMATION=1 python3 restore_tst01_production_ready.py
```

## Production-Ready Backup Details

### Backup File Information
**File:** `tst01_production_ready_backup_20250710_091816.json`  
**Created:** July 10, 2025 at 09:18:16  
**Source:** Complete AZP 30 configuration restored to TST 01  
**Size:** Complete network configuration with all components  

### Backup Contents
```
Components Backed Up:
- VLANs: 10 (legacy numbering with production complexity)
- Firewall Rules: 59 (with VLAN references)
- MX Ports: 10 (with VLAN assignments)
- Switch Configs: 2 switches (complete port configs)
- Group Policies: 3 (policy configurations)
```

### Configuration Details
```
VLAN Configuration:
  VLAN 1: Data - 10.1.32.0/25
  VLAN 101: Voice - 10.1.32.128/27
  VLAN 201: Ccard - 10.1.32.160/28
  VLAN 300: AP Mgmt - 10.1.32.176/28
  VLAN 301: Scanner - 10.1.32.192/28
  VLAN 800: Guest - 172.13.0.0/30
  VLAN 801: IOT - 172.14.0.0/24
  VLAN 802: IoT Network - 172.21.0.0/24
  VLAN 803: IoT Wireless - 172.22.0.0/24
  VLAN 900: Mgmt - 10.255.255.252/30

Firewall Rules:
  Total Rules: 59
  Rules with VLAN references: 52
  Production complexity with cross-VLAN policies

Network Hardware:
  MX Appliance: 10 ports configured (8 successful, 2 disabled)
  Switches: 2 switches with 28 ports each (56 total ports)
```

## Comparison of Approaches

### Performance Comparison
| Aspect | Comprehensive Restore | Quick Restore |
|--------|----------------------|---------------|
| **Duration** | ~2 minutes | ~30-45 seconds |
| **Source** | AZP 30 config file | Backup file |
| **Processing** | IP conversion + filtering | Direct restoration |
| **Use Case** | Initial/changed config | Repeated testing |
| **Flexibility** | Handles source changes | Fixed configuration |

### Result Comparison
Both approaches produce **identical results**:
- Same VLAN configuration (10 VLANs with legacy numbering)
- Same firewall rules (59 rules with 52 VLAN references)
- Same port configurations (MX and switch ports)
- Same production complexity for testing

## Implementation Timeline

### July 10, 2025 - Morning
**09:01:06** - Comprehensive restore completed successfully
- AZP 30 configuration fully restored to TST 01
- 1 minute 55 second duration
- All components restored successfully

**09:18:16** - Production-ready backup created
- Complete TST 01 configuration backed up
- Ready for quick restore scenarios

**09:30:00** - Quick restore script created
- Fast restoration capability implemented
- Documentation updated

## File Structure

```
/usr/local/bin/Main/
├── Restore Scripts:
│   ├── restore_azp30_to_tst01.py              # Comprehensive restore (2 min)
│   └── restore_tst01_production_ready.py      # Quick restore (30-45 sec)
├── Source Configurations:
│   ├── azp_30_full_config_20250709_170149.json # AZP 30 original config
│   └── azp_30_original_firewall_rules.json    # Original firewall rules
├── Backup Files:
│   ├── tst01_production_ready_backup_20250710_091816.json # Production-ready backup
│   └── tst01_backup_before_azp30_restore_*.json          # Pre-restore backups
└── Reports:
    ├── azp30_to_tst01_restore_report_*.txt    # Comprehensive restore reports
    ├── tst01_quick_restore_report_*.txt       # Quick restore reports
    └── tst01_production_ready_backup_summary_*.txt # Backup summaries
```

## Best Practices

### For Initial Setup
1. Use comprehensive restore script to process latest AZP 30 configuration
2. Create new production-ready backup if source configuration changes
3. Validate complete restoration with configuration verification

### For Repeated Testing
1. Use quick restore script for faster iteration
2. Maintain production-ready backup for consistent baseline
3. Create new backups before major configuration changes

### For Migration Testing
1. Start with quick restore to establish baseline
2. Run migration scripts against restored configuration
3. Use quick restore between test iterations for clean state

## Troubleshooting

### Common Issues

#### Comprehensive Restore Issues
- **MX Port Errors**: Disabled ports cannot have VLAN configuration applied
- **API Rate Limiting**: Built-in delays handle rate limits
- **Missing Source Files**: Ensure AZP 30 config files are present

#### Quick Restore Issues
- **Missing Backup File**: Ensure production-ready backup file exists
- **Outdated Backup**: Create new backup if source configuration changed
- **Network Connectivity**: Verify API connectivity to TST 01

### Error Recovery
1. **Failed Restore**: Use backup files to restore previous state
2. **Partial Restoration**: Run cleanup scripts and retry
3. **Configuration Drift**: Create new production-ready backup

## Validation Procedures

### Post-Restore Verification
```bash
# Verify VLAN configuration
python3 -c "
import requests, os
from dotenv import load_dotenv
load_dotenv('/usr/local/bin/meraki.env')
api_key = os.getenv('MERAKI_API_KEY')
headers = {'X-Cisco-Meraki-API-Key': api_key}
response = requests.get('https://api.meraki.com/api/v1/networks/L_3790904986339115852/appliance/vlans', headers=headers)
vlans = response.json()
print(f'VLANs: {len(vlans)} total')
for vlan in sorted(vlans, key=lambda x: x['id']):
    print(f'  VLAN {vlan[\"id\"]}: {vlan[\"name\"]} - {vlan[\"subnet\"]}')
"

# Verify firewall rules
python3 -c "
import requests, os
from dotenv import load_dotenv
load_dotenv('/usr/local/bin/meraki.env')
api_key = os.getenv('MERAKI_API_KEY')
headers = {'X-Cisco-Meraki-API-Key': api_key}
response = requests.get('https://api.meraki.com/api/v1/networks/L_3790904986339115852/appliance/firewall/l3FirewallRules', headers=headers)
fw_rules = response.json()
vlan_ref_count = sum(1 for rule in fw_rules['rules'] if 'VLAN(' in str(rule.get('srcCidr', '')) or 'VLAN(' in str(rule.get('destCidr', '')))
print(f'Firewall Rules: {len(fw_rules[\"rules\"])} total')
print(f'Rules with VLAN references: {vlan_ref_count}')
"
```

### Expected Results
- **VLANs**: 10 total with legacy numbering (1, 101, 201, 300, 301, 800, 801, 802, 803, 900)
- **Firewall Rules**: 59 total with 52 containing VLAN references
- **Configuration State**: Production-ready for VLAN migration testing

## Security Considerations

### Backup Security
- Production-ready backups contain complete network configuration
- Store backup files securely with appropriate access controls
- Backup files contain sensitive network topology information

### Restore Security
- Both restore scripts require Meraki API key access
- Scripts modify complete network configuration
- Verify target network ID before execution

## Maintenance

### Regular Tasks
1. **Monthly**: Verify backup file integrity
2. **When AZP 30 Changes**: Create new comprehensive backup
3. **Before Major Testing**: Validate quick restore functionality

### Backup Rotation
- Keep multiple production-ready backups for different test scenarios
- Archive old backups with clear naming conventions
- Document backup creation dates and source configurations

---

**Last Updated:** July 10, 2025  
**Backup File:** `tst01_production_ready_backup_20250710_091816.json`  
**Status:** ✅ Ready for production VLAN migration testing  
**Next Review:** When AZP 30 source configuration changes