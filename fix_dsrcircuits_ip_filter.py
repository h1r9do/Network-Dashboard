#!/usr/bin/env python3
"""
Fix the dsrcircuits filter to properly check IPs from meraki_inventory
"""

import re

def fix_dsrcircuits_filter():
    # Read the current blueprint
    with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'r') as f:
        content = f.read()
    
    # First, remove the bad filter I added
    bad_filter_start = content.find(').filter(\n            # Exclude sites without any IP addresses (not live)')
    if bad_filter_start != -1:
        # Find the end of this bad filter
        bad_filter_end = content.find('))', bad_filter_start) + 2
        # Remove the entire bad filter section
        content = content[:bad_filter_start] + ')' + content[bad_filter_end:]
        print("✅ Removed incorrect IP filter")
    
    # Now update the query to properly filter using meraki_inventory
    # Find the enriched_circuits query
    query_start = content.find('enriched_circuits = EnrichedCircuit.query.filter(')
    if query_start == -1:
        print("❌ Could not find enriched_circuits query")
        return
    
    # Find the full query section
    all_end = content.find('.all()', query_start) + 6
    
    # Replace with a proper query that joins with meraki_inventory
    old_query = content[query_start:all_end]
    
    new_query = '''enriched_circuits = db.session.query(EnrichedCircuit).join(
            MerakiInventory,
            EnrichedCircuit.network_name == MerakiInventory.network_name
        ).filter(
            # Exclude hub/lab/voice/test sites
            ~(
                EnrichedCircuit.network_name.ilike('%hub%') |
                EnrichedCircuit.network_name.ilike('%lab%') |
                EnrichedCircuit.network_name.ilike('%voice%') |
                EnrichedCircuit.network_name.ilike('%test%')
            )
        ).filter(
            # Exclude sites without any IP addresses in Meraki (not live)
            ~(
                ((MerakiInventory.wan1_ip.is_(None)) | (MerakiInventory.wan1_ip == '') | (MerakiInventory.wan1_ip == 'None')) &
                ((MerakiInventory.wan2_ip.is_(None)) | (MerakiInventory.wan2_ip == '') | (MerakiInventory.wan2_ip == 'None'))
            )
        ).order_by(EnrichedCircuit.network_name).all()'''
    
    # Replace the query
    content = content[:query_start] + new_query + content[all_end:]
    
    # Save the updated blueprint
    with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'w') as f:
        f.write(content)
    
    print("✅ Updated dsrcircuits to properly filter sites without IPs using meraki_inventory")
    print("✅ Only ~6 sites (like VAW 04, MSG 01) will be filtered out")

if __name__ == "__main__":
    fix_dsrcircuits_filter()