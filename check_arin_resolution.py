#!/usr/bin/env python3
"""
Check ARIN lookup status for IP addresses in the database
"""

import psycopg2
import json
from datetime import datetime

def check_arin_resolution():
    # Connect to database
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )
    cursor = conn.cursor()
    
    print("=== CHECKING ARIN RESOLUTION STATUS ===\n")
    
    # First, let's check the meraki_inventory table structure for ARIN data
    print("1. Checking ARIN-related columns in meraki_inventory:")
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'meraki_inventory' 
        AND column_name LIKE '%arin%'
        ORDER BY ordinal_position
    """)
    arin_columns = cursor.fetchall()
    print(f"ARIN columns found: {[col[0] for col in arin_columns]}\n")
    
    # Check enriched_circuits for ARIN data
    print("2. Checking ARIN-related columns in enriched_circuits:")
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'enriched_circuits' 
        AND column_name LIKE '%arin%'
        ORDER BY ordinal_position
    """)
    enriched_arin_columns = cursor.fetchall()
    print(f"ARIN columns found: {[col[0] for col in enriched_arin_columns]}\n")
    
    # Get IPs without ARIN resolution from meraki_inventory
    print("3. Analyzing ARIN resolution in meraki_inventory:")
    cursor.execute("""
        SELECT 
            network_name,
            wan1_ip,
            wan1_arin_provider,
            wan2_ip,
            wan2_arin_provider
        FROM meraki_inventory
        WHERE (wan1_ip IS NOT NULL AND wan1_ip != '' AND wan1_ip != 'None')
           OR (wan2_ip IS NOT NULL AND wan2_ip != '' AND wan2_ip != 'None')
    """)
    
    results = cursor.fetchall()
    
    unresolved_ips = []
    resolved_count = 0
    total_ips = 0
    
    for row in results:
        network_name, wan1_ip, wan1_arin, wan2_ip, wan2_arin = row
        
        # Check WAN1
        if wan1_ip and wan1_ip not in ['', 'None']:
            total_ips += 1
            if not wan1_arin or wan1_arin in ['', 'None', 'Unknown']:
                unresolved_ips.append({
                    'network_name': network_name,
                    'interface': 'WAN1',
                    'ip_address': wan1_ip,
                    'current_arin_value': wan1_arin
                })
            else:
                resolved_count += 1
        
        # Check WAN2
        if wan2_ip and wan2_ip not in ['', 'None']:
            total_ips += 1
            if not wan2_arin or wan2_arin in ['', 'None', 'Unknown']:
                unresolved_ips.append({
                    'network_name': network_name,
                    'interface': 'WAN2',
                    'ip_address': wan2_ip,
                    'current_arin_value': wan2_arin
                })
            else:
                resolved_count += 1
    
    print(f"Total IPs found: {total_ips}")
    print(f"Resolved IPs: {resolved_count}")
    print(f"Unresolved IPs: {len(unresolved_ips)}")
    print(f"Resolution rate: {(resolved_count/total_ips*100):.1f}%" if total_ips > 0 else "N/A")
    
    # Check enriched_circuits ARIN data
    print("\n4. Analyzing ARIN resolution in enriched_circuits:")
    cursor.execute("""
        SELECT 
            network_name,
            wan1_ip,
            wan1_arin_org,
            wan2_ip,
            wan2_arin_org
        FROM enriched_circuits
        WHERE (wan1_ip IS NOT NULL AND wan1_ip != '' AND wan1_ip != 'None')
           OR (wan2_ip IS NOT NULL AND wan2_ip != '' AND wan2_ip != 'None')
    """)
    
    enriched_results = cursor.fetchall()
    enriched_unresolved = []
    
    for row in enriched_results:
        network_name, wan1_ip, wan1_arin, wan2_ip, wan2_arin = row
        
        if wan1_ip and wan1_ip not in ['', 'None'] and (not wan1_arin or wan1_arin in ['', 'None']):
            enriched_unresolved.append({
                'network_name': network_name,
                'interface': 'WAN1',
                'ip_address': wan1_ip
            })
        
        if wan2_ip and wan2_ip not in ['', 'None'] and (not wan2_arin or wan2_arin in ['', 'None']):
            enriched_unresolved.append({
                'network_name': network_name,
                'interface': 'WAN2',
                'ip_address': wan2_ip
            })
    
    print(f"Unresolved in enriched_circuits: {len(enriched_unresolved)}")
    
    # Get unique unresolved IPs
    unique_ips = {}
    for item in unresolved_ips:
        ip = item['ip_address']
        if ip not in unique_ips:
            unique_ips[ip] = []
        unique_ips[ip].append({
            'network_name': item['network_name'],
            'interface': item['interface']
        })
    
    # Create summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'statistics': {
            'total_ips_found': total_ips,
            'resolved_ips': resolved_count,
            'unresolved_ips': len(unresolved_ips),
            'unique_unresolved_ips': len(unique_ips),
            'resolution_rate': f"{(resolved_count/total_ips*100):.1f}%" if total_ips > 0 else "N/A"
        },
        'unresolved_ips_by_site': unresolved_ips,
        'unique_unresolved_ips': unique_ips
    }
    
    # Save to JSON file
    json_file = '/usr/local/bin/unresolved_arin_ips.json'
    with open(json_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✅ Saved unresolved IPs to: {json_file}")
    
    # Show sample of unresolved IPs
    print("\nSample of unresolved IPs:")
    for i, (ip, sites) in enumerate(list(unique_ips.items())[:10]):
        print(f"  {ip}: {len(sites)} site(s)")
        for site in sites[:3]:
            print(f"    - {site['network_name']} ({site['interface']})")
        if len(sites) > 3:
            print(f"    ... and {len(sites)-3} more")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_arin_resolution()