#!/usr/bin/env python3
"""
FIXED VERSION of nightly_meraki_enriched_db.py
Key fixes:
1. Uses meraki_inventory instead of meraki_live_data
2. Preserves existing DSR data - only updates when there's new/better data
3. Handles Cell provider correctly
4. Does NOT delete all data every night
"""

import os
import sys
import json
import requests
import re
import time
import logging
import ipaddress
import glob
import pandas as pd
from datetime import datetime, timezone
from fuzzywuzzy import fuzz
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the script directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/nightly-meraki-enriched-db.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
DATABASE_URI = Config.SQLALCHEMY_DATABASE_URI
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
ORG_NAME = "DTC-Store-Inventory-All"
BASE_URL = "https://api.meraki.com/api/v1"
DATA_DIR = "/var/www/html/meraki-data"
CIRCUITINFO_DIR = "/var/www/html/circuitinfo"

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Exclude tags - matches any tag containing these patterns
EXCLUDE_TAG_PATTERNS = ["hub", "lab", "voice", "test", "datacenter"]

# Provider normalization mapping (shortened for this example)
PROVIDER_MAPPING = {
    "spectrum": "Charter Communications",
    "cox business/boi": "Cox Communications",
    "at&t": "AT&T",
    "comcast": "Comcast",
    "verizon": "Verizon Business",
    "frontier": "Frontier Communications",
    "centurylink": "CenturyLink",
    # Add all other mappings from original file
}

def get_db_session():
    """Create database session"""
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)
    return Session()

def normalize_provider(provider_name, is_dsr=False):
    """Normalize provider names"""
    if not provider_name or provider_name == 'nan':
        return ''
    
    provider_str = str(provider_name).strip()
    
    # If speed is Cell but provider is empty/N/A, set provider to Cell
    if provider_str in ['', 'N/A', 'Unknown'] or provider_str.lower() == 'cell':
        return 'Cell'
    
    # Use mapping
    provider_lower = provider_str.lower()
    for key, value in PROVIDER_MAPPING.items():
        if key in provider_lower:
            return value
    
    return provider_str

def reformat_speed(speed, provider=''):
    """Reformat speed to consistent format"""
    if not speed or speed == 'nan' or speed == 'Unknown':
        return ''
    
    speed_str = str(speed).strip()
    
    # If speed is "Cell", return as is
    if speed_str == 'Cell':
        return 'Cell'
    
    # Handle satellite
    if 'satellite' in provider.lower() or 'starlink' in provider.lower():
        return 'Satellite'
    
    return speed_str

def normalize_cost(cost):
    """Normalize cost to currency format"""
    if not cost or cost == 'nan' or pd.isna(cost):
        return '$0.00'
    
    try:
        cost_float = float(cost)
        return f'${cost_float:.2f}'
    except:
        return '$0.00'

def load_tracking_data():
    """Load DSR tracking data from database"""
    session = get_db_session()
    try:
        # Get enabled circuits from database
        result = session.execute(text("""
            SELECT site_name, circuit_purpose, provider_name, 
                   details_ordered_service_speed, billing_monthly_cost,
                   ip_address_start, status
            FROM circuits
            WHERE status IN ('Enabled', 'Service Activated', 
                           'Enabled Using Existing Broadband', 
                           'Enabled/Disconnected', 'Enabled/Disconnect Pending')
            ORDER BY site_name, circuit_purpose
        """))
        
        data = []
        for row in result:
            data.append({
                'site_name': row[0],
                'circuit_purpose': row[1],
                'provider_name': row[2],
                'details_ordered_service_speed': row[3],
                'billing_monthly_cost': row[4],
                'ip_address_start': row[5],
                'status': row[6]
            })
        
        df = pd.DataFrame(data)
        logging.info(f"Loaded {len(df)} enabled circuits from database")
        return df
        
    except Exception as e:
        logging.error(f"Error loading tracking data: {e}")
        return pd.DataFrame()
    finally:
        session.close()

def enrich_meraki_data():
    """Main enrichment function - FIXED VERSION"""
    session = get_db_session()
    
    try:
        # Load DSR tracking data
        tracking_df = load_tracking_data()
        if tracking_df.empty:
            logging.error("No tracking data found")
            return False
        
        # Get all MX devices from meraki_inventory (NOT meraki_live_data)
        result = session.execute(text("""
            SELECT DISTINCT mi.network_name, mi.device_tags, mi.device_serial
            FROM meraki_inventory mi
            WHERE mi.device_model LIKE 'MX%'
            AND mi.network_name NOT ILIKE '%hub%'
            AND mi.network_name NOT ILIKE '%lab%'
            AND mi.network_name NOT ILIKE '%voice%'
            AND mi.network_name NOT ILIKE '%test%'
            AND mi.network_name NOT ILIKE '%datacenter%'
            AND mi.network_name NOT ILIKE '%store in a box%'
            AND (mi.device_tags IS NULL OR (
                NOT 'hub' = ANY(mi.device_tags) AND
                NOT 'Hub' = ANY(mi.device_tags) AND
                NOT 'lab' = ANY(mi.device_tags) AND
                NOT 'Lab' = ANY(mi.device_tags) AND
                NOT 'voice' = ANY(mi.device_tags) AND
                NOT 'Voice' = ANY(mi.device_tags) AND
                NOT 'test' = ANY(mi.device_tags) AND
                NOT 'Test' = ANY(mi.device_tags)
            ))
            ORDER BY mi.network_name
        """))
        
        networks = result.fetchall()
        logging.info(f"Processing {len(networks)} MX networks for enrichment")
        
        enriched_count = 0
        updated_count = 0
        preserved_count = 0
        
        for network_name, device_tags, device_serial in networks:
            # Get existing enriched data
            existing = session.execute(text("""
                SELECT wan1_provider, wan1_speed, wan1_monthly_cost,
                       wan2_provider, wan2_speed, wan2_monthly_cost,
                       wan1_confirmed, wan2_confirmed
                FROM enriched_circuits
                WHERE network_name = :network_name
            """), {'network_name': network_name}).fetchone()
            
            # Find matching DSR circuits
            network_normalized = re.sub(r'[^a-zA-Z0-9]', '', network_name.upper())
            tracking_matches = tracking_df[
                tracking_df['site_name'].apply(lambda x: re.sub(r'[^a-zA-Z0-9]', '', str(x).upper()) == network_normalized)
            ]
            
            # Prepare enriched data
            enriched = {
                'network_name': network_name,
                'device_tags': device_tags or [],
                'wan1_provider': '',
                'wan1_speed': '',
                'wan1_monthly_cost': '$0.00',
                'wan1_circuit_role': 'Primary',
                'wan1_confirmed': False,
                'wan2_provider': '',
                'wan2_speed': '',
                'wan2_monthly_cost': '$0.00',
                'wan2_circuit_role': 'Secondary',
                'wan2_confirmed': False
            }
            
            # Process DSR tracking matches
            if not tracking_matches.empty:
                # Look for primary circuit
                primary_matches = tracking_matches[
                    tracking_matches['circuit_purpose'].str.lower().str.contains('primary', na=False)
                ]
                if primary_matches.empty:
                    primary_matches = tracking_matches[
                        ~tracking_matches['circuit_purpose'].str.lower().str.contains('secondary|backup', na=False)
                    ]
                
                if not primary_matches.empty:
                    primary = primary_matches.iloc[0]
                    enriched['wan1_provider'] = normalize_provider(primary['provider_name'], True)
                    enriched['wan1_speed'] = reformat_speed(primary['details_ordered_service_speed'], enriched['wan1_provider'])
                    enriched['wan1_monthly_cost'] = normalize_cost(primary['billing_monthly_cost'])
                    enriched['wan1_confirmed'] = True
                
                # Look for secondary circuit
                secondary_matches = tracking_matches[
                    tracking_matches['circuit_purpose'].str.lower().str.contains('secondary|backup', na=False)
                ]
                
                if not secondary_matches.empty:
                    secondary = secondary_matches.iloc[0]
                    enriched['wan2_provider'] = normalize_provider(secondary['provider_name'], True)
                    enriched['wan2_speed'] = reformat_speed(secondary['details_ordered_service_speed'], enriched['wan2_provider'])
                    enriched['wan2_monthly_cost'] = normalize_cost(secondary['billing_monthly_cost'])
                    enriched['wan2_confirmed'] = True
            
            # Fix Cell provider when speed is Cell
            if enriched['wan1_speed'] == 'Cell' and not enriched['wan1_provider']:
                enriched['wan1_provider'] = 'Cell'
            if enriched['wan2_speed'] == 'Cell' and not enriched['wan2_provider']:
                enriched['wan2_provider'] = 'Cell'
            
            # CRITICAL: Preserve existing DSR data if no new data found
            if existing:
                # Preserve WAN1 if we don't have new DSR data
                if not enriched['wan1_confirmed'] and existing[0]:  # existing wan1_provider
                    enriched['wan1_provider'] = existing[0]
                    enriched['wan1_speed'] = existing[1]
                    enriched['wan1_monthly_cost'] = existing[2]
                    enriched['wan1_confirmed'] = existing[6]  # existing wan1_confirmed
                    preserved_count += 1
                
                # Preserve WAN2 if we don't have new DSR data
                if not enriched['wan2_confirmed'] and existing[3]:  # existing wan2_provider
                    enriched['wan2_provider'] = existing[3]
                    enriched['wan2_speed'] = existing[4]
                    enriched['wan2_monthly_cost'] = existing[5]
                    enriched['wan2_confirmed'] = existing[7]  # existing wan2_confirmed
                
                # Update existing record
                session.execute(text("""
                    UPDATE enriched_circuits
                    SET wan1_provider = :wan1_provider,
                        wan1_speed = :wan1_speed,
                        wan1_monthly_cost = :wan1_monthly_cost,
                        wan1_circuit_role = :wan1_circuit_role,
                        wan1_confirmed = :wan1_confirmed,
                        wan2_provider = :wan2_provider,
                        wan2_speed = :wan2_speed,
                        wan2_monthly_cost = :wan2_monthly_cost,
                        wan2_circuit_role = :wan2_circuit_role,
                        wan2_confirmed = :wan2_confirmed,
                        device_tags = :device_tags,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE network_name = :network_name
                """), enriched)
                updated_count += 1
            else:
                # Insert new record
                session.execute(text("""
                    INSERT INTO enriched_circuits (
                        network_name, device_tags, wan1_provider, wan1_speed, 
                        wan1_monthly_cost, wan1_circuit_role, wan1_confirmed,
                        wan2_provider, wan2_speed, wan2_monthly_cost, 
                        wan2_circuit_role, wan2_confirmed, last_updated
                    ) VALUES (
                        :network_name, :device_tags, :wan1_provider, :wan1_speed,
                        :wan1_monthly_cost, :wan1_circuit_role, :wan1_confirmed,
                        :wan2_provider, :wan2_speed, :wan2_monthly_cost,
                        :wan2_circuit_role, :wan2_confirmed, CURRENT_TIMESTAMP
                    )
                """), enriched)
                enriched_count += 1
        
        session.commit()
        logging.info(f"Enrichment complete: {enriched_count} new, {updated_count} updated, {preserved_count} preserved")
        return True
        
    except Exception as e:
        logging.error(f"Error during enrichment: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def main():
    """Main function"""
    logging.info("Starting FIXED nightly Meraki enrichment process")
    
    # Note: This script focuses only on enrichment
    # Meraki inventory collection should be done by nightly_inventory_db.py
    
    success = enrich_meraki_data()
    
    if success:
        logging.info("Enrichment completed successfully")
        
        # Fix any remaining Cell provider issues
        session = get_db_session()
        try:
            result = session.execute(text("""
                UPDATE enriched_circuits
                SET wan1_provider = 'Cell'
                WHERE wan1_speed = 'Cell' 
                AND (wan1_provider = '' OR wan1_provider IS NULL);
                
                UPDATE enriched_circuits
                SET wan2_provider = 'Cell'
                WHERE wan2_speed = 'Cell' 
                AND (wan2_provider = '' OR wan2_provider IS NULL);
            """))
            session.commit()
            logging.info("Fixed Cell provider issues")
        except Exception as e:
            logging.error(f"Error fixing Cell providers: {e}")
        finally:
            session.close()
    else:
        logging.error("Enrichment failed")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)