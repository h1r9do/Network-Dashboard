#!/usr/bin/env python3
"""
Check AZP 21 pricing and cost assignment logic
"""

import psycopg2
import psycopg2.extras
from config import Config
import re

# Parse database connection
match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
if match:
    user, password, host, port, database = match.groups()
    
    conn = psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password
    )
    
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    print("=== AZP 21 Pricing Investigation ===\n")
    
    # Check in enriched_circuits
    print("1. Enriched Circuits Table:")
    cursor.execute("""
        SELECT network_name, wan1_provider, wan1_speed, wan2_provider, wan2_speed
        FROM enriched_circuits
        WHERE network_name = 'AZP 21'
    """)
    
    enriched = cursor.fetchone()
    if enriched:
        print(f"  Network: {enriched['network_name']}")
        print(f"  WAN1: {enriched['wan1_provider']} - {enriched['wan1_speed']}")
        print(f"  WAN2: {enriched['wan2_provider']} - {enriched['wan2_speed']}")
    else:
        print("  Not found in enriched_circuits")
    
    # Check all circuits for AZP 21
    print("\n2. All Circuits for AZP 21:")
    cursor.execute("""
        SELECT 
            site_name,
            circuit_purpose,
            provider_name,
            details_service_speed,
            billing_monthly_cost,
            status,
            record_number
        FROM circuits
        WHERE site_name = 'AZP 21'
        ORDER BY circuit_purpose
    """)
    
    circuits = cursor.fetchall()
    if circuits:
        for circuit in circuits:
            print(f"  {circuit['circuit_purpose']}: {circuit['provider_name']} - {circuit['details_service_speed']} - ${circuit['billing_monthly_cost']} ({circuit['status']})")
    else:
        print("  No circuits found in circuits table")
    
    # Check what the cost assignment logic would return
    print("\n3. Cost Assignment Logic Test:")
    if enriched and circuits:
        print("  Available circuit costs:")
        for circuit in circuits:
            if circuit['status'] == 'Enabled':
                print(f"    {circuit['circuit_purpose']}: ${circuit['billing_monthly_cost']}")
        
        # Simulate the cost assignment logic
        primary_circuits = [c for c in circuits if c['circuit_purpose'] == 'Primary' and c['status'] == 'Enabled']
        secondary_circuits = [c for c in circuits if c['circuit_purpose'] == 'Secondary' and c['status'] == 'Enabled']
        
        print(f"\n  Primary circuits: {len(primary_circuits)}")
        print(f"  Secondary circuits: {len(secondary_circuits)}")
        
        if primary_circuits:
            print(f"  WAN1 would get cost from Primary: ${primary_circuits[0]['billing_monthly_cost']}")
        if secondary_circuits:
            print(f"  WAN2 would get cost from Secondary: ${secondary_circuits[0]['billing_monthly_cost']}")
    
    # Check meraki inventory for AZP 21
    print("\n4. Meraki Inventory:")
    cursor.execute("""
        SELECT network_name, wan1_ip, wan2_ip, wan1_arin_provider, wan2_arin_provider
        FROM meraki_inventory
        WHERE network_name = 'AZP 21'
    """)
    
    meraki = cursor.fetchone()
    if meraki:
        print(f"  Network: {meraki['network_name']}")
        print(f"  WAN1 IP: {meraki['wan1_ip']} - ARIN: {meraki['wan1_arin_provider']}")
        print(f"  WAN2 IP: {meraki['wan2_ip']} - ARIN: {meraki['wan2_arin_provider']}")
    else:
        print("  Not found in meraki_inventory")
    
    conn.close()