#!/usr/bin/env python3
"""
Fix Starlink detection and provider filter issues
"""

print("=== FIXING STARLINK DETECTION AND PROVIDER FILTERS ===\n")

# Read the blueprint file
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'r') as f:
    content = f.read()

# Fix Starlink detection in WAN1 logic
old_wan1_starlink = '''                # Check for Starlink in provider name
                if circuit.wan1_provider and 'starlink' in circuit.wan1_provider.lower():
                    wan1_wireless_badge = 'STARLINK' '''

new_wan1_starlink = '''                # Check for Starlink in provider name OR ARIN provider
                if circuit.wan1_provider and 'starlink' in circuit.wan1_provider.lower():
                    wan1_wireless_badge = 'STARLINK'
                # Also check ARIN provider for SpaceX Services, Inc.
                if meraki_device and meraki_device.wan1_arin_provider:
                    if 'SPACEX' in meraki_device.wan1_arin_provider.upper() or 'STARLINK' in meraki_device.wan1_arin_provider.upper():
                        wan1_wireless_badge = 'STARLINK' '''

if old_wan1_starlink in content:
    content = content.replace(old_wan1_starlink, new_wan1_starlink)
    print("✅ Fixed WAN1 Starlink detection")
else:
    print("❌ Could not find WAN1 Starlink logic")

# Fix Starlink detection in WAN2 logic
old_wan2_starlink = '''                # Check for Starlink in provider name
                if circuit.wan2_provider and 'starlink' in circuit.wan2_provider.lower():
                    wan2_wireless_badge = 'STARLINK' '''

new_wan2_starlink = '''                # Check for Starlink in provider name OR ARIN provider
                if circuit.wan2_provider and 'starlink' in circuit.wan2_provider.lower():
                    wan2_wireless_badge = 'STARLINK'
                # Also check ARIN provider for SpaceX Services, Inc.
                if meraki_device and meraki_device.wan2_arin_provider:
                    if 'SPACEX' in meraki_device.wan2_arin_provider.upper() or 'STARLINK' in meraki_device.wan2_arin_provider.upper():
                        wan2_wireless_badge = 'STARLINK' '''

if old_wan2_starlink in content:
    content = content.replace(old_wan2_starlink, new_wan2_starlink)
    print("✅ Fixed WAN2 Starlink detection")
else:
    print("❌ Could not find WAN2 Starlink logic")

# Write the updated content
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'w') as f:
    f.write(content)

print("\nNow checking template filter issues...")

# Check the template for provider filter issues
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    template_content = f.read()

# Look for the provider filter sections
import re
provider_filter_matches = re.findall(r'WAN\d Provider.*?</select>', template_content, re.DOTALL)

if provider_filter_matches:
    print(f"Found {len(provider_filter_matches)} provider filter sections")
    for i, match in enumerate(provider_filter_matches):
        print(f"\nProvider Filter {i+1}:")
        # Show first 200 chars
        print(match[:200] + "..." if len(match) > 200 else match)
else:
    print("❌ Could not find provider filter sections")

print("\nStarlink detection updated to check ARIN provider for 'SpaceX Services, Inc.'!")
print("Please check the provider filters in the web interface and let me know what weird text you're seeing.")