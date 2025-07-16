#!/usr/bin/env python3
"""
Add badge counting to the test route
"""

print("=== ADDING BADGE COUNTING TO TEST ROUTE ===\n")

# Read the test file
with open('/usr/local/bin/Main/dsrcircuits_test.py', 'r') as f:
    content = f.read()

# Find where we build grouped_data and add badge counting after
badge_code = '''
            # Count badges
            dsr_count = 0
            vzw_count = 0
            att_count = 0
            starlink_count = 0
            
            for entry in grouped_data:
                # Check for DSR badge
                if entry.get('wan1', {}).get('confirmed') or entry.get('wan2', {}).get('confirmed'):
                    dsr_count += 1
                
                # Get network name for Meraki lookup
                network_name = entry.get('network_name')
                meraki_device = MerakiInventory.query.filter_by(network_name=network_name).first() if network_name else None
                
                # Check WAN1 for wireless badges
                wan1_speed = (entry.get('wan1', {}).get('speed') or '').lower()
                wan1_provider = (entry.get('wan1', {}).get('provider') or '').lower()
                
                # Check for VZW/AT&T (cell speed)
                if 'cell' in wan1_speed and meraki_device and meraki_device.wan1_arin_provider:
                    if 'VERIZON' in meraki_device.wan1_arin_provider.upper():
                        vzw_count += 1
                    elif 'AT&T' in meraki_device.wan1_arin_provider.upper():
                        att_count += 1
                
                # Check for Starlink (satellite speed OR provider name OR SpaceX ARIN)
                if ('satellite' in wan1_speed or 
                    'starlink' in wan1_provider or
                    (meraki_device and meraki_device.wan1_arin_provider and 
                     'SPACEX' in meraki_device.wan1_arin_provider.upper())):
                    starlink_count += 1
                
                # Check WAN2 for wireless badges
                wan2_speed = (entry.get('wan2', {}).get('speed') or '').lower()
                wan2_provider = (entry.get('wan2', {}).get('provider') or '').lower()
                
                if 'cell' in wan2_speed and meraki_device and meraki_device.wan2_arin_provider:
                    if 'VERIZON' in meraki_device.wan2_arin_provider.upper():
                        vzw_count += 1
                    elif 'AT&T' in meraki_device.wan2_arin_provider.upper():
                        att_count += 1
                
                if ('satellite' in wan2_speed or 
                    'starlink' in wan2_provider or
                    (meraki_device and meraki_device.wan2_arin_provider and 
                     'SPACEX' in meraki_device.wan2_arin_provider.upper())):
                    starlink_count += 1
            
            badge_counts = {
                'dsr': dsr_count,
                'vzw': vzw_count,
                'att': att_count,
                'starlink': starlink_count
            }
            
            # Get last updated time
            last_updated = None
            latest_circuit = db.session.query(Circuit).order_by(Circuit.updated_at.desc()).first()
            if latest_circuit and latest_circuit.updated_at:
                last_updated = latest_circuit.updated_at.strftime('%B %d, %Y')
            
'''

# Find all return render_template calls and update them
import re

# Pattern to find render_template calls
pattern = r"(return render_template\('dsrcircuits_test\.html',\s*grouped_data=grouped_data)"

# Replace with badge_counts and last_updated added
replacement = r"\1, badge_counts=badge_counts, last_updated=last_updated"

# First, we need to add the badge counting code before the return statements
# Find the main route handler
route_pattern = r'(@dsrcircuits_test_bp\.route\(\'/dsrcircuits-test\'\).*?)(return render_template.*?grouped_data=grouped_data)'
match = re.search(route_pattern, content, re.DOTALL)

if match:
    # Find where grouped_data is populated
    # Look for the line before the return statement
    lines = match.group(0).split('\n')
    insert_index = -1
    
    for i, line in enumerate(lines):
        if 'grouped_data.append(' in line or 'grouped_data = ' in line:
            # Find the next return statement after this
            for j in range(i, len(lines)):
                if 'return render_template' in lines[j]:
                    insert_index = j
                    break
            if insert_index > 0:
                break
    
    if insert_index > 0:
        # Insert badge counting code before the return
        lines.insert(insert_index, badge_code)
        new_route = '\n'.join(lines)
        content = content.replace(match.group(0), new_route)
        print("✅ Added badge counting logic to main route")

# Now update all render_template calls to include badge_counts and last_updated
content = re.sub(pattern, replacement, content)

# Also need to handle the other render_template calls that might not have grouped_data
other_pattern = r"(return render_template\('dsrcircuits_test\.html',)"
other_matches = re.finditer(other_pattern, content)

for match in other_matches:
    # Check if this already has badge_counts
    context = content[match.start():match.end()+200]
    if 'badge_counts' not in context:
        # Add empty badge_counts and last_updated for error cases
        old_text = match.group(0)
        new_text = old_text.rstrip(',') + ''',
                badge_counts={'dsr': 0, 'vzw': 0, 'att': 0, 'starlink': 0},
                last_updated=None,'''
        content = content.replace(old_text, new_text, 1)

# Write the updated file
with open('/usr/local/bin/Main/dsrcircuits_test.py', 'w') as f:
    f.write(content)

print("✅ Updated test route with badge counting logic")