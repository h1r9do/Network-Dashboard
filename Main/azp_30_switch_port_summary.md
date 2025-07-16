# AZP 30 Switch Port Configuration Summary

## Network Information
- **Network ID**: L_650207196201635912
- **Network Name**: AZP 30
- **Extraction Date**: July 10, 2025

## Switch Inventory
- **Total Switches**: 2
- **Total Ports**: 56 (28 ports per switch)

### Switch 1: azp_30sw01
- **Model**: MS125-24P
- **Serial**: Q3DB-7H4V-YGPG
- **IP Address**: 10.1.32.188
- **MAC Address**: 98:18:88:e0:84:40

### Switch 2: azp_30sw02
- **Model**: MS125-24P
- **Serial**: Q3DB-RNYT-SC2N
- **IP Address**: 10.1.32.189
- **MAC Address**: 98:18:88:b8:db:ec

## VLAN Usage Summary

### Original VLANs (Before Remapping)
- **VLAN 1**: Data (Legacy) - Used on workstation ports
- **VLAN 101**: Voice - Used as voice VLAN on all access ports
- **VLAN 201**: Credit Card - Used on ports 8-10 of each switch
- **VLAN 300**: Network Management - Used on trunk ports 21-24
- **VLAN 801**: IoT - Used on ports 11-19/20
- **VLAN 999**: Native VLAN on trunk ports

### VLAN Remapping (For TST 01 Migration)
- VLAN 1 → VLAN 100 (Data)
- VLAN 101 → VLAN 200 (Voice)
- VLAN 201 → VLAN 410 (Credit Card)
- VLAN 300 → VLAN 300 (Network Management - no change)
- VLAN 801 → VLAN 400 (IoT)

## Port Configuration Details

### Access Port Configuration (Ports 1-20)
- **Type**: Access
- **PoE**: Enabled
- **STP Guard**: BPDU Guard
- **RSTP**: Enabled
- **Link Negotiation**: Auto negotiate
- **Access Policy**: Open
- **Storm Control**: Disabled
- **UDLD**: Alert only

### Port Assignments by Function

#### Workstation Data Ports (VLAN 1/101)
- **azp_30sw01**: Ports 1-7, 20
- **azp_30sw02**: Ports 1-7, 20
- **Total**: 16 ports

#### Credit Card Ports (VLAN 201/101)
- **azp_30sw01**: Ports 8-10
- **azp_30sw02**: Ports 8-10
- **Total**: 6 ports

#### IoT Device Ports (VLAN 801/101)
- **azp_30sw01**: Ports 11-19
- **azp_30sw02**: Ports 11-19
- **Total**: 18 ports

#### Trunk Ports (Multiple VLANs)
- **azp_30sw01**: Ports 21-24
- **azp_30sw02**: Ports 21-24
- **Type**: Trunk
- **Native VLAN**: 999
- **Allowed VLANs**: 1,100,201,300-301,800-803
- **Total**: 8 ports

#### Special Ports
- **azp_30sw01 Port 4**: Named "Algo Horn" (Paging system)
- **azp_30sw01 Port 20**: IoT device port (VLAN 801)
- **azp_30sw02 Port 20**: Workstation port (VLAN 1)

## Files Generated

1. **azp_30_switch_config.json**
   - Configuration with VLAN remapping applied
   - Ready for deployment to TST 01

2. **azp_30_switch_config_original_20250710_065006.json**
   - Original configuration without remapping
   - Complete port details including all settings
   - Use this for reference and backup

## Migration Notes

When migrating to TST 01:
1. The VLAN IDs will be automatically remapped using the standard mapping
2. All port settings (PoE, STP, etc.) will be preserved
3. Port names and descriptions will be maintained
4. Trunk port configurations will be updated with new VLAN IDs
5. The migration script handles the deployment automatically

## Usage

To deploy this configuration to TST 01:
```bash
python3 switch_config_migration.py --deploy --network-id <TST_01_NETWORK_ID> --config azp_30_switch_config.json
```

To extract without VLAN remapping:
```bash
python3 extract_azp30_original_config.py
```