#!/usr/bin/env python3
"""
Complete recovery of Meraki notes from git history
Implements the full original enrichment logic
"""

import json
import subprocess
import sys
import re
from datetime import datetime
sys.path.insert(0, '/usr/local/bin/Main')
from nightly_meraki_db import get_db_connection, parse_raw_notes, get_provider_for_ip, compare_providers, KNOWN_IPS
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Provider normalization from old logic
def normalize_provider_name(provider):
    """Normalize provider names to canonical form"""
    if not provider:
        return provider
    
    # Remove prefixes
    provider = re.sub(r'^(DSR|NOT DSR|AGG)\s+', '', provider, flags=re.IGNORECASE)
    
    # Special handling for cell providers
    if 'VZG' in provider or 'VZW' in provider or 'VZN' in provider:
        if 'IMEI' in provider:
            return provider  # Keep the full IMEI info
        return 'VZW Cell'
    
    # Map common variations
    mappings = {
        'frontier fiber': 'Frontier Communications',
        'spectrum': 'Charter Communications',
        'charter': 'Charter Communications',
        'at&t broadband': 'AT&T',
        'comcast workplace': 'Comcast',
        'cox business': 'Cox Communications',
        'centurylink': 'CenturyLink',
        'clink': 'CenturyLink',
        'brightspeed': 'Brightspeed',
        'altice': 'Optimum',
        'digi': 'Digi Cell',
        'starlink': 'Starlink'
    }
    
    provider_lower = provider.lower()
    for key, value in mappings.items():
        if key in provider_lower:
            return value
    
    return provider

def determine_final_provider(notes_provider, arin_provider, comparison, dsr_provider=None, dsr_enabled=False):
    """Apply the original logic hierarchy"""
    
    # If we have enabled DSR data, that's the highest priority
    if dsr_enabled and dsr_provider and dsr_provider.strip():
        return dsr_provider
    
    # Otherwise use the comparison logic
    if comparison == "No match" and notes_provider:
        # When ARIN doesn't match notes, trust the notes
        return normalize_provider_name(notes_provider)
    elif arin_provider and arin_provider not in ["Unknown", "Private IP"]:
        # Use ARIN when it matches or when no notes
        return arin_provider
    elif notes_provider:
        # Fall back to notes
        return normalize_provider_name(notes_provider)
    else:
        return "Unknown"

def main():
    # Get historical data from June 24
    logger.info("Retrieving historical Meraki data from June 24...")
    cmd = "git -C /var/www/html/meraki-data show 019677c:mx_inventory_live.json"
    json_content = subprocess.check_output(cmd, shell=True).decode()
    historical_data = json.loads(json_content)
    logger.info(f"Found {len(historical_data)} devices in historical data")
    
    # Get enabled circuits from database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT site_name, circuit_purpose, provider_name, status
        FROM circuits
        WHERE LOWER(status) = 'enabled'
    """)
    
    enabled_circuits = {}
    for site, purpose, provider, status in cursor.fetchall():
        if site not in enabled_circuits:
            enabled_circuits[site] = {}
        wan = 'wan1' if 'primary' in purpose.lower() else 'wan2'
        enabled_circuits[site][wan] = provider
    
    logger.info(f"Loaded {len(enabled_circuits)} sites with enabled circuits")
    
    # Process each device
    ip_cache = {}
    missing_ips = set()
    updated_count = 0
    
    for device in historical_data:
        network_name = device.get('network_name', '')
        device_serial = device.get('device_serial', '')
        raw_notes = device.get('raw_notes', '')
        
        if not device_serial or not device.get('device_model', '').startswith('MX'):
            continue
        
        # Parse the historical notes
        wan1_label, wan1_speed_label, wan2_label, wan2_speed_label = parse_raw_notes(raw_notes)
        
        # Get IPs
        wan1_ip = device.get('wan1', {}).get('ip', '')
        wan2_ip = device.get('wan2', {}).get('ip', '')
        
        # ARIN lookups
        wan1_arin = get_provider_for_ip(wan1_ip, ip_cache, missing_ips) if wan1_ip else "Unknown"
        wan2_arin = get_provider_for_ip(wan2_ip, ip_cache, missing_ips) if wan2_ip else "Unknown"
        
        # Compare
        wan1_comparison = compare_providers(wan1_arin, wan1_label) if wan1_label else None
        wan2_comparison = compare_providers(wan2_arin, wan2_label) if wan2_label else None
        
        # Get DSR data
        site_enabled = network_name in enabled_circuits
        wan1_dsr = enabled_circuits.get(network_name, {}).get('wan1', '')
        wan2_dsr = enabled_circuits.get(network_name, {}).get('wan2', '')
        
        # Determine final providers
        wan1_final = determine_final_provider(wan1_label, wan1_arin, wan1_comparison, wan1_dsr, site_enabled)
        wan2_final = determine_final_provider(wan2_label, wan2_arin, wan2_comparison, wan2_dsr, site_enabled)
        
        # Special handling for cell/satellite speeds
        if wan1_final and any(x in wan1_final.lower() for x in ['cell', 'digi', 'vzw', 'vzg', 'inseego']):
            wan1_speed_final = 'Cell'
        elif 'starlink' in wan1_final.lower():
            wan1_speed_final = 'Satellite'
        else:
            wan1_speed_final = wan1_speed_label or '0.0M x 0.0M'
            
        if wan2_final and any(x in wan2_final.lower() for x in ['cell', 'digi', 'vzw', 'vzg', 'inseego']):
            wan2_speed_final = 'Cell'
        elif 'starlink' in wan2_final.lower():
            wan2_speed_final = 'Satellite'
        else:
            wan2_speed_final = wan2_speed_label or '0.0M x 0.0M'
        
        # Update meraki_inventory
        cursor.execute("""
            UPDATE meraki_inventory
            SET device_notes = %s,
                wan1_provider_label = %s,
                wan1_speed_label = %s,
                wan2_provider_label = %s,
                wan2_speed_label = %s,
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
            wan1_comparison,
            wan2_comparison,
            device_serial
        ))
        
        # Update enriched_circuits
        if cursor.rowcount > 0:
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
                wan1_speed_final,
                wan2_final,
                wan2_speed_final,
                network_name
            ))
            
            if cursor.rowcount > 0:
                updated_count += 1
                if updated_count % 50 == 0:
                    logger.info(f"Progress: Updated {updated_count} devices...")
    
    # Update RDAP cache
    for ip, provider in ip_cache.items():
        if provider and provider not in ['Unknown', 'Private IP']:
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
    
    logger.info(f"Recovery complete! Updated {updated_count} devices")
    logger.info(f"Updated {len(ip_cache)} RDAP cache entries")

if __name__ == "__main__":
    main()