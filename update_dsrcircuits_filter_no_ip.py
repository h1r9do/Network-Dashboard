#!/usr/bin/env python3
"""
Update dsrcircuits route to filter out sites without any IP addresses
"""

import re

def update_dsrcircuits_filter():
    # Read the current blueprint
    with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'r') as f:
        content = f.read()
    
    # Find the main dsrcircuits function
    function_start = content.find('@dsrcircuits_bp.route(\'/dsrcircuits\')')
    if function_start == -1:
        print("❌ Could not find dsrcircuits route")
        return
    
    # Find where enriched_circuits are queried
    query_start = content.find('enriched_circuits = EnrichedCircuit.query.filter(', function_start)
    if query_start == -1:
        print("❌ Could not find enriched_circuits query")
        return
    
    # Find the end of the filter (looking for order_by)
    order_by_pos = content.find(').order_by(EnrichedCircuit.network_name).all()', query_start)
    if order_by_pos == -1:
        print("❌ Could not find end of query")
        return
    
    # Find the existing filter conditions end
    filter_end = content.rfind(')', query_start, order_by_pos)
    
    # Add the new IP filter condition
    new_filter = '''
        ).filter(
            # Exclude sites without any IP addresses (not live)
            ~(
                (EnrichedCircuit.wan1_ip.is_(None) | (EnrichedCircuit.wan1_ip == '')) &
                (EnrichedCircuit.wan2_ip.is_(None) | (EnrichedCircuit.wan2_ip == ''))
            )'''
    
    # Insert the new filter
    content = content[:filter_end] + new_filter + content[filter_end:]
    
    # Save the updated blueprint
    with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'w') as f:
        f.write(content)
    
    print("✅ Updated dsrcircuits route to filter out sites without IP addresses")
    print("✅ Sites like VAW 04 and MSG 01 will no longer appear on the main page")

if __name__ == "__main__":
    update_dsrcircuits_filter()