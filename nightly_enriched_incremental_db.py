#!/usr/bin/env python3
"""
INCREMENTAL Nightly Enriched Database Script
Only processes sites that have changed since last run
Tracks changes in WAN IPs, device notes, or DSR circuits
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timezone
import re
import json
from fuzzywuzzy import fuzz

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/nightly-enriched-incremental-db.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import all the functions from the full enrichment script
sys.path.insert(0, '/usr/local/bin/Main')
from nightly_enriched_db import (
    parse_raw_notes, normalize_provider_for_comparison, normalize_provider,
    compare_providers, reformat_speed, match_dsr_circuit_by_ip,
    match_dsr_circuit_by_provider, determine_final_provider, get_dsr_circuits
)

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(Config.SQLALCHEMY_DATABASE_URI)

def get_changed_sites(conn):
    """Get sites that have changed since last enrichment run"""
    cursor = conn.cursor()
    
    # Create change tracking table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enrichment_change_tracking (
            network_name VARCHAR(255) PRIMARY KEY,
            last_device_notes_hash VARCHAR(64),
            last_wan1_ip VARCHAR(45),
            last_wan2_ip VARCHAR(45),
            last_enrichment_run TIMESTAMP,
            dsr_circuits_hash VARCHAR(64)
        )
    """)
    
    # Get current state of all sites
    cursor.execute("""
        SELECT DISTINCT
            mi.network_name,
            mi.device_notes,
            mi.wan1_ip,
            mi.wan2_ip,
            md5(mi.device_notes || COALESCE(mi.wan1_ip, '') || COALESCE(mi.wan2_ip, '')) as current_hash,
            COALESCE(ect.last_device_notes_hash, '') as last_hash,
            COALESCE(ect.last_enrichment_run, '1970-01-01'::timestamp) as last_run
        FROM meraki_inventory mi
        LEFT JOIN enrichment_change_tracking ect ON mi.network_name = ect.network_name
        WHERE mi.device_model LIKE 'MX%'
        ORDER BY mi.network_name
    """)
    
    changed_sites = []
    all_sites = cursor.fetchall()
    
    for row in all_sites:
        network_name, device_notes, wan1_ip, wan2_ip, current_hash, last_hash, last_run = row
        
        # Check if site has changed
        if current_hash != last_hash:
            changed_sites.append({
                'network_name': network_name,
                'device_notes': device_notes,
                'wan1_ip': wan1_ip,
                'wan2_ip': wan2_ip,
                'current_hash': current_hash,
                'reason': 'Device notes or IP changed'
            })
    
    # Also check for DSR circuit changes
    cursor.execute("""
        SELECT DISTINCT site_name
        FROM circuits
        WHERE date_record_updated > (
            SELECT COALESCE(MAX(last_enrichment_run), '1970-01-01'::timestamp)
            FROM enrichment_change_tracking
        )
        AND status = 'Enabled'
    """)
    
    dsr_results = cursor.fetchall()
    logger.info(f"DSR query returned {len(dsr_results)} results")
    dsr_changed_sites = []
    for row in dsr_results:
        if row and len(row) > 0:
            dsr_changed_sites.append(row[0])
        else:
            logger.warning(f"Empty or invalid DSR result row: {row}")
    
    # Add DSR changed sites
    for i, site_name in enumerate(dsr_changed_sites):
        if i < 10:  # Log first 10 for debugging
            logger.info(f"Processing DSR site {i+1}: {site_name}")
        
        if not site_name:  # Skip empty site names
            logger.warning(f"Empty site name found at index {i}")
            continue
            
        if not any(site['network_name'].lower() == site_name.lower() for site in changed_sites):
            # Get device info for this site
            try:
                cursor.execute("""
                    SELECT device_notes, wan1_ip, wan2_ip
                    FROM meraki_inventory
                    WHERE LOWER(network_name) = LOWER(%s)
                    AND device_model LIKE 'MX%'
                    LIMIT 1
                """, (site_name,))
            except Exception as e:
                logger.error(f"Error querying Meraki inventory for site '{site_name}': {e}")
                continue
            
            device_info = cursor.fetchone()
            if device_info:
                changed_sites.append({
                    'network_name': site_name,
                    'device_notes': device_info[0],
                    'wan1_ip': device_info[1],
                    'wan2_ip': device_info[2],
                    'current_hash': '',
                    'reason': 'DSR circuit updated'
                })
            else:
                logger.info(f"DSR site {site_name} not found in Meraki inventory - skipping")
    
    cursor.close()
    return changed_sites

def update_change_tracking(conn, network_name, current_hash):
    """Update change tracking for a site"""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO enrichment_change_tracking 
        (network_name, last_device_notes_hash, last_enrichment_run)
        VALUES (%s, %s, CURRENT_TIMESTAMP)
        ON CONFLICT (network_name) DO UPDATE SET
            last_device_notes_hash = EXCLUDED.last_device_notes_hash,
            last_enrichment_run = EXCLUDED.last_enrichment_run
    """, (network_name, current_hash))
    cursor.close()

def enrich_changed_sites(conn, changed_sites):
    """Enrich only the sites that have changed"""
    if not changed_sites:
        logger.info("No changed sites found - nothing to process")
        return
    
    logger.info(f"Processing {len(changed_sites)} changed sites")
    
    # Get DSR circuits for all sites
    dsr_circuits_by_site = get_dsr_circuits(conn)
    
    enriched_data = []
    
    for site_info in changed_sites:
        network_name = site_info['network_name']
        device_notes = site_info['device_notes']
        wan1_ip = site_info['wan1_ip']
        wan2_ip = site_info['wan2_ip']
        
        logger.info(f"Processing {network_name}: {site_info['reason']}")
        
        # Skip excluded network names
        network_lower = network_name.lower()
        if any(pattern in network_lower for pattern in ['hub', 'lab', 'voice', 'datacenter', 'test', 'store in a box', 'sib']):
            logger.info(f"Skipping {network_name}: excluded network name")
            continue
            
        # Also check device notes for test indicators
        notes_lower = (device_notes or '').lower()
        if any(pattern in notes_lower for pattern in ['test store', 'test site', 'lab site', 'hub site', 'voice site']):
            logger.info(f"Skipping {network_name}: test/lab site")
            continue
        
        # Parse device notes
        wan1_notes, wan1_speed, wan2_notes, wan2_speed = parse_raw_notes(device_notes)
        
        # Get ARIN data from meraki_inventory (already available)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT wan1_arin_provider, wan2_arin_provider
                FROM meraki_inventory
                WHERE network_name = %s
                AND device_model LIKE 'MX%'
                LIMIT 1
            """, (network_name,))
        except Exception as e:
            logger.error(f"Error querying ARIN data for site '{network_name}': {e}")
            cursor.close()
            continue
        
        arin_data = cursor.fetchone()
        wan1_arin = arin_data[0] if arin_data and len(arin_data) > 0 else None
        wan2_arin = arin_data[1] if arin_data and len(arin_data) > 1 else None
        cursor.close()
        
        # Compare ARIN vs notes
        wan1_comparison = compare_providers(wan1_arin, wan1_notes)
        wan2_comparison = compare_providers(wan2_arin, wan2_notes)
        
        # Get DSR circuits for this site
        dsr_circuits = dsr_circuits_by_site.get(network_name, [])
        
        # Match DSR circuits by IP first, then by provider
        wan1_dsr = match_dsr_circuit_by_ip(dsr_circuits, wan1_ip)
        if not wan1_dsr:
            wan1_dsr = match_dsr_circuit_by_provider(dsr_circuits, wan1_notes)
        
        wan2_dsr = match_dsr_circuit_by_ip(dsr_circuits, wan2_ip)
        if not wan2_dsr:
            wan2_dsr = match_dsr_circuit_by_provider(dsr_circuits, wan2_notes)
        
        # Determine final providers
        wan1_provider, wan1_confirmed = determine_final_provider(
            wan1_notes, wan1_arin, wan1_comparison, wan1_dsr
        )
        wan2_provider, wan2_confirmed = determine_final_provider(
            wan2_notes, wan2_arin, wan2_comparison, wan2_dsr
        )
        
        # Format speeds - prefer DSR speeds when available, fall back to Meraki notes
        wan1_speed_to_use = wan1_dsr['speed'] if wan1_dsr and wan1_dsr.get('speed') else wan1_speed
        wan2_speed_to_use = wan2_dsr['speed'] if wan2_dsr and wan2_dsr.get('speed') else wan2_speed
        
        wan1_speed_final = reformat_speed(wan1_speed_to_use, wan1_provider)
        wan2_speed_final = reformat_speed(wan2_speed_to_use, wan2_provider)
        
        # Get roles (costs are handled by dsrcircuits.py from DSR data)
        wan1_role = wan1_dsr['purpose'] if wan1_dsr else "Primary"
        wan2_role = wan2_dsr['purpose'] if wan2_dsr else "Secondary"
        
        enriched_data.append({
            'network_name': network_name,
            'wan1_provider': wan1_provider,
            'wan1_speed': wan1_speed_final,
            'wan1_circuit_role': wan1_role,
            'wan1_confirmed': wan1_confirmed,
            'wan2_provider': wan2_provider,
            'wan2_speed': wan2_speed_final,
            'wan2_circuit_role': wan2_role,
            'wan2_confirmed': wan2_confirmed,
            'last_updated': datetime.now(timezone.utc).isoformat()
        })
        
        # Update change tracking
        update_change_tracking(conn, network_name, site_info.get('current_hash', ''))
    
    if enriched_data:
        # Update enriched_circuits table for changed sites only
        cursor = conn.cursor()
        
        for data in enriched_data:
            cursor.execute("""
                INSERT INTO enriched_circuits (
                    network_name, wan1_provider, wan1_speed, wan1_circuit_role, wan1_confirmed,
                    wan2_provider, wan2_speed, wan2_circuit_role, wan2_confirmed, last_updated
                ) VALUES (%(network_name)s, %(wan1_provider)s, %(wan1_speed)s, %(wan1_circuit_role)s, 
                         %(wan1_confirmed)s, %(wan2_provider)s, %(wan2_speed)s, %(wan2_circuit_role)s, 
                         %(wan2_confirmed)s, %(last_updated)s)
                ON CONFLICT (network_name) DO UPDATE SET
                    wan1_provider = EXCLUDED.wan1_provider,
                    wan1_speed = EXCLUDED.wan1_speed,
                    wan1_circuit_role = EXCLUDED.wan1_circuit_role,
                    wan1_confirmed = EXCLUDED.wan1_confirmed,
                    wan2_provider = EXCLUDED.wan2_provider,
                    wan2_speed = EXCLUDED.wan2_speed,
                    wan2_circuit_role = EXCLUDED.wan2_circuit_role,
                    wan2_confirmed = EXCLUDED.wan2_confirmed,
                    last_updated = EXCLUDED.last_updated
            """, data)
        
        conn.commit()
        cursor.close()
        
        logger.info(f"Successfully updated {len(enriched_data)} enriched circuits")

def main():
    """Main function - incremental processing only"""
    logger.info("=== Starting INCREMENTAL Nightly Enriched Database Script ===")
    logger.info("Processing only sites with changes since last run")
    
    try:
        conn = get_db_connection()
        
        # Get changed sites
        changed_sites = get_changed_sites(conn)
        
        if not changed_sites:
            logger.info("No changes detected - no processing needed")
        else:
            logger.info(f"Found {len(changed_sites)} sites with changes:")
            for site in changed_sites[:10]:  # Log first 10
                logger.info(f"  {site['network_name']}: {site['reason']}")
            if len(changed_sites) > 10:
                logger.info(f"  ... and {len(changed_sites) - 10} more")
            
            # Process only changed sites
            enrich_changed_sites(conn, changed_sites)
        
        conn.close()
        logger.info("=== Incremental Enrichment Complete ===")
        
    except Exception as e:
        import traceback
        logger.error(f"Error during incremental enrichment: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

if __name__ == "__main__":
    main()