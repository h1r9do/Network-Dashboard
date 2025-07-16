#!/usr/bin/env python3
"""
Patch for nightly_enriched_db.py to add SpaceX to Starlink conversion
"""

print("PATCH FOR nightly_enriched_db.py")
print("="*60)
print()
print("Add the following code after line 583 where ARIN data is obtained:")
print()
print("OLD CODE (around line 581-587):")
print("""
    for device in devices:
        (network_name, device_serial, device_model, device_tags,
         device_notes, wan1_ip, wan1_arin, wan2_ip, wan2_arin) = device
        
        # Skip excluded tags and network names
        if device_tags and any(tag.lower() in ['hub', 'lab', 'voice', 'test'] for tag in device_tags):
            continue
""")

print("\nNEW CODE (add SpaceX conversion):")
print("""
    for device in devices:
        (network_name, device_serial, device_model, device_tags,
         device_notes, wan1_ip, wan1_arin, wan2_ip, wan2_arin) = device
        
        # Convert SpaceX to Starlink in ARIN data
        if wan1_arin and 'spacex' in wan1_arin.lower():
            wan1_arin = 'Starlink'
        if wan2_arin and 'spacex' in wan2_arin.lower():
            wan2_arin = 'Starlink'
        
        # Skip excluded tags and network names
        if device_tags and any(tag.lower() in ['hub', 'lab', 'voice', 'test'] for tag in device_tags):
            continue
""")

print("\n" + "="*60)
print("\nAdditionally, to improve the preservation logic and prevent bad data:")
print("\n1. Update the needs_update function to check if speeds are in bad format:")
print()
print("ADD this function before the needs_update function:")
print("""
def is_bad_speed_format(speed):
    \"\"\"Check if speed is in the bad format (e.g., '20.0 M')\"\"\"
    if not speed:
        return False
    # Check for pattern like "123.4 M" (number, space, M)
    import re
    return bool(re.match(r'^\\d+\\.?\\d*\\s+M$', speed))
""")

print("\n2. Update needs_update to force update if bad speeds exist:")
print()
print("MODIFY the needs_update function to add this check at the beginning:")
print("""
def needs_update(current, new_data):
    \"\"\"Check if record needs updating\"\"\"
    # Force update if current speeds are in bad format
    if (is_bad_speed_format(current.get('wan1_speed')) or 
        is_bad_speed_format(current.get('wan2_speed'))):
        return True
    
    # Rest of the existing function...
""")

print("\n" + "="*60)
print("\n3. To implement the skip logic when IPs haven't changed:")
print("\nADD this code after getting the current record (around line 603):")
print("""
        # Get current record
        current_record = current_enriched.get(network_name, {})
        
        # Check if IPs have changed
        ip_changed = False
        if current_record:
            if (current_record.get('wan1_ip') != wan1_ip or 
                current_record.get('wan2_ip') != wan2_ip):
                ip_changed = True
        
        # If IPs haven't changed and we have valid ARIN data, skip entirely
        if not ip_changed and current_record:
            if (wan1_arin and wan1_arin not in ["Unknown", ""] and 
                wan2_arin and wan2_arin not in ["Unknown", ""]):
                # Only skip if speeds are in correct format
                if (not is_bad_speed_format(current_record.get('wan1_speed')) and
                    not is_bad_speed_format(current_record.get('wan2_speed'))):
                    skipped_count += 1
                    logger.debug(f"{network_name}: No IP changes, has valid ARIN data, and speeds are correct - skipping")
                    continue
""")

print("\n" + "="*60)
print("\n4. Update the data structure to include IP addresses:")
print("\nMODIFY the new_data dictionary (around line 732) to include:")
print("""
        new_data = {
            'network_name': network_name,
            'wan1_provider': wan1_provider,
            'wan1_speed': wan1_speed_final,
            'wan1_circuit_role': wan1_role,
            'wan1_confirmed': wan1_confirmed,
            'wan1_ip': wan1_ip,              # ADD THIS
            'wan1_arin_org': wan1_arin,      # ADD THIS
            'wan2_provider': wan2_provider,
            'wan2_speed': wan2_speed_final,
            'wan2_circuit_role': wan2_role,
            'wan2_confirmed': wan2_confirmed,
            'wan2_ip': wan2_ip,              # ADD THIS
            'wan2_arin_org': wan2_arin,      # ADD THIS
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
""")

print("\n" + "="*60)
print("\nNote: The enriched_circuits table needs these columns added if they don't exist:")
print("- wan1_ip")
print("- wan2_ip") 
print("- wan1_arin_org")
print("- wan2_arin_org")
print("\nRun this SQL to add them if needed:")
print("""
ALTER TABLE enriched_circuits 
ADD COLUMN IF NOT EXISTS wan1_ip VARCHAR(50),
ADD COLUMN IF NOT EXISTS wan2_ip VARCHAR(50),
ADD COLUMN IF NOT EXISTS wan1_arin_org VARCHAR(255),
ADD COLUMN IF NOT EXISTS wan2_arin_org VARCHAR(255);
""")