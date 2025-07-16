#!/usr/bin/env python3
"""
Import the enhanced inventory CSV (with proper FEX models) into the database
This replaces the non-enhanced data in inventory_web_format table
"""
import csv
import psycopg2
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsruser'
}

def get_site_from_hostname(hostname):
    """Determine site based on hostname patterns"""
    if not hostname:
        return 'Unknown'
    
    hostname_lower = hostname.lower()
    if hostname_lower.startswith(('ala-', 'al-')):
        return 'AZ-Alameda-DC'
    elif hostname_lower.startswith(('mdf-', 'n5k-', 'n7k-', '2960', 'hq-')):
        return 'AZ-Scottsdale-HQ-Corp'
    elif hostname_lower.startswith('fw-'):
        return 'AZ-Alameda-DC'  # Firewall switches
    elif hostname_lower.startswith('eqx-'):
        return 'Equinix-Seattle'
    elif 'dtc_phx' in hostname_lower:
        return 'AZ-Scottsdale-HQ-Corp'
    else:
        return 'Other'

def import_enhanced_csv():
    """Import the enhanced inventory CSV into the database"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Clear existing data
        logger.info("Clearing existing inventory_web_format data...")
        cursor.execute("TRUNCATE TABLE inventory_web_format")
        
        # Read and import the enhanced CSV
        with open('/usr/local/bin/Main/inventory_complete.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            
            row_order = 0
            parent_hostname = None
            imported_count = 0
            
            for row in reader:
                row_order += 1
                
                # Determine parent hostname
                if row['hostname']:  # This is a master device
                    parent_hostname = row['hostname']
                    site = get_site_from_hostname(row['hostname'])
                else:
                    site = get_site_from_hostname(parent_hostname)
                
                # Determine relationship based on position
                relationship = 'Standalone'
                if row['position'] == 'Parent Switch':
                    relationship = 'Parent'
                elif row['position'] == 'Master':
                    relationship = 'Master'
                elif row['position'] == 'Slave':
                    relationship = 'Slave'
                elif row['position'] in ['Module', 'SFP'] or row['position'].startswith('FEX-'):
                    relationship = 'Component'
                
                # Insert into database
                cursor.execute("""
                    INSERT INTO inventory_web_format 
                    (site, hostname, parent_hostname, relationship, ip_address, 
                     position, model, serial_number, port_location, vendor, 
                     notes, row_order)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    site,
                    row['hostname'] or None,
                    parent_hostname,
                    relationship,
                    row['ip_address'] or None,
                    row['position'],
                    row['model'],
                    row['serial_number'],
                    row['port_location'] or None,
                    row['vendor'] or 'Cisco',
                    None,  # notes
                    row_order
                ))
                
                imported_count += 1
                
                if imported_count % 100 == 0:
                    logger.info(f"Imported {imported_count} rows...")
        
        conn.commit()
        logger.info(f"✅ Successfully imported {imported_count} enhanced inventory records")
        
        # Verify import
        cursor.execute("SELECT COUNT(*) FROM inventory_web_format")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM inventory_web_format 
            WHERE model LIKE 'N2K-%'
        """)
        fex_count = cursor.fetchone()[0]
        
        logger.info(f"Total records in database: {total_count}")
        logger.info(f"FEX devices with proper models: {fex_count}")
        
        # Show sample FEX devices
        cursor.execute("""
            SELECT site, parent_hostname, position, model, serial_number 
            FROM inventory_web_format 
            WHERE model LIKE 'N2K-%' 
            LIMIT 5
        """)
        
        logger.info("\nSample FEX devices:")
        for row in cursor.fetchall():
            logger.info(f"  {row[0]} - {row[1]} - {row[2]}: {row[3]} ({row[4]})")
            
    except Exception as e:
        logger.error(f"Error importing enhanced inventory: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    logger.info("Starting enhanced inventory import...")
    import_enhanced_csv()
    logger.info("Enhanced inventory import complete!")