#!/usr/bin/env python3
"""
Debug script to check HQ-HUB entry in enriched_circuits table
"""

import psycopg2
import json

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="dsrcircuits",
        user="dsruser",
        password="dsrpass123"
    )

def check_hq_hub():
    """Check HQ-HUB entry in enriched_circuits table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if HQ-HUB exists in enriched_circuits
    cursor.execute("""
        SELECT network_name, device_tags, wan1_provider, wan1_speed, 
               wan2_provider, wan2_speed, wan1_confirmed, wan2_confirmed
        FROM enriched_circuits 
        WHERE network_name ILIKE '%hq%hub%' OR network_name = 'HQ-HUB'
    """)
    
    results = cursor.fetchall()
    if results:
        print(f"Found {len(results)} HQ-HUB entries in enriched_circuits:")
        for row in results:
            network_name, device_tags, wan1_prov, wan1_speed, wan2_prov, wan2_speed, wan1_conf, wan2_conf = row
            print(f"  Network: {network_name}")
            print(f"  Device Tags: {device_tags}")
            print(f"  WAN1: {wan1_prov} - {wan1_speed} (confirmed: {wan1_conf})")
            print(f"  WAN2: {wan2_prov} - {wan2_speed} (confirmed: {wan2_conf})")
            print("  ---")
    else:
        print("No HQ-HUB entries found in enriched_circuits table")
    
    # Check total count with and without filtering
    cursor.execute("SELECT COUNT(*) FROM enriched_circuits")
    total_count = cursor.fetchone()[0]
    print(f"Total enriched circuits: {total_count}")
    
    # Count circuits with hub/lab/voice tags
    cursor.execute("""
        SELECT COUNT(*) FROM enriched_circuits 
        WHERE EXISTS (
            SELECT 1 FROM unnest(device_tags) AS tag 
            WHERE LOWER(tag) LIKE '%hub%' 
               OR LOWER(tag) LIKE '%lab%' 
               OR LOWER(tag) LIKE '%voice%'
        )
    """)
    excluded_count = cursor.fetchone()[0]
    print(f"Circuits with hub/lab/voice tags (should be excluded): {excluded_count}")
    
    # Count circuits without excluded tags
    cursor.execute("""
        SELECT COUNT(*) FROM enriched_circuits 
        WHERE NOT EXISTS (
            SELECT 1 FROM unnest(device_tags) AS tag 
            WHERE LOWER(tag) LIKE '%hub%' 
               OR LOWER(tag) LIKE '%lab%' 
               OR LOWER(tag) LIKE '%voice%'
        )
    """)
    filtered_count = cursor.fetchone()[0]
    print(f"Circuits after filtering (should be displayed): {filtered_count}")
    
    # Get examples of circuits with excluded tags
    cursor.execute("""
        SELECT network_name, device_tags FROM enriched_circuits 
        WHERE EXISTS (
            SELECT 1 FROM unnest(device_tags) AS tag 
            WHERE LOWER(tag) LIKE '%hub%' 
               OR LOWER(tag) LIKE '%lab%' 
               OR LOWER(tag) LIKE '%voice%'
        )
        LIMIT 10
    """)
    
    excluded_examples = cursor.fetchall()
    if excluded_examples:
        print(f"\nExamples of circuits with excluded tags:")
        for network_name, device_tags in excluded_examples:
            print(f"  {network_name}: {device_tags}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_hq_hub()