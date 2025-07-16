# NEO 07 Firewall Template Documentation

**Generated:** 2025-07-10 07:27:25  
**Source Network:** NEO 07 (L_3790904986339115847)  
**Total Rules:** 55

## VLAN Mapping Applied

| Original VLAN | New VLAN | Purpose |
|--------------|----------|---------|
| 1 | 100 | Data |
| 101 | 200 | Voice |
| 201 | 400 | Credit Card |
| 301 | 410 | Scanner |
| 300 | 300 | AP Mgmt (no change) |
| 800-803 | 800-803 | Guest/IoT (no change) |

## Files Generated

1. **neo07_firewall_template_20250710_original.json** - Original NEO 07 firewall rules
2. **neo07_firewall_template_20250710.json** - Updated rules with new VLAN IDs
3. **neo07_firewall_template_20250710_documentation.md** - This documentation

## Usage

After completing VLAN migration, apply the updated firewall rules:

```bash
# Apply updated firewall rules
curl -X PUT \
  https://api.meraki.com/api/v1/networks/YOUR_NETWORK_ID/appliance/firewall/l3FirewallRules \
  -H 'X-Cisco-Meraki-API-Key: YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d @neo07_firewall_template_20250710.json
```

## Important Notes

- These rules are from NEO 07 and represent the standard store firewall configuration
- Apply these rules AFTER completing VLAN number migration
- The rules maintain all original policies, just with updated VLAN references
