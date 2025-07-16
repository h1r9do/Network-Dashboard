# DHCP Configuration Comparison Report: AZP 30 vs TST 01

**Report Generated:** July 10, 2025  
**Purpose:** Identify DHCP configuration differences between AZP 30 (production) and TST 01 (test) networks

## Executive Summary

The comparison reveals significant DHCP configuration differences between AZP 30 and TST 01 networks. Key findings:

- **10 VLANs** are common between both networks
- **5 VLANs** require DHCP configuration updates in TST 01
- **Critical differences** include DHCP handling modes, relay servers, DHCP options, and DNS servers

## Detailed Findings

### 1. DHCP Handling Mode Mismatches

Two VLANs in TST 01 are incorrectly configured as DHCP servers when they should relay DHCP:

| VLAN ID | VLAN Name | AZP 30 Mode | TST 01 Mode | Required Action |
|---------|-----------|-------------|-------------|-----------------|
| 1 | Data | Relay DHCP | Run DHCP server | Change to Relay mode |
| 201 | Ccard | Relay DHCP | Run DHCP server | Change to Relay mode |

### 2. DHCP Relay Server Configuration

VLANs that need DHCP relay servers configured:

| VLAN | Required Relay Servers |
|------|------------------------|
| VLAN 1 (Data) | 10.0.175.5, 10.101.175.5 |
| VLAN 201 (Ccard) | 10.0.175.5, 10.101.175.5, 10.0.130.30, 10.101.130.30 |

### 3. DHCP Options Configuration

**VLAN 101 (Voice)** requires critical DHCP options for phone provisioning:

- **Option 42 (NTP Servers):** 10.0.130.102, 10.0.130.82, 10.101.130.228, 10.101.130.227
- **Option 66 (TFTP Server Name):** https://159357:68473900@config.tetravx.com/provision/us3/app/
- **Option 150 (TFTP Server IP):** 10.0.99.100, 10.101.99.102

### 4. DNS Server Configuration

Multiple VLANs need DNS server updates:

| VLAN | Current TST 01 DNS | Required DNS Servers |
|------|-------------------|---------------------|
| VLAN 101 (Voice) | upstream_dns | 10.0.175.27, 10.101.175.28 |
| VLAN 300 (AP Mgmt) | upstream_dns | 10.0.175.27, 10.101.175.28 |
| VLAN 301 (Scanner) | upstream_dns | 10.0.175.27, 10.101.175.28 |

### 5. DHCP Lease Time

| VLAN | AZP 30 Lease | TST 01 Lease | Required Action |
|------|--------------|--------------|-----------------|
| VLAN 101 (Voice) | 12 hours | 1 day | Change to 12 hours |

### 6. Fixed IP Assignments

**VLAN 300 (AP Mgmt)** requires 7 fixed IP assignments for network devices:

| MAC Address | IP Address | Device Name |
|-------------|------------|-------------|
| 00:18:0a:35:fe:2e | 10.1.32.180 | azp_30ap01 |
| 00:18:0a:81:04:4e | 10.1.32.181 | azp_30ap02 |
| 0c:8d:db:93:22:f6 | 10.1.32.182 | azp_30ap03 |
| 98:18:88:b8:cc:67 | 10.1.32.188 | azp_30sw01 |
| 98:18:88:b8:db:ec | 10.1.32.189 | azp_30sw02 |
| e4:55:a8:16:00:29 | 10.1.32.186 | azp_30ap11 |
| e4:55:a8:16:00:6f | 10.1.32.187 | azp_30ap10 |

## VLANs with Matching Configuration

The following VLANs have matching DHCP configurations and require no changes:

- VLAN 800 (Guest)
- VLAN 801 (IOT)
- VLAN 802 (IoT Network)
- VLAN 803 (IoT Wireless)
- VLAN 900 (Mgmt)

## Implementation Priority

Based on the impact to network operations, implement changes in this order:

1. **HIGH PRIORITY:**
   - VLAN 1 (Data) - Change to DHCP relay mode
   - VLAN 201 (Ccard) - Change to DHCP relay mode
   - VLAN 101 (Voice) - Add DHCP options for phone provisioning

2. **MEDIUM PRIORITY:**
   - DNS server updates for VLANs 101, 300, 301
   - VLAN 101 lease time adjustment

3. **LOW PRIORITY:**
   - VLAN 300 fixed IP assignments (can be added as devices are deployed)

## Configuration Commands

### Meraki Dashboard API Updates

To implement these changes via Meraki API:

```python
# Example: Update VLAN 1 to DHCP Relay mode
vlan_update = {
    "dhcpHandling": "Relay DHCP to another server",
    "dhcpRelayServerIps": ["10.0.175.5", "10.101.175.5"]
}

# Example: Add DHCP options to VLAN 101
vlan_101_update = {
    "dhcpLeaseTime": "12 hours",
    "dnsNameservers": "10.0.175.27\n10.101.175.28",
    "dhcpOptions": [
        {
            "code": "42",
            "type": "ip",
            "value": "10.0.130.102, 10.0.130.82, 10.101.130.228, 10.101.130.227"
        },
        {
            "code": "66",
            "type": "text",
            "value": "https://159357:68473900@config.tetravx.com/provision/us3/app/"
        },
        {
            "code": "150",
            "type": "ip",
            "value": "10.0.99.100, 10.101.99.102"
        }
    ]
}
```

## Testing Recommendations

After implementing changes:

1. **DHCP Relay Testing:**
   - Verify clients in VLANs 1 and 201 receive IP addresses from central DHCP servers
   - Check DHCP relay counters on MX appliance

2. **Voice VLAN Testing:**
   - Deploy test phone and verify it receives correct NTP and TFTP server information
   - Confirm phone can download configuration from provisioning server

3. **DNS Resolution Testing:**
   - Test DNS resolution from clients in updated VLANs
   - Verify both primary and secondary DNS servers are reachable

4. **Fixed IP Testing:**
   - Verify devices in VLAN 300 receive their assigned static IPs
   - Check for IP conflicts before implementation

## Conclusion

TST 01 requires significant DHCP configuration updates to match AZP 30. The most critical changes involve switching VLANs 1 and 201 from local DHCP server mode to DHCP relay mode, and adding voice provisioning options to VLAN 101. These changes should be implemented and tested systematically to ensure network stability.