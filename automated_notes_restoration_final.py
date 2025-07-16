#!/usr/bin/env python3
"""
FINAL Automated Notes Restoration Script
Uses the exact logic from legacy scripts:
1. Uses already-parsed provider labels from 6/24 JSON (not re-parsing raw notes)
2. Applies DSR matching and fallback logic
3. Preserves DSR provider names exactly
"""

import os
import sys
import json
import requests
import time
import re
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
sys.path.insert(0, '/usr/local/bin/Main')
from nightly_meraki_db import get_db_connection
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
BASE_URL = "https://api.meraki.com/api/v1"
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
ROLLBACK_LOG = "/tmp/automated_notes_restoration_final_rollback.log"
DEBUG_LOG = "/tmp/automated_notes_restoration_final_debug.log"

# Provider mapping for comparison only
PROVIDER_MAPPING = {
    "spectrum": "Charter Communications",
    "cox business/boi": "Cox Communications",
    "cox business": "Cox Communications",
    "comcast workplace": "Comcast",
    "at&t broadband ii": "AT&T",
    "at&t": "AT&T",
    "comcast": "Comcast",
    "verizon": "Verizon",
    "vzg": "VZW Cell",
    "vzw": "VZW Cell",
    "starlink": "Starlink",
    "digi": "Digi",
    "inseego": "Inseego",
}

def setup_debug_logging():
    """Setup comprehensive debug logging"""
    debug_handler = logging.FileHandler(DEBUG_LOG, mode='w')
    debug_handler.setLevel(logging.DEBUG)
    debug_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    debug_handler.setFormatter(debug_formatter)
    
    debug_logger = logging.getLogger('debug')
    debug_logger.addHandler(debug_handler)
    debug_logger.setLevel(logging.DEBUG)
    
    return debug_logger

def get_headers():
    return {
        "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
        "Content-Type": "application/json"
    }

def make_api_request(url, method="GET", data=None):
    headers = get_headers()
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=30)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=30)
        
        response.raise_for_status()
        
        if method == "GET":
            return response.json()
        else:
            return {"success": True}
            
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def load_6_24_source_data():
    """Load the 6/24 source data with already-parsed provider labels"""
    try:
        with open('/var/www/html/meraki-data/mx_inventory_live.json', 'r') as f:
            data = json.load(f)
        
        # Create lookup by network name
        source_data = {}
        for device in data:
            if device.get('network_name'):
                source_data[device['network_name']] = {
                    'raw_notes': device.get('raw_notes', ''),
                    'wan1_provider_label': device.get('wan1', {}).get('provider_label', ''),
                    'wan1_speed': device.get('wan1', {}).get('speed', ''),
                    'wan1_comparison': device.get('wan1', {}).get('provider_comparison', ''),
                    'wan1_arin': device.get('wan1', {}).get('provider', ''),
                    'wan2_provider_label': device.get('wan2', {}).get('provider_label', ''),
                    'wan2_speed': device.get('wan2', {}).get('speed', ''),
                    'wan2_comparison': device.get('wan2', {}).get('provider_comparison', ''),
                    'wan2_arin': device.get('wan2', {}).get('provider', ''),
                }
        
        logger.info(f"Loaded 6/24 source data for {len(source_data)} networks")
        return source_data
        
    except Exception as e:
        logger.error(f"Failed to load 6/24 source data: {e}")
        return {}

def get_all_mx_sites():
    """Get all MX sites alphabetically, excluding hubs/labs/voice"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT mi.network_name, mi.device_serial, mi.device_model
        FROM meraki_inventory mi 
        WHERE mi.device_model LIKE 'MX%'
        AND mi.network_name NOT LIKE '%HUB%'
        AND mi.network_name NOT LIKE '%LAB%' 
        AND mi.network_name NOT LIKE '%VOICE%'
        ORDER BY mi.network_name
    """)
    
    sites = []
    for row in cursor.fetchall():
        network_name, device_serial, device_model = row
        sites.append({
            "network_name": network_name,
            "device_serial": device_serial, 
            "device_model": device_model
        })
    
    cursor.close()
    conn.close()
    
    logger.info(f"Found {len(sites)} MX sites to process")
    return sites

def get_current_meraki_notes(device_serial):
    """Get current notes from Meraki device"""
    device_url = f"{BASE_URL}/devices/{device_serial}"
    device_info = make_api_request(device_url)
    
    if "error" in device_info:
        return None
    
    return device_info.get("notes", "") or ""

def get_dsr_circuits_for_site(network_name):
    """Get DSR circuits for a site from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            provider_name,
            details_ordered_service_speed,
            circuit_purpose,
            ip_address_start
        FROM circuits
        WHERE site_name = %s
        AND status = 'Enabled'
        ORDER BY circuit_purpose
    """, (network_name,))
    
    circuits = []
    for row in cursor.fetchall():
        circuits.append({
            'provider': row[0],
            'speed': row[1],
            'purpose': row[2],
            'ip': row[3]
        })
    
    cursor.close()
    conn.close()
    
    return circuits

def normalize_provider_for_comparison(provider):
    """Normalize provider for comparison ONLY (not for display)"""
    if not provider or provider.lower() in ['nan', 'null', '', 'unknown']:
        return ""
    
    provider_str = str(provider).strip()
    if not provider_str:
        return ""
    
    provider_lower = provider_str.lower()
    
    # Remove common prefixes and suffixes for comparison
    provider_clean = re.sub(
        r'^\s*(?:dsr|agg|comcastagg|clink|not\s*dsr|--|-)?\s+',
        '', provider_lower, flags=re.IGNORECASE
    ).strip()
    
    # Check mapping
    for key, mapped_value in PROVIDER_MAPPING.items():
        if key in provider_clean:
            return mapped_value.lower()
    
    return provider_clean

def match_dsr_provider(provider_label, dsr_circuits):
    """Match provider label with DSR circuits"""
    if not provider_label or not dsr_circuits:
        return None
    
    label_norm = normalize_provider_for_comparison(provider_label)
    if not label_norm:
        return None
    
    for circuit in dsr_circuits:
        dsr_norm = normalize_provider_for_comparison(circuit['provider'])
        if label_norm == dsr_norm:
            return circuit
    
    return None

def normalize_cell_provider(provider):
    """Normalize cell provider names properly"""
    if not provider:
        return provider
        
    provider_str = str(provider).strip()
    
    # Remove leading dashes and clean up
    provider_str = re.sub(r'^[-\s]+', '', provider_str)
    
    # VZG/VZW/VZN variations -> VZW Cell (including IMEI/IMIE typos)
    if re.search(r'vzg|vzw|vzn', provider_str, re.IGNORECASE):
        return "VZW Cell"
    
    # DIGI variations -> Digi
    if re.search(r'digi', provider_str, re.IGNORECASE):
        return "Digi"
    
    # Inseego remains as is
    if re.search(r'inseego', provider_str, re.IGNORECASE):
        return "Inseego"
    
    # Starlink variations -> Starlink (remove serial numbers, IP addresses, etc)
    if re.search(r'starlink', provider_str, re.IGNORECASE):
        return "Starlink"
        
    # Handle corrupted "Cell Cell" -> VZW Cell
    if provider_str.lower() == 'cell cell':
        return "VZW Cell"
        
    # Cell variations - if it just says "Cell" make it VZW Cell
    if provider_str.lower() == 'cell':
        return "VZW Cell"
        
    return provider

def determine_final_provider(provider_label, arin_provider, comparison, dsr_circuit):
    """
    Determine final provider using exact legacy logic:
    1. If DSR match exists, use DSR provider name EXACTLY
    2. If no DSR match, use comparison logic with cell normalization
    """
    if dsr_circuit:
        # DSR match found - use exact DSR provider name
        return dsr_circuit['provider'], True  # confirmed = True
    
    # No DSR match - use comparison logic
    if comparison == "No match":
        # Trust notes over ARIN when they don't match
        # But normalize cell providers
        final_provider = normalize_cell_provider(provider_label)
        return final_provider, False
    else:
        # Trust ARIN when it matches
        return arin_provider, False

def reformat_speed(speed, provider):
    """Reformat speed with special cases"""
    # Special cases for cell and satellite providers
    provider_lower = str(provider).lower()
    
    # Cell providers always get "Cell" speed
    if any(term in provider_lower for term in ['vzw cell', 'verizon cell', 'digi', 'inseego', 'vzw', 'vzg']):
        return "Cell"
    
    # Starlink always gets "Satellite" speed
    if 'starlink' in provider_lower:
        return "Satellite"
    
    # For other providers, return the actual speed if available
    if not speed:
        return ""
    
    # Standard speed format
    if re.match(r'^\d+(?:\.\d+)?[MG]?\s*x\s*\d+(?:\.\d+)?[MG]?$', str(speed), re.IGNORECASE):
        return speed
    
    return speed

def build_clean_notes(wan1_provider, wan1_speed, wan2_provider, wan2_speed):
    """Build clean notes format"""
    lines = []
    
    if wan1_provider or wan1_speed:
        lines.append("WAN 1")
        if wan1_provider:
            lines.append(wan1_provider)
        if wan1_speed:
            lines.append(wan1_speed)
    
    if wan2_provider or wan2_speed:
        lines.append("WAN 2")
        if wan2_provider:
            lines.append(wan2_provider)
        if wan2_speed:
            lines.append(wan2_speed)
    
    return '\\n'.join(lines)

def update_device_notes(device_serial, new_notes):
    """Update notes for device"""
    device_url = f"{BASE_URL}/devices/{device_serial}"
    data = {"notes": new_notes}
    
    result = make_api_request(device_url, method="PUT", data=data)
    return result

def log_action(site_name, action_type, details, debug_info=None):
    """Log action to rollback file with comprehensive details"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = f"""
{site_name}:
  Status: {action_type}
  {details}
  Timestamp: {timestamp}"""
    
    if debug_info:
        log_entry += f"""
  Debug Info:
{debug_info}"""
    
    with open(ROLLBACK_LOG, 'a') as f:
        f.write(log_entry + "\\n")

def process_single_site(site, source_data):
    """Process a single site using exact legacy logic"""
    debug_logger = logging.getLogger('debug')
    network_name = site['network_name']
    device_serial = site['device_serial']
    
    logger.info(f"Processing {network_name} ({device_serial})")
    debug_logger.debug(f"\\n{'='*80}")
    debug_logger.debug(f"PROCESSING: {network_name}")
    debug_logger.debug(f"Serial: {device_serial}")
    debug_logger.debug(f"{'='*80}")
    
    # Get current Meraki notes
    current_notes = get_current_meraki_notes(device_serial)
    if current_notes is None:
        logger.error(f"Failed to get current notes for {network_name}")
        return False
    
    debug_logger.debug(f"Current Meraki notes: {repr(current_notes)}")
    
    # Get 6/24 source data (already parsed)
    source_info = source_data.get(network_name, {})
    if not source_info:
        logger.warning(f"No 6/24 source data for {network_name}")
        return False
    
    # Use already-parsed provider labels from 6/24
    wan1_provider_label = source_info['wan1_provider_label']
    wan1_speed = source_info['wan1_speed']
    wan1_comparison = source_info['wan1_comparison']
    wan1_arin = source_info['wan1_arin']
    
    wan2_provider_label = source_info['wan2_provider_label']
    wan2_speed = source_info['wan2_speed']
    wan2_comparison = source_info['wan2_comparison']
    wan2_arin = source_info['wan2_arin']
    
    debug_logger.debug(f"6/24 Parsed Data:")
    debug_logger.debug(f"  WAN1: label='{wan1_provider_label}', speed='{wan1_speed}', comparison='{wan1_comparison}', ARIN='{wan1_arin}'")
    debug_logger.debug(f"  WAN2: label='{wan2_provider_label}', speed='{wan2_speed}', comparison='{wan2_comparison}', ARIN='{wan2_arin}'")
    
    # Get DSR circuits
    dsr_circuits = get_dsr_circuits_for_site(network_name)
    debug_logger.debug(f"DSR circuits: {dsr_circuits}")
    
    # Match DSR circuits
    wan1_dsr = match_dsr_provider(wan1_provider_label, dsr_circuits)
    wan2_dsr = match_dsr_provider(wan2_provider_label, dsr_circuits)
    
    if wan1_dsr:
        debug_logger.debug(f"WAN1 matched DSR: {wan1_dsr['provider']}")
    if wan2_dsr:
        debug_logger.debug(f"WAN2 matched DSR: {wan2_dsr['provider']}")
    
    # Determine final providers using legacy logic
    wan1_provider_final, wan1_confirmed = determine_final_provider(
        wan1_provider_label, wan1_arin, wan1_comparison, wan1_dsr
    )
    wan2_provider_final, wan2_confirmed = determine_final_provider(
        wan2_provider_label, wan2_arin, wan2_comparison, wan2_dsr
    )
    
    # Format speeds
    wan1_speed_final = reformat_speed(wan1_speed, wan1_provider_final)
    wan2_speed_final = reformat_speed(wan2_speed, wan2_provider_final)
    
    debug_logger.debug(f"Final providers:")
    debug_logger.debug(f"  WAN1: '{wan1_provider_final}' (confirmed={wan1_confirmed}), speed='{wan1_speed_final}'")
    debug_logger.debug(f"  WAN2: '{wan2_provider_final}' (confirmed={wan2_confirmed}), speed='{wan2_speed_final}'")
    
    # Build expected notes
    expected_notes = build_clean_notes(wan1_provider_final, wan1_speed_final, wan2_provider_final, wan2_speed_final)
    debug_logger.debug(f"Expected notes: {repr(expected_notes)}")
    
    # Create debug info
    debug_info = f"""    6/24 WAN1: label='{wan1_provider_label}', ARIN='{wan1_arin}', comparison='{wan1_comparison}'
    6/24 WAN2: label='{wan2_provider_label}', ARIN='{wan2_arin}', comparison='{wan2_comparison}'
    DSR Circuits: {len(dsr_circuits)} found
    Final WAN1: '{wan1_provider_final}' (DSR match: {wan1_dsr is not None})
    Final WAN2: '{wan2_provider_final}' (DSR match: {wan2_dsr is not None})
    Current: {repr(current_notes)}
    Expected: {repr(expected_notes)}"""
    
    # Compare and update
    if current_notes.strip() == expected_notes.strip():
        logger.info(f"  ✅ {network_name}: Notes already correct")
        details = "Notes already match expected format"
        log_action(network_name, "✅ ALREADY CORRECT", details, debug_info)
        return True
    else:
        logger.info(f"  🔄 {network_name}: Updating device notes")
        debug_logger.debug(f"Updating device with: {repr(expected_notes)}")
        
        result = update_device_notes(device_serial, expected_notes)
        
        if "error" in result:
            logger.error(f"  ❌ {network_name}: Update failed - {result['error']}")
            details = f"Update failed: {result['error']}"
            log_action(network_name, "❌ UPDATE FAILED", details, debug_info)
            return False
        else:
            logger.info(f"  ✅ {network_name}: Update successful")
            details = f"Updated Meraki notes\\n  From: {repr(current_notes)}\\n  To: {repr(expected_notes)}"
            log_action(network_name, "✅ MERAKI NOTES UPDATED", details, debug_info)
            return True

def main():
    """Main automation function"""
    # Setup debug logging
    debug_logger = setup_debug_logging()
    
    logger.info("Starting FINAL automated notes restoration...")
    debug_logger.debug("=== STARTING AUTOMATED RESTORATION WITH FINAL LOGIC ===")
    debug_logger.debug("Using already-parsed provider labels from 6/24 JSON")
    
    # Initialize rollback log
    with open(ROLLBACK_LOG, 'w') as f:
        f.write(f"FINAL Automated Notes Restoration Log\\n")
        f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
        f.write(f"Using parsed provider labels from 6/24 JSON\\n")
        f.write(f"{'='*60}\\n")
    
    # Load 6/24 source data
    source_data = load_6_24_source_data()
    if not source_data:
        logger.error("Failed to load 6/24 source data - aborting")
        return
    
    # Get all sites
    sites = get_all_mx_sites()
    if not sites:
        logger.error("No sites found - aborting")
        return
    
    # Process sites
    total_sites = len(sites)
    successful = 0
    failed = 0
    
    for i, site in enumerate(sites, 1):
        logger.info(f"Processing {i}/{total_sites}: {site['network_name']}")
        
        try:
            if process_single_site(site, source_data):
                successful += 1
            else:
                failed += 1
                
        except Exception as e:
            logger.error(f"Error processing {site['network_name']}: {e}")
            debug_logger.error(f"Exception for {site['network_name']}: {e}", exc_info=True)
            failed += 1
        
        # Small delay to avoid API rate limits
        time.sleep(0.5)
    
    # Summary
    logger.info("="*60)
    logger.info(f"RESTORATION COMPLETE")
    logger.info(f"Total Sites: {total_sites}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Rollback log: {ROLLBACK_LOG}")
    logger.info(f"Debug log: {DEBUG_LOG}")
    
    # Add summary to logs
    with open(ROLLBACK_LOG, 'a') as f:
        f.write(f"\\n{'='*60}\\n")
        f.write(f"FINAL SUMMARY:\\n")
        f.write(f"Total Sites: {total_sites}\\n")
        f.write(f"Successful: {successful}\\n") 
        f.write(f"Failed: {failed}\\n")
        f.write(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")

if __name__ == "__main__":
    main()