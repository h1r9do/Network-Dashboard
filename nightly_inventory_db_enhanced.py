#!/usr/bin/env python3
"""
Enhanced Full Inventory Collection Script - Database Version with EOL Integration
Collects ALL devices from ALL Meraki organizations and integrates with EOL database
"""

import os
import sys
import json
import requests
import time
import logging
import psycopg2
from psycopg2.extras import Json, execute_values
from datetime import datetime, timezone
from dotenv import load_dotenv
from collections import defaultdict

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"
HEADERS = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/nightly-inventory-db-enhanced.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection using config"""
    import re
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
    if not match:
        raise ValueError("Invalid database URI")
    
    user, password, host, port, database = match.groups()
    
    return psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password
    )

def meraki_get_paginated(url_base, key_type='serial'):
    """Get paginated results from Meraki API"""
    results, starting_after = [], None
    while True:
        url = f"{url_base}&perPage=1000"
        if starting_after:
            url += f"&startingAfter={starting_after}"
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code == 429:
            wait = int(resp.headers.get('Retry-After', 2))
            logger.warning(f"429 hit, waiting {wait}s")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        page = resp.json()
        if not page:
            break
        results.extend(page)
        if len(page) < 1000:
            break
        starting_after = page[-1].get(key_type)
    return results

def get_organizations():
    """Get all organizations"""
    logger.info("Fetching organizations...")
    return meraki_get_paginated(f"{BASE_URL}/organizations?", key_type='id')

def get_network_map(org_id):
    """Get network ID to name mapping for an organization"""
    logger.info(f"Getting networks for org {org_id}")
    url = f"{BASE_URL}/organizations/{org_id}/networks?"
    nets = meraki_get_paginated(url, key_type='id')
    return {n['id']: n['name'] for n in nets}

def get_inventory(org_id):
    """Get inventory for an organization"""
    logger.info(f"Getting inventory for org {org_id}")
    url = f"{BASE_URL}/organizations/{org_id}/inventory/devices?"
    return meraki_get_paginated(url, key_type='serial')

def get_eol_data_from_db(conn):
    """Get EOL data from the enhanced EOL database"""
    cursor = conn.cursor()
    eol_lookup = {}
    
    try:
        # Get the most recent EOL data for each model
        cursor.execute("""
            SELECT DISTINCT ON (model) 
                model,
                model_variants,
                announcement_date,
                end_of_sale_date,
                end_of_support_date,
                pdf_url,
                csv_source,
                pdf_source
            FROM meraki_eol
            ORDER BY model, updated_at DESC
        """)
        
        for row in cursor.fetchall():
            model = row[0]
            variants = row[1] if row[1] else [model]
            
            # Store data for primary model and all variants
            eol_data = {
                "announcement_date": row[2],
                "end_of_sale_date": row[3],
                "end_of_support_date": row[4],
                "pdf_url": row[5],
                "csv_source": row[6],
                "pdf_source": row[7]
            }
            
            # Add entry for main model
            eol_lookup[model] = eol_data
            
            # Also add entries for all variants
            for variant in variants:
                if variant and variant != model:
                    eol_lookup[variant] = eol_data
        
        logger.info(f"Loaded EOL data for {len(eol_lookup)} models from database")
        
        # Also check for pattern-based matches
        cursor.execute("""
            SELECT model, model_variants, announcement_date, end_of_sale_date, end_of_support_date
            FROM meraki_eol
            WHERE model LIKE '%-%'
            ORDER BY LENGTH(model) DESC
        """)
        
        pattern_models = cursor.fetchall()
        
        return eol_lookup, pattern_models
        
    except Exception as e:
        logger.error(f"Error loading EOL data: {e}")
        return {}, []
    finally:
        cursor.close()

def normalize_model(m):
    """Normalize model name"""
    return m.strip().upper() if m else ""

def get_eol_for_model(model, eol_lookup, pattern_models):
    """Get EOL data for a specific model with improved matching"""
    model = normalize_model(model)
    
    # Direct match
    if model in eol_lookup:
        return eol_lookup[model]
    
    # Try pattern matching for complex models
    for pattern_model, variants, ann_date, eos_date, eol_date in pattern_models:
        # Check if model starts with the pattern
        if model.startswith(pattern_model.replace('-HW', '')):
            return {
                "announcement_date": ann_date,
                "end_of_sale_date": eos_date,
                "end_of_support_date": eol_date
            }
        
        # Check variants
        if variants:
            for variant in variants:
                if model == variant or model.startswith(variant.replace('-HW', '')):
                    return {
                        "announcement_date": ann_date,
                        "end_of_sale_date": eos_date,
                        "end_of_support_date": eol_date
                    }
    
    # No match found
    return {
        "announcement_date": None,
        "end_of_sale_date": None,
        "end_of_support_date": None
    }

def create_inventory_tables(conn):
    """Create/verify inventory tables"""
    cursor = conn.cursor()
    
    try:
        # Create inventory_devices table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_devices (
                id SERIAL PRIMARY KEY,
                serial VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(200),
                model VARCHAR(50),
                mac VARCHAR(20),
                network_id VARCHAR(50),
                network_name VARCHAR(200),
                organization VARCHAR(200),
                product_type VARCHAR(50),
                tags TEXT,
                notes TEXT,
                lan_ip VARCHAR(45),
                firmware VARCHAR(50),
                details JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create enhanced inventory_summary table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_summary (
                id SERIAL PRIMARY KEY,
                model VARCHAR(50) UNIQUE NOT NULL,
                total_count INTEGER DEFAULT 0,
                org_counts JSONB,
                announcement_date DATE,
                end_of_sale DATE,
                end_of_support DATE,
                highlight VARCHAR(50),
                eol_source VARCHAR(20),  -- 'pdf', 'csv', 'both', 'none'
                eol_confidence VARCHAR(20),  -- 'exact', 'pattern', 'none'
                last_updated TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_devices_serial ON inventory_devices(serial)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_devices_model ON inventory_devices(model)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_devices_organization ON inventory_devices(organization)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_summary_model ON inventory_summary(model)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventory_summary_highlight ON inventory_summary(highlight)")
        
        conn.commit()
        logger.info("Inventory tables created/verified")
        
    except Exception as e:
        logger.warning(f"Table/Index creation warning: {e}")
        conn.rollback()
    finally:
        cursor.close()

def process_inventory(conn):
    """Process inventory from all organizations"""
    cursor = conn.cursor()
    
    try:
        # Get all organizations
        orgs = get_organizations()
        logger.info(f"Found {len(orgs)} organizations")
        
        # Get EOL data from database
        eol_lookup, pattern_models = get_eol_data_from_db(conn)
        
        # Track device counts
        summary_counter = defaultdict(lambda: defaultdict(int))
        all_devices = []
        org_names = []
        
        # Process each organization
        for org in orgs:
            org_id = org['id']
            org_name = org['name']
            logger.info(f"\nProcessing organization: {org_name}")
            org_names.append(org_name)
            
            try:
                # Get networks for this org
                networks = get_network_map(org_id)
                
                # Get inventory for this org
                inventory = get_inventory(org_id)
                logger.info(f"Found {len(inventory)} devices in {org_name}")
                
                # Process each device
                for device in inventory:
                    model = normalize_model(device.get('model', ''))
                    serial = device.get('serial', '')
                    
                    if not serial:
                        continue
                    
                    # Get network name
                    network_id = device.get('networkId')
                    network_name = networks.get(network_id, 'Unassigned') if network_id else 'Unassigned'
                    
                    # Count by model and org
                    if model:
                        summary_counter[model][org_name] += 1
                    
                    # Prepare device data
                    device_data = {
                        'serial': serial,
                        'name': device.get('name', ''),
                        'model': model,
                        'mac': device.get('mac', ''),
                        'network_id': network_id or '',
                        'network_name': network_name,
                        'organization': org_name,
                        'product_type': device.get('productType', model),
                        'tags': json.dumps(device.get('tags', [])) if device.get('tags') else '[]',
                        'notes': device.get('notes', ''),
                        'lan_ip': device.get('lanIp', ''),
                        'firmware': device.get('firmware', ''),
                        'details': Json(device)
                    }
                    
                    all_devices.append(device_data)
                
            except Exception as e:
                logger.error(f"Failed to process {org_name}: {e}")
                continue
            
            time.sleep(1)  # Rate limiting
        
        # Insert all devices
        if all_devices:
            logger.info(f"Inserting {len(all_devices)} devices into database...")
            
            # Clear existing data
            cursor.execute("DELETE FROM inventory_devices")
            
            # Bulk upsert
            for device in all_devices:
                cursor.execute("""
                    INSERT INTO inventory_devices (
                        serial, name, model, mac, network_id, network_name,
                        organization, product_type, tags, notes, lan_ip, 
                        firmware, details
                    ) VALUES (
                        %(serial)s, %(name)s, %(model)s, %(mac)s, %(network_id)s,
                        %(network_name)s, %(organization)s, %(product_type)s,
                        %(tags)s, %(notes)s, %(lan_ip)s, %(firmware)s, %(details)s
                    )
                    ON CONFLICT (serial) DO UPDATE SET
                        name = EXCLUDED.name,
                        model = EXCLUDED.model,
                        mac = EXCLUDED.mac,
                        network_id = EXCLUDED.network_id,
                        network_name = EXCLUDED.network_name,
                        organization = EXCLUDED.organization,
                        product_type = EXCLUDED.product_type,
                        tags = EXCLUDED.tags,
                        notes = EXCLUDED.notes,
                        lan_ip = EXCLUDED.lan_ip,
                        firmware = EXCLUDED.firmware,
                        details = EXCLUDED.details
                """, device)
            
            logger.info(f"Inserted {len(all_devices)} devices")
        
        # Create inventory summary with enhanced EOL data
        logger.info("Creating inventory summary with enhanced EOL data...")
        
        # Clear existing summary
        cursor.execute("DELETE FROM inventory_summary")
        
        # Get today's date for EOL comparisons
        today = datetime.today().date()
        
        # Process each model
        for model, org_counts in summary_counter.items():
            total_count = sum(org_counts.values())
            
            # Get EOL data with improved matching
            eol_info = get_eol_for_model(model, eol_lookup, pattern_models)
            
            # Determine EOL source and confidence
            eol_source = 'none'
            eol_confidence = 'none'
            
            if model in eol_lookup:
                eol_confidence = 'exact'
                if eol_lookup[model].get('pdf_source') and eol_lookup[model].get('csv_source'):
                    eol_source = 'both'
                elif eol_lookup[model].get('pdf_source'):
                    eol_source = 'pdf'
                elif eol_lookup[model].get('csv_source'):
                    eol_source = 'csv'
            elif eol_info['end_of_sale_date'] is not None:
                eol_confidence = 'pattern'
                eol_source = 'pattern'
            
            # Determine highlight status
            highlight = ""
            if eol_info['end_of_sale_date'] and eol_info['end_of_sale_date'] <= today:
                highlight = "eos"
            if eol_info['end_of_support_date'] and eol_info['end_of_support_date'] <= today:
                highlight = "eol"
            
            # Insert summary
            cursor.execute("""
                INSERT INTO inventory_summary (
                    model, total_count, org_counts,
                    announcement_date, end_of_sale, end_of_support,
                    highlight, eol_source, eol_confidence, last_updated
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                model,
                total_count,
                Json(dict(org_counts)),
                eol_info['announcement_date'],
                eol_info['end_of_sale_date'],
                eol_info['end_of_support_date'],
                highlight,
                eol_source,
                eol_confidence
            ))
        
        logger.info(f"Created summary for {len(summary_counter)} models")
        
        # Log enhanced summary stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total_models,
                COUNT(*) FILTER (WHERE eol_confidence = 'exact') as exact_matches,
                COUNT(*) FILTER (WHERE eol_confidence = 'pattern') as pattern_matches,
                COUNT(*) FILTER (WHERE eol_confidence = 'none') as no_matches,
                COUNT(*) FILTER (WHERE highlight = 'eos') as eos_models,
                COUNT(*) FILTER (WHERE highlight = 'eol') as eol_models
            FROM inventory_summary
        """)
        
        stats = cursor.fetchone()
        logger.info(f"""
Enhanced Inventory Summary:
- Total Models: {stats[0]}
- Exact EOL Matches: {stats[1]}
- Pattern EOL Matches: {stats[2]}
- No EOL Data: {stats[3]}
- End-of-Sale Models: {stats[4]}
- End-of-Support Models: {stats[5]}
        """)
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"Error processing inventory: {e}")
        import traceback
        logger.error(traceback.format_exc())
        conn.rollback()
        return False
    finally:
        cursor.close()

def main():
    """Main execution function"""
    logger.info("Starting enhanced full inventory collection process")
    
    try:
        # Get database connection
        conn = get_db_connection()
        
        # Create tables if needed
        create_inventory_tables(conn)
        
        # Process inventory
        success = process_inventory(conn)
        
        if success:
            logger.info("Enhanced inventory collection completed successfully")
        else:
            logger.error("Enhanced inventory collection failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()