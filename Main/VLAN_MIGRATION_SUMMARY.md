# VLAN Number Migration Summary

**Purpose:** Migrate existing networks from legacy VLAN numbering to new corporate standard  
**Date:** July 10, 2025

## Overview

Networks like NEO 07 use legacy VLAN numbering that needs to be migrated to the new corporate standard. Since IP ranges overlap between old and new VLANs, a specific migration process is required.

## VLAN Number Changes

| Old VLAN | New VLAN | Purpose | IP Range (No Change) |
|----------|----------|---------|---------------------|
| 1 | 100 | Data | 10.x.x.0/25 |
| 101 | 200 | Voice | 10.x.x.128/27 |
| 201 | 400 | Credit Card | 10.x.x.160/28 |
| 301 | 410 | Scanner | 10.x.x.192/28 |
| 300 | 300 | AP Mgmt | No change |
| 800 | 800 | Guest | No change |
| 801 | 801 | IOT | No change |
| 802 | 802 | IoT Network | No change |
| 803 | 803 | IoT Wireless | No change |

## Critical Migration Process (Order Matters!)

### 1. **Backup Phase**
Extract and store for each VLAN:
- IP subnet and appliance IP
- DHCP mode (server/relay/disabled)
- DHCP options (VoIP settings, etc.)
- DNS servers
- DHCP lease time
- Fixed IP assignments (reservations)
- Group policy assignments

### 2. **VLAN Migration (One at a Time)**
For each VLAN that needs a new ID:
1. Delete old VLAN (e.g., VLAN 1)
2. Create new VLAN (e.g., VLAN 100) with:
   - Same IP subnet
   - Same DHCP configuration
   - Same reservations
   - Same group policy
3. Wait for creation to complete
4. Repeat for next VLAN

### 3. **Firewall Rules Update**
Replace all VLAN references in firewall rules:
- `VLAN(1).*` → `VLAN(100).*`
- `VLAN(101).*` → `VLAN(200).*`
- `VLAN(201).*` → `VLAN(400).*`
- `VLAN(301).*` → `VLAN(410).*`

### 4. **Port Configuration Updates**

#### Switch Ports:
- Access port VLAN assignments
- Voice VLAN 101 → 200
- Trunk allowed VLAN lists
- Native VLANs on trunks

#### MX Ports:
- Access port VLANs
- Trunk allowed VLANs
- Native VLANs

## Example Migration Flow

```
1. Backup all configurations
2. Migrate VLAN 1:
   - Store: 10.1.67.0/25, DHCP relay to 10.0.175.5
   - Delete VLAN 1
   - Create VLAN 100 with same 10.1.67.0/25
   - Restore DHCP relay settings
3. Migrate VLAN 101:
   - Store: 10.1.67.128/27, DHCP server, VoIP options
   - Delete VLAN 101
   - Create VLAN 200 with same settings
4. Continue for VLANs 201→400, 301→410
5. Update firewall rules with new VLAN IDs
6. Update all switch ports
7. Update all MX ports
```

## Key Considerations

### Why This Order?
- **IP Overlap Prevention**: Can't have VLAN 1 and VLAN 100 both using 10.1.67.0/25
- **Zero Downtime**: Each VLAN is recreated immediately after deletion
- **Settings Preservation**: All DHCP reservations and options maintained

### What Gets Preserved?
- ✅ IP addressing (no changes)
- ✅ DHCP mode and settings
- ✅ DHCP reservations
- ✅ DHCP options (VoIP, etc.)
- ✅ DNS servers
- ✅ Group policies
- ✅ Firewall rule logic

### What Changes?
- ❗ VLAN IDs only
- ❗ Firewall rule VLAN references
- ❗ Port VLAN assignments

## Migration Script Usage

```bash
# Dry run first (no changes)
python3 vlan_number_migration.py --network-id L_XXXXXXXXX --dry-run

# Execute migration
python3 vlan_number_migration.py --network-id L_XXXXXXXXX

# Check backup files
ls -la vlan_migration_backup_*.json

# Review report
cat vlan_migration_report_*.txt
```

## Rollback Plan

If issues occur:
1. Use backup file to restore original configuration
2. Manually recreate VLANs with original IDs
3. Restore firewall rules from backup
4. Reset port configurations

## Testing Checklist

After migration:
- [ ] Verify all VLANs exist with new IDs
- [ ] Check IP ranges are correct
- [ ] Confirm DHCP is working
- [ ] Test DHCP reservations
- [ ] Verify VoIP phones get correct options
- [ ] Check firewall rules have no old VLAN references
- [ ] Test inter-VLAN routing
- [ ] Verify all ports have correct VLAN assignments

## Common Issues

1. **"IP already in use" error**
   - Ensure old VLAN is fully deleted before creating new one

2. **"VLAN 100 already exists"**
   - Delete default VLAN 100 if migrating VLAN 1

3. **Firewall rules not working**
   - Check all VLAN references were updated
   - Verify policy objects still exist

4. **Ports on wrong VLAN**
   - Run port update section of script
   - May need to update trunk allowed VLANs

---

**Important:** Always test on a non-production network first!