# TST 01 DHCP Configuration Summary

**Date:** July 9, 2025  
**Network:** TST 01 (L_3790904986339115852)  
**Status:** ✅ Fully Configured to Match AZP 30

## DHCP Configuration by VLAN

### VLAN 1 (Data) - 10.255.255.0/25
- **DHCP Mode:** Run a DHCP server (converted from relay due to test environment)
- **Lease Time:** 12 hours
- **DNS Servers:** 10.255.255.5, 10.255.255.6
- **Note:** In production AZP 30 uses DHCP relay to 10.0.175.5, 10.101.175.5

### VLAN 101 (Voice) - 10.255.255.128/27 ✅
- **DHCP Mode:** Run a DHCP server
- **Lease Time:** 1 day
- **DNS Servers:** 10.255.255.5, 10.255.255.6
- **DHCP Options:**
  - Option 42 (NTP Server): 10.255.255.30
  - Option 66 (TFTP Server): 10.255.255.35
- **Purpose:** VoIP phone provisioning

### VLAN 201 (Ccard) - 10.255.255.160/28
- **DHCP Mode:** Run a DHCP server (converted from relay due to test environment)
- **Lease Time:** 12 hours
- **DNS Servers:** 10.255.255.5, 10.255.255.6
- **Note:** In production AZP 30 uses DHCP relay to 10.0.175.5, 10.101.175.5

### VLAN 300 (AP Mgmt) - 10.255.255.176/28 ✅
- **DHCP Mode:** Run a DHCP server
- **Lease Time:** 1 day
- **DNS Servers:** 10.255.255.5, 10.255.255.6
- **Fixed IP Assignments:** 7 devices
  - 00:18:0a:80:8b:6a → 10.255.255.180 (AP1)
  - 00:18:0a:80:91:46 → 10.255.255.181 (AP2)
  - 00:18:0a:80:92:fc → 10.255.255.182 (AP3)
  - 00:18:0a:80:8b:e4 → 10.255.255.183 (AP4)
  - 0c:8d:db:6e:be:2c → 10.255.255.188 (SW1)
  - 0c:8d:db:b3:0e:78 → 10.255.255.189 (SW2)
  - 0c:8d:db:6e:bb:dc → 10.255.255.190 (SW3)

### VLAN 301 (Scanner) - 10.255.255.192/28
- **DHCP Mode:** Run a DHCP server
- **Lease Time:** 1 day
- **DNS Servers:** 10.255.255.5, 10.255.255.6

### VLAN 800 (Guest) - 172.13.0.0/30
- **DHCP Mode:** Run a DHCP server
- **Lease Time:** 1 day
- **DNS Servers:** upstream_dns
- **Group Policy:** Guest Network

### VLAN 801 (IOT) - 172.14.0.0/24
- **DHCP Mode:** Run a DHCP server
- **Lease Time:** 1 day
- **DNS Servers:** upstream_dns

### VLAN 802 (IoT Network) - 172.21.0.0/24
- **DHCP Mode:** Run a DHCP server
- **Lease Time:** 1 day
- **DNS Servers:** upstream_dns

### VLAN 803 (IoT Wireless) - 172.22.0.0/24
- **DHCP Mode:** Run a DHCP server
- **Lease Time:** 1 day
- **DNS Servers:** upstream_dns

### VLAN 900 (Mgmt) - 10.255.255.252/30
- **DHCP Mode:** Run a DHCP server
- **Lease Time:** 1 day
- **DNS Servers:** upstream_dns

## Key Differences from Production (AZP 30)

1. **DHCP Relay → Server Conversion:**
   - VLANs 1 and 201 use DHCP relay in production (10.0.175.5, 10.101.175.5)
   - Converted to local DHCP server for test environment
   - These servers are not reachable from test network

2. **DNS Server Translation:**
   - Production DNS: 10.0.175.5, 10.101.175.5
   - Test DNS: 10.255.255.5, 10.255.255.6 (translated to test range)

3. **DHCP Options Translation:**
   - NTP Server: 10.0.175.30 → 10.255.255.30
   - TFTP Server: 10.103.80.35 → 10.255.255.35

## Summary

TST 01 now has complete DHCP configuration matching AZP 30 with appropriate adjustments for the test environment:
- ✅ All DHCP modes configured correctly
- ✅ VoIP phone provisioning options added
- ✅ Fixed IP assignments for infrastructure devices
- ✅ DNS servers configured for all VLANs
- ✅ Lease times match production settings

The network is fully configured for VLAN migration testing.