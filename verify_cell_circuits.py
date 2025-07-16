#!/usr/bin/env python3
"""
More careful analysis of cell circuits in 6/24 vs current data
"""

import json
import psycopg2
from collections import defaultdict, Counter

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="dsrcircuits",
        user="dsruser",
        password="dsrpass123"
    )

def load_624_enriched_data():
    """Load the 6/24 enriched JSON data"""
    enriched_file = "/var/www/html/meraki-data/mx_inventory_enriched_2025-06-24.json"
    
    try:
        with open(enriched_file, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading 6/24 enriched data: {e}")
        return []

def analyze_cell_circuits():
    """Carefully analyze cell circuits"""
    print("Loading 6/24 enriched data...")
    enriched_624 = load_624_enriched_data()
    
    # Analyze 6/24 cell circuits more carefully
    print(f"\n=== 6/24 CELL CIRCUIT ANALYSIS ===")
    
    cell_keywords = ['cell', 'satellite', 'vzw', 'att cell', 'wireless']
    
    cell_sites_624 = set()
    cell_details_624 = []
    
    for site_data in enriched_624:
        site_name = site_data.get('network_name', '')
        wan1 = site_data.get('wan1', {})
        wan2 = site_data.get('wan2', {})
        
        # Check WAN1 for cell indicators
        wan1_provider = (wan1.get('provider', '') or '').lower()
        wan1_speed = (wan1.get('speed', '') or '').lower()
        wan1_is_cell = any(keyword in wan1_provider or keyword in wan1_speed for keyword in cell_keywords)
        
        # Check WAN2 for cell indicators
        wan2_provider = (wan2.get('provider', '') or '').lower()
        wan2_speed = (wan2.get('speed', '') or '').lower()
        wan2_is_cell = any(keyword in wan2_provider or keyword in wan2_speed for keyword in cell_keywords)
        
        if wan1_is_cell or wan2_is_cell:
            cell_sites_624.add(site_name)
            cell_details_624.append({
                'site': site_name,
                'wan1_cell': wan1_is_cell,
                'wan2_cell': wan2_is_cell,
                'wan1_provider': wan1.get('provider', ''),
                'wan1_speed': wan1.get('speed', ''),
                'wan2_provider': wan2.get('provider', ''),
                'wan2_speed': wan2.get('speed', '')
            })
    
    print(f"Total sites with cell circuits in 6/24: {len(cell_sites_624)}")
    print("First 10 examples:")
    for detail in cell_details_624[:10]:
        site = detail['site']
        print(f"  {site}:")
        if detail['wan1_cell']:
            print(f"    WAN1: {detail['wan1_provider']} - {detail['wan1_speed']}")
        if detail['wan2_cell']:
            print(f"    WAN2: {detail['wan2_provider']} - {detail['wan2_speed']}")
    
    # Now check current database
    print(f"\n=== CURRENT DATABASE ANALYSIS ===")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check enriched_circuits for cell circuits
    cursor.execute("""
        SELECT network_name, wan1_provider, wan1_speed, wan2_provider, wan2_speed
        FROM enriched_circuits 
        ORDER BY network_name
    """)
    
    current_enriched = cursor.fetchall()
    cell_sites_current = set()
    cell_details_current = []
    
    for row in current_enriched:
        site_name, wan1_prov, wan1_speed, wan2_prov, wan2_speed = row
        
        # Check for cell indicators
        wan1_text = f"{wan1_prov or ''} {wan1_speed or ''}".lower()
        wan2_text = f"{wan2_prov or ''} {wan2_speed or ''}".lower()
        
        wan1_is_cell = any(keyword in wan1_text for keyword in cell_keywords)
        wan2_is_cell = any(keyword in wan2_text for keyword in cell_keywords)
        
        if wan1_is_cell or wan2_is_cell:
            cell_sites_current.add(site_name)
            cell_details_current.append({
                'site': site_name,
                'wan1_cell': wan1_is_cell,
                'wan2_cell': wan2_is_cell,
                'wan1_provider': wan1_prov or '',
                'wan1_speed': wan1_speed or '',
                'wan2_provider': wan2_prov or '',
                'wan2_speed': wan2_speed or ''
            })
    
    print(f"Total sites with cell circuits in current database: {len(cell_sites_current)}")
    print("First 10 examples:")
    for detail in cell_details_current[:10]:
        site = detail['site']
        print(f"  {site}:")
        if detail['wan1_cell']:
            print(f"    WAN1: {detail['wan1_provider']} - {detail['wan1_speed']}")
        if detail['wan2_cell']:
            print(f"    WAN2: {detail['wan2_provider']} - {detail['wan2_speed']}")
    
    # Compare differences
    print(f"\n=== COMPARISON ===")
    missing_sites = cell_sites_624 - cell_sites_current
    new_sites = cell_sites_current - cell_sites_624
    
    print(f"Sites with cell circuits only in 6/24: {len(missing_sites)}")
    if missing_sites:
        print("  Examples:", list(missing_sites)[:10])
    
    print(f"Sites with cell circuits only in current: {len(new_sites)}")
    if new_sites:
        print("  Examples:", list(new_sites)[:10])
    
    # Check if any of the "missing" sites still exist but without cell circuits
    if missing_sites:
        print(f"\n=== CHECKING STATUS OF 'MISSING' CELL SITES ===")
        missing_list = list(missing_sites)[:5]  # Check first 5
        
        placeholders = ','.join(['%s'] * len(missing_list))
        cursor.execute(f"""
            SELECT network_name, wan1_provider, wan1_speed, wan2_provider, wan2_speed
            FROM enriched_circuits 
            WHERE network_name IN ({placeholders})
        """, missing_list)
        
        still_exist = cursor.fetchall()
        print(f"Of the first 5 'missing' sites, {len(still_exist)} still exist in current DB:")
        for row in still_exist:
            site_name, wan1_prov, wan1_speed, wan2_prov, wan2_speed = row
            print(f"  {site_name}: WAN1={wan1_prov}-{wan1_speed}, WAN2={wan2_prov}-{wan2_speed}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    analyze_cell_circuits()