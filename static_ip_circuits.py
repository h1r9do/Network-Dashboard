#!/usr/bin/env python3
"""
Generate CSV file with site names, interfaces, and provider names for circuits with static IP addresses
"""

import csv
import psycopg2
from psycopg2.extras import RealDictCursor
import sys

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='dsrcircuits',
            user='dsruser',
            password='dsrpass123'
        )
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

def query_static_ip_circuits():
    """Query circuits with static IP addresses"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query for static IP circuits from meraki_inventory and enriched_circuits with discount-tire tag
        query = """
        SELECT DISTINCT
            mi.network_name as site_name,
            'WAN1' as interface,
            mi.wan1_ip as ip_address,
            COALESCE(
                NULLIF(ec.wan1_provider, ''), 
                NULLIF(mi.wan1_provider_label, ''), 
                NULLIF(mi.wan1_arin_provider, ''), 
                rc1.provider_name, 
                'Unknown'
            ) as provider_name,
            mi.wan1_assignment as ip_assignment_status,
            CASE 
                WHEN c.provider_name IS NOT NULL THEN 'DSR'
                ELSE 'Non-DSR'
            END as circuit_type
        FROM meraki_inventory mi
        LEFT JOIN enriched_circuits ec ON mi.network_name = ec.network_name
        LEFT JOIN rdap_cache rc1 ON mi.wan1_ip = rc1.ip_address
        LEFT JOIN circuits c ON (mi.network_name = c.site_name OR mi.network_name = c.site_id)
                            AND c.provider_name = COALESCE(
                                NULLIF(ec.wan1_provider, ''), 
                                NULLIF(mi.wan1_provider_label, ''), 
                                NULLIF(mi.wan1_arin_provider, ''), 
                                rc1.provider_name
                            )
        WHERE mi.wan1_assignment = 'static' 
          AND mi.wan1_ip IS NOT NULL 
          AND mi.wan1_ip != ''
          AND mi.wan1_ip != '0.0.0.0'
          AND 'Discount-Tire' = ANY(mi.device_tags)
        
        UNION ALL
        
        SELECT DISTINCT
            mi.network_name as site_name,
            'WAN2' as interface,
            mi.wan2_ip as ip_address,
            COALESCE(
                NULLIF(ec.wan2_provider, ''), 
                NULLIF(mi.wan2_provider_label, ''), 
                NULLIF(mi.wan2_arin_provider, ''), 
                rc2.provider_name, 
                'Unknown'
            ) as provider_name,
            mi.wan2_assignment as ip_assignment_status,
            CASE 
                WHEN c.provider_name IS NOT NULL THEN 'DSR'
                ELSE 'Non-DSR'
            END as circuit_type
        FROM meraki_inventory mi
        LEFT JOIN enriched_circuits ec ON mi.network_name = ec.network_name
        LEFT JOIN rdap_cache rc2 ON mi.wan2_ip = rc2.ip_address
        LEFT JOIN circuits c ON (mi.network_name = c.site_name OR mi.network_name = c.site_id)
                            AND c.provider_name = COALESCE(
                                NULLIF(ec.wan2_provider, ''), 
                                NULLIF(mi.wan2_provider_label, ''), 
                                NULLIF(mi.wan2_arin_provider, ''), 
                                rc2.provider_name
                            )
        WHERE mi.wan2_assignment = 'static' 
          AND mi.wan2_ip IS NOT NULL 
          AND mi.wan2_ip != ''
          AND mi.wan2_ip != '0.0.0.0'
          AND 'Discount-Tire' = ANY(mi.device_tags)
        
        ORDER BY site_name, interface;
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return results
        
    except Exception as e:
        print(f"Query failed: {e}")
        if conn:
            conn.close()
        return []

def generate_csv(results, filename='static_ip_circuits.csv'):
    """Generate CSV file from query results"""
    if not results:
        print("No static IP circuits found")
        return
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['site_name', 'interface', 'ip_address', 'provider_name', 'ip_assignment_status', 'circuit_type']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write data rows
            for row in results:
                writer.writerow({
                    'site_name': row['site_name'],
                    'interface': row['interface'],
                    'ip_address': row['ip_address'],
                    'provider_name': row['provider_name'],
                    'ip_assignment_status': row['ip_assignment_status'],
                    'circuit_type': row['circuit_type']
                })
        
        print(f"CSV file generated: {filename}")
        print(f"Total rows: {len(results)}")
        
    except Exception as e:
        print(f"CSV generation failed: {e}")

def main():
    """Main function"""
    print("Querying static IP circuits...")
    results = query_static_ip_circuits()
    
    if results:
        generate_csv(results)
        
        # Show preview of first 10 rows
        print("\nPreview of first 10 rows:")
        print("Site Name | Interface | IP Address | Provider | Assignment | Type")
        print("-" * 90)
        for i, row in enumerate(results[:10]):
            print(f"{row['site_name']:<15} | {row['interface']:<9} | {row['ip_address']:<15} | {row['provider_name']:<20} | {row['ip_assignment_status']:<10} | {row['circuit_type']}")
        
        if len(results) > 10:
            print(f"... and {len(results) - 10} more rows")
    else:
        print("No static IP circuits found or query failed")

if __name__ == "__main__":
    main()