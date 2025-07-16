# Subnet Analysis Page

## Quick Overview
The Subnet Analysis page provides comprehensive network visualization for all VLANs across the infrastructure, helping with IP space management and network planning.

## Access
- **URL**: http://neamsatcor1ld01.trtc.com:5052/subnets
- **Documentation**: http://neamsatcor1ld01.trtc.com:5052/docs/SUBNET_ANALYSIS.md

## Key Features
- **Group by /16 Networks**: Identify which sites share network space
- **Interactive Filtering**: Search by network or site name
- **Site Details**: Click any site to see complete VLAN configuration
- **Export Options**: Download as Excel or CSV
- **Real-time Statistics**: 503 networks, 3,093 VLANs tracked

## Common Uses
1. **IP Space Planning**: Find available subnets for new sites
2. **Conflict Detection**: Check if a subnet is already in use
3. **Standard Verification**: Review network usage patterns
4. **Regional Analysis**: Filter by region for subnet usage

## Data Sources
- Collected from Meraki API via nightly VLAN collection
- Stored in `network_vlans` table
- Excludes 172.x guest networks automatically
- Updates nightly at 1 AM

## Related Pages
- [Inventory Summary](/inventory-summary) - Device tracking
- [Switch Port Visibility](/switch-visibility) - Port-level details
- [System Health](/system-health) - Monitor collection status