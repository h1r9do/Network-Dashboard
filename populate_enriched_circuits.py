#!/usr/bin/env python3
"""
Populate enriched_circuits table from enriched_networks data
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import execute_values

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=int(os.environ.get('DB_PORT', 5432)),
        database=os.environ.get('DB_NAME', 'dsrcircuits'),
        user=os.environ.get('DB_USER', 'dsruser'),
        password=os.environ.get('DB_PASSWORD', 'dsrpass123')
    )

def main():
    """Populate enriched_circuits from enriched_networks"""
    logger.info("Starting enriched_circuits population")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get unique networks from enriched_networks
        cursor.execute("""
            SELECT DISTINCT network_name 
            FROM enriched_networks 
            WHERE network_name IS NOT NULL
            ORDER BY network_name
        """)
        networks = cursor.fetchall()
        logger.info(f"Found {len(networks)} unique networks")
        
        # Clear existing enriched_circuits
        cursor.execute("TRUNCATE TABLE enriched_circuits")
        logger.info("Cleared enriched_circuits table")
        
        enriched_data = []
        
        for (network_name,) in networks:
            # Get circuits for this network
            cursor.execute("""
                SELECT site_name, status, provider_name, circuit_purpose, 
                       service_speed, monthly_cost
                FROM enriched_networks 
                WHERE network_name = %s
                ORDER BY circuit_purpose
            """, (network_name,))
            
            network_circuits = cursor.fetchall()
            
            # Initialize data
            wan1_data = {
                'provider': '',
                'speed': '',
                'cost': '$0.00',
                'role': 'Primary',
                'confirmed': False
            }
            wan2_data = {
                'provider': '',
                'speed': '',
                'cost': '$0.00',
                'role': 'Secondary',
                'confirmed': False
            }
            
            # Process circuits
            for circuit in network_circuits:
                site_name, status, provider, purpose, speed, cost = circuit
                
                # Format cost
                if cost:
                    try:
                        cost_str = f"${float(cost):.2f}"
                    except:
                        cost_str = "$0.00"
                else:
                    cost_str = "$0.00"
                
                # Assign to WAN1 or WAN2
                if purpose and purpose.lower() == 'primary' and not wan1_data['provider']:
                    wan1_data = {
                        'provider': provider or '',
                        'speed': speed or '',
                        'cost': cost_str,
                        'role': 'Primary',
                        'confirmed': True
                    }
                elif purpose and purpose.lower() == 'secondary' and not wan2_data['provider']:
                    wan2_data = {
                        'provider': provider or '',
                        'speed': speed or '',
                        'cost': cost_str,
                        'role': 'Secondary',
                        'confirmed': True
                    }
            
            # Add to enriched data
            enriched_record = (
                network_name,  # network_name
                [],  # device_tags (empty for now)
                wan1_data['provider'],  # wan1_provider
                wan1_data['speed'],  # wan1_speed
                wan1_data['cost'],  # wan1_monthly_cost
                wan1_data['role'],  # wan1_circuit_role
                wan1_data['confirmed'],  # wan1_confirmed
                wan2_data['provider'],  # wan2_provider
                wan2_data['speed'],  # wan2_speed
                wan2_data['cost'],  # wan2_monthly_cost
                wan2_data['role'],  # wan2_circuit_role
                wan2_data['confirmed']  # wan2_confirmed
            )
            
            enriched_data.append(enriched_record)
        
        # Insert into enriched_circuits
        if enriched_data:
            insert_sql = """
                INSERT INTO enriched_circuits (
                    network_name, device_tags,
                    wan1_provider, wan1_speed, wan1_monthly_cost, 
                    wan1_circuit_role, wan1_confirmed,
                    wan2_provider, wan2_speed, wan2_monthly_cost,
                    wan2_circuit_role, wan2_confirmed
                ) VALUES %s
            """
            
            execute_values(cursor, insert_sql, enriched_data)
            conn.commit()
            
            logger.info(f"Inserted {len(enriched_data)} enriched circuit records")
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM enriched_circuits")
        count = cursor.fetchone()[0]
        logger.info(f"Enriched_circuits table now has {count} records")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()