#!/usr/bin/env python3
"""
Fix Starlink detection for satellite speed and duplicate provider dropdown
"""

print("=== FIXING STARLINK SATELLITE + DROPDOWN DUPLICATES ===\n")

# 1. Fix Starlink detection to look for 'satellite' speed instead of 'cell'
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'r') as f:
    content = f.read()

# Update WAN1 Starlink detection - look for satellite speed + SpaceX ARIN
old_wan1_logic = '''            # Check WAN1 for wireless
            if circuit.wan1_speed and 'cell' in circuit.wan1_speed.lower():
                # Get ARIN provider from meraki_inventory
                meraki_device = MerakiInventory.query.filter_by(network_name=circuit.network_name).first()
                if meraki_device and meraki_device.wan1_arin_provider:
                    arin_provider = meraki_device.wan1_arin_provider.upper()
                    if 'VERIZON' in arin_provider or 'VZW' in arin_provider:
                        wan1_wireless_badge = 'VZW'
                    elif 'AT&T' in arin_provider or 'ATT' in arin_provider:
                        wan1_wireless_badge = 'ATT'
                # Check for Starlink in provider name OR ARIN provider
                if circuit.wan1_provider and 'starlink' in circuit.wan1_provider.lower():
                    wan1_wireless_badge = 'STARLINK'
                # Also check ARIN provider for SpaceX Services, Inc.
                if meraki_device and meraki_device.wan1_arin_provider:
                    if 'SPACEX' in meraki_device.wan1_arin_provider.upper() or 'STARLINK' in meraki_device.wan1_arin_provider.upper():
                        wan1_wireless_badge = 'STARLINK' '''

new_wan1_logic = '''            # Check WAN1 for wireless (cell = VZW/AT&T, satellite = Starlink)
            meraki_device = MerakiInventory.query.filter_by(network_name=circuit.network_name).first()
            
            # Check for cellular (VZW/AT&T)
            if circuit.wan1_speed and 'cell' in circuit.wan1_speed.lower():
                if meraki_device and meraki_device.wan1_arin_provider:
                    arin_provider = meraki_device.wan1_arin_provider.upper()
                    if 'VERIZON' in arin_provider or 'VZW' in arin_provider:
                        wan1_wireless_badge = 'VZW'
                    elif 'AT&T' in arin_provider or 'ATT' in arin_provider:
                        wan1_wireless_badge = 'ATT'
            
            # Check for Starlink (satellite speed OR SpaceX ARIN provider)
            if (circuit.wan1_speed and 'satellite' in circuit.wan1_speed.lower()) or \
               (circuit.wan1_provider and 'starlink' in circuit.wan1_provider.lower()) or \
               (meraki_device and meraki_device.wan1_arin_provider and 'SPACEX' in meraki_device.wan1_arin_provider.upper()):
                wan1_wireless_badge = 'STARLINK' '''

if old_wan1_logic in content:
    content = content.replace(old_wan1_logic, new_wan1_logic)
    print("✅ Fixed WAN1 Starlink detection for satellite speed")

# Update WAN2 Starlink detection
old_wan2_logic = '''            # Check WAN2 for wireless  
            if circuit.wan2_speed and 'cell' in circuit.wan2_speed.lower():
                # Get ARIN provider from meraki_inventory
                meraki_device = MerakiInventory.query.filter_by(network_name=circuit.network_name).first()
                if meraki_device and meraki_device.wan2_arin_provider:
                    arin_provider = meraki_device.wan2_arin_provider.upper()
                    if 'VERIZON' in arin_provider or 'VZW' in arin_provider:
                        wan2_wireless_badge = 'VZW'
                    elif 'AT&T' in arin_provider or 'ATT' in arin_provider:
                        wan2_wireless_badge = 'ATT'
                # Check for Starlink in provider name OR ARIN provider
                if circuit.wan2_provider and 'starlink' in circuit.wan2_provider.lower():
                    wan2_wireless_badge = 'STARLINK'
                # Also check ARIN provider for SpaceX Services, Inc.
                if meraki_device and meraki_device.wan2_arin_provider:
                    if 'SPACEX' in meraki_device.wan2_arin_provider.upper() or 'STARLINK' in meraki_device.wan2_arin_provider.upper():
                        wan2_wireless_badge = 'STARLINK' '''

new_wan2_logic = '''            # Check WAN2 for wireless (cell = VZW/AT&T, satellite = Starlink)  
            if not meraki_device:
                meraki_device = MerakiInventory.query.filter_by(network_name=circuit.network_name).first()
                
            # Check for cellular (VZW/AT&T)
            if circuit.wan2_speed and 'cell' in circuit.wan2_speed.lower():
                if meraki_device and meraki_device.wan2_arin_provider:
                    arin_provider = meraki_device.wan2_arin_provider.upper()
                    if 'VERIZON' in arin_provider or 'VZW' in arin_provider:
                        wan2_wireless_badge = 'VZW'
                    elif 'AT&T' in arin_provider or 'ATT' in arin_provider:
                        wan2_wireless_badge = 'ATT'
            
            # Check for Starlink (satellite speed OR SpaceX ARIN provider)
            if (circuit.wan2_speed and 'satellite' in circuit.wan2_speed.lower()) or \
               (circuit.wan2_provider and 'starlink' in circuit.wan2_provider.lower()) or \
               (meraki_device and meraki_device.wan2_arin_provider and 'SPACEX' in meraki_device.wan2_arin_provider.upper()):
                wan2_wireless_badge = 'STARLINK' '''

if old_wan2_logic in content:
    content = content.replace(old_wan2_logic, new_wan2_logic)
    print("✅ Fixed WAN2 Starlink detection for satellite speed")

# Write the updated blueprint
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'w') as f:
    f.write(content)

# 2. Fix the provider dropdown duplicates in template
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    template_content = f.read()

# Replace the existing broken filter logic with working unique filter
old_wan1_dropdown = '''                <select id="wan1ProviderFilter">
                    <option value="">All WAN1 Providers</option>
                    {% set wan1_providers = [] %}
                    {% for network in grouped_data %}
                        {% if network.wan1.provider and network.wan1.provider not in wan1_providers %}
                            {% set _ = wan1_providers.append(network.wan1.provider) %}
                        {% endif %}
                    {% endfor %}
                    {% for provider in wan1_providers|sort %}
                        <option value="{{ provider }}">{{ provider }}</option>
                    {% endfor %}
                </select>'''

new_wan1_dropdown = '''                <select id="wan1ProviderFilter">
                    <option value="">All WAN1 Providers</option>
                    {% set wan1_providers = grouped_data | map(attribute='wan1.provider') | select('string') | unique | sort %}
                    {% for provider in wan1_providers %}
                        <option value="{{ provider }}">{{ provider }}</option>
                    {% endfor %}
                </select>'''

if old_wan1_dropdown in template_content:
    template_content = template_content.replace(old_wan1_dropdown, new_wan1_dropdown)
    print("✅ Fixed WAN1 provider dropdown duplicates")

old_wan2_dropdown = '''                <select id="wan2ProviderFilter">
                    <option value="">All WAN2 Providers</option>
                    {% set wan2_providers = [] %}
                    {% for network in grouped_data %}
                        {% if network.wan2.provider and network.wan2.provider not in wan2_providers %}
                            {% set _ = wan2_providers.append(network.wan2.provider) %}
                        {% endif %}
                    {% endfor %}
                    {% for provider in wan2_providers|sort %}
                        <option value="{{ provider }}">{{ provider }}</option>
                    {% endfor %}
                </select>'''

new_wan2_dropdown = '''                <select id="wan2ProviderFilter">
                    <option value="">All WAN2 Providers</option>
                    {% set wan2_providers = grouped_data | map(attribute='wan2.provider') | select('string') | unique | sort %}
                    {% for provider in wan2_providers %}
                        <option value="{{ provider }}">{{ provider }}</option>
                    {% endfor %}
                </select>'''

if old_wan2_dropdown in template_content:
    template_content = template_content.replace(old_wan2_dropdown, new_wan2_dropdown)
    print("✅ Fixed WAN2 provider dropdown duplicates")

# Write the updated template
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'w') as f:
    f.write(template_content)

print("\n🛰️ Starlink detection now works for:")
print("  - Speed contains 'satellite'")
print("  - Provider contains 'starlink'") 
print("  - ARIN provider contains 'SpaceX'")
print("\n📋 Provider dropdowns now show unique providers only!")