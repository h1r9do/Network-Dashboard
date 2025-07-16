#!/usr/bin/env python3
"""
Fix Starlink detection to use ARIN provider for SpaceX Services, Inc.
"""

print("=== FIXING STARLINK DETECTION FOR SPACEX ARIN ===\n")

# Read the blueprint file
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'r') as f:
    content = f.read()

# Fix first instance of WAN1 Starlink detection
old_wan1_1 = '''                # Check for Starlink in provider name
                if circuit.wan1_provider and 'starlink' in circuit.wan1_provider.lower():
                    wan1_wireless_badge = 'STARLINK' '''

new_wan1_1 = '''                # Check for Starlink in provider name OR ARIN provider
                if circuit.wan1_provider and 'starlink' in circuit.wan1_provider.lower():
                    wan1_wireless_badge = 'STARLINK'
                # Also check ARIN provider for SpaceX Services, Inc.
                if meraki_device and meraki_device.wan1_arin_provider:
                    if 'SPACEX' in meraki_device.wan1_arin_provider.upper() or 'STARLINK' in meraki_device.wan1_arin_provider.upper():
                        wan1_wireless_badge = 'STARLINK' '''

if old_wan1_1 in content:
    content = content.replace(old_wan1_1, new_wan1_1, 1)  # Replace only first occurrence
    print("✅ Fixed first WAN1 Starlink detection")

# Fix first instance of WAN2 Starlink detection
old_wan2_1 = '''                # Check for Starlink in provider name
                if circuit.wan2_provider and 'starlink' in circuit.wan2_provider.lower():
                    wan2_wireless_badge = 'STARLINK' '''

new_wan2_1 = '''                # Check for Starlink in provider name OR ARIN provider
                if circuit.wan2_provider and 'starlink' in circuit.wan2_provider.lower():
                    wan2_wireless_badge = 'STARLINK'
                # Also check ARIN provider for SpaceX Services, Inc.
                if meraki_device and meraki_device.wan2_arin_provider:
                    if 'SPACEX' in meraki_device.wan2_arin_provider.upper() or 'STARLINK' in meraki_device.wan2_arin_provider.upper():
                        wan2_wireless_badge = 'STARLINK' '''

if old_wan2_1 in content:
    content = content.replace(old_wan2_1, new_wan2_1, 1)  # Replace only first occurrence
    print("✅ Fixed first WAN2 Starlink detection")

# Fix second instance of WAN1 Starlink detection (in test route)
old_wan1_2 = '''                # Check for Starlink in provider name
                if circuit.wan1_provider and 'starlink' in circuit.wan1_provider.lower():
                    wan1_wireless_badge = 'STARLINK' '''

new_wan1_2 = '''                # Check for Starlink in provider name OR ARIN provider
                if circuit.wan1_provider and 'starlink' in circuit.wan1_provider.lower():
                    wan1_wireless_badge = 'STARLINK'
                # Also check ARIN provider for SpaceX Services, Inc.
                if meraki_device and meraki_device.wan1_arin_provider:
                    if 'SPACEX' in meraki_device.wan1_arin_provider.upper() or 'STARLINK' in meraki_device.wan1_arin_provider.upper():
                        wan1_wireless_badge = 'STARLINK' '''

if old_wan1_2 in content:
    content = content.replace(old_wan1_2, new_wan1_2)  # Replace remaining occurrences
    print("✅ Fixed second WAN1 Starlink detection")

# Fix second instance of WAN2 Starlink detection (in test route)
old_wan2_2 = '''                # Check for Starlink in provider name
                if circuit.wan2_provider and 'starlink' in circuit.wan2_provider.lower():
                    wan2_wireless_badge = 'STARLINK' '''

new_wan2_2 = '''                # Check for Starlink in provider name OR ARIN provider
                if circuit.wan2_provider and 'starlink' in circuit.wan2_provider.lower():
                    wan2_wireless_badge = 'STARLINK'
                # Also check ARIN provider for SpaceX Services, Inc.
                if meraki_device and meraki_device.wan2_arin_provider:
                    if 'SPACEX' in meraki_device.wan2_arin_provider.upper() or 'STARLINK' in meraki_device.wan2_arin_provider.upper():
                        wan2_wireless_badge = 'STARLINK' '''

if old_wan2_2 in content:
    content = content.replace(old_wan2_2, new_wan2_2)  # Replace remaining occurrences
    print("✅ Fixed second WAN2 Starlink detection")

# Write the updated content
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'w') as f:
    f.write(content)

print("\nStarlink detection now checks both:")
print("1. Provider name contains 'starlink'")
print("2. ARIN provider contains 'SPACEX' or 'STARLINK'")
print("\nThis should capture circuits with SpaceX Services, Inc. as ARIN provider!")