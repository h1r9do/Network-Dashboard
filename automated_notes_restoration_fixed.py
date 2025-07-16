#!/usr/bin/env python3
"""
FIXED Automated Notes Restoration Script
Uses proper parsing logic from circuit_logic.md with comprehensive debug logging
"""

import os
import sys
import json
import requests
import time
import re
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
ROLLBACK_LOG = "/tmp/automated_notes_restoration_fixed_rollback.log"
DEBUG_LOG = "/tmp/automated_notes_restoration_debug.log"

# Provider mapping from circuit_logic.md
PROVIDER_MAPPING = {
    "vzg": "VZW Cell",
    "vzw": "VZW Cell", 
    "verizon": "VZW Cell",
    "vz": "VZW Cell",
    "spectrum": "Charter Communications",
    "cox business": "Cox Communications",
    "comcast workplace": "Comcast",
    "at&t broadband ii": "AT&T",
    "frontier fiber": "Frontier Communications",
    "digi": "Digi",
    "starlink": "Starlink",
    "inseego": "Inseego"
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
                source_data[device['network_name']] = device['raw_notes']
        
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

def normalize_provider_original(provider, is_dsr=False):
    """Original provider normalization from circuit_logic.md"""
    if not provider or provider.lower() in ['nan', 'null', '']:
        return ""
    
    provider_str = str(provider).strip()
    if not provider_str:
        return ""
    
    provider_lower = provider_str.lower()
    
    # Remove IMEI, serial numbers, etc.
    provider_clean = re.sub(
        r'\s*(?:##.*##|\s*imei.*$|\s*kitp.*$|\s*sn.*$|\s*port.*$|\s*location.*$|\s*in\s+the\s+bay.*$|\s*up\s+front.*$|\s*under\s+.*$|\s*wireless\s+gateway.*$|\s*serial.*$|\s*poe\s+injector.*$|\s*supported\s+through.*$|\s*static\s+ip.*$|\s*subnet\s+mask.*$|\s*gateway\s+ip.*$|\s*service\s+id.*$|\s*circuit\s+id.*$|\s*ip\s+address.*$|\s*5g.*$|\s*currently.*$)',
        '', provider_str, flags=re.IGNORECASE
    ).strip()
    
    # Remove DSR, AGG, NOT DSR prefixes and suffixes
    provider_clean = re.sub(
        r'^\s*(?:dsr|agg|comcastagg|clink|not\s*dsr|--|-)\s+|\s*(?:extended\s+cable|dsl|fiber|adi|workpace)\s*',
        '', provider_clean, flags=re.IGNORECASE
    ).strip()
    
    provider_lower = provider_clean.lower()
    
    # Special provider detection
    if provider_lower.startswith('digi'):
        return "Digi"
    if provider_lower.startswith('starlink') or 'starlink' in provider_lower:
        return "Starlink"
    if provider_lower.startswith('inseego') or 'inseego' in provider_lower:
        return "Inseego"
    if provider_lower.startswith(('vz', 'vzw', 'vzn', 'verizon', 'vzm')) and not is_dsr:
        return "VZW Cell"
    
    # Fuzzy matching with provider mapping
    for key, mapped_value in PROVIDER_MAPPING.items():
        if key in provider_lower:
            return mapped_value
    
    # Return cleaned provider if no mapping found
    return provider_clean

def reformat_speed_original(speed, provider):
    """Original speed reformatting from circuit_logic.md"""
    if not speed:
        return ""
    
    # Override speed for specific providers - EXACT MATCHING
    if provider in ["Inseego", "VZW Cell", "Digi", ""]:
        return "Cell"
    if provider == "Starlink":
        return "Satellite"
    
    return str(speed).strip()

def parse_raw_notes_original(raw_notes):
    """Original notes parsing logic from circuit_logic.md"""
    debug_logger = logging.getLogger('debug')
    
    if not raw_notes:
        debug_logger.debug("No raw notes provided")
        return "", "", "", ""
    
    debug_logger.debug(f"Parsing raw notes: {repr(raw_notes)}")
    
    # Text preprocessing - normalize spaces
    cleaned_notes = re.sub(r'\s+', ' ', raw_notes.strip())
    debug_logger.debug(f"Cleaned notes: {repr(cleaned_notes)}")
    
    # Pattern definitions
    wan1_pattern = r'(?:WAN1|WAN\s*1)\s*:?\s*'
    wan2_pattern = r'(?:WAN2|WAN\s*2)\s*:?\s*'
    speed_pattern = r'(\d+(?:\.\d+)?)\s*([MG]B?)\s*x\s*(\d+(?:\.\d+)?)\s*([MG]B?)'
    
    # Split on WAN patterns
    wan1_match = re.search(wan1_pattern, cleaned_notes, re.IGNORECASE)
    wan2_match = re.search(wan2_pattern, cleaned_notes, re.IGNORECASE)
    
    wan1_segment = ""
    wan2_segment = ""
    
    if wan1_match:
        start_pos = wan1_match.end()
        if wan2_match:
            end_pos = wan2_match.start()
            wan1_segment = cleaned_notes[start_pos:end_pos].strip()
            wan2_segment = cleaned_notes[wan2_match.end():].strip()
        else:
            wan1_segment = cleaned_notes[start_pos:].strip()
    elif wan2_match:
        wan2_segment = cleaned_notes[wan2_match.end():].strip()
    else:
        # No WAN labels found, treat as WAN1
        wan1_segment = cleaned_notes
    
    debug_logger.debug(f"WAN1 segment: {repr(wan1_segment)}")
    debug_logger.debug(f"WAN2 segment: {repr(wan2_segment)}")
    
    # Extract provider/speed for each segment
    def extract_provider_speed(segment):
        if not segment:
            return "", ""
        
        # Remove IP/network details
        segment = re.sub(r'IP:\s*[\d.]+|GW:\s*[\d.]+|Sub:\s*[\d.]+|Gateway\s*[\d.]+|Subnet\s*[\d.]+', '', segment, flags=re.IGNORECASE).strip()
        
        # Search for speed pattern
        speed_match = re.search(speed_pattern, segment, re.IGNORECASE)
        
        if speed_match:
            # Extract speed
            up_speed = float(speed_match.group(1))
            up_unit = speed_match.group(2).upper()
            down_speed = float(speed_match.group(3))
            down_unit = speed_match.group(4).upper()
            
            # Convert G to M
            if up_unit.startswith('G'):
                up_speed *= 1000
                up_unit = 'M'
            if down_unit.startswith('G'):
                down_speed *= 1000
                down_unit = 'M'
            
            speed = f"{up_speed:.1f}{up_unit} x {down_speed:.1f}{down_unit}"
            
            # Provider is text before speed
            provider = segment[:speed_match.start()].strip()
        else:
            # No speed found, entire segment is provider
            provider = segment.strip()
            speed = ""
        
        # Clean provider
        provider = re.sub(r'[^\w\s.&|-]', ' ', provider).strip()
        
        return provider, speed
    
    wan1_provider, wan1_speed = extract_provider_speed(wan1_segment)
    wan2_provider, wan2_speed = extract_provider_speed(wan2_segment)
    
    debug_logger.debug(f"Extracted - WAN1: provider='{wan1_provider}', speed='{wan1_speed}'")
    debug_logger.debug(f"Extracted - WAN2: provider='{wan2_provider}', speed='{wan2_speed}'")
    
    return wan1_provider, wan1_speed, wan2_provider, wan2_speed

def parse_6_24_notes_to_clean_format_fixed(raw_notes):
    """FIXED: Parse 6/24 raw notes using proper circuit logic"""
    debug_logger = logging.getLogger('debug')
    
    if not raw_notes:
        return ""
    
    debug_logger.debug(f"=== PARSING 6/24 NOTES ===")
    debug_logger.debug(f"Raw input: {repr(raw_notes)}")
    
    # Step 1: Parse using original logic
    wan1_provider_raw, wan1_speed_raw, wan2_provider_raw, wan2_speed_raw = parse_raw_notes_original(raw_notes)
    
    debug_logger.debug(f"Raw parsed - WAN1: '{wan1_provider_raw}' / '{wan1_speed_raw}'")
    debug_logger.debug(f"Raw parsed - WAN2: '{wan2_provider_raw}' / '{wan2_speed_raw}'")
    
    # Step 2: Normalize providers
    wan1_provider = normalize_provider_original(wan1_provider_raw)
    wan2_provider = normalize_provider_original(wan2_provider_raw)
    
    debug_logger.debug(f"Normalized - WAN1: '{wan1_provider_raw}' -> '{wan1_provider}'")
    debug_logger.debug(f"Normalized - WAN2: '{wan2_provider_raw}' -> '{wan2_provider}'")
    
    # Step 3: Reformat speeds
    wan1_speed = reformat_speed_original(wan1_speed_raw, wan1_provider)
    wan2_speed = reformat_speed_original(wan2_speed_raw, wan2_provider)
    
    # Special case: If VZW Cell has no speed, default to "Cell"
    if wan2_provider == "VZW Cell" and not wan2_speed:
        wan2_speed = "Cell"
    
    debug_logger.debug(f"Speed reformatted - WAN1: '{wan1_speed_raw}' -> '{wan1_speed}'")
    debug_logger.debug(f"Speed reformatted - WAN2: '{wan2_speed_raw}' -> '{wan2_speed}'")
    
    # Step 4: Build clean format
    result_lines = []
    
    if wan1_provider or wan1_speed:
        result_lines.append("WAN 1")
        if wan1_provider:
            result_lines.append(wan1_provider)
        if wan1_speed:
            result_lines.append(wan1_speed)
    
    if wan2_provider or wan2_speed:
        result_lines.append("WAN 2")
        if wan2_provider:
            result_lines.append(wan2_provider)
        if wan2_speed:
            result_lines.append(wan2_speed)
    
    result = '\\n'.join(result_lines)
    debug_logger.debug(f"Final clean format: {repr(result)}")
    
    return result

def normalize_notes_for_comparison(notes):
    """Normalize notes for comparison"""
    if not notes:
        return ""
    
    # Split into lines and clean up
    lines = [line.strip() for line in notes.split('\\n') if line.strip()]
    return '\\n'.join(lines)

def update_device_notes(device_serial, new_notes):
    """Update notes for device"""
    device_url = f"{BASE_URL}/devices/{device_serial}"
    data = {"notes": new_notes}
    
    result = make_api_request(device_url, method="PUT", data=data)
    return result

def fix_database_for_site(network_name, wan1_provider, wan1_speed, wan2_provider, wan2_speed):
    """Fix database to preserve correct provider names"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Update enriched_circuits
        cursor.execute("""
            UPDATE enriched_circuits 
            SET wan1_provider = %s, wan1_speed = %s, wan2_provider = %s, wan2_speed = %s
            WHERE network_name = %s
        """, (wan1_provider, wan1_speed, wan2_provider, wan2_speed, network_name))
        
        # Update meraki_inventory  
        cursor.execute("""
            UPDATE meraki_inventory
            SET wan1_provider_label = %s, wan1_speed_label = %s, wan2_provider_label = %s, wan2_speed_label = %s
            WHERE network_name = %s
        """, (wan1_provider, wan1_speed, wan2_provider, wan2_speed, network_name))
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"Database update failed for {network_name}: {e}")
        conn.rollback()
        return False
        
    finally:
        cursor.close()
        conn.close()

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
    """Process a single site with automated decision making and comprehensive logging"""
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
    
    # Get 6/24 source notes
    source_raw_notes = source_data.get(network_name, "")
    if not source_raw_notes:
        logger.warning(f"No 6/24 source data for {network_name}")
        return False
    
    debug_logger.debug(f"6/24 source raw notes: {repr(source_raw_notes)}")
    
    # Parse 6/24 source to clean format using FIXED logic
    expected_clean_notes = parse_6_24_notes_to_clean_format_fixed(source_raw_notes)
    debug_logger.debug(f"Expected clean notes: {repr(expected_clean_notes)}")
    
    # Normalize for comparison
    current_normalized = normalize_notes_for_comparison(current_notes)
    expected_normalized = normalize_notes_for_comparison(expected_clean_notes)
    
    debug_logger.debug(f"Current normalized: {repr(current_normalized)}")
    debug_logger.debug(f"Expected normalized: {repr(expected_normalized)}")
    
    # Create debug info for logging
    debug_info = f"""    6/24 Raw: {repr(source_raw_notes)}
    Expected Clean: {repr(expected_clean_notes)}
    Current Device: {repr(current_notes)}
    Match: {current_normalized == expected_normalized}"""
    
    # Decision logic
    if current_normalized == expected_normalized:
        # Notes match - fix database instead
        logger.info(f"  ✅ {network_name}: Notes already correct, fixing database")
        
        # Extract components for database update
        wan1_provider, wan1_speed, wan2_provider, wan2_speed = parse_raw_notes_original(source_raw_notes)
        wan1_provider = normalize_provider_original(wan1_provider)
        wan2_provider = normalize_provider_original(wan2_provider)
        wan1_speed = reformat_speed_original(wan1_speed, wan1_provider)
        wan2_speed = reformat_speed_original(wan2_speed, wan2_provider)
        
        fix_database_for_site(network_name, wan1_provider, wan1_speed, wan2_provider, wan2_speed)
        
        details = f"Database fixed to preserve 6/24 source provider names\\n  WAN1: {wan1_provider} / {wan1_speed}\\n  WAN2: {wan2_provider} / {wan2_speed}"
        log_action(network_name, "✅ DATABASE FIXED (Meraki notes already correct)", details, debug_info)
        
        return True
        
    else:
        # Notes don't match - update device
        logger.info(f"  🔄 {network_name}: Updating device notes to match 6/24 source")
        debug_logger.debug(f"Updating device with: {repr(expected_clean_notes)}")
        
        result = update_device_notes(device_serial, expected_clean_notes)
        
        if "error" in result:
            logger.error(f"  ❌ {network_name}: Update failed - {result['error']}")
            details = f"Update failed: {result['error']}"
            log_action(network_name, "❌ UPDATE FAILED", details, debug_info)
            return False
        else:
            logger.info(f"  ✅ {network_name}: Update successful")
            details = f"Updated Meraki notes to match 6/24 source\\n  Updated to: {repr(expected_clean_notes)}"
            log_action(network_name, "✅ MERAKI NOTES UPDATED", details, debug_info)
            return True

def main():
    """Main automation function"""
    # Setup debug logging
    debug_logger = setup_debug_logging()
    
    logger.info("Starting FIXED automated notes restoration...")
    debug_logger.debug("=== STARTING AUTOMATED RESTORATION WITH FIXED LOGIC ===")
    
    # Initialize rollback log
    with open(ROLLBACK_LOG, 'w') as f:
        f.write(f"FIXED Automated Notes Restoration Log\\n")
        f.write(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
        f.write(f"Using proper circuit_logic.md parsing\\n")
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