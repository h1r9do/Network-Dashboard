#!/usr/bin/env python3
"""
Cisco EoL CSV Lookup Script
===========================

This script provides a template for looking up EoL data from CSV files
or manual research results. It's designed to be populated with data
from Cisco's official EoL notices.
"""

import os
import csv
import psycopg2
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'T3dC$gLp9'
}

def load_models_from_file(filepath):
    """Load model numbers from text file"""
    models = []
    with open(filepath, 'r') as f:
        for line in f:
            model = line.strip()
            if model and not model.startswith('#'):
                models.append(model)
    return models

def create_csv_template(models, output_file):
    """Create a CSV template for manual EoL data entry"""
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = [
            'model', 'vendor', 'device_type', 'category',
            'announcement_date', 'end_of_sale_date', 'end_of_support_date',
            'end_sw_maintenance_date', 'last_support_date', 'notes', 'source_url'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for model in models:
            # Pre-fill vendor and basic device type
            vendor = 'Arista' if 'DCS-' in model else 'Cisco'
            
            device_type = 'Unknown'
            if any(x in model for x in ['WS-C', 'CBS']):
                device_type = 'Switch'
            elif any(x in model for x in ['C8300', 'C8500', 'CISCO3945', 'VG']):
                device_type = 'Router'
            elif any(x in model for x in ['N2K-', 'N5K-', 'N7K-', 'N9K-']):
                device_type = 'Nexus'
            elif any(x in model for x in ['C9400-LC', 'WS-X4', 'N7K-F', 'N56-M']):
                device_type = 'Line Card'
            elif any(x in model for x in ['SUP', 'SPE']):
                device_type = 'Supervisor/Engine'
            elif any(x in model for x in ['PVDM', 'SM-D', 'NIM']):
                device_type = 'Module'
            elif model.startswith('800-'):
                device_type = 'Accessory'
                
            writer.writerow({
                'model': model,
                'vendor': vendor,
                'device_type': device_type,
                'category': '',
                'announcement_date': '',
                'end_of_sale_date': '',
                'end_of_support_date': '',
                'end_sw_maintenance_date': '',
                'last_support_date': '',
                'notes': '',
                'source_url': ''
            })
    
    logger.info(f"Created CSV template: {output_file}")
    logger.info(f"Please fill in the EoL dates and run with --import flag")

def import_csv_data(csv_file):
    """Import EoL data from filled CSV file"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    imported = 0
    skipped = 0
    errors = 0
    
    with open(csv_file, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            try:
                # Skip rows without EoL data
                if not row['end_of_sale_date'] and not row['end_of_support_date']:
                    skipped += 1
                    continue
                    
                # Parse dates
                dates = {}
                for date_field in ['announcement_date', 'end_of_sale_date', 'end_of_support_date']:
                    if row[date_field]:
                        dates[date_field] = parse_date(row[date_field])
                    else:
                        dates[date_field] = None
                        
                # Check if model exists
                cursor.execute("SELECT id FROM corporate_eol WHERE model = %s", (row['model'],))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing
                    cursor.execute("""
                        UPDATE corporate_eol 
                        SET vendor = %s,
                            device_type = %s,
                            category = %s,
                            announcement_date = %s,
                            end_of_sale_date = %s,
                            end_of_support_date = %s,
                            source = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE model = %s
                    """, (
                        row['vendor'],
                        row['device_type'],
                        row['category'],
                        dates['announcement_date'],
                        dates['end_of_sale_date'],
                        dates['end_of_support_date'],
                        'csv_import',
                        row['model']
                    ))
                else:
                    # Insert new
                    cursor.execute("""
                        INSERT INTO corporate_eol 
                        (model, vendor, device_type, category, announcement_date,
                         end_of_sale_date, end_of_support_date, source)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        row['model'],
                        row['vendor'],
                        row['device_type'],
                        row['category'],
                        dates['announcement_date'],
                        dates['end_of_sale_date'],
                        dates['end_of_support_date'],
                        'csv_import'
                    ))
                    
                imported += 1
                logger.info(f"Imported: {row['model']} (EoS: {dates['end_of_sale_date']}, EoL: {dates['end_of_support_date']})")
                
            except Exception as e:
                logger.error(f"Error importing {row['model']}: {e}")
                errors += 1
                conn.rollback()
                continue
                
        conn.commit()
        
    cursor.close()
    conn.close()
    
    logger.info(f"\nImport Summary:")
    logger.info(f"  Imported: {imported}")
    logger.info(f"  Skipped (no dates): {skipped}")
    logger.info(f"  Errors: {errors}")

def parse_date(date_str):
    """Parse various date formats"""
    if not date_str:
        return None
        
    # Try common formats
    formats = [
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%d/%m/%Y',
        '%B %d, %Y',
        '%b %d, %Y',
        '%d-%b-%Y'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
            
    logger.warning(f"Could not parse date: {date_str}")
    return None

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Cisco EoL CSV Lookup Tool')
    parser.add_argument('--create-template', action='store_true',
                       help='Create CSV template for manual data entry')
    parser.add_argument('--import', dest='import_csv',
                       help='Import EoL data from filled CSV file')
    parser.add_argument('--models-file', default='/usr/local/bin/Main/datacenter_models_list.txt',
                       help='Path to models list file')
    parser.add_argument('--output', default='/usr/local/bin/Main/cisco_eol_template.csv',
                       help='Output CSV file path')
    
    args = parser.parse_args()
    
    if args.create_template:
        models = load_models_from_file(args.models_file)
        create_csv_template(models, args.output)
        
        logger.info("\nNext steps:")
        logger.info("1. Open the CSV file and fill in EoL dates")
        logger.info("2. You can find EoL dates at:")
        logger.info("   - https://www.cisco.com/c/en/us/support/eol/eos-eol-listings.html")
        logger.info("   - https://www.cisco.com/c/en/us/products/eos-eol-listing.html")
        logger.info("3. Run: python3 cisco_eol_csv_lookup.py --import cisco_eol_template.csv")
        
    elif args.import_csv:
        if not os.path.exists(args.import_csv):
            logger.error(f"CSV file not found: {args.import_csv}")
            return
        import_csv_data(args.import_csv)
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()