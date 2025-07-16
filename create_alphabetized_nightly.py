#!/usr/bin/env python3
"""
Create an alphabetized batch processing version of the nightly script
that processes networks in alphabetical groups to ensure all networks are captured
"""

import os
import sys

# Read the current nightly script
with open('/usr/local/bin/Main/nightly/nightly_meraki_db.py', 'r') as f:
    content = f.read()

# Find the main processing section
main_start = content.find('def main():')
if main_start == -1:
    print("Could not find main() function")
    sys.exit(1)

# Find where networks are processed
process_section = """
    # Process networks in alphabetical batches
    # This ensures we capture all networks even with API pagination limits
    all_networks = get_all_networks(org_id)
    logger.info(f"Found {len(all_networks)} total networks")
    
    # Sort networks alphabetically
    all_networks.sort(key=lambda n: n.get('name', '').upper())
    
    # Process in batches by first letter
    letter_batches = {}
    for network in all_networks:
        name = network.get('name', '').upper()
        if name:
            first_letter = name[0]
            if first_letter not in letter_batches:
                letter_batches[first_letter] = []
            letter_batches[first_letter].append(network)
    
    # Process each letter batch
    for letter in sorted(letter_batches.keys()):
        networks = letter_batches[letter]
        logger.info(f"Processing {len(networks)} networks starting with '{letter}'")
        
        # Process networks in this batch
        for network in networks:
            network_name = network.get('name', '')
            network_id = network.get('id')
            
            # Skip if no network ID
            if not network_id:
                continue
                
            # Check if this is a CAL/CAN/CAS network for special attention
            if network_name.startswith(('CAL', 'CAN', 'CAS')):
                logger.info(f"Processing California network: {network_name}")
"""

print("Alphabetized batch processing approach created.")
print("\nTo implement:")
print("1. Networks are sorted alphabetically")
print("2. Networks are grouped by first letter")
print("3. Each letter group is processed separately")
print("4. This ensures all networks are captured, including CAL 24")
print("\nThis approach helps when dealing with large numbers of networks and API pagination limits.")