#!/usr/bin/env python3
"""
Restore Meraki device notes to clean format based on database parsing results
Updates devices to have clean WAN 1/WAN 2 format based on our processed data
"""

import os
import sys
import json
import requests
import time
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

# API rate limiting
MAX_REQUESTS = 900
REQUEST_WINDOW = 300
REQUESTS = []

def get_headers():
    return {
        "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
        "Content-Type": "application/json"
    }

def clean_request_timestamps():
    global REQUESTS
    current_time = time.time()
    REQUESTS = [t for t in REQUESTS if current_time - t < REQUEST_WINDOW]

def make_api_request(url, method="GET", data=None, max_retries=3):
    headers = get_headers()
    for attempt in range(max_retries):
        clean_request_timestamps()
        if len(REQUESTS) >= MAX_REQUESTS:
            time.sleep(REQUEST_WINDOW / MAX_REQUESTS)
            clean_request_timestamps()
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=30)
            
            response.raise_for_status()
            REQUESTS.append(time.time())
            
            if method == "GET":
                return response.json()
            else:
                return {"success": True}
                
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                logger.error(f"API request failed: {e}")
                return {"error": str(e)}
            time.sleep(2 ** attempt)
    return {"error": "Max retries exceeded"}

def format_clean_notes(wan1_provider, wan1_speed, wan2_provider, wan2_speed):
    """Format notes in clean WAN 1/WAN 2 format"""
    lines = []
    
    # WAN 1 section
    if wan1_provider or wan1_speed:
        lines.append("WAN 1")
        if wan1_provider:
            lines.append(wan1_provider)
        if wan1_speed:
            lines.append(wan1_speed)
    
    # WAN 2 section  
    if wan2_provider or wan2_speed:
        lines.append("WAN 2")
        if wan2_provider:
            lines.append(wan2_provider)
        if wan2_speed:
            lines.append(wan2_speed)
    
    return "\\n".join(lines) if lines else ""

def get_devices_to_update(limit=None):
    """Get devices that need notes updates from database"""
    logger.info("Getting devices from database...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get enriched circuit data for clean notes
    cursor.execute("""
        SELECT 
            mi.device_serial,
            mi.network_name,
            mi.device_model,
            ec.wan1_provider,
            ec.wan1_speed,
            ec.wan2_provider, 
            ec.wan2_speed
        FROM meraki_inventory mi
        LEFT JOIN enriched_circuits ec ON mi.network_name = ec.network_name
        WHERE mi.device_model LIKE 'MX%'
        AND mi.device_serial IS NOT NULL
        ORDER BY mi.network_name
        {} 
    """.format(f"LIMIT {limit}" if limit else ""))
    
    devices = []
    for row in cursor.fetchall():
        device_serial, network_name, device_model, w1p, w1s, w2p, w2s = row
        
        # Format clean notes
        clean_notes = format_clean_notes(w1p or "", w1s or "", w2p or "", w2s or "")
        
        devices.append({
            "device_serial": device_serial,
            "network_name": network_name,
            "device_model": device_model,
            "wan1_provider": w1p or "",
            "wan1_speed": w1s or "",
            "wan2_provider": w2p or "",
            "wan2_speed": w2s or "",
            "clean_notes": clean_notes
        })
    
    cursor.close()
    conn.close()
    
    logger.info(f"Found {len(devices)} MX devices to process")
    return devices

def get_current_device_notes(device_serial):
    """Get current notes for a specific device"""
    device_url = f"{BASE_URL}/devices/{device_serial}"
    device_info = make_api_request(device_url)
    
    if "error" in device_info:
        return None
    
    return device_info.get("notes", "") or ""

def update_device_notes(device_serial, new_notes):
    """Update notes for a specific device"""
    device_url = f"{BASE_URL}/devices/{device_serial}"
    data = {"notes": new_notes}
    
    result = make_api_request(device_url, method="PUT", data=data)
    return result

def restore_notes(dry_run=True, limit=None, specific_sites=None):
    """Main restoration function"""
    logger.info(f"Starting notes restoration (dry_run={dry_run}, limit={limit})...")
    
    devices = get_devices_to_update(limit=limit)
    
    # Filter to specific sites if requested
    if specific_sites:
        devices = [d for d in devices if d["network_name"] in specific_sites]
        logger.info(f"Filtered to {len(devices)} devices for specific sites: {specific_sites}")
    
    results = {
        "total_processed": 0,
        "needs_update": 0,
        "already_correct": 0,
        "updated_successfully": 0,
        "update_failed": 0,
        "details": []
    }
    
    for i, device in enumerate(devices):
        device_serial = device["device_serial"]
        network_name = device["network_name"]
        expected_notes = device["clean_notes"]
        
        logger.info(f"Processing {i+1}/{len(devices)}: {network_name} ({device_serial})")
        
        # Get current notes
        current_notes = get_current_device_notes(device_serial)
        if current_notes is None:
            logger.error(f"Failed to get current notes for {network_name}")
            results["update_failed"] += 1
            continue
        
        results["total_processed"] += 1
        
        # Check if update is needed
        needs_update = current_notes.strip() != expected_notes.strip()
        
        detail = {
            "device_serial": device_serial,
            "network_name": network_name,
            "current_notes": current_notes[:100] + "..." if len(current_notes) > 100 else current_notes,
            "expected_notes": expected_notes,
            "needs_update": needs_update,
            "wan1": f"{device['wan1_provider']} ({device['wan1_speed']})",
            "wan2": f"{device['wan2_provider']} ({device['wan2_speed']})"
        }
        
        if not needs_update:
            logger.info(f"  ✅ Already correct")
            results["already_correct"] += 1
            detail["action"] = "no_change_needed"
        else:
            results["needs_update"] += 1
            logger.info(f"  📝 Needs update")
            logger.info(f"     Current: {current_notes[:50]}...")
            logger.info(f"     Expected: {expected_notes}")
            
            if not dry_run:
                # Actually update the device
                update_result = update_device_notes(device_serial, expected_notes)
                
                if "error" in update_result:
                    logger.error(f"  ❌ Update failed: {update_result['error']}")
                    results["update_failed"] += 1
                    detail["action"] = "update_failed"
                    detail["error"] = update_result["error"]
                else:
                    logger.info(f"  ✅ Updated successfully")
                    results["updated_successfully"] += 1
                    detail["action"] = "updated"
            else:
                detail["action"] = "would_update"
        
        results["details"].append(detail)
        
        # Rate limiting - small delay between devices
        if not dry_run:
            time.sleep(0.5)
    
    # Summary
    logger.info("=== RESTORATION SUMMARY ===")
    logger.info(f"Total Processed: {results['total_processed']}")
    logger.info(f"Already Correct: {results['already_correct']}")
    logger.info(f"Need Update: {results['needs_update']}")
    if not dry_run:
        logger.info(f"Updated Successfully: {results['updated_successfully']}")
        logger.info(f"Update Failed: {results['update_failed']}")
    
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Restore Meraki device notes to clean format")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Show what would be updated without making changes")
    parser.add_argument("--execute", action="store_true", help="Actually perform the updates")
    parser.add_argument("--limit", type=int, help="Limit number of devices to process")
    parser.add_argument("--sites", nargs="+", help="Specific site names to update")
    
    args = parser.parse_args()
    
    dry_run = not args.execute
    
    if dry_run:
        logger.info("🔍 DRY RUN MODE - No changes will be made")
    else:
        logger.info("🚀 EXECUTE MODE - Changes will be made to Meraki devices")
    
    results = restore_notes(dry_run=dry_run, limit=args.limit, specific_sites=args.sites)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"/tmp/notes_restoration_{timestamp}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\\nResults saved to: {results_file}")
    if dry_run:
        print("\\nTo actually perform updates, run with --execute flag")
    print(f"\\nDevices needing update: {results['needs_update']}")