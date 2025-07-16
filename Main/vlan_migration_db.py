#!/usr/bin/env python3
"""
Database-based VLAN migration network discovery
Uses existing database tables to get network and VLAN information
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment
load_dotenv('/usr/local/bin/meraki.env')

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "dsrcircuits"
DB_USER = "dsruser"
DB_PASS = "dsrpass123"

def get_db_connection():
    """Get direct database connection"""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def get_networks_from_db():
    """Get all networks with VLAN information from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get networks with VLANs from database
        query = """
        WITH network_summary AS (
            SELECT 
                mi.network_id,
                mi.network_name,
                mi.device_tags,
                COUNT(DISTINCT nv.vlan_id) as vlan_count,
                -- Aggregate legacy VLANs
                STRING_AGG(DISTINCT 
                    CASE WHEN nv.vlan_id IN (1, 101, 201, 801) 
                    THEN nv.vlan_id::text 
                    END, ','
                ) as legacy_vlans_str,
                -- Get primary subnet for /16 calculation
                MAX(CASE 
                    WHEN nv.vlan_id = 1 THEN nv.subnet 
                    WHEN nv.vlan_id = 100 THEN nv.subnet 
                    WHEN nv.vlan_id = 900 THEN nv.subnet 
                END) as primary_subnet
            FROM meraki_inventory mi
            LEFT JOIN network_vlans nv ON mi.network_id = nv.network_id
            WHERE mi.device_model LIKE 'MX%'
            GROUP BY mi.network_id, mi.network_name, mi.device_tags
            HAVING COUNT(DISTINCT nv.vlan_id) > 0
        )
        SELECT 
            ns.*,
            -- Get all VLANs with names
            ARRAY_AGG(
                json_build_object(
                    'id', nv.vlan_id::text,
                    'name', COALESCE(nv.name, 'VLAN_' || nv.vlan_id),
                    'subnet', nv.subnet
                ) ORDER BY nv.vlan_id
            ) as all_vlans
        FROM network_summary ns
        JOIN network_vlans nv ON ns.network_id = nv.network_id
        GROUP BY ns.network_id, ns.network_name, ns.device_tags, 
                 ns.vlan_count, ns.legacy_vlans_str, ns.primary_subnet
        ORDER BY ns.network_name
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        networks = []
        for row in rows:
            network_id, network_name, device_tags, vlan_count, legacy_vlans_str, primary_subnet, all_vlans = row
            
            # Process legacy VLANs
            legacy_vlans = []
            if legacy_vlans_str:
                legacy_vlans = [v.strip() for v in legacy_vlans_str.split(',') if v and v.strip()]
            
            # Calculate /16 subnet
            subnet_16 = None
            if primary_subnet:
                try:
                    subnet_parts = primary_subnet.split('.')
                    if len(subnet_parts) >= 2:
                        subnet_16 = f"{subnet_parts[0]}.{subnet_parts[1]}.0.0/16"
                except:
                    pass
            
            # Parse tags (device_tags is already an array in DB)
            tags = []
            if device_tags:
                if isinstance(device_tags, list):
                    tags = device_tags
                elif isinstance(device_tags, str):
                    tags = [tag.strip() for tag in device_tags.split() if tag.strip()]
            
            # Determine migration status
            needs_migration = len(legacy_vlans) > 0
            
            # Create network info
            network_info = {
                'id': network_id,
                'name': network_name,
                'tags': tags,
                'subnet': primary_subnet,
                'subnet_16': subnet_16,
                'legacy_vlans': legacy_vlans,
                'all_vlans': all_vlans,
                'vlan_count': vlan_count,
                'needs_migration': needs_migration,
                'timezone': 'US/Arizona',
                'last_migration': None,
                'status': 'legacy' if needs_migration else 'migrated'
            }
            
            networks.append(network_info)
        
        return networks
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Test the function
    print("Fetching networks from database...")
    networks = get_networks_from_db()
    print(f"Found {len(networks)} networks")
    
    # Show some statistics
    needs_migration = len([n for n in networks if n['needs_migration']])
    print(f"Networks needing migration: {needs_migration}")
    
    # Show first few networks
    for i, network in enumerate(networks[:5]):
        print(f"\n{i+1}. {network['name']} ({network['id']})")
        print(f"   Subnet: {network.get('subnet_16', 'None')}")
        print(f"   Legacy VLANs: {network.get('legacy_vlans', [])}")
        print(f"   Needs migration: {network.get('needs_migration', False)}")