#!/usr/bin/env python3
"""Update Unknown entries for private IPs to show 'Private IP'"""

import psycopg2
import sys
sys.path.insert(0, '/usr/local/bin/Main')
from nightly_meraki_db import get_db_connection

def main():
    # Update existing Unknown entries that are private IPs
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("Updating private IP addresses from 'Unknown' to 'Private IP'...")
    
    # Update WAN1 private IPs
    cursor.execute("""
        UPDATE meraki_inventory 
        SET wan1_arin_provider = 'Private IP'
        WHERE wan1_arin_provider = 'Unknown'
        AND (wan1_ip LIKE '192.168%' 
             OR wan1_ip LIKE '10.%' 
             OR wan1_ip LIKE '172.%'
             OR wan1_ip LIKE '169.254%')
        AND wan1_ip != ''
    """)
    wan1_updated = cursor.rowcount
    
    # Update WAN2 private IPs
    cursor.execute("""
        UPDATE meraki_inventory 
        SET wan2_arin_provider = 'Private IP'
        WHERE wan2_arin_provider = 'Unknown'
        AND (wan2_ip LIKE '192.168%' 
             OR wan2_ip LIKE '10.%' 
             OR wan2_ip LIKE '172.%'
             OR wan2_ip LIKE '169.254%')
        AND wan2_ip != ''
    """)
    wan2_updated = cursor.rowcount
    
    # Also update enriched_circuits table
    cursor.execute("""
        UPDATE enriched_circuits 
        SET wan1_provider = 'Private IP'
        WHERE wan1_provider = 'Unknown'
        AND (wan1_ip LIKE '192.168%' 
             OR wan1_ip LIKE '10.%' 
             OR wan1_ip LIKE '172.%'
             OR wan1_ip LIKE '169.254%')
        AND wan1_ip != ''
    """)
    enriched_wan1_updated = cursor.rowcount
    
    cursor.execute("""
        UPDATE enriched_circuits 
        SET wan2_provider = 'Private IP'
        WHERE wan2_provider = 'Unknown'
        AND (wan2_ip LIKE '192.168%' 
             OR wan2_ip LIKE '10.%' 
             OR wan2_ip LIKE '172.%'
             OR wan2_ip LIKE '169.254%')
        AND wan2_ip != ''
    """)
    enriched_wan2_updated = cursor.rowcount
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f'\nMeraki Inventory Table:')
    print(f'  Updated {wan1_updated} WAN1 private IPs')
    print(f'  Updated {wan2_updated} WAN2 private IPs')
    print(f'  Subtotal: {wan1_updated + wan2_updated} entries')
    
    print(f'\nEnriched Circuits Table:')
    print(f'  Updated {enriched_wan1_updated} WAN1 private IPs')
    print(f'  Updated {enriched_wan2_updated} WAN2 private IPs')
    print(f'  Subtotal: {enriched_wan1_updated + enriched_wan2_updated} entries')
    
    print(f'\nTotal: {wan1_updated + wan2_updated + enriched_wan1_updated + enriched_wan2_updated} private IPs updated to show "Private IP"')

if __name__ == "__main__":
    main()