#!/usr/bin/env python3
"""
Update production route to include wireless badges and counts
"""

print("=== UPDATING PRODUCTION ROUTE ===\n")

# Read the blueprint file
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'r') as f:
    content = f.read()

# Find the production dsrcircuits route (not the test one)
import re

# We need to update the main dsrcircuits() function to include the wireless logic
# Find the main route function
main_route_match = re.search(r'@dsrcircuits_bp\.route\(\'/dsrcircuits\'\)\s*\ndef dsrcircuits\(\):.*?return render_template', content, re.DOTALL)

if main_route_match:
    print("Found main dsrcircuits route")
    
    # The production route needs to:
    # 1. Add wireless badge logic
    # 2. Calculate badge counts
    # 3. Get DSR last updated timestamp
    # 4. Pass these to the template
    
    # Find where grouped_data is built
    # Insert the wireless badge logic before grouped_data.append
    
    # Look for the pattern where we build grouped_data
    old_append = '''            grouped_data.append({
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
    
    new_append = '''            # Check for wireless badges
            wan1_wireless_badge = None
            wan2_wireless_badge = None
            
            # Check WAN1 for wireless (cell=VZW/AT&T, satellite=Starlink)
            meraki_device = MerakiInventory.query.filter_by(network_name=circuit.network_name).first()
            
            # Check for cellular providers
            if circuit.wan1_speed and 'cell' in circuit.wan1_speed.lower():
                if meraki_device and meraki_device.wan1_arin_provider:
                    arin_provider = meraki_device.wan1_arin_provider.upper()
                    if 'VERIZON' in arin_provider or 'VZW' in arin_provider:
                        wan1_wireless_badge = 'VZW'
                    elif 'AT&T' in arin_provider or 'ATT' in arin_provider:
                        wan1_wireless_badge = 'ATT'
            
            # Check for Starlink (satellite speed OR provider name OR SpaceX ARIN)
            if (circuit.wan1_speed and 'satellite' in circuit.wan1_speed.lower()) or \
               (circuit.wan1_provider and 'starlink' in circuit.wan1_provider.lower()) or \
               (meraki_device and meraki_device.wan1_arin_provider and 'SPACEX' in meraki_device.wan1_arin_provider.upper()):
                wan1_wireless_badge = 'STARLINK'
            
            # Check WAN2 for wireless (cell=VZW/AT&T, satellite=Starlink)
            if not meraki_device:
                meraki_device = MerakiInventory.query.filter_by(network_name=circuit.network_name).first()
            
            # Check for cellular providers
            if circuit.wan2_speed and 'cell' in circuit.wan2_speed.lower():
                if meraki_device and meraki_device.wan2_arin_provider:
                    arin_provider = meraki_device.wan2_arin_provider.upper()
                    if 'VERIZON' in arin_provider or 'VZW' in arin_provider:
                        wan2_wireless_badge = 'VZW'
                    elif 'AT&T' in arin_provider or 'ATT' in arin_provider:
                        wan2_wireless_badge = 'ATT'
            
            # Check for Starlink (satellite speed OR provider name OR SpaceX ARIN)
            if (circuit.wan2_speed and 'satellite' in circuit.wan2_speed.lower()) or \
               (circuit.wan2_provider and 'starlink' in circuit.wan2_provider.lower()) or \
               (meraki_device and meraki_device.wan2_arin_provider and 'SPACEX' in meraki_device.wan2_arin_provider.upper()):
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
    
    content = content.replace(old_append, new_append)
    print("✅ Added wireless badge logic to production route")
    
    # Now add the badge counting and timestamp before the return statement
    old_return = '''        return render_template('dsrcircuits.html', grouped_data=grouped_data)'''
    
    new_return = '''        # Calculate badge counts for header display
        dsr_count = vzw_count = att_count = starlink_count = 0
        
        for entry in grouped_data:
            # Count DSR badges - check if match_info is dict or object
            wan1_info = entry['wan1']['match_info']
            if wan1_info:
                if hasattr(wan1_info, 'dsr_verified'):
                    if wan1_info.dsr_verified:
                        dsr_count += 1
                elif isinstance(wan1_info, dict) and wan1_info.get('dsr_verified'):
                    dsr_count += 1
                    
            wan2_info = entry['wan2']['match_info']
            if wan2_info:
                if hasattr(wan2_info, 'dsr_verified'):
                    if wan2_info.dsr_verified:
                        dsr_count += 1
                elif isinstance(wan2_info, dict) and wan2_info.get('dsr_verified'):
                    dsr_count += 1
                
            # Count wireless providers (not badges, actual providers)
            # Count Starlink based on provider name
            if entry['wan1']['provider'] and 'starlink' in entry['wan1']['provider'].lower():
                starlink_count += 1
                    
            # Check WAN1 wireless badges
            if entry['wan1'].get('wireless_badge'):
                if entry['wan1']['wireless_badge'] == 'VZW':
                    vzw_count += 1
                elif entry['wan1']['wireless_badge'] == 'ATT':
                    att_count += 1
            
            # Count Starlink based on provider name
            if entry['wan2']['provider'] and 'starlink' in entry['wan2']['provider'].lower():
                starlink_count += 1
                    
            # Check WAN2 wireless badges
            if entry['wan2'].get('wireless_badge'):
                if entry['wan2']['wireless_badge'] == 'VZW':
                    vzw_count += 1
                elif entry['wan2']['wireless_badge'] == 'ATT':
                    att_count += 1
        
        badge_counts = {
            'dsr': dsr_count,
            'vzw': vzw_count, 
            'att': att_count,
            'starlink': starlink_count
        }
        
        # Get DSR data last updated timestamp from circuits table
        from datetime import datetime
        try:
            # Get the most recent updated_at from circuits table (when DSR data was last pulled)
            latest_dsr_update = db.session.execute(
                db.text("SELECT MAX(updated_at) FROM circuits WHERE updated_at IS NOT NULL")
            ).scalar()
            
            if latest_dsr_update:
                last_updated = latest_dsr_update.strftime("%B %d, %Y at %I:%M %p")
            else:
                # Fallback - check if we have any timestamp data
                last_updated = "DSR data timestamp unavailable"
        except Exception as e:
            print(f"Error getting DSR timestamp: {e}")
            last_updated = "Unable to determine DSR update time"
        
        return render_template('dsrcircuits.html', grouped_data=grouped_data, badge_counts=badge_counts, last_updated=last_updated)'''
    
    content = content.replace(old_return, new_return)
    print("✅ Added badge counting and timestamp to production route")

# Write the updated blueprint
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'w') as f:
    f.write(content)

print("\n✅ Production route updated!")
print("The production /dsrcircuits route now includes:")
print("  - Wireless badge detection (VZW, AT&T, Starlink)")
print("  - Badge counts calculation")
print("  - DSR last updated timestamp")
print("\nThe production template already has the display logic from our copy!")