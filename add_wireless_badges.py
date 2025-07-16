#!/usr/bin/env python3
"""
Add wireless provider badges to the test page
"""

# Read the blueprint file
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'r') as f:
    content = f.read()

print("=== ADDING WIRELESS BADGES TO TEST PAGE ===\n")

# Find the test route function and add wireless badge logic
old_wan_data = '''            grouped_data.append({
                'network_name': circuit.network_name,
                'device_tags': circuit.device_tags or [],
                'wan1': {
                    'provider': circuit.wan1_provider or '',
                    'speed': circuit.wan1_speed or '',
                    'monthly_cost': wan1_cost,
                    'circuit_role': circuit.wan1_circuit_role or 'Primary',
                    'confirmed': circuit.wan1_confirmed or False,
                    'match_info': wan1_info
                },
                'wan2': {
                    'provider': circuit.wan2_provider or '',
                    'speed': circuit.wan2_speed or '',
                    'monthly_cost': wan2_cost,
                    'circuit_role': circuit.wan2_circuit_role or 'Secondary',
                    'confirmed': circuit.wan2_confirmed or False,
                    'match_info': wan2_info
                }
            })'''

new_wan_data = '''            # Check for wireless badges
            wan1_wireless_badge = None
            wan2_wireless_badge = None
            
            # Check WAN1 for wireless
            if circuit.wan1_speed and 'cell' in circuit.wan1_speed.lower():
                # Get ARIN provider from meraki_inventory
                meraki_device = MerakiInventory.query.filter_by(network_name=circuit.network_name).first()
                if meraki_device and meraki_device.wan1_arin_provider:
                    arin_provider = meraki_device.wan1_arin_provider.upper()
                    if 'VERIZON' in arin_provider or 'VZW' in arin_provider:
                        wan1_wireless_badge = 'VZW'
                    elif 'AT&T' in arin_provider or 'ATT' in arin_provider:
                        wan1_wireless_badge = 'ATT'
                # Check for Starlink in provider name
                if circuit.wan1_provider and 'starlink' in circuit.wan1_provider.lower():
                    wan1_wireless_badge = 'STARLINK'
            
            # Check WAN2 for wireless  
            if circuit.wan2_speed and 'cell' in circuit.wan2_speed.lower():
                # Get ARIN provider from meraki_inventory
                meraki_device = MerakiInventory.query.filter_by(network_name=circuit.network_name).first()
                if meraki_device and meraki_device.wan2_arin_provider:
                    arin_provider = meraki_device.wan2_arin_provider.upper()
                    if 'VERIZON' in arin_provider or 'VZW' in arin_provider:
                        wan2_wireless_badge = 'VZW'
                    elif 'AT&T' in arin_provider or 'ATT' in arin_provider:
                        wan2_wireless_badge = 'ATT'
                # Check for Starlink in provider name
                if circuit.wan2_provider and 'starlink' in circuit.wan2_provider.lower():
                    wan2_wireless_badge = 'STARLINK'
            
            grouped_data.append({
                'network_name': circuit.network_name,
                'device_tags': circuit.device_tags or [],
                'wan1': {
                    'provider': circuit.wan1_provider or '',
                    'speed': circuit.wan1_speed or '',
                    'monthly_cost': wan1_cost,
                    'circuit_role': circuit.wan1_circuit_role or 'Primary',
                    'confirmed': circuit.wan1_confirmed or False,
                    'match_info': wan1_info,
                    'wireless_badge': wan1_wireless_badge
                },
                'wan2': {
                    'provider': circuit.wan2_provider or '',
                    'speed': circuit.wan2_speed or '',
                    'monthly_cost': wan2_cost,
                    'circuit_role': circuit.wan2_circuit_role or 'Secondary',
                    'confirmed': circuit.wan2_confirmed or False,
                    'match_info': wan2_info,
                    'wireless_badge': wan2_wireless_badge
                }
            })'''

if old_wan_data in content:
    content = content.replace(old_wan_data, new_wan_data)
    print("✅ Added wireless badge logic to test route")
else:
    print("❌ Could not find test route data structure")

# Write the updated content
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'w') as f:
    f.write(content)

print("\nNext: Need to update the template to display the badges")
print("The test route now passes wireless_badge data to the template")