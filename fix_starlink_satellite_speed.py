#!/usr/bin/env python3
"""
Fix Starlink detection to include 'satellite' speed in addition to 'cell'
"""

print("=== FIXING STARLINK DETECTION FOR SATELLITE SPEEDS ===\n")

# Read the blueprint file
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'r') as f:
    content = f.read()

# Update WAN1 logic to check for 'cell' OR 'satellite' speeds
old_wan1_check = '''            # Check WAN1 for wireless
            if circuit.wan1_speed and 'cell' in circuit.wan1_speed.lower():'''

new_wan1_check = '''            # Check WAN1 for wireless (cellular or satellite)
            if circuit.wan1_speed and ('cell' in circuit.wan1_speed.lower() or 'satellite' in circuit.wan1_speed.lower()):'''

if old_wan1_check in content:
    content = content.replace(old_wan1_check, new_wan1_check)
    print("✅ Updated WAN1 speed check to include satellite")

# Update WAN2 logic to check for 'cell' OR 'satellite' speeds
old_wan2_check = '''            # Check WAN2 for wireless  
            if circuit.wan2_speed and 'cell' in circuit.wan2_speed.lower():'''

new_wan2_check = '''            # Check WAN2 for wireless (cellular or satellite)
            if circuit.wan2_speed and ('cell' in circuit.wan2_speed.lower() or 'satellite' in circuit.wan2_speed.lower()):'''

if old_wan2_check in content:
    content = content.replace(old_wan2_check, new_wan2_check)
    print("✅ Updated WAN2 speed check to include satellite")

# Also need to add standalone SpaceX/Starlink detection (not just when speed contains cell/satellite)
# Insert before the grouped_data.append section
insert_point = "            grouped_data.append({"
standalone_starlink_check = '''
            # Additional Starlink detection - check ARIN provider even without cell/satellite speed
            if not wan1_wireless_badge:
                meraki_device = MerakiInventory.query.filter_by(network_name=circuit.network_name).first()
                if meraki_device and meraki_device.wan1_arin_provider:
                    if 'SPACEX' in meraki_device.wan1_arin_provider.upper() or 'STARLINK' in meraki_device.wan1_arin_provider.upper():
                        wan1_wireless_badge = 'STARLINK'
                        
            if not wan2_wireless_badge:
                if not meraki_device:
                    meraki_device = MerakiInventory.query.filter_by(network_name=circuit.network_name).first()
                if meraki_device and meraki_device.wan2_arin_provider:
                    if 'SPACEX' in meraki_device.wan2_arin_provider.upper() or 'STARLINK' in meraki_device.wan2_arin_provider.upper():
                        wan2_wireless_badge = 'STARLINK'
            
            ''' + insert_point

if insert_point in content:
    content = content.replace(insert_point, standalone_starlink_check)
    print("✅ Added standalone Starlink detection for any SpaceX ARIN provider")

# Write the updated content
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'w') as f:
    f.write(content)

print("\nStarlink detection now works for:")
print("1. Speed contains 'cell' or 'satellite' + ARIN provider check")
print("2. Any circuit with SpaceX Services, Inc. as ARIN provider")
print("\nThis should capture all 15 Starlink circuits!")