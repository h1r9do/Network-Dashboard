# AZP 30 MX Appliance Port Configuration Summary

**Network Name:** AZP 30  
**Network ID:** L_650207196201635912  
**Extraction Date:** July 9, 2025  

## Port Configuration Overview

The AZP 30 MX appliance has 10 configured ports (ports 3-12), with 8 ports enabled and 2 disabled.

### Active Ports

| Port | Type | Native VLAN | Allowed VLANs | Purpose |
|------|------|-------------|---------------|----------|
| 3 | Trunk | 1 (Data) | 1,101,201,300,301,900,803 | Main trunk - excludes guest VLANs (800,801,802) |
| 4 | Trunk | 300 (AP Mgmt) | 1,101,201,300,301,800,801,802,803 | Full trunk - all VLANs |
| 5 | Trunk | 300 (AP Mgmt) | 1,101,201,300,301,800,801,802,803 | Full trunk - all VLANs |
| 6 | Trunk | 300 (AP Mgmt) | 1,101,201,300,301,800,801,802,803 | Full trunk - all VLANs |
| 8 | Trunk | 802 (IoT Network) | 802 only | Dedicated IoT Network trunk |
| 9 | Access | 801 (IOT) | N/A | IOT access port |
| 10 | Trunk | 1 (Data) | 1,101,201,300,301 | Limited trunk - corporate VLANs only |
| 12 | Trunk | 800 (Guest) | 800,802 | Guest/IoT trunk |

### Disabled Ports
- Port 7: Trunk port configured for all VLANs (currently disabled)
- Port 11: Trunk port configured for all VLANs (currently disabled)

## VLAN Configuration and DHCP Settings

### Corporate VLANs

1. **VLAN 1 - Data**
   - Subnet: 10.1.32.0/25
   - Gateway: 10.1.32.1
   - DHCP: Relay to another server

2. **VLAN 101 - Voice**
   - Subnet: 10.1.32.128/27
   - Gateway: 10.1.32.129
   - DHCP: Running local DHCP server (12-hour lease)
   - DHCP Options:
     - Option 42 (NTP Servers): 10.0.130.102, 10.0.130.82, 10.101.130.228, 10.101.130.227
     - Option 66 (TFTP Server): https://159357:68473900@config.tetravx.com/provision/us3/app/
     - Option 150 (TFTP Server IPs): 10.0.99.100, 10.101.99.102

3. **VLAN 201 - Ccard**
   - Subnet: 10.1.32.160/28
   - Gateway: 10.1.32.161
   - DHCP: Relay to another server

4. **VLAN 300 - AP Management**
   - Subnet: 10.1.32.176/28
   - Gateway: 10.1.32.177
   - DHCP: Running local DHCP server (1-day lease)
   - Fixed IP Assignments:
     - azp_30ap01: 10.1.32.180 (00:18:0a:35:fe:2e)
     - azp_30ap02: 10.1.32.181 (00:18:0a:81:04:4e)
     - azp_30ap03: 10.1.32.182 (0c:8d:db:93:22:f6)
     - azp_30ap11: 10.1.32.186 (e4:55:a8:16:00:29)
     - azp_30ap10: 10.1.32.187 (e4:55:a8:16:00:6f)
     - azp_30sw01: 10.1.32.188 (98:18:88:b8:cc:67)
     - azp_30sw02: 10.1.32.189 (98:18:88:b8:db:ec)

5. **VLAN 301 - Scanner**
   - Subnet: 10.1.32.192/28
   - Gateway: 10.1.32.193
   - DHCP: Running local DHCP server (1-day lease)

6. **VLAN 900 - Management**
   - Subnet: 10.1.32.252/30
   - Gateway: 10.1.32.253
   - DHCP: Running local DHCP server (1-day lease)

### Guest/IoT VLANs

7. **VLAN 800 - Guest**
   - Subnet: 172.13.0.0/30
   - Gateway: 172.13.0.1
   - DHCP: Running local DHCP server (1-day lease)
   - Group Policy: 100

8. **VLAN 801 - IOT**
   - Subnet: 172.14.0.0/24
   - Gateway: 172.14.0.1
   - DHCP: Running local DHCP server (1-day lease)
   - Group Policy: 100

9. **VLAN 802 - IoT Network**
   - Subnet: 172.21.0.0/24
   - Gateway: 172.21.0.1
   - DHCP: Running local DHCP server (1-day lease)

10. **VLAN 803 - IoT Wireless**
    - Subnet: 172.22.0.0/24
    - Gateway: 172.22.0.1
    - DHCP: Running local DHCP server (1-day lease)
    - Group Policy: 100

## Appliance Settings

- **Deployment Mode:** Routed
- **Client Tracking Method:** MAC address
- **Dynamic DNS:** Not configured

## Key Observations

1. **Port Usage Pattern:**
   - Ports 4, 5, 6 are configured identically as full trunks with AP Management as native VLAN
   - Port 3 and 10 exclude guest/IoT VLANs (800, 801, 802, 803)
   - Dedicated ports for specific purposes (Port 8 for IoT Network, Port 9 for IOT access)

2. **DHCP Configuration:**
   - Corporate data and credit card VLANs use DHCP relay
   - Voice VLAN has local DHCP with VoIP-specific options
   - All management, guest, and IoT VLANs run local DHCP servers

3. **Security Segmentation:**
   - Clear separation between corporate (10.x.x.x) and guest/IoT (172.x.x.x) networks
   - Group Policy 100 applied to guest and IoT VLANs for access control

## Files Generated

1. **Port Configuration:** `/usr/local/bin/mx_ports_azp30_20250709_164932.json`
2. **VLAN Configuration:** `/usr/local/bin/mx_vlans_azp30_20250709_164933.json`
3. **Appliance Settings:** `/usr/local/bin/mx_settings_azp30_20250709_164933.json`
4. **Complete Report:** `/usr/local/bin/mx_complete_config_azp30_20250709_164933.json`