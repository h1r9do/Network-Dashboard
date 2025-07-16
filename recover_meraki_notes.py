#!/usr/bin/env python3
"""
Recover Meraki notes from git history and apply proper enrichment logic
Uses June 24th data as source of truth
"""

import json
import subprocess
import sys
import re
import ipaddress
import requests
import time
from datetime import datetime
sys.path.insert(0, '/usr/local/bin/Main')
from nightly_meraki_db import get_db_connection, parse_raw_notes, get_provider_for_ip, KNOWN_IPS, compare_providers
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_historical_meraki_data(date="2025-06-24"):
    """Get Meraki inventory from git history"""
    logger.info(f"Retrieving historical Meraki data from {date}")
    
    # Get the commit hash for the date
    cmd = f"git -C /var/www/html/meraki-data log --since='{date} 00:00' --until='{date} 23:59' --oneline -- mx_inventory_live.json | head -1 | cut -d' ' -f1"
    commit_hash = subprocess.check_output(cmd, shell=True).decode().strip()
    
    if not commit_hash:
        logger.error(f"No commits found for {date}")
        return None
    
    logger.info(f"Using commit {commit_hash} from {date}")
    
    # Get the file content from that commit
    cmd = f"git -C /var/www/html/meraki-data show {commit_hash}:mx_inventory_live.json"
    json_content = subprocess.check_output(cmd, shell=True).decode()
    
    return json.loads(json_content)

def get_enabled_circuits_from_db():
    """Get only ENABLED circuits from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT site_name, circuit_purpose, provider_name, 
               details_ordered_service_speed, billing_monthly_cost, status
        FROM circuits
        WHERE LOWER(status) = 'enabled'
        ORDER BY site_name, circuit_purpose
    """)
    
    circuits = {}
    for row in cursor.fetchall():
        site_name = row[0]
        if site_name not in circuits:
            circuits[site_name] = {}
        
        purpose = 'wan1' if 'primary' in row[1].lower() else 'wan2'
        circuits[site_name][purpose] = {
            'provider': row[2] or '',
            'speed': row[3] or '',
            'cost': row[4] or 0,
            'status': row[5]
        }
    
    cursor.close()
    conn.close()
    
    logger.info(f"Loaded {len(circuits)} sites with enabled circuits")
    return circuits

def determine_final_provider(notes_provider, arin_provider, comparison, dsr_provider=None):
    """Apply the old logic hierarchy to determine final provider"""
    
    # If we have a valid DSR provider from an ENABLED circuit, that takes precedence
    if dsr_provider and dsr_provider.strip() and dsr_provider.lower() != 'unknown':
        return dsr_provider
    
    # Otherwise apply the comparison logic
    if comparison == "No match" and notes_provider:
        # Trust the notes over ARIN when they disagree
        return notes_provider
    elif arin_provider and arin_provider != "Unknown" and arin_provider != "Private IP":
        # Use ARIN when available and matches or no notes
        return arin_provider
    elif notes_provider:
        # Fall back to notes
        return notes_provider
    else:
        return "Unknown"

def recover_and_update():
    """Main recovery function"""
    
    # Get historical data
    historical_data = get_historical_meraki_data("2025-06-24")
    if not historical_data:
        logger.error("Failed to get historical data")
        return
    
    logger.info(f"Found {len(historical_data)} devices in historical data")
    
    # Get current enabled circuits
    enabled_circuits = get_enabled_circuits_from_db()
    
    # Get database connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Cache for IP lookups
    ip_cache = {}
    missing_ips = set()
    
    # Process each device
    updated_count = 0
    for device in historical_data:
        network_name = device.get('network_name', '')
        device_serial = device.get('device_serial', '')
        raw_notes = device.get('raw_notes', '')
        
        if not device_serial or not device.get('device_model', '').startswith('MX'):
            continue
        
        # Parse the historical raw notes
        wan1_label, wan1_speed_label, wan2_label, wan2_speed_label = parse_raw_notes(raw_notes)
        
        # Get IPs from device data
        wan1_ip = device.get('wan1', {}).get('ip', '')
        wan2_ip = device.get('wan2', {}).get('ip', '')
        
        # Get ARIN providers
        wan1_arin = get_provider_for_ip(wan1_ip, ip_cache, missing_ips) if wan1_ip else "Unknown"
        wan2_arin = get_provider_for_ip(wan2_ip, ip_cache, missing_ips) if wan2_ip else "Unknown"
        
        # Compare providers
        wan1_comparison = compare_providers(wan1_arin, wan1_label) if wan1_label else None
        wan2_comparison = compare_providers(wan2_arin, wan2_label) if wan2_label else None
        
        # Get DSR data if available (ENABLED only)
        dsr_data = enabled_circuits.get(network_name, {})
        wan1_dsr = dsr_data.get('wan1', {}).get('provider', '')
        wan2_dsr = dsr_data.get('wan2', {}).get('provider', '')
        
        # Determine final providers using the hierarchy
        wan1_final = determine_final_provider(wan1_label, wan1_arin, wan1_comparison, wan1_dsr)
        wan2_final = determine_final_provider(wan2_label, wan2_arin, wan2_comparison, wan2_dsr)
        
        # Update the database with recovered data
        cursor.execute("""
            UPDATE meraki_inventory
            SET device_notes = %s,
                wan1_provider_label = %s,
                wan1_speed_label = %s,
                wan2_provider_label = %s,
                wan2_speed_label = %s,
                wan1_arin_provider = %s,
                wan2_arin_provider = %s,
                wan1_provider_comparison = %s,
                wan2_provider_comparison = %s,
                last_updated = NOW()
            WHERE device_serial = %s
        """, (
            raw_notes,
            wan1_label,
            wan1_speed_label,
            wan2_label,
            wan2_speed_label,
            wan1_arin,
            wan2_arin,
            wan1_comparison,
            wan2_comparison,
            device_serial
        ))
        
        # Also update enriched_circuits with the final providers
        cursor.execute("""
            UPDATE enriched_circuits
            SET wan1_provider = %s,
                wan1_speed = %s,
                wan2_provider = %s,
                wan2_speed = %s,
                last_updated = NOW()
            WHERE network_name = %s
        """, (
            wan1_final,
            wan1_speed_label or '0.0M x 0.0M',
            wan2_final,
            wan2_speed_label or '0.0M x 0.0M',
            network_name
        ))
        
        if cursor.rowcount > 0:
            updated_count += 1
            logger.info(f"Updated {network_name}: WAN1={wan1_final} (was {wan1_label}), WAN2={wan2_final} (was {wan2_label})")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    logger.info(f"Recovery complete. Updated {updated_count} devices")
    
    # Update RDAP cache
    if ip_cache:
        conn = get_db_connection()
        cursor = conn.cursor()
        for ip, provider in ip_cache.items():
            cursor.execute("""
                INSERT INTO rdap_cache (ip_address, provider_name)
                VALUES (%s, %s)
                ON CONFLICT (ip_address) DO UPDATE SET
                    provider_name = EXCLUDED.provider_name,
                    last_queried = NOW()
            """, (ip, provider))
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Updated {len(ip_cache)} entries in RDAP cache")

if __name__ == "__main__":
    logger.info("Starting Meraki notes recovery from historical data...")
    recover_and_update()