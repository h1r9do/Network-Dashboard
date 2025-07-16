#!/usr/bin/env python3
"""
CORRECT Automated Notes Restoration Script
Implements the EXACT logic from legacy meraki_mx.py and nightly_enriched.py
Preserves DSR provider names exactly as they appear
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
ROLLBACK_LOG = "/tmp/automated_notes_restoration_correct_rollback.log"
DEBUG_LOG = "/tmp/automated_notes_restoration_correct_debug.log"

# Provider mapping from legacy nightly_enriched.py
PROVIDER_MAPPING = {
    "spectrum": "Charter Communications",
    "cox business/boi": "Cox Communications",
    "cox business boi | extended cable |": "Cox Communications",
    "cox business boi extended cable": "Cox Communications",
    "cox business": "Cox Communications",
    "comcast workplace": "Comcast",
    "comcast workplace cable": "Comcast",
    "agg comcast": "Comcast",
    "comcastagg clink dsl": "CenturyLink",
    "comcastagg comcast": "Comcast",
    "verizon cell": "Verizon",
    "cell": "Verizon",
    "verizon business": "Verizon",
    "accelerated": "",  # Clean off
    "digi": "Digi",
    "digi cellular": "Digi",
    "starlink": "Starlink",
    "inseego": "Inseego",
    "charter communications": "Charter Communications",
    "at&t broadband ii": "AT&T",
    "at&t abf": "AT&T",
    "at&t adi": "AT&T",
    "not dsr at&t | at&t adi |": "AT&T",
    "at&t": "AT&T",
    "cox communications": "Cox Communications",
    "comcast": "Comcast",
    "verizon": "Verizon",
    "vzg": "VZW Cell",
}

def setup_debug_logging():
    """Setup comprehensive debug logging"""
    debug_handler = logging.FileHandler(DEBUG_LOG)
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
    """Load the 6/24 source data"""
    try:
        with open('/var/www/html/meraki-data/mx_inventory_live.json', 'r') as f:
            data = json.load(f)
        
        # Create lookup by network name
        source_data = {}
        for device in data:
            if device.get('network_name') and device.get('raw_notes'):
                source_data[device['network_name']] = {
                    'raw_notes': device['raw_notes'],
                    'wan1_comparison': device.get('wan1', {}).get('provider_comparison', ''),
                    'wan2_comparison': device.get('wan2', {}).get('provider_comparison', ''),
                    'wan1_arin': device.get('wan1', {}).get('provider', ''),
                    'wan2_arin': device.get('wan2', {}).get('provider', ''),
                    'wan1_label': device.get('wan1', {}).get('provider_label', ''),
                    'wan2_label': device.get('wan2', {}).get('provider_label', '')
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
            details_ordered_service_speed as speed,
            circuit_purpose,
            status
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
            'status': row[3]
        })
    
    cursor.close()
    conn.close()
    
    return circuits

def normalize_provider_for_comparison(provider):
    """Normalize provider for comparison ONLY (not for display)"""
    if not provider or provider.lower() in ['nan', 'null', '']:
        return ""
    
    provider_str = str(provider).strip()
    if not provider_str:
        return ""
    
    provider_lower = provider_str.lower()
    
    # Remove common prefixes and suffixes for comparison
    provider_clean = re.sub(
        r'^\\s*(?:dsr|agg|comcastagg|clink|not\\s*dsr|--|-)\\s+|\\s*(?:extended\\s+cable|dsl|fiber|adi|workpace)\\s*',
        '', provider_lower, flags=re.IGNORECASE
    ).strip()
    
    # Check mapping
    for key, mapped_value in PROVIDER_MAPPING.items():
        if key in provider_clean:
            return mapped_value.lower()
    
    return provider_clean

def parse_raw_notes(raw_notes):
    """Parse raw notes - exact logic from legacy meraki_mx.py"""
    if not raw_notes or not raw_notes.strip():
        return "", "", "", ""
    
    text = re.sub(r'\\s+', ' ', raw_notes.strip())
    wan1_pattern = re.compile(r'(?:WAN1|WAN\\s*1)\\s*:?\\s*', re.IGNORECASE)
    wan2_pattern = re.compile(r'(?:WAN2|WAN\\s*2)\\s*:?\\s*', re.IGNORECASE)
    speed_pattern = re.compile(r'(\\d+(?:\\.\\d+)?)\\s*([MG]B?)\\s*x\\s*(\\d+(?:\\.\\d+)?)\\s*([MG]B?)', re.IGNORECASE)
    
    def extract_provider_and_speed(segment):
        """Helper to extract provider name and speed from a text segment."""
        match = speed_pattern.search(segment)
        if match:
            up_speed = float(match.group(1))
            up_unit = match.group(2).upper()
            down_speed = float(match.group(3))
            down_unit = match.group(4).upper()
            
            if up_unit in ['G', 'GB']:
                up_speed *= 1000
                up_unit = 'M'
            elif up_unit in ['M', 'MB']:
                up_unit = 'M'
                
            if down_unit in ['G', 'GB']:
                down_speed *= 1000
                down_unit = 'M'
            elif down_unit in ['M', 'MB']:
                down_unit = 'M'
                
            speed_str = f"{up_speed:.1f}{up_unit} x {down_speed:.1f}{down_unit}"
            provider_name = segment[:match.start()].strip()
            provider_name = re.sub(r'[^\\w\\s.&|-]', ' ', provider_name).strip()
            provider_name = re.sub(r'\\s+', ' ', provider_name).strip()
            return provider_name, speed_str
        else:
            provider_name = re.sub(r'[^\\w\\s.&|-]', ' ', segment).strip()
            provider_name = re.sub(r'\\s+', ' ', provider_name).strip()
            return provider_name, ""
    
    wan1_text = ""
    wan2_text = ""
    parts = re.split(wan1_pattern, text, maxsplit=1)
    if len(parts) > 1:
        after_wan1 = parts[1]
        wan2_split = re.split(wan2_pattern, after_wan1, maxsplit=1)
        wan1_text = wan2_split[0].strip()
        if len(wan2_split) > 1:
            wan2_text = wan2_split[1].strip()
    else:
        parts = re.split(wan2_pattern, text, maxsplit=1)
        if len(parts) > 1:
            wan2_text = parts[1].strip()
        else:
            wan1_text = text.strip()
    
    wan1_provider, wan1_speed = extract_provider_and_speed(wan1_text)
    wan2_provider, wan2_speed = extract_provider_and_speed(wan2_text)
    
    return wan1_provider, wan1_speed, wan2_provider, wan2_speed

def determine_final_provider(notes_provider, arin_provider, comparison, dsr_circuits):
    """
    Determine final provider using exact legacy logic:
    1. Check if we have DSR match (by normalized comparison)
    2. If no DSR, use comparison logic from meraki_mx.py
    """
    debug_logger = logging.getLogger('debug')
    
    # First check for DSR match
    if dsr_circuits:
        notes_normalized = normalize_provider_for_comparison(notes_provider)
        debug_logger.debug(f"Checking DSR matches for '{notes_provider}' (normalized: '{notes_normalized}')")
        
        for circuit in dsr_circuits:
            dsr_normalized = normalize_provider_for_comparison(circuit['provider'])
            debug_logger.debug(f"  Comparing with DSR '{circuit['provider']}' (normalized: '{dsr_normalized}')")
            
            if notes_normalized and dsr_normalized and notes_normalized == dsr_normalized:
                debug_logger.debug(f"  -> MATCH! Using DSR provider exactly: '{circuit['provider']}'")
                return circuit['provider'], True  # Return DSR name exactly, mark as confirmed
        
        debug_logger.debug(f"  No DSR match found")
    
    # No DSR match - use legacy fallback logic
    if comparison == "No match":
        # Trust notes over ARIN when they don't match
        debug_logger.debug(f"No DSR match, comparison='No match' -> using notes: '{notes_provider}'")
        return notes_provider, False
    else:
        # Trust ARIN when it matches or no comparison
        debug_logger.debug(f"No DSR match, comparison='{comparison}' -> using ARIN: '{arin_provider}'")
        return arin_provider, False

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
        f.write(log_entry)

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
    
    # Get 6/24 source data
    source_info = source_data.get(network_name, {})
    if not source_info:
        logger.warning(f"No 6/24 source data for {network_name}")
        return False
    
    source_raw_notes = source_info['raw_notes']
    wan1_comparison = source_info['wan1_comparison']
    wan2_comparison = source_info['wan2_comparison']
    wan1_arin = source_info['wan1_arin']
    wan2_arin = source_info['wan2_arin']
    
    debug_logger.debug(f"6/24 source raw notes: {repr(source_raw_notes)}")
    debug_logger.debug(f"WAN1: comparison='{wan1_comparison}', ARIN='{wan1_arin}'")
    debug_logger.debug(f"WAN2: comparison='{wan2_comparison}', ARIN='{wan2_arin}'")
    
    # Get DSR circuits
    dsr_circuits = get_dsr_circuits_for_site(network_name)
    debug_logger.debug(f"DSR circuits: {dsr_circuits}")
    
    # Parse 6/24 notes
    wan1_provider_notes, wan1_speed, wan2_provider_notes, wan2_speed = parse_raw_notes(source_raw_notes)
    debug_logger.debug(f"Parsed notes - WAN1: '{wan1_provider_notes}' / '{wan1_speed}'")
    debug_logger.debug(f"Parsed notes - WAN2: '{wan2_provider_notes}' / '{wan2_speed}'")
    
    # Determine final providers using legacy logic
    wan1_provider_final, wan1_confirmed = determine_final_provider(
        wan1_provider_notes, wan1_arin, wan1_comparison, dsr_circuits
    )
    wan2_provider_final, wan2_confirmed = determine_final_provider(
        wan2_provider_notes, wan2_arin, wan2_comparison, dsr_circuits
    )
    
    debug_logger.debug(f"Final WAN1: '{wan1_provider_final}' (confirmed={wan1_confirmed})")
    debug_logger.debug(f"Final WAN2: '{wan2_provider_final}' (confirmed={wan2_confirmed})")
    
    # Build expected notes
    expected_notes = build_clean_notes(wan1_provider_final, wan1_speed, wan2_provider_final, wan2_speed)
    debug_logger.debug(f"Expected notes: {repr(expected_notes)}")
    
    # Create debug info
    debug_info = f"""    6/24 Raw: {repr(source_raw_notes)}
    WAN1: notes='{wan1_provider_notes}', ARIN='{wan1_arin}', comparison='{wan1_comparison}', final='{wan1_provider_final}'
    WAN2: notes='{wan2_provider_notes}', ARIN='{wan2_arin}', comparison='{wan2_comparison}', final='{wan2_provider_final}'
    DSR Circuits: {len(dsr_circuits)} found
    Expected: {repr(expected_notes)}
    Current: {repr(current_notes)}"""
    
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
    
    logger.info("Starting CORRECT automated notes restoration...")
    debug_logger.debug("=== STARTING AUTOMATED RESTORATION WITH CORRECT LEGACY LOGIC ===")
    
    # Initialize rollback log
    with open(ROLLBACK_LOG, 'w') as f:
        f.write(f"CORRECT Automated Notes Restoration Log\\n")
        f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
        f.write(f"Using exact legacy meraki_mx.py and nightly_enriched.py logic\\n")
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