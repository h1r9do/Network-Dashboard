#!/usr/bin/env python3
"""
Fix for nightly_enriched_db.py to address:
1. Speed parsing issue (300.0 M instead of 300.0M x 35.0M)
2. Preservation logic for sites with no changes
3. SpaceX to Starlink conversion
"""

# Key changes needed:

print("FIXES NEEDED FOR nightly_enriched_db.py:")
print("="*60)

print("""
1. FIX SPEED PARSING ISSUE
   Problem: Line 129 converts all whitespace to single spaces
   Current: text = re.sub(r'\\s+', ' ', raw_notes.strip())
   
   This turns:
   WAN 1
   Comcast
   300.0M x 35.0M
   
   Into: WAN 1 Comcast 300.0M x 35.0M
   
   Then the regex extracts "Comcast 300.0M x 35.0M" as one segment
   But there's a bug where it's only returning part of the speed.

2. BETTER PRESERVATION LOGIC
   Current logic only preserves if ARIN matches, but should preserve if:
   - IP hasn't changed AND has valid ARIN data
   - Is a confirmed circuit with no source data changes
   - Device notes haven't changed

3. ADD SPACEX TO STARLINK CONVERSION
   After getting ARIN data, check if provider contains 'spacex' and convert to 'Starlink'

4. SKIP LOGIC
   If IP hasn't changed and has valid ARIN info -> skip entirely
   If IP hasn't changed but missing ARIN -> do lookup but don't change data
   Only update if DSR circuit info has changed
""")

print("\n" + "="*60)
print("\nPROPOSED CHANGES:")
print("="*60)

# Show the actual code changes needed
print("""
1. Fix parse_raw_notes function (around line 124):
""")

new_parse_function = '''def parse_raw_notes(raw_notes):
    """Parse raw notes - FIXED to handle newlines properly"""
    if not raw_notes or not raw_notes.strip():
        return "", "", "", ""
    
    # DON'T normalize newlines away - we need them for parsing!
    wan1_pattern = re.compile(r'(?:WAN1|WAN\\s*1)\\s*:?\\s*', re.IGNORECASE)
    wan2_pattern = re.compile(r'(?:WAN2|WAN\\s*2)\\s*:?\\s*', re.IGNORECASE)
    
    # Split by WAN patterns
    parts = re.split(wan1_pattern, raw_notes, maxsplit=1)
    wan1_text = ""
    wan2_text = ""
    
    if len(parts) > 1:
        after_wan1 = parts[1]
        wan2_split = re.split(wan2_pattern, after_wan1, maxsplit=1)
        wan1_text = wan2_split[0].strip()
        if len(wan2_split) > 1:
            wan2_text = wan2_split[1].strip()
    else:
        parts = re.split(wan2_pattern, raw_notes, maxsplit=1)
        if len(parts) > 1:
            wan2_text = parts[1].strip()
        else:
            wan1_text = raw_notes.strip()
    
    # Extract provider and speed from multiline text
    def extract_provider_and_speed_fixed(text):
        """Extract provider and speed from multiline text"""
        if not text:
            return "", ""
        
        lines = [line.strip() for line in text.split('\\n') if line.strip()]
        provider = ""
        speed = ""
        
        # Look for speed pattern in lines
        speed_pattern = re.compile(r'(\\d+(?:\\.\\d+)?)\\s*([MG]B?)\\s*x\\s*(\\d+(?:\\.\\d+)?)\\s*([MG]B?)', re.IGNORECASE)
        
        for i, line in enumerate(lines):
            match = speed_pattern.search(line)
            if match:
                # Format the speed properly
                down_speed = float(match.group(1))
                down_unit = match.group(2).upper().rstrip('B')
                up_speed = float(match.group(3))
                up_unit = match.group(4).upper().rstrip('B')
                
                if down_unit == 'G':
                    down_speed *= 1000
                    down_unit = 'M'
                if up_unit == 'G':
                    up_speed *= 1000
                    up_unit = 'M'
                    
                speed = f"{down_speed:.1f}{down_unit} x {up_speed:.1f}{up_unit}"
                
                # Provider is usually the line before the speed
                if i > 0:
                    provider = lines[i-1]
                break
        
        # Handle special cases (Cell, Satellite, etc.)
        if not speed and provider:
            if 'cell' in provider.lower() or provider.strip().endswith(' Cell'):
                return provider.replace(' Cell', '').strip(), "Cell"
            elif 'satellite' in provider.lower() or 'starlink' in provider.lower():
                return "Starlink", "Satellite"
        
        return provider, speed
    
    wan1_provider, wan1_speed = extract_provider_and_speed_fixed(wan1_text)
    wan2_provider, wan2_speed = extract_provider_and_speed_fixed(wan2_text)
    
    return wan1_provider, wan1_speed, wan2_provider, wan2_speed'''

print(new_parse_function)

print("""

2. Update the main processing loop to check for changes properly:
""")

print('''
# Around line 580 in the main processing loop:

# Get current enriched record
current_record = current_enriched.get(network_name, {})

# Check if IPs have changed
ip_changed = False
if current_record:
    if (current_record.get('wan1_ip') != wan1_ip or 
        current_record.get('wan2_ip') != wan2_ip):
        ip_changed = True

# If IPs haven't changed and we have valid ARIN data, skip entirely
if not ip_changed and current_record:
    if (wan1_arin and wan1_arin != "Unknown" and 
        wan2_arin and wan2_arin != "Unknown"):
        skipped_count += 1
        logger.debug(f"{network_name}: No IP changes and has valid ARIN data, skipping")
        continue

# Parse device notes
wan1_notes, wan1_speed, wan2_notes, wan2_speed = parse_raw_notes(device_notes)

# If this is a non-DSR confirmed circuit with no changes, preserve it
if not dsr_circuits and current_record:
    if (current_record.get('wan1_confirmed') and 
        current_record.get('wan2_confirmed') and
        not ip_changed):
        # Check if device notes changed
        old_notes = parse_raw_notes(current_record.get('device_notes', ''))
        if (old_notes[0] == wan1_notes and old_notes[1] == wan1_speed and
            old_notes[2] == wan2_notes and old_notes[3] == wan2_speed):
            non_dsr_preserved += 1
            logger.debug(f"{network_name}: Confirmed non-DSR circuit unchanged, preserving")
            continue
''')

print("""

3. Add SpaceX to Starlink conversion after ARIN lookup:
""")

print('''
# After getting ARIN provider (around line 600):
if wan1_arin and 'spacex' in wan1_arin.lower():
    wan1_arin = 'Starlink'
if wan2_arin and 'spacex' in wan2_arin.lower():
    wan2_arin = 'Starlink'
''')

print("""

4. Update enriched_circuits to store IP addresses:
""")

print('''
# Need to add wan1_ip and wan2_ip to the update/insert statements
# Around line 732, add to new_data:
new_data = {
    'network_name': network_name,
    'wan1_provider': wan1_provider,
    'wan1_speed': wan1_speed_final,
    'wan1_circuit_role': wan1_role,
    'wan1_confirmed': wan1_confirmed,
    'wan1_ip': wan1_ip,  # ADD THIS
    'wan1_arin_org': wan1_arin,  # ADD THIS
    'wan2_provider': wan2_provider,
    'wan2_speed': wan2_speed_final,
    'wan2_circuit_role': wan2_role,
    'wan2_confirmed': wan2_confirmed,
    'wan2_ip': wan2_ip,  # ADD THIS
    'wan2_arin_org': wan2_arin,  # ADD THIS
    'device_notes': device_notes,  # ADD THIS
    'last_updated': datetime.now(timezone.utc).isoformat()
}
''')