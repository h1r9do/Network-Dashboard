#!/usr/bin/env python3
"""
Find all provider labels in meraki_inventory that start and end with 'n'
This indicates corrupted parsing from device notes
"""

import sys
sys.path.append('/usr/local/bin/test')
from config import Config
import psycopg2

def find_corrupted_labels():
    """Find all provider labels that start and end with 'n'"""
    
    # Connect to database
    conn = psycopg2.connect(Config.SQLALCHEMY_DATABASE_URI)
    cur = conn.cursor()
    
    print("Finding provider labels that start and end with 'n'...")
    print("=" * 60)
    
    # Query for corrupted WAN1 provider labels
    query = """
    SELECT network_name, wan1_provider_label, wan1_speed_label
    FROM meraki_inventory 
    WHERE wan1_provider_label LIKE 'n%n'
    AND wan1_provider_label IS NOT NULL
    AND LENGTH(wan1_provider_label) > 2
    ORDER BY network_name;
    """
    
    cur.execute(query)
    wan1_results = cur.fetchall()
    
    print(f"WAN1 Provider Labels (corrupted): {len(wan1_results)} found")
    print("-" * 40)
    
    for network_name, provider_label, speed_label in wan1_results[:10]:  # Show first 10
        print(f"{network_name:12} | WAN1: {repr(provider_label)}")
    
    if len(wan1_results) > 10:
        print(f"... and {len(wan1_results) - 10} more")
    
    print()
    
    # Query for corrupted WAN2 provider labels
    query = """
    SELECT network_name, wan2_provider_label, wan2_speed_label
    FROM meraki_inventory 
    WHERE wan2_provider_label LIKE 'n%n'
    AND wan2_provider_label IS NOT NULL
    AND LENGTH(wan2_provider_label) > 2
    ORDER BY network_name;
    """
    
    cur.execute(query)
    wan2_results = cur.fetchall()
    
    print(f"WAN2 Provider Labels (corrupted): {len(wan2_results)} found")
    print("-" * 40)
    
    for network_name, provider_label, speed_label in wan2_results[:10]:  # Show first 10
        print(f"{network_name:12} | WAN2: {repr(provider_label)}")
    
    if len(wan2_results) > 10:
        print(f"... and {len(wan2_results) - 10} more")
    
    print()
    
    # Get sample of original device notes to compare
    print("Sample device notes for comparison:")
    print("-" * 40)
    
    if wan1_results:
        sample_network = wan1_results[0][0]
        cur.execute("SELECT device_notes FROM meraki_inventory WHERE network_name = %s", (sample_network,))
        notes_result = cur.fetchone()
        if notes_result:
            print(f"{sample_network} device notes:")
            print(repr(notes_result[0]))
    
    print()
    
    # Summary statistics
    cur.execute("SELECT COUNT(*) FROM meraki_inventory WHERE wan1_provider_label IS NOT NULL")
    total_wan1 = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM meraki_inventory WHERE wan2_provider_label IS NOT NULL")
    total_wan2 = cur.fetchone()[0]
    
    print("Summary:")
    print(f"Total WAN1 provider labels: {total_wan1}")
    print(f"Corrupted WAN1 labels: {len(wan1_results)} ({len(wan1_results)/total_wan1*100:.1f}%)")
    print(f"Total WAN2 provider labels: {total_wan2}")
    print(f"Corrupted WAN2 labels: {len(wan2_results)} ({len(wan2_results)/total_wan2*100:.1f}%)")
    
    conn.close()
    
    return wan1_results, wan2_results

if __name__ == "__main__":
    find_corrupted_labels()