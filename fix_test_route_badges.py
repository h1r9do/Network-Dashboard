#!/usr/bin/env python3
"""
Fix the test route to:
1. Use dsrcircuits_test.html template
2. Use production tables (not test tables)
3. Add badge counting
"""

print("=== FIXING TEST ROUTE WITH BADGES ===\n")

# Read the test route file
with open('/usr/local/bin/Main/dsrcircuits_test.py', 'r') as f:
    content = f.read()

# Replace all occurrences of test tables with production tables
content = content.replace('enriched_circuits_test', 'enriched_circuits')
content = content.replace('circuits_test', 'circuits')
content = content.replace('FROM test_', 'FROM ')

# Replace template name
content = content.replace("render_template('dsrcircuits.html'", "render_template('dsrcircuits_test.html'")

# Now we need to add badge counting before the return statement
# Find the main route handler
import re

# Find the route handler and add badge counting
route_pattern = r'(@dsrcircuits_test_bp\.route\(\'/dsrcircuits-test\'\).*?)(return render_template.*?grouped_data=grouped_data\))'
match = re.search(route_pattern, content, re.DOTALL)

if match:
    before_return = match.group(1)
    return_statement = match.group(2)
    
    # Add badge counting logic before the return
    badge_logic = '''
        # Count badges
        dsr_count = 0
        vzw_count = 0
        att_count = 0
        starlink_count = 0
        
        for entry in grouped_data:
            # Check for DSR badge (wan1_confirmed or wan2_confirmed)
            if entry.get('wan1', {}).get('confirmed') or entry.get('wan2', {}).get('confirmed'):
                dsr_count += 1
            
            # Check WAN1 for wireless badges
            wan1_speed = entry.get('wan1', {}).get('speed', '').lower()
            wan1_provider = entry.get('wan1', {}).get('provider', '').lower()
            
            # Check for cell speed with VZW/AT&T
            if 'cell' in wan1_speed:
                # Need to check ARIN provider from meraki device
                network_name = entry.get('network_name')
                meraki_device = MerakiInventory.query.filter_by(network_name=network_name).first()
                if meraki_device and meraki_device.wan1_arin_provider:
                    if 'VERIZON' in meraki_device.wan1_arin_provider.upper():
                        vzw_count += 1
                    elif 'AT&T' in meraki_device.wan1_arin_provider.upper():
                        att_count += 1
            
            # Check for Starlink (satellite speed OR provider name)
            if 'satellite' in wan1_speed or 'starlink' in wan1_provider:
                starlink_count += 1
            
            # Same checks for WAN2
            wan2_speed = entry.get('wan2', {}).get('speed', '').lower()
            wan2_provider = entry.get('wan2', {}).get('provider', '').lower()
            
            if 'cell' in wan2_speed:
                network_name = entry.get('network_name')
                meraki_device = MerakiInventory.query.filter_by(network_name=network_name).first()
                if meraki_device and meraki_device.wan2_arin_provider:
                    if 'VERIZON' in meraki_device.wan2_arin_provider.upper():
                        vzw_count += 1
                    elif 'AT&T' in meraki_device.wan2_arin_provider.upper():
                        att_count += 1
            
            if 'satellite' in wan2_speed or 'starlink' in wan2_provider:
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
    
    # Update the return statement to include badge_counts and last_updated
    new_return = return_statement.replace(
        "grouped_data=grouped_data)",
        "grouped_data=grouped_data, badge_counts=badge_counts, last_updated=last_updated)"
    )
    
    # Replace in content
    content = content.replace(
        match.group(0),
        before_return + badge_logic + new_return
    )
    
    print("✅ Added badge counting logic to test route")
else:
    print("❌ Could not find test route pattern")

# Write the updated file
with open('/usr/local/bin/Main/dsrcircuits_test.py', 'w') as f:
    f.write(content)

print("✅ Updated test route to use production tables and dsrcircuits_test.html template")
print("✅ Test route now includes badge counting")