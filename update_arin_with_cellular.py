#!/usr/bin/env python3
"""
Update nightly_meraki_db.py to detect cellular carriers for private IPs
Based on known patterns and device notes
"""

import os
import re

# Known private IP patterns for cellular carriers
CELLULAR_PRIVATE_IP_PATTERNS = {
    # Verizon patterns
    '192.168.0.151': 'Verizon Wireless',  # ALB 03 confirmed by user
    '192.168.2.122': 'Verizon Wireless',
    '192.168.2.125': 'Verizon Wireless', 
    '192.168.2.139': 'Verizon Wireless',
    
    # AT&T patterns
    '192.168.1.75': 'AT&T Mobility',
    '192.168.1.1': 'AT&T Mobility',
    
    # T-Mobile patterns  
    '192.168.2.185': 'T-Mobile USA',
    '10.': 'T-Mobile USA',  # Common T-Mobile pattern
}

# Pattern to insert into nightly_meraki_db.py
cellular_detection_code = '''
def detect_cellular_carrier_from_private_ip(ip_address, device_notes):
    """Detect cellular carrier for private IPs based on patterns and notes"""
    if not ip_address or not is_private_ip(ip_address):
        return None
    
    # Known private IP to carrier mappings
    CELLULAR_PRIVATE_IPS = {
        '192.168.0.151': 'Verizon Wireless',  # Confirmed patterns
        '192.168.2.122': 'Verizon Wireless',
        '192.168.2.125': 'Verizon Wireless',
        '192.168.2.139': 'Verizon Wireless',
        '192.168.1.75': 'AT&T Mobility',
        '192.168.1.1': 'AT&T Mobility',
        '192.168.2.185': 'T-Mobile USA',
    }
    
    # Check exact IP match first
    if ip_address in CELLULAR_PRIVATE_IPS:
        return CELLULAR_PRIVATE_IPS[ip_address]
    
    # Check device notes for carrier indicators
    if device_notes:
        notes_lower = device_notes.lower()
        if any(term in notes_lower for term in ['verizon', 'vzw', 'vzg']):
            return 'Verizon Wireless'
        elif any(term in notes_lower for term in ['at&t', 'att ']):
            return 'AT&T Mobility'
        elif any(term in notes_lower for term in ['t-mobile', 'tmobile']):
            return 'T-Mobile USA'
        elif 'digi' in notes_lower:
            return 'Digi International'
        elif 'inseego' in notes_lower:
            return 'Inseego Corp'
    
    # Default patterns
    if ip_address.startswith('10.'):
        return 'T-Mobile USA'  # Common T-Mobile pattern
    
    return None

def is_private_ip(ip_str):
    """Check if IP is private"""
    try:
        import ipaddress
        return ipaddress.ip_address(ip_str).is_private
    except:
        return False
'''

# Read the current nightly_meraki_db.py file
file_path = '/usr/local/bin/Main/nightly_meraki_db.py'
with open(file_path, 'r') as f:
    content = f.read()

# Find where to insert the new functions (after imports, before get_arin_provider)
import_section_end = content.find('def get_arin_provider')
if import_section_end == -1:
    print("Could not find get_arin_provider function")
    exit(1)

# Insert the new functions
new_content = (
    content[:import_section_end] + 
    cellular_detection_code + '\n\n' +
    content[import_section_end:]
)

# Now update the get_arin_provider function to use cellular detection
old_get_arin = '''def get_arin_provider(ip_address):
    """Get provider information from ARIN RDAP API"""
    if not ip_address or ip_address == 'nan':
        return None'''

new_get_arin = '''def get_arin_provider(ip_address, device_notes=None):
    """Get provider information from ARIN RDAP API or cellular detection"""
    if not ip_address or ip_address == 'nan':
        return None
    
    # Check for cellular carrier if private IP
    if is_private_ip(ip_address):
        carrier = detect_cellular_carrier_from_private_ip(ip_address, device_notes)
        if carrier:
            logger.info(f"Detected cellular carrier for {ip_address}: {carrier}")
            return carrier
        return None'''

new_content = new_content.replace(old_get_arin, new_get_arin)

# Update the calls to get_arin_provider to include device_notes
# Find the section where WAN IPs are processed
wan_processing_pattern = r"wan1_arin_provider = get_arin_provider\(wan1_ip\)"
wan_replacement = "wan1_arin_provider = get_arin_provider(wan1_ip, device.get('device_notes'))"

new_content = re.sub(wan_processing_pattern, wan_replacement, new_content)

wan2_pattern = r"wan2_arin_provider = get_arin_provider\(wan2_ip\)"
wan2_replacement = "wan2_arin_provider = get_arin_provider(wan2_ip, device.get('device_notes'))"

new_content = re.sub(wan2_pattern, wan2_replacement, new_content)

# Write the updated file
output_path = '/usr/local/bin/Main/nightly_meraki_db_with_cellular.py'
with open(output_path, 'w') as f:
    f.write(new_content)

print(f"Created updated file: {output_path}")
print("\nThe updated file includes:")
print("1. Cellular carrier detection for private IPs")
print("2. Known IP patterns (including ALB 03's 192.168.0.151 = Verizon)")
print("3. Device notes parsing for carrier hints")
print("4. Integration with ARIN provider lookups")
print("\nTo apply these changes, replace the original file:")
print(f"  cp {output_path} {file_path}")