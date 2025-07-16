# Complete Network Migration - Usage Guide

## Overview
The Complete Network Migration tool provides a single-script solution for migrating Meraki MX network configurations with VLAN remapping, policy objects, group policies, and firewall rules.

## Prerequisites

### Environment Setup
```bash
# 1. Ensure Python packages are installed
pip install requests python-dotenv ipaddress

# 2. Configure Meraki API key in /usr/local/bin/meraki.env
echo "MERAKI_API_KEY=your_api_key_here" > /usr/local/bin/meraki.env

# 3. Make script executable
chmod +x complete_network_migration.py
```

### Required Files
- **Source Configuration**: JSON export of source network (e.g., `azp_30_config.json`)
- **Firewall Template**: Firewall rules template (e.g., `firewall_rules_template.json`)
- **Migration Steps**: Reference documentation (`migration_steps.json`)

## Usage Examples

### 1. Dry Run (Recommended First)
```bash
python3 complete_network_migration.py \
  --network-id L_3790904986339115852 \
  --source-config azp_30_config.json \
  --firewall-template firewall_rules_template.json \
  --mode test \
  --dry-run
```

### 2. Test Environment Deployment
```bash
python3 complete_network_migration.py \
  --network-id L_3790904986339115852 \
  --source-config azp_30_config.json \
  --firewall-template firewall_rules_template.json \
  --mode test \
  --auto-confirm
```

### 3. Production Deployment
```bash
python3 complete_network_migration.py \
  --network-id L_12345678901234567890 \
  --source-config azp_30_config.json \
  --firewall-template firewall_rules_template.json \
  --mode production
```

### 4. Custom Syslog Server
```bash
python3 complete_network_migration.py \
  --network-id L_12345678901234567890 \
  --source-config azp_30_config.json \
  --firewall-template firewall_rules_template.json \
  --mode production \
  --syslog-server 10.1.1.100 \
  --syslog-port 514
```

## Command Line Options

| Option | Required | Description |
|--------|----------|-------------|
| `--network-id` | Yes | Target Meraki network ID (L_xxxxxxxxxxxxx) |
| `--source-config` | Yes | Source network configuration JSON file |
| `--firewall-template` | Yes | Firewall rules template JSON file |
| `--mode` | No | Migration mode: `test` or `production` (default: production) |
| `--syslog-server` | No | Custom syslog server IP (default: 10.0.175.30) |
| `--syslog-port` | No | Custom syslog port (default: 514) |
| `--dry-run` | No | Show what would be done without making changes |
| `--auto-confirm` | No | Skip confirmation prompt |

## Migration Modes

### Test Mode
- **Purpose**: Testing and validation environments
- **IP Changes**: 
  - 10.x.x.x networks → 10.255.255.x
  - Guest/IoT networks → 172.16.x.x ranges
  - Syslog server → Updated to test IP
- **Use Cases**: TST 01, staging environments, development

### Production Mode  
- **Purpose**: Live store deployments
- **IP Preservation**: All original IP addresses maintained
- **Use Cases**: New stores, existing store migrations, VLAN renumbering

## Migration Process

The script performs these steps automatically:

### Step 1: Policy Object Discovery (2-3 min)
- Scans firewall rules for OBJ() and GRP() references
- Identifies required policy objects and groups

### Step 2: Policy Object Migration (3-5 min)
- Migrates network objects from source organization
- Creates object groups with proper dependencies
- Maps old IDs to new IDs for firewall rules

### Step 3: Group Policy Creation (1-2 min)
- Creates bandwidth and access control policies
- Maps policy IDs for VLAN assignments

### Step 4: VLAN Cleanup (2-3 min)
- Removes existing VLANs (maintains minimum of 1)
- Handles Meraki constraints gracefully

### Step 5: VLAN Migration (5-8 min)
- Creates VLANs with new ID mapping:
  - VLAN 1 → 100 (Data)
  - VLAN 101 → 200 (Voice)
  - VLAN 201 → 410 (Ccard)
  - VLAN 801 → 400 (IoT)
  - etc.
- Preserves all DHCP settings and options
- Applies group policies appropriately

### Step 6: Syslog Configuration (1 min)
- Configures syslog server for security logging
- Enables all required logging roles

### Step 7: Firewall Rules Deployment (2-3 min)
- Applies complete 55+ rule set from template
- Updates object/group references with new IDs
- Handles VLAN number translations

### Step 8: Validation (1-2 min)
- Verifies all components deployed correctly
- Generates comprehensive report

## Output Files

### Migration Report
```
complete_migration_report_<network_id>_<timestamp>.txt
```
Contains complete log of all operations with timing and results.

### ID Mappings
```
migration_mappings_<network_id>_<timestamp>.json
```
Contains mapping of old IDs to new IDs for reference.

## Success Criteria

✅ **VLANs**: 9 VLANs created with correct IDs and subnets
✅ **Group Policies**: 3 policies created and applied
✅ **Policy Objects**: All referenced objects migrated
✅ **Firewall Rules**: 55+ rules applied with working references
✅ **Syslog**: Server configured for security logging
✅ **DHCP**: All settings preserved and functional

## Troubleshooting

### Common Issues

**API Rate Limits**
- Script includes automatic retry with 60-second delays
- Large deployments may take 20-25 minutes total

**VLAN Conflicts**
- Script handles existing VLANs and provides clean errors
- Use dry-run first to identify potential issues

**Missing Policy Objects**
- Script auto-migrates from DTC-Store-Inventory-All org (436883)
- Requires read access to source organization

**Group Policy Name Conflicts**
- Script skips existing policies and maps to existing IDs
- No duplicate policies will be created

### Getting Help

1. **Review the migration report** for detailed error messages
2. **Check the mappings file** for ID translation issues  
3. **Run with dry-run first** to validate configuration
4. **Verify API permissions** for both source and target organizations

## Rollback Procedure

If migration fails or needs to be reverted:

```bash
# 1. Reset network to default state
python3 reset_tst_01_vlans.py  # For TST 01

# 2. Manually remove group policies via Dashboard
# 3. Clear firewall rules via Dashboard  
# 4. Remove syslog configuration via Dashboard
```

## Best Practices

1. **Always run dry-run first** to validate configuration
2. **Use test mode** for staging environments
3. **Backup original configuration** before migration
4. **Verify all prerequisites** before starting
5. **Monitor API rate limits** during large deployments
6. **Test connectivity** after migration completes

## Estimated Times

- **Small Network** (< 10 VLANs): 15-20 minutes
- **Large Network** (10+ VLANs): 20-25 minutes  
- **Test Mode**: Slightly faster due to IP simplification
- **Production Mode**: May take longer due to DHCP complexity

## Support

For issues or questions:
1. Review migration logs and reports
2. Check API permissions and connectivity
3. Verify source file formats and content
4. Consult migration_steps.json for detailed process flow