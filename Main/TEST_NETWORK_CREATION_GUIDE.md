# Complete Guide: Creating a Test Network from Production Configuration

**Author:** Claude  
**Date:** July 10, 2025  
**Version:** 1.0

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Phase 1: Configuration Extraction](#phase-1-configuration-extraction)
4. [Phase 2: Network Preparation](#phase-2-network-preparation)
5. [Phase 3: Configuration Migration](#phase-3-configuration-migration)
6. [Phase 4: Verification](#phase-4-verification)
7. [Troubleshooting](#troubleshooting)
8. [Scripts Reference](#scripts-reference)

---

## Overview

This guide documents the complete process of creating an exact test network replica from a production Meraki network configuration. The test network will have identical settings except for IP addresses, which are translated to a test range to avoid conflicts.

### Key Principles

1. **Exact Configuration Match**: All settings match production except IP addresses
2. **IP Translation**: Production IPs (10.x.x.x) → Test IPs (10.255.255.x)
3. **Component Order**: Specific order required due to dependencies
4. **Test Environment Adaptations**: DHCP relay → server mode when necessary

### What Gets Migrated

- ✅ VLANs (with exact IDs)
- ✅ Group Policies
- ✅ Policy Objects and Groups
- ✅ Firewall Rules
- ✅ MX Appliance Port Configuration
- ✅ Switch Port Configuration
- ✅ DHCP Settings
- ✅ Syslog Configuration

---

## Prerequisites

### Required Access
- Meraki Dashboard API access
- Organization admin permissions
- Access to both source and target networks

### Environment Setup
```bash
# 1. Set up API key
export MERAKI_API_KEY="your-api-key-here"

# Or use environment file
echo "MERAKI_API_KEY=your-api-key-here" > /usr/local/bin/meraki.env

# 2. Install required Python packages
pip install requests meraki python-dotenv
```

### Network Information Needed
- Source network ID (e.g., L_650207196201635912)
- Target network ID (e.g., L_3790904986339115852)
- Organization IDs for both networks

---

## Phase 1: Configuration Extraction

### Step 1.1: Extract Complete Network Configuration

Create the extraction script:

```python
#!/usr/bin/env python3
"""
extract_network_config.py - Extract complete network configuration
"""
import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv('MERAKI_API_KEY')
BASE_URL = 'https://api.meraki.com/api/v1'
HEADERS = {'X-Cisco-Meraki-API-Key': API_KEY, 'Content-Type': 'application/json'}

def extract_network_config(network_id, network_name):
    """Extract complete network configuration"""
    print(f"Extracting configuration for {network_name}...")
    
    config = {
        'network_id': network_id,
        'network_name': network_name,
        'extraction_time': datetime.now().isoformat(),
        'appliance': {},
        'switch': {},
        'wireless': {}
    }
    
    # Get VLANs
    url = f"{BASE_URL}/networks/{network_id}/appliance/vlans"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        config['appliance']['vlans'] = response.json()
        print(f"  ✓ Extracted {len(config['appliance']['vlans'])} VLANs")
    
    # Get firewall rules
    url = f"{BASE_URL}/networks/{network_id}/appliance/firewall/l3FirewallRules"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        config['appliance']['firewall_rules'] = response.json()
        print(f"  ✓ Extracted {len(config['appliance']['firewall_rules']['rules'])} firewall rules")
    
    # Get group policies
    url = f"{BASE_URL}/networks/{network_id}/groupPolicies"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        config['appliance']['groupPolicies'] = response.json()
        print(f"  ✓ Extracted {len(config['appliance']['groupPolicies'])} group policies")
    
    # Get MX ports
    url = f"{BASE_URL}/networks/{network_id}/appliance/ports"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        config['appliance']['ports'] = response.json()
        print(f"  ✓ Extracted {len(config['appliance']['ports'])} MX ports")
    
    # Get syslog
    url = f"{BASE_URL}/networks/{network_id}/syslogServers"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        config['appliance']['syslog'] = response.json()
        print(f"  ✓ Extracted syslog configuration")
    
    # Save configuration
    filename = f"{network_name.lower().replace(' ', '_')}_config.json"
    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Configuration saved to {filename}")
    return config

# Extract source network
source_config = extract_network_config('L_650207196201635912', 'AZP 30')
```

### Step 1.2: Extract Switch Configuration

```python
#!/usr/bin/env python3
"""
extract_switch_config.py - Extract switch port configurations
"""

def extract_switch_config(network_id):
    """Extract switch configuration"""
    # Get switches in network
    url = f"{BASE_URL}/networks/{network_id}/devices"
    response = requests.get(url, headers=HEADERS)
    devices = response.json()
    
    switches = [d for d in devices if d['model'].startswith('MS')]
    print(f"Found {len(switches)} switches")
    
    config = {'switches': {}}
    
    for switch in switches:
        serial = switch['serial']
        print(f"\nExtracting ports for {switch['name']}...")
        
        # Get port configuration
        url = f"{BASE_URL}/devices/{serial}/switch/ports"
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code == 200:
            ports = response.json()
            config['switches'][serial] = {
                'device_info': switch,
                'ports': ports
            }
            print(f"  ✓ Extracted {len(ports)} ports")
    
    return config
```

### Step 1.3: Identify Policy Objects

Extract policy objects and groups referenced in firewall rules:

```python
def extract_policy_objects(org_id, firewall_rules):
    """Extract policy objects and groups"""
    import re
    
    # Find all object and group references
    object_refs = set()
    group_refs = set()
    
    for rule in firewall_rules:
        src = rule.get('srcCidr', '')
        dst = rule.get('destCidr', '')
        
        # Extract OBJ() and GRP() references
        obj_pattern = r'OBJ\((\d+)\)'
        grp_pattern = r'GRP\((\d+)\)'
        
        object_refs.update(re.findall(obj_pattern, src))
        object_refs.update(re.findall(obj_pattern, dst))
        group_refs.update(re.findall(grp_pattern, src))
        group_refs.update(re.findall(grp_pattern, dst))
    
    print(f"Found {len(object_refs)} object references, {len(group_refs)} group references")
    
    # Get actual objects and groups
    url = f"{BASE_URL}/organizations/{org_id}/policyObjects"
    objects = requests.get(url, headers=HEADERS).json()
    
    url = f"{BASE_URL}/organizations/{org_id}/policyObjects/groups"
    groups = requests.get(url, headers=HEADERS).json()
    
    return {
        'objects': [o for o in objects if str(o['id']) in object_refs],
        'groups': [g for g in groups if str(g['id']) in group_refs]
    }
```

---

## Phase 2: Network Preparation

### Step 2.1: Clean Target Network

Before applying configuration, clean the target network:

```python
#!/usr/bin/env python3
"""
clean_network.py - Clean target network before migration
"""

def clean_network(network_id):
    """Clean network to prepare for migration"""
    print(f"Cleaning network {network_id}...")
    
    # 1. Clear firewall rules (set to default allow)
    url = f"{BASE_URL}/networks/{network_id}/appliance/firewall/l3FirewallRules"
    data = {'rules': []}
    requests.put(url, headers=HEADERS, json=data)
    print("  ✓ Cleared firewall rules")
    
    # 2. Clear syslog
    url = f"{BASE_URL}/networks/{network_id}/syslogServers"
    data = {'servers': []}
    requests.put(url, headers=HEADERS, json=data)
    print("  ✓ Cleared syslog configuration")
    
    # 3. Delete VLANs (except default)
    url = f"{BASE_URL}/networks/{network_id}/appliance/vlans"
    vlans = requests.get(url, headers=HEADERS).json()
    
    for vlan in vlans:
        if vlan['id'] != 1:  # Keep VLAN 1
            url = f"{BASE_URL}/networks/{network_id}/appliance/vlans/{vlan['id']}"
            requests.delete(url, headers=HEADERS)
            print(f"  ✓ Deleted VLAN {vlan['id']}")
            time.sleep(1)
    
    # 4. Delete group policies
    url = f"{BASE_URL}/networks/{network_id}/groupPolicies"
    policies = requests.get(url, headers=HEADERS).json()
    
    for policy in policies:
        url = f"{BASE_URL}/networks/{network_id}/groupPolicies/{policy['groupPolicyId']}"
        requests.delete(url, headers=HEADERS)
        print(f"  ✓ Deleted group policy {policy['name']}")
    
    print("\n✅ Network cleaned and ready for configuration")
```

### Step 2.2: Create IP Translation Function

```python
def translate_ip_to_test(ip_address):
    """Translate production IP to test range"""
    # Convert 10.x.x.x to 10.255.255.x
    if ip_address.startswith('10.') and not ip_address.startswith('10.255.255.'):
        parts = ip_address.split('.')
        if len(parts) >= 4:
            # Keep last octet, change first three
            subnet_parts = ip_address.split('/')
            ip_parts = subnet_parts[0].split('.')
            new_ip = f"10.255.255.{ip_parts[3]}"
            
            # Preserve subnet mask if present
            if len(subnet_parts) > 1:
                return f"{new_ip}/{subnet_parts[1]}"
            return new_ip
    
    # Leave other IPs unchanged (172.x for IoT/Guest)
    return ip_address
```

---

## Phase 3: Configuration Migration

### Step 3.1: Migration Order (CRITICAL!)

The order of operations is critical due to dependencies:

1. **Policy Objects and Groups** (firewall rules reference these)
2. **Group Policies** (VLANs reference these)
3. **VLANs** (everything else depends on these)
4. **Syslog Configuration**
5. **Firewall Rules** (requires objects, groups, and VLANs)
6. **MX Ports** (requires VLANs)
7. **Switch Ports** (requires VLANs)
8. **DHCP Configuration** (update existing VLANs)

### Step 3.2: Apply Configuration Script

```python
#!/usr/bin/env python3
"""
apply_test_config.py - Apply configuration to test network
"""

class TestNetworkMigrator:
    def __init__(self, target_network_id):
        self.network_id = target_network_id
        self.object_mapping = {}  # Old ID -> New ID
        self.group_mapping = {}
        self.policy_mapping = {}
    
    def migrate_policy_objects(self, source_objects, target_org_id):
        """Step 1: Migrate policy objects"""
        print("\nMigrating policy objects...")
        
        for obj in source_objects:
            # Create object in target org
            data = {
                'name': obj['name'],
                'category': obj['category'],
                'type': obj['type'],
                'cidr': obj.get('cidr'),
                'fqdn': obj.get('fqdn')
            }
            
            url = f"{BASE_URL}/organizations/{target_org_id}/policyObjects"
            response = requests.post(url, headers=HEADERS, json=data)
            
            if response.status_code == 201:
                new_obj = response.json()
                self.object_mapping[str(obj['id'])] = str(new_obj['id'])
                print(f"  ✓ Created object: {obj['name']}")
    
    def migrate_group_policies(self, policies):
        """Step 2: Migrate group policies"""
        print("\nMigrating group policies...")
        
        for policy in policies:
            data = policy.copy()
            data.pop('groupPolicyId', None)
            data.pop('networkId', None)
            
            url = f"{BASE_URL}/networks/{self.network_id}/groupPolicies"
            response = requests.post(url, headers=HEADERS, json=data)
            
            if response.status_code == 201:
                new_policy = response.json()
                self.policy_mapping[policy['groupPolicyId']] = new_policy['groupPolicyId']
                print(f"  ✓ Created policy: {policy['name']}")
    
    def migrate_vlans(self, vlans):
        """Step 3: Migrate VLANs with IP translation"""
        print("\nMigrating VLANs...")
        
        # Delete default VLAN 100 if we need VLAN 1
        if any(v['id'] == 1 for v in vlans):
            url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans/100"
            requests.delete(url, headers=HEADERS)
            time.sleep(1)
        
        for vlan in sorted(vlans, key=lambda v: v['id']):
            data = vlan.copy()
            
            # Translate IPs
            if data.get('subnet'):
                data['subnet'] = translate_ip_to_test(data['subnet'])
            if data.get('applianceIp'):
                data['applianceIp'] = translate_ip_to_test(data['applianceIp'])
            
            # Handle DHCP relay -> server conversion
            if data.get('dhcpRelayServerIps'):
                print(f"    Converting VLAN {vlan['id']} from relay to server mode")
                data['dhcpHandling'] = 'Run a DHCP server'
                data['dhcpLeaseTime'] = '12 hours'
                data.pop('dhcpRelayServerIps', None)
            
            # Update group policy ID
            if 'groupPolicyId' in data:
                old_id = str(data['groupPolicyId'])
                if old_id in self.policy_mapping:
                    data['groupPolicyId'] = self.policy_mapping[old_id]
            
            # Clean fields
            for field in ['networkId', 'interfaceId']:
                data.pop(field, None)
            
            # Create VLAN
            url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans"
            response = requests.post(url, headers=HEADERS, json=data)
            
            if response.status_code == 201:
                print(f"  ✓ Created VLAN {vlan['id']} - {vlan.get('name')}")
            
            time.sleep(1)
    
    def apply_firewall_rules(self, rules):
        """Step 5: Apply firewall rules with mapping"""
        print("\nApplying firewall rules...")
        
        updated_rules = []
        for rule in rules:
            new_rule = rule.copy()
            
            # Update object/group references
            src = rule.get('srcCidr', '')
            dst = rule.get('destCidr', '')
            
            # Replace object IDs
            for old_id, new_id in self.object_mapping.items():
                src = src.replace(f'OBJ({old_id})', f'OBJ({new_id})')
                dst = dst.replace(f'OBJ({old_id})', f'OBJ({new_id})')
            
            # Replace group IDs
            for old_id, new_id in self.group_mapping.items():
                src = src.replace(f'GRP({old_id})', f'GRP({new_id})')
                dst = dst.replace(f'GRP({old_id})', f'GRP({new_id})')
            
            new_rule['srcCidr'] = src
            new_rule['destCidr'] = dst
            updated_rules.append(new_rule)
        
        # Apply all rules
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/firewall/l3FirewallRules"
        data = {'rules': updated_rules}
        response = requests.put(url, headers=HEADERS, json=data)
        
        if response.status_code == 200:
            print(f"  ✓ Applied {len(updated_rules)} firewall rules")
```

### Step 3.3: Configure MX Ports

```python
def configure_mx_ports(network_id, ports):
    """Configure MX appliance ports"""
    print("\nConfiguring MX ports...")
    
    for port in ports:
        if port['number'] in [1, 2]:  # Skip WAN ports
            continue
        
        port_num = port['number']
        
        # Build configuration
        data = {
            'enabled': port.get('enabled', True),
            'type': port.get('type', 'access'),
            'dropUntaggedTraffic': port.get('dropUntaggedTraffic', False)
        }
        
        if data['type'] == 'access':
            data['vlan'] = port.get('vlan', 1)
        elif data['type'] == 'trunk':
            # For trunk, 'vlan' field is native VLAN
            data['vlan'] = port.get('vlan', 1)
            data['allowedVlans'] = port.get('allowedVlans', 'all')
        
        url = f"{BASE_URL}/networks/{network_id}/appliance/ports/{port_num}"
        response = requests.put(url, headers=HEADERS, json=data)
        
        if response.status_code == 200:
            print(f"  ✓ Configured port {port_num}")
```

### Step 3.4: Configure Switch Ports

```python
def configure_switch_ports(network_id, switch_configs):
    """Configure switch ports"""
    print("\nConfiguring switch ports...")
    
    # Get target switches
    url = f"{BASE_URL}/networks/{network_id}/devices"
    devices = requests.get(url, headers=HEADERS).json()
    target_switches = [d for d in devices if d['model'].startswith('MS')]
    
    # Map source to target switches by order
    source_switches = sorted(switch_configs.items(), key=lambda x: x[1]['device_info']['name'])
    
    for i, (source_serial, source_data) in enumerate(source_switches):
        if i < len(target_switches):
            target_switch = target_switches[i]
            print(f"\nConfiguring {target_switch['name']}...")
            
            for port in source_data['ports']:
                port_id = port['portId']
                
                # Build configuration
                data = {
                    'name': port.get('name', ''),
                    'tags': port.get('tags', []),
                    'enabled': port.get('enabled', True),
                    'type': port.get('type', 'access'),
                    'vlan': port.get('vlan', 1),
                    'voiceVlan': port.get('voiceVlan'),
                    'allowedVlans': port.get('allowedVlans', 'all'),
                    'poeEnabled': port.get('poeEnabled', True)
                }
                
                # Remove None values
                data = {k: v for k, v in data.items() if v is not None}
                
                url = f"{BASE_URL}/devices/{target_switch['serial']}/switch/ports/{port_id}"
                response = requests.put(url, headers=HEADERS, json=data)
                
                if response.status_code == 200:
                    print(f"  ✓ Port {port_id}: {port.get('name', 'Unnamed')}")
```

### Step 3.5: Configure DHCP Settings

```python
def configure_dhcp_settings(network_id):
    """Configure DHCP settings for test environment"""
    print("\nConfiguring DHCP settings...")
    
    # Test network DNS servers
    test_dns = '10.255.255.5\\n10.255.255.6'
    
    dhcp_configs = {
        # VLAN 101 - Voice (VoIP options)
        101: {
            'dnsNameservers': test_dns,
            'dhcpOptions': [
                {'code': '42', 'type': 'ip', 'value': '10.255.255.30'},  # NTP
                {'code': '66', 'type': 'text', 'value': '10.255.255.35'}  # TFTP
            ]
        },
        # VLAN 300 - AP Mgmt (Fixed IPs)
        300: {
            'dnsNameservers': test_dns,
            'fixedIpAssignments': {
                '00:18:0a:80:8b:6a': {'ip': '10.255.255.180', 'name': 'AP1'},
                '00:18:0a:80:91:46': {'ip': '10.255.255.181', 'name': 'AP2'},
                # ... more assignments
            }
        }
    }
    
    for vlan_id, config in dhcp_configs.items():
        url = f"{BASE_URL}/networks/{network_id}/appliance/vlans/{vlan_id}"
        response = requests.put(url, headers=HEADERS, json=config)
        
        if response.status_code == 200:
            print(f"  ✓ Updated DHCP for VLAN {vlan_id}")
```

---

## Phase 4: Verification

### Step 4.1: Verification Script

```python
#!/usr/bin/env python3
"""
verify_test_network.py - Verify test network configuration
"""

def verify_network_config(network_id):
    """Verify all components are configured correctly"""
    print("Verifying network configuration...")
    
    results = {
        'vlans': {'expected': 10, 'actual': 0},
        'policies': {'expected': 3, 'actual': 0},
        'firewall_rules': {'expected': 59, 'actual': 0},
        'mx_ports': {'expected': 10, 'actual': 0},
        'switches': {'expected': 2, 'actual': 0}
    }
    
    # Check VLANs
    url = f"{BASE_URL}/networks/{network_id}/appliance/vlans"
    vlans = requests.get(url, headers=HEADERS).json()
    results['vlans']['actual'] = len(vlans)
    
    # Check group policies
    url = f"{BASE_URL}/networks/{network_id}/groupPolicies"
    policies = requests.get(url, headers=HEADERS).json()
    results['policies']['actual'] = len(policies)
    
    # Check firewall rules
    url = f"{BASE_URL}/networks/{network_id}/appliance/firewall/l3FirewallRules"
    rules = requests.get(url, headers=HEADERS).json()
    results['firewall_rules']['actual'] = len(rules.get('rules', []))
    
    # Display results
    print("\nVerification Results:")
    print("=" * 50)
    
    all_good = True
    for component, counts in results.items():
        status = "✅" if counts['expected'] == counts['actual'] else "❌"
        print(f"{status} {component}: {counts['actual']}/{counts['expected']}")
        if counts['expected'] != counts['actual']:
            all_good = False
    
    return all_good
```

### Step 4.2: Detailed Verification Checklist

```markdown
## Manual Verification Checklist

### VLANs
- [ ] All 10 VLANs created with correct IDs
- [ ] IP addresses in test range (10.255.255.x)
- [ ] DHCP mode correct (server vs relay)
- [ ] Group policy assignments correct

### Firewall Rules
- [ ] All 59 rules present
- [ ] Object/group references updated
- [ ] Rule order preserved
- [ ] Syslog settings preserved

### MX Ports
- [ ] Ports 3-12 configured
- [ ] Trunk ports have correct allowed VLANs
- [ ] Native VLANs set correctly
- [ ] Disabled ports are disabled

### Switch Ports
- [ ] All 56 ports configured
- [ ] VLAN assignments correct
- [ ] Voice VLAN 101 on appropriate ports
- [ ] Trunk ports configured correctly

### DHCP Settings
- [ ] VoIP options on VLAN 101
- [ ] Fixed IP assignments on VLAN 300
- [ ] DNS servers updated to test range
- [ ] Lease times appropriate
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. "DHCP relay IP must be in subnet" Error
**Cause:** Production DHCP relay servers not reachable from test network  
**Solution:** Convert to DHCP server mode instead of relay

#### 2. "Policy object not found" Error
**Cause:** Firewall rules reference objects not in target organization  
**Solution:** Create policy objects in target org before applying firewall rules

#### 3. "VLAN already exists" Error
**Cause:** Trying to create VLAN that already exists  
**Solution:** Clean network first or update existing VLAN instead

#### 4. "Native VLAN required" Error
**Cause:** Trunk ports require native VLAN specification  
**Solution:** Set 'vlan' field (not 'nativeVlan') for trunk ports

#### 5. "Sticky MAC list" Error
**Cause:** Port security settings incompatible  
**Solution:** Only apply sticky MAC settings when accessPolicyType matches

### API Rate Limiting

Add delays between operations to avoid rate limits:
```python
time.sleep(0.5)  # Between port configurations
time.sleep(1.0)  # Between VLAN operations
```

---

## Scripts Reference

### Complete Script Package

All scripts needed for test network creation:

1. **extract_complete_config.py** - Extract source configuration
2. **clean_target_network.py** - Prepare target network
3. **apply_exact_config.py** - Main migration script
4. **apply_mx_ports_complete.py** - MX port configuration
5. **apply_dhcp_config_test.py** - DHCP configuration
6. **apply_switch_ports_to_tst01.py** - Switch port configuration
7. **verify_test_network.py** - Verification script

### Execution Order

```bash
# 1. Extract configuration
python3 extract_complete_config.py --network-id L_650207196201635912 --name "AZP 30"

# 2. Clean target network
python3 clean_target_network.py --network-id L_3790904986339115852

# 3. Apply main configuration
python3 apply_exact_config.py \
  --network-id L_3790904986339115852 \
  --source-config azp_30_config.json \
  --firewall-template azp_30_firewall_rules.json

# 4. Configure MX ports
python3 apply_mx_ports_complete.py

# 5. Configure switch ports
python3 apply_switch_ports_to_tst01.py

# 6. Configure DHCP
python3 apply_dhcp_config_test.py

# 7. Verify
python3 verify_test_network.py --network-id L_3790904986339115852
```

---

## Summary

Creating a test network from production configuration requires:

1. **Systematic extraction** of all configuration components
2. **Careful preparation** of the target network
3. **Ordered application** of configuration (dependencies matter!)
4. **IP translation** to avoid conflicts
5. **Test environment adaptations** (DHCP relay → server)
6. **Thorough verification** of all components

Total time: Approximately 15-20 minutes for complete migration

The result is an exact replica of production suitable for testing migrations, changes, and procedures without affecting production systems.

---

**Document Version:** 1.0  
**Last Updated:** July 10, 2025  
**Tested With:** Meraki Dashboard API v1