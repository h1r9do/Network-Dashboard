#!/usr/bin/env python3
"""
Compare 6/24 enriched JSON file to current database to identify cell circuit issues
"""

import json
import psycopg2
from collections import defaultdict, Counter
import sys

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

def get_current_db_data():
    """Get current circuit data from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT site_name, provider_name, details_service_speed, circuit_purpose,
               billing_monthly_cost, status
        FROM circuits 
        ORDER BY site_name
    """)
    
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    # Convert to dict format - group by site and circuit purpose
    current_data = {}
    for row in results:
        site_name, provider, speed, purpose, cost, status = row
        
        if site_name not in current_data:
            current_data[site_name] = {
                'network_name': site_name,
                'wan1': {'provider': '', 'speed': '', 'monthly_cost': '', 'circuit_role': ''},
                'wan2': {'provider': '', 'speed': '', 'monthly_cost': '', 'circuit_role': ''}
            }
        
        # Assign to wan1 or wan2 based on purpose
        if purpose == 'Primary':
            current_data[site_name]['wan1'] = {
                'provider': provider or '',
                'speed': speed or '',
                'monthly_cost': str(cost) if cost else '',
                'circuit_role': purpose or ''
            }
        elif purpose == 'Secondary':
            current_data[site_name]['wan2'] = {
                'provider': provider or '',
                'speed': speed or '',
                'monthly_cost': str(cost) if cost else '',
                'circuit_role': purpose or ''
            }
    
    return current_data

def analyze_differences():
    """Analyze differences between 6/24 and current data"""
    print("Loading 6/24 enriched data...")
    enriched_624 = load_624_enriched_data()
    
    print("Loading current database data...")
    current_db = get_current_db_data()
    
    # Convert enriched list to dict for easier comparison
    enriched_dict = {item['network_name']: item for item in enriched_624}
    
    print(f"\n=== COMPARISON RESULTS ===")
    print(f"6/24 Enriched Sites: {len(enriched_dict)}")
    print(f"Current DB Sites: {len(current_db)}")
    
    # Find sites only in 6/24
    only_in_624 = set(enriched_dict.keys()) - set(current_db.keys())
    print(f"Sites only in 6/24: {len(only_in_624)}")
    if only_in_624:
        print("  Examples:", list(only_in_624)[:5])
    
    # Find sites only in current DB
    only_in_current = set(current_db.keys()) - set(enriched_dict.keys())
    print(f"Sites only in current DB: {len(only_in_current)}")
    if only_in_current:
        print("  Examples:", list(only_in_current)[:5])
    
    # Analyze cell circuits specifically
    print(f"\n=== CELL CIRCUIT ANALYSIS ===")
    
    # Cell circuits in 6/24
    cell_624_wan1 = [site for site, data in enriched_dict.items() 
                     if 'cell' in data.get('wan1', {}).get('provider', '').lower() or
                        'satellite' in data.get('wan1', {}).get('speed', '').lower()]
    cell_624_wan2 = [site for site, data in enriched_dict.items() 
                     if 'cell' in data.get('wan2', {}).get('provider', '').lower() or
                        'satellite' in data.get('wan2', {}).get('speed', '').lower()]
    
    print(f"6/24 Cell WAN1 circuits: {len(cell_624_wan1)}")
    print(f"6/24 Cell WAN2 circuits: {len(cell_624_wan2)}")
    
    # Cell circuits in current DB
    cell_current_wan1 = [site for site, data in current_db.items() 
                         if 'cell' in data.get('wan1', {}).get('provider', '').lower() or
                            'satellite' in data.get('wan1', {}).get('speed', '').lower()]
    cell_current_wan2 = [site for site, data in current_db.items() 
                         if 'cell' in data.get('wan2', {}).get('provider', '').lower() or
                            'satellite' in data.get('wan2', {}).get('speed', '').lower()]
    
    print(f"Current Cell WAN1 circuits: {len(cell_current_wan1)}")
    print(f"Current Cell WAN2 circuits: {len(cell_current_wan2)}")
    
    # Find differences in cell circuits
    cell_624_all = set(cell_624_wan1 + cell_624_wan2)
    cell_current_all = set(cell_current_wan1 + cell_current_wan2)
    
    print(f"\nTotal sites with cell circuits in 6/24: {len(cell_624_all)}")
    print(f"Total sites with cell circuits currently: {len(cell_current_all)}")
    
    # New cell circuits
    new_cell_circuits = cell_current_all - cell_624_all
    print(f"New cell circuits since 6/24: {len(new_cell_circuits)}")
    if new_cell_circuits:
        print("  Examples:", list(new_cell_circuits)[:10])
    
    # Lost cell circuits
    lost_cell_circuits = cell_624_all - cell_current_all
    print(f"Lost cell circuits since 6/24: {len(lost_cell_circuits)}")
    if lost_cell_circuits:
        print("  Examples:", list(lost_cell_circuits)[:10])
    
    # Check specific examples of changes
    print(f"\n=== PROVIDER CHANGES ===")
    provider_changes = 0
    speed_changes = 0
    
    common_sites = set(enriched_dict.keys()) & set(current_db.keys())
    for site in list(common_sites)[:10]:  # Check first 10 for examples
        old_data = enriched_dict[site]
        new_data = current_db[site]
        
        # Check WAN1 changes
        old_wan1_prov = old_data.get('wan1', {}).get('provider', '')
        new_wan1_prov = new_data.get('wan1', {}).get('provider', '')
        old_wan1_speed = old_data.get('wan1', {}).get('speed', '')
        new_wan1_speed = new_data.get('wan1', {}).get('speed', '')
        
        if old_wan1_prov != new_wan1_prov:
            provider_changes += 1
            print(f"{site} WAN1 provider: '{old_wan1_prov}' -> '{new_wan1_prov}'")
        
        if old_wan1_speed != new_wan1_speed:
            speed_changes += 1
            print(f"{site} WAN1 speed: '{old_wan1_speed}' -> '{new_wan1_speed}'")
    
    print(f"\nSample provider changes: {provider_changes}")
    print(f"Sample speed changes: {speed_changes}")

if __name__ == "__main__":
    analyze_differences()