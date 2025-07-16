#!/usr/bin/env python3
"""
Fix bad speed data in enriched_circuits table
Corrects speeds that have space before M (e.g., "20.0 M" -> "20.0M x 20.0M")
"""
import psycopg2
import re
from datetime import datetime

# Read config
with open('/usr/local/bin/Main/config.py', 'r') as f:
    config_content = f.read()
    
uri_match = re.search(r"SQLALCHEMY_DATABASE_URI = ['\"]postgresql://([^:]+):([^@]+)@([^/]+)/([^'\"]+)['\"]", config_content)
if uri_match:
    user, password, host, database = uri_match.groups()
else:
    print("Could not find database URI")
    exit(1)

# Parse device notes function
def parse_raw_notes(raw_notes):
    """Parse device notes to extract speeds"""
    if not raw_notes or not raw_notes.strip():
        return "", "", "", ""
    
    # Split by WAN sections
    wan1_pattern = re.compile(r'(?:WAN1|WAN\s*1)\s*:?\s*', re.IGNORECASE)
    wan2_pattern = re.compile(r'(?:WAN2|WAN\s*2)\s*:?\s*', re.IGNORECASE)
    
    # Split the text
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
    
    # Extract speeds from multiline text
    def extract_speed(text):
        if not text:
            return ""
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        speed_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*([MG]B?)\s*x\s*(\d+(?:\.\d+)?)\s*([MG]B?)', re.IGNORECASE)
        
        for line in lines:
            match = speed_pattern.search(line)
            if match:
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
                    
                return f"{down_speed:.1f}{down_unit} x {up_speed:.1f}{up_unit}"
        
        return ""
    
    wan1_speed = extract_speed(wan1_text)
    wan2_speed = extract_speed(wan2_text)
    
    return wan1_speed, wan2_speed

try:
    conn = psycopg2.connect(
        host=host.split(':')[0],
        port=5432,
        database=database,
        user=user,
        password=password
    )
    cursor = conn.cursor()
    
    print("Finding sites with bad speed formats...")
    
    # Find all sites with space before M
    cursor.execute("""
        SELECT ec.network_name, ec.wan1_speed, ec.wan2_speed, 
               ec.wan1_provider, ec.wan2_provider,
               mi.device_notes
        FROM enriched_circuits ec
        JOIN meraki_inventory mi ON ec.network_name = mi.network_name
        WHERE (ec.wan1_speed ~ '^\d+\.?\d*\s+M$' OR ec.wan2_speed ~ '^\d+\.?\d*\s+M$')
        AND mi.device_notes IS NOT NULL
        ORDER BY ec.network_name
    """)
    
    sites_to_fix = cursor.fetchall()
    print(f"\nFound {len(sites_to_fix)} sites with bad speed format")
    
    fixes = []
    
    for row in sites_to_fix:
        network_name, wan1_speed, wan2_speed, wan1_provider, wan2_provider, device_notes = row
        
        # Parse device notes to get correct speeds
        correct_wan1_speed, correct_wan2_speed = parse_raw_notes(device_notes)
        
        fix_needed = False
        wan1_fix = wan1_speed
        wan2_fix = wan2_speed
        
        # Check if WAN1 needs fixing
        if re.match(r'^\d+\.?\d*\s+M$', wan1_speed) and correct_wan1_speed:
            wan1_fix = correct_wan1_speed
            fix_needed = True
            
        # Check if WAN2 needs fixing
        if re.match(r'^\d+\.?\d*\s+M$', wan2_speed) and correct_wan2_speed:
            wan2_fix = correct_wan2_speed
            fix_needed = True
            
        if fix_needed:
            fixes.append({
                'network_name': network_name,
                'wan1_old': wan1_speed,
                'wan1_new': wan1_fix,
                'wan2_old': wan2_speed,
                'wan2_new': wan2_fix,
                'wan1_provider': wan1_provider,
                'wan2_provider': wan2_provider
            })
    
    print(f"\nWill fix {len(fixes)} sites:")
    
    # Show preview
    for i, fix in enumerate(fixes[:10]):
        print(f"\n{fix['network_name']}:")
        if fix['wan1_old'] != fix['wan1_new']:
            print(f"  WAN1: '{fix['wan1_old']}' -> '{fix['wan1_new']}' ({fix['wan1_provider']})")
        if fix['wan2_old'] != fix['wan2_new']:
            print(f"  WAN2: '{fix['wan2_old']}' -> '{fix['wan2_new']}' ({fix['wan2_provider']})")
    
    if len(fixes) > 10:
        print(f"\n... and {len(fixes) - 10} more")
    
    # Ask for confirmation
    print("\nDo you want to apply these fixes? (yes/no): ", end='')
    response = input().strip().lower()
    
    if response == 'yes':
        print("\nApplying fixes...")
        
        for fix in fixes:
            cursor.execute("""
                UPDATE enriched_circuits
                SET wan1_speed = %s,
                    wan2_speed = %s,
                    last_updated = %s
                WHERE network_name = %s
            """, (
                fix['wan1_new'],
                fix['wan2_new'],
                datetime.utcnow(),
                fix['network_name']
            ))
        
        conn.commit()
        print(f"\nSuccessfully updated {len(fixes)} sites")
        
        # Verify a few
        print("\nVerifying fixes...")
        cursor.execute("""
            SELECT network_name, wan1_speed, wan2_speed
            FROM enriched_circuits
            WHERE network_name IN %s
            LIMIT 5
        """, (tuple([fix['network_name'] for fix in fixes[:5]]),))
        
        for row in cursor.fetchall():
            print(f"  {row[0]}: WAN1='{row[1]}', WAN2='{row[2]}'")
    else:
        print("\nFixes cancelled")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()