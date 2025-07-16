#!/usr/bin/env python3
"""
Import the inventory_ultimate_final.csv into the database
This CSV has the properly deduplicated and enhanced data
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

def main():
    """Import the ultimate final CSV into the database"""
    
    # Database configuration
    db_config = {
        'host': 'localhost',
        'database': 'dsrcircuits',
        'user': 'dsruser',
        'password': 'T3dC$gLp9'
    }
    
    csv_file = '/usr/local/bin/Main/inventory_ultimate_final.csv'
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute("DELETE FROM inventory_web_format")
        logging.info("Cleared existing inventory_web_format data")
        
        # Read CSV file
        with open(csv_file, 'r') as f:
            csv_reader = csv.DictReader(f)
            
            # Insert each row
            insert_query = """
            INSERT INTO inventory_web_format 
            (hostname, parent_hostname, ip_address, position, model, serial_number, port_location, vendor, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            row_count = 0
            fex_models = {}
            current_parent = ''  # Track the current parent device
            
            for row in csv_reader:
                # Map CSV columns to database columns
                hostname = row.get('hostname', '')
                ip_address = row.get('ip_address', '')
                position = row.get('position', '')
                model = row.get('model', '')
                serial_number = row.get('serial_number', '')
                vendor = row.get('vendor', 'Cisco')
                
                # If hostname is present, this is a parent device
                if hostname:
                    current_parent = hostname
                    parent_hostname = ''
                else:
                    # This is a child component of the current parent
                    parent_hostname = current_parent
                
                # Combine description into notes if available
                description = row.get('description', '')
                notes = row.get('notes', description)
                
                cursor.execute(insert_query, (
                    hostname,
                    parent_hostname,
                    ip_address,
                    position,
                    model,
                    serial_number,
                    '',  # port_location
                    vendor,
                    notes
                ))
                
                row_count += 1
                
                # Track FEX models
                if position.startswith('FEX') and model.startswith('N2K'):
                    if model not in fex_models:
                        fex_models[model] = 0
                    fex_models[model] += 1
                
                if row_count % 100 == 0:
                    logging.info(f"Imported {row_count} rows...")
        
        conn.commit()
        logging.info(f"Successfully imported {row_count} rows to inventory_web_format")
        
        # Report FEX summary
        if fex_models:
            logging.info("FEX Model Summary:")
            for model, count in sorted(fex_models.items()):
                logging.info(f"  {model}: {count} units")
        
        # Check for duplicates
        cursor.execute("""
            SELECT serial_number, COUNT(*) as count 
            FROM inventory_web_format 
            WHERE serial_number IS NOT NULL 
            AND serial_number != '' 
            AND position LIKE 'FEX%'
            GROUP BY serial_number 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """)
        
        duplicates = cursor.fetchall()
        if duplicates:
            logging.warning("Found duplicate FEX serial numbers:")
            for serial, count in duplicates:
                logging.warning(f"  {serial}: {count} occurrences")
        else:
            logging.info("No duplicate FEX serial numbers found - deduplication successful!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logging.error(f"Import failed: {e}")
        raise

if __name__ == '__main__':
    main()