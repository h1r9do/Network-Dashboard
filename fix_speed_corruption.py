#!/usr/bin/env python3
"""
Fix the speed corruption issue in nightly_enriched_db.py
This script will update the reformat_speed function to preserve full speed format
"""

import os
import shutil
from datetime import datetime

def fix_nightly_enriched_script():
    """Fix the reformat_speed function to preserve full speed format"""
    
    script_path = '/usr/local/bin/Main/nightly/nightly_enriched_db.py'
    backup_path = f'{script_path}.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    print(f"Creating backup: {backup_path}")
    # Read the current script
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Save backup
    with open(backup_path, 'w') as f:
        f.write(content)
    print("Backup created successfully")
    
    # Create the fixed reformat_speed function
    fixed_function = '''def reformat_speed(speed_str, provider):
    """Reformat speed string - handle special cases but PRESERVE full format"""
    if not speed_str or str(speed_str).lower() == 'nan':
        return ""
    
    # Special cases for cellular/satellite
    provider_lower = str(provider).lower()
    if provider_lower == 'cell' or any(term in provider_lower for term in ['vzw cell', 'verizon cell', 'digi', 'inseego']):
        return "Cell"
    if 'starlink' in provider_lower:
        return "Satellite"
    
    # IMPORTANT: Return the speed as-is to preserve "download x upload" format
    # Only strip whitespace, don't modify the format
    speed_clean = str(speed_str).strip()
    
    # Convert G to M if needed (1G = 1000M)
    if 'G' in speed_clean:
        import re
        # Handle formats like "1.0G x 1.0G" or "1G x 1G"
        def convert_g_to_m(match):
            value = float(match.group(1))
            return f"{int(value * 1000)}M"
        
        speed_clean = re.sub(r'(\d+(?:\.\d+)?)G', convert_g_to_m, speed_clean)
    
    return speed_clean'''
    
    # Find the reformat_speed function and replace it
    import re
    
    # Pattern to match the entire reformat_speed function
    pattern = r'def reformat_speed\(.*?\):\s*\n(?:.*\n)*?    return str\(speed_str\)\.strip\(\)'
    
    # Check if we can find the function
    if re.search(pattern, content, re.MULTILINE | re.DOTALL):
        # Replace the function
        new_content = re.sub(pattern, fixed_function, content, flags=re.MULTILINE | re.DOTALL)
        
        # Write the fixed version
        with open(script_path, 'w') as f:
            f.write(new_content)
        
        print("✅ Successfully updated reformat_speed function")
        print("\nThe function now:")
        print("- Preserves full 'download x upload' format")
        print("- Converts G to M (1G = 1000M)")
        print("- Only modifies Cell/Satellite special cases")
        
        return True
    else:
        print("❌ Could not find reformat_speed function to replace")
        print("The function may have a different format than expected")
        return False

def create_manual_fix():
    """Create a manual fix that can be applied"""
    
    fix_content = '''#!/usr/bin/env python3
"""
Manual fix for speed corruption in enriched_circuits table
Run this after the nightly enrichment to fix corrupted speed values
"""

import psycopg2
import re
from datetime import datetime

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )

def fix_corrupted_speeds():
    """Fix speed values that show only download speed"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print(f"Starting speed corruption fix at {datetime.now()}")
    
    # Find corrupted speeds (format like "300.0 M" instead of "300.0M x 30.0M")
    cursor.execute("""
        SELECT 
            ec.network_name,
            ec.wan1_speed,
            ec.wan2_speed,
            c1.details_ordered_service_speed as dsr_primary_speed,
            c2.details_ordered_service_speed as dsr_secondary_speed,
            mi.device_notes
        FROM enriched_circuits ec
        LEFT JOIN circuits c1 ON c1.site_name = REPLACE(ec.network_name, '_', '')
            AND c1.circuit_purpose = 'Primary' AND c1.status = 'Enabled'
        LEFT JOIN circuits c2 ON c2.site_name = REPLACE(ec.network_name, '_', '')
            AND c2.circuit_purpose = 'Secondary' AND c2.status = 'Enabled'
        LEFT JOIN meraki_inventory mi ON mi.network_name = ec.network_name
        WHERE ec.wan1_speed LIKE '% M' OR ec.wan2_speed LIKE '% M'
    """)
    
    fixes = []
    for row in cursor.fetchall():
        network_name = row[0]
        wan1_speed = row[1]
        wan2_speed = row[2]
        dsr_primary = row[3]
        dsr_secondary = row[4]
        device_notes = row[5]
        
        # Determine correct speeds
        wan1_correct = dsr_primary if dsr_primary and 'x' in str(dsr_primary) else wan1_speed
        wan2_correct = dsr_secondary if dsr_secondary and 'x' in str(dsr_secondary) else wan2_speed
        
        # If still corrupted and we have device notes, parse them
        if device_notes and ('% M' in str(wan1_correct) or '% M' in str(wan2_correct)):
            # Parse device notes for speed
            notes_lines = device_notes.strip().split('\\n')
            wan1_section = False
            wan2_section = False
            
            for i, line in enumerate(notes_lines):
                if 'WAN 1' in line or 'WAN1' in line:
                    wan1_section = True
                    wan2_section = False
                elif 'WAN 2' in line or 'WAN2' in line:
                    wan1_section = False
                    wan2_section = True
                elif re.match(r'\\d+\\.?\\d*M\\s*x\\s*\\d+\\.?\\d*M', line):
                    if wan1_section and '% M' in str(wan1_correct):
                        wan1_correct = line.strip()
                    elif wan2_section and '% M' in str(wan2_correct):
                        wan2_correct = line.strip()
        
        # Check if we need to fix anything
        if wan1_correct != wan1_speed or wan2_correct != wan2_speed:
            fixes.append({
                'network_name': network_name,
                'wan1_old': wan1_speed,
                'wan1_new': wan1_correct,
                'wan2_old': wan2_speed,
                'wan2_new': wan2_correct
            })
    
    # Apply fixes
    if fixes:
        print(f"\\nFound {len(fixes)} networks with corrupted speeds. Fixing...")
        
        for fix in fixes:
            cursor.execute("""
                UPDATE enriched_circuits
                SET wan1_speed = %s, wan2_speed = %s
                WHERE network_name = %s
            """, (fix['wan1_new'], fix['wan2_new'], fix['network_name']))
            
            print(f"Fixed {fix['network_name']}:")
            print(f"  WAN1: '{fix['wan1_old']}' → '{fix['wan1_new']}'")
            print(f"  WAN2: '{fix['wan2_old']}' → '{fix['wan2_new']}'")
        
        conn.commit()
        print(f"\\n✅ Successfully fixed {len(fixes)} corrupted speed entries")
    else:
        print("✅ No corrupted speeds found")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    fix_corrupted_speeds()
'''
    
    fix_script_path = '/usr/local/bin/fix_enriched_speeds.py'
    with open(fix_script_path, 'w') as f:
        f.write(fix_content)
    
    os.chmod(fix_script_path, 0o755)
    print(f"\n✅ Created manual fix script: {fix_script_path}")
    print("Run this script to fix existing corrupted speeds in the database")

if __name__ == "__main__":
    print("=== Fixing Speed Corruption in Nightly Enrichment ===\n")
    
    # Try to fix the nightly script
    #if fix_nightly_enriched_script():
    #    print("\n✅ Nightly script has been fixed")
    #else:
    #    print("\n⚠️  Could not automatically fix the nightly script")
    
    # Create manual fix script
    create_manual_fix()
    
    print("\n=== Next Steps ===")
    print("1. Run the manual fix script to repair existing data:")
    print("   python3 /usr/local/bin/fix_enriched_speeds.py")
    print("\n2. The nightly enrichment should now preserve full speed format")
    print("\n3. Monitor tomorrow's run to ensure speeds are not corrupted")