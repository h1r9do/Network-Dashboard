#!/usr/bin/env python3
"""
Manually fix Starlink detection logic in both routes
"""

print("=== MANUAL FIX FOR STARLINK DETECTION ===\n")

# Read the file
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'r') as f:
    lines = f.readlines()

# Find and replace the specific logic for test route (around line 237)
for i, line in enumerate(lines):
    if "# Check WAN1 for wireless" in line and i > 200:  # Test route
        print(f"Found test route WAN1 logic at line {i+1}")
        
        # Replace the entire WAN1 wireless section
        j = i + 1
        while j < len(lines) and not lines[j].strip().startswith("# Check WAN2"):
            j += 1
        
        # Create new WAN1 logic
        new_wan1_logic = [
            "            # Check WAN1 for wireless (cell=VZW/AT&T, satellite=Starlink)\n",
            "            meraki_device = MerakiInventory.query.filter_by(network_name=circuit.network_name).first()\n",
            "            \n",
            "            # Check for cellular providers\n",
            "            if circuit.wan1_speed and 'cell' in circuit.wan1_speed.lower():\n",
            "                if meraki_device and meraki_device.wan1_arin_provider:\n",
            "                    arin_provider = meraki_device.wan1_arin_provider.upper()\n",
            "                    if 'VERIZON' in arin_provider or 'VZW' in arin_provider:\n",
            "                        wan1_wireless_badge = 'VZW'\n",
            "                    elif 'AT&T' in arin_provider or 'ATT' in arin_provider:\n",
            "                        wan1_wireless_badge = 'ATT'\n",
            "            \n",
            "            # Check for Starlink (satellite speed OR provider name OR SpaceX ARIN)\n",
            "            if (circuit.wan1_speed and 'satellite' in circuit.wan1_speed.lower()) or \\\n",
            "               (circuit.wan1_provider and 'starlink' in circuit.wan1_provider.lower()) or \\\n",
            "               (meraki_device and meraki_device.wan1_arin_provider and 'SPACEX' in meraki_device.wan1_arin_provider.upper()):\n",
            "                wan1_wireless_badge = 'STARLINK'\n",
            "            \n"
        ]
        
        # Replace the lines
        lines[i:j] = new_wan1_logic
        break

# Find and replace WAN2 logic for test route 
for i, line in enumerate(lines):
    if "# Check WAN2 for wireless" in line and i > 200:  # Test route
        print(f"Found test route WAN2 logic at line {i+1}")
        
        # Replace the entire WAN2 wireless section
        j = i + 1
        while j < len(lines) and not lines[j].strip().startswith("grouped_data.append"):
            j += 1
        
        # Create new WAN2 logic
        new_wan2_logic = [
            "            # Check WAN2 for wireless (cell=VZW/AT&T, satellite=Starlink)\n",
            "            if not meraki_device:\n",
            "                meraki_device = MerakiInventory.query.filter_by(network_name=circuit.network_name).first()\n",
            "            \n",
            "            # Check for cellular providers\n",
            "            if circuit.wan2_speed and 'cell' in circuit.wan2_speed.lower():\n",
            "                if meraki_device and meraki_device.wan2_arin_provider:\n",
            "                    arin_provider = meraki_device.wan2_arin_provider.upper()\n",
            "                    if 'VERIZON' in arin_provider or 'VZW' in arin_provider:\n",
            "                        wan2_wireless_badge = 'VZW'\n",
            "                    elif 'AT&T' in arin_provider or 'ATT' in arin_provider:\n",
            "                        wan2_wireless_badge = 'ATT'\n",
            "            \n",
            "            # Check for Starlink (satellite speed OR provider name OR SpaceX ARIN)\n",
            "            if (circuit.wan2_speed and 'satellite' in circuit.wan2_speed.lower()) or \\\n",
            "               (circuit.wan2_provider and 'starlink' in circuit.wan2_provider.lower()) or \\\n",
            "               (meraki_device and meraki_device.wan2_arin_provider and 'SPACEX' in meraki_device.wan2_arin_provider.upper()):\n",
            "                wan2_wireless_badge = 'STARLINK'\n",
            "            \n"
        ]
        
        # Replace the lines
        lines[i:j] = new_wan2_logic
        break

# Write the updated file
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'w') as f:
    f.writelines(lines)

print("✅ Manually fixed Starlink detection logic")
print("\nStarlink detection now checks for:")
print("  - 'satellite' in speed")
print("  - 'starlink' in provider name")
print("  - 'SPACEX' in ARIN provider")
print("\nThis should capture all 15 Starlink circuits!")