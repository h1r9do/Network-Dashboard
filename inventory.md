# SNMP Inventory Collection Status

## Last Updated: 2025-07-06

## Current Task: Collect inventory data from all network devices

### Project Goal
Collect SNMP inventory data from all devices to understand data structure and create appropriate database tables for non-Meraki devices.

## Database Tables Found
1. **device_inventory** - 13,092 devices (Meraki devices)
2. **collected_raw_inventory** - Raw SNMP output storage
3. **comprehensive_device_inventory** - Combined inventory
4. **netdisco_inventory_summary** - Netdisco device summaries
5. **inventory_devices** - Main inventory table with 13,092 records

## Device Sources
1. **Device Connections File**: `/var/www/html/meraki-data/device_connections_sample_full.json`
   - Contains 10 test devices with IPs and hostnames
   - Includes switches from various locations (NOC, ADMIN, CORE, EDGE, PCI)

2. **Database**: 13,092 devices in inventory_devices table

## SNMP Credentials

### Working Credentials Found
- **Device**: 10.44.158.41 (EQX-CldTrst-8500-01.trtc.com)
- **Working v3 User**: EQX_DC_SNMPv3
- **Auth**: SHA / EQX_SNMP_Pass
- **Priv**: AES / 3s6v9y$ShVkYp3s6

### v2c Communities to Test
- DTC4nmgt
- DTC4nmgt98
- T1r3s4u
- L1v3th3Dr3aM
- 3$laC0mm@ndM3

### v3 Users to Test
1. **NNMIuser**
   - Auth: SHA / m@k3\!tS0nuMb341\!
   - Priv: DES / m@k3\!tS0nuMb341\!

2. **EQX_DC_SNMPv3**
   - Auth: SHA / EQX_SNMP_Pass
   - Priv: AES / 3s6v9y$ShVkYp3s6

3. **Network-Team**
   - Auth: SHA / dj@?*ndXI^RArm&i
   - Priv: AES / dj@?*ndXI^RArm&i

## Scripts Created
1. **/usr/local/bin/test_snmp_inventory.py**
   - Tests SNMP v2/v3 credentials against all devices
   - Collects inventory using working credentials
   - Saves results to JSON file

## Key Files
- **Credentials**: `/usr/local/bin/test/snmp_credentials.json`
- **Device List**: `/var/www/html/meraki-data/device_connections_sample_full.json`
- **Output**: `/var/www/html/meraki-data/snmp_inventory_test_results.json`

## Next Steps
1. Run test_snmp_inventory.py to collect data from all devices
2. Analyze JSON output to understand inventory data structure
3. Design database schema for non-Meraki device inventory
4. Create tables and import collected data

## Test Devices Available
- 10.0.255.10 - 2960-CX-Series-NOC Switch
- 10.101.145.125 - AL-5000-01 Switch
- 10.101.145.126 - AL-5000-02 Switch
- 10.101.145.123 - AL-7000-01-ADMIN Switch
- 10.101.255.244 - AL-7000-01-CORE Switch
- 10.101.100.209 - AL-7000-01-EDGE Switch
- 10.101.100.189 - AL-7000-01-PCI Switch
- 10.101.145.124 - AL-7000-02-ADMIN Switch
- 10.0.184.20 - AL-7000-02-CORE Switch
- 10.101.100.217 - AL-7000-02-EDGE Switch

## Status
- Database schema review: ✅ Complete
- Device list compiled: ✅ Complete
- SNMP credentials documented: ✅ Complete
- Test script created: ✅ Complete
- Inventory collection: 🔄 In Progress
EOF < /dev/null
