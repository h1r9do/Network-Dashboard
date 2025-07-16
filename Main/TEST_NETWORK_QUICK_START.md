# Quick Start: Test Network Creation from Production

**Time Required:** ~15 minutes  
**Skill Level:** Intermediate

## Prerequisites Checklist

- [ ] Meraki API key with organization admin access
- [ ] Source network ID (production)
- [ ] Target network ID (test network)
- [ ] Python 3.x with requests library
- [ ] Network already created in Meraki dashboard

## Step-by-Step Commands

### 1. Setup Environment (One Time)

```bash
# Create working directory
mkdir -p /usr/local/bin/Main
cd /usr/local/bin/Main

# Set up API key
echo "MERAKI_API_KEY=your-api-key-here" > /usr/local/bin/meraki.env

# Install dependencies
pip install requests python-dotenv meraki
```

### 2. Download Migration Scripts

Save these scripts to your working directory:

```bash
# Main migration script
wget https://raw.githubusercontent.com/your-repo/apply_exact_config.py
wget https://raw.githubusercontent.com/your-repo/apply_mx_ports_complete.py
wget https://raw.githubusercontent.com/your-repo/apply_switch_ports_to_tst01.py
wget https://raw.githubusercontent.com/your-repo/apply_dhcp_config_test.py

# Or create them from the documentation
```

### 3. Extract Source Configuration

```bash
# Extract complete configuration including firewall rules
python3 -c "
import os, json, requests
from dotenv import load_dotenv

load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv('MERAKI_API_KEY')
BASE_URL = 'https://api.meraki.com/api/v1'
HEADERS = {'X-Cisco-Meraki-API-Key': API_KEY}

# Set your source network ID here
SOURCE_NETWORK = 'L_650207196201635912'  # Example: AZP 30

print('Extracting configuration...')

# Get VLANs
url = f'{BASE_URL}/networks/{SOURCE_NETWORK}/appliance/vlans'
vlans = requests.get(url, headers=HEADERS).json()

# Get firewall rules
url = f'{BASE_URL}/networks/{SOURCE_NETWORK}/appliance/firewall/l3FirewallRules'
firewall = requests.get(url, headers=HEADERS).json()

# Get group policies
url = f'{BASE_URL}/networks/{SOURCE_NETWORK}/groupPolicies'
policies = requests.get(url, headers=HEADERS).json()

# Get MX ports
url = f'{BASE_URL}/networks/{SOURCE_NETWORK}/appliance/ports'
ports = requests.get(url, headers=HEADERS).json()

# Save configuration
config = {
    'network_id': SOURCE_NETWORK,
    'appliance': {
        'vlans': vlans,
        'groupPolicies': policies,
        'ports': ports
    }
}

with open('source_config.json', 'w') as f:
    json.dump(config, f, indent=2)

with open('source_firewall.json', 'w') as f:
    json.dump(firewall, f, indent=2)

print(f'✓ Extracted {len(vlans)} VLANs')
print(f'✓ Extracted {len(firewall[\"rules\"])} firewall rules')
print(f'✓ Extracted {len(policies)} group policies')
print('✓ Configuration saved to source_config.json and source_firewall.json')
"
```

### 4. Clean Target Network

```bash
# Set your target network ID
export TARGET_NETWORK='L_3790904986339115852'  # Your test network

# Clean the target network
python3 -c "
import os, requests, time
from dotenv import load_dotenv

load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv('MERAKI_API_KEY')
BASE_URL = 'https://api.meraki.com/api/v1'
HEADERS = {'X-Cisco-Meraki-API-Key': API_KEY, 'Content-Type': 'application/json'}

network_id = os.getenv('TARGET_NETWORK')
print(f'Cleaning network {network_id}...')

# Clear firewall rules
url = f'{BASE_URL}/networks/{network_id}/appliance/firewall/l3FirewallRules'
requests.put(url, headers=HEADERS, json={'rules': []})
print('✓ Cleared firewall rules')

# Clear syslog
url = f'{BASE_URL}/networks/{network_id}/syslogServers'
requests.put(url, headers=HEADERS, json={'servers': []})
print('✓ Cleared syslog')

# Delete non-default VLANs
url = f'{BASE_URL}/networks/{network_id}/appliance/vlans'
vlans = requests.get(url, headers=HEADERS).json()

for vlan in vlans:
    if vlan['id'] not in [1, 100]:  # Keep default VLANs
        url = f'{BASE_URL}/networks/{network_id}/appliance/vlans/{vlan[\"id\"]}'
        requests.delete(url, headers=HEADERS)
        print(f'✓ Deleted VLAN {vlan[\"id\"]}')
        time.sleep(1)

print('✓ Network cleaned')
"
```

### 5. Apply Configuration (Main Script)

```bash
# Run the main migration
python3 apply_exact_config.py \
  --network-id $TARGET_NETWORK \
  --source-config source_config.json \
  --firewall-template source_firewall.json
```

### 6. Configure MX Ports

```bash
python3 apply_mx_ports_complete.py
```

### 7. Configure Switch Ports

```bash
# First extract switch config from source
python3 -c "
import os, json, requests
from dotenv import load_dotenv

load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv('MERAKI_API_KEY')
BASE_URL = 'https://api.meraki.com/api/v1'
HEADERS = {'X-Cisco-Meraki-API-Key': API_KEY}

SOURCE_NETWORK = 'L_650207196201635912'

# Get switches
url = f'{BASE_URL}/networks/{SOURCE_NETWORK}/devices'
devices = requests.get(url, headers=HEADERS).json()
switches = [d for d in devices if d['model'].startswith('MS')]

config = {'switches': {}}
for switch in switches:
    url = f'{BASE_URL}/devices/{switch[\"serial\"]}/switch/ports'
    ports = requests.get(url, headers=HEADERS).json()
    config['switches'][switch['serial']] = {
        'device_info': switch,
        'ports': ports
    }

with open('azp_30_switch_config_original_20250710_065006.json', 'w') as f:
    json.dump(config, f, indent=2)

print(f'✓ Extracted config for {len(switches)} switches')
"

# Apply switch configuration
python3 apply_switch_ports_to_tst01.py
```

### 8. Configure DHCP Settings

```bash
python3 apply_dhcp_config_test.py
```

### 9. Verify Configuration

```bash
python3 -c "
import os, requests
from dotenv import load_dotenv

load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv('MERAKI_API_KEY')
BASE_URL = 'https://api.meraki.com/api/v1'
HEADERS = {'X-Cisco-Meraki-API-Key': API_KEY}

network_id = os.getenv('TARGET_NETWORK')
print(f'Verifying network {network_id}...\n')

# Check VLANs
url = f'{BASE_URL}/networks/{network_id}/appliance/vlans'
vlans = requests.get(url, headers=HEADERS).json()
print(f'✓ VLANs: {len(vlans)} configured')

# Check firewall rules
url = f'{BASE_URL}/networks/{network_id}/appliance/firewall/l3FirewallRules'
rules = requests.get(url, headers=HEADERS).json()
print(f'✓ Firewall rules: {len(rules[\"rules\"])} configured')

# Check group policies
url = f'{BASE_URL}/networks/{network_id}/groupPolicies'
policies = requests.get(url, headers=HEADERS).json()
print(f'✓ Group policies: {len(policies)} configured')

# Check switches
url = f'{BASE_URL}/networks/{network_id}/devices'
devices = requests.get(url, headers=HEADERS).json()
switches = [d for d in devices if d['model'].startswith('MS')]
print(f'✓ Switches: {len(switches)} configured')

print('\n✅ Test network configuration complete!')
"
```

## Complete One-Line Setup

For experienced users, here's the complete process in one script:

```bash
#!/bin/bash
# complete_test_network_setup.sh

# Configuration
export SOURCE_NETWORK='L_650207196201635912'  # Your source network
export TARGET_NETWORK='L_3790904986339115852'  # Your test network

echo "🚀 Starting test network creation..."
echo "Source: $SOURCE_NETWORK"
echo "Target: $TARGET_NETWORK"

# Extract configuration
echo -e "\n📥 Extracting source configuration..."
python3 extract_complete_config.py --network-id $SOURCE_NETWORK

# Clean target
echo -e "\n🧹 Cleaning target network..."
python3 clean_target_network.py --network-id $TARGET_NETWORK

# Apply configuration
echo -e "\n📤 Applying configuration..."
python3 apply_exact_config.py \
  --network-id $TARGET_NETWORK \
  --source-config source_config.json \
  --firewall-template source_firewall.json

# Configure ports
echo -e "\n🔧 Configuring MX ports..."
python3 apply_mx_ports_complete.py

echo -e "\n🔧 Configuring switch ports..."
python3 apply_switch_ports_to_tst01.py

echo -e "\n🔧 Configuring DHCP..."
python3 apply_dhcp_config_test.py

# Verify
echo -e "\n✅ Verifying configuration..."
python3 verify_test_network.py --network-id $TARGET_NETWORK

echo -e "\n🎉 Test network creation complete!"
```

## Important Notes

1. **IP Translation**: All 10.x.x.x addresses are automatically translated to 10.255.255.x
2. **DHCP Relay**: Converted to DHCP server mode in test environment
3. **Order Matters**: Scripts must run in the specified order due to dependencies
4. **Rate Limiting**: Scripts include delays to avoid API rate limits
5. **Verification**: Always verify the configuration after completion

## Troubleshooting Quick Fixes

```bash
# If VLANs fail to create
# Delete VLAN 100 first if creating VLAN 1
curl -X DELETE \
  "https://api.meraki.com/api/v1/networks/$TARGET_NETWORK/appliance/vlans/100" \
  -H "X-Cisco-Meraki-API-Key: $MERAKI_API_KEY"

# If firewall rules fail
# Check that all policy objects exist in target org

# If switch ports fail
# Ensure all referenced VLANs exist first

# If DHCP fails
# Check that DNS servers are in correct format: "10.255.255.5\n10.255.255.6"
```

## Expected Results

After successful completion:
- ✅ 10 VLANs with exact IDs from source
- ✅ 59 firewall rules (example)
- ✅ 3 group policies
- ✅ 10 MX ports configured
- ✅ 56 switch ports configured (28 per switch)
- ✅ DHCP settings with VoIP options
- ✅ All IPs in test range (10.255.255.x)

**Total Time:** ~15 minutes

---

**Quick Start Version:** 1.0  
**Last Updated:** July 10, 2025