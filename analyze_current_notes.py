#!/usr/bin/env python3
"""
Analyze current Meraki device notes vs database vs historical data
Downloads current notes and compares with database and June 24th data
"""

import os
import sys
import json
import requests
import subprocess
import time
from datetime import datetime
from dotenv import load_dotenv
sys.path.insert(0, '/usr/local/bin/Main')
from nightly_meraki_db import get_db_connection
from recover_with_correct_logic import parse_raw_notes_original
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
BASE_URL = "https://api.meraki.com/api/v1"
ORG_NAME = "DTC-Store-Inventory-All"
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

def make_api_request(url, max_retries=3):
    headers = get_headers()
    for attempt in range(max_retries):
        clean_request_timestamps()
        if len(REQUESTS) >= MAX_REQUESTS:
            time.sleep(REQUEST_WINDOW / MAX_REQUESTS)
            clean_request_timestamps()
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            REQUESTS.append(time.time())
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                logger.error(f"API request failed: {e}")
                return {"error": str(e)}
            time.sleep(2 ** attempt)
    return {"error": "Max retries exceeded"}

def get_current_device_notes():
    """Download current notes from all MX devices"""
    logger.info("Getting current device notes from Meraki API...")
    
    # Get organization ID
    orgs_url = f"{BASE_URL}/organizations"
    orgs = make_api_request(orgs_url)
    if "error" in orgs:
        logger.error(f"Failed to get organizations: {orgs['error']}")
        return {}
    
    org_id = None
    for org in orgs:
        if org.get("name") == ORG_NAME:
            org_id = org["id"]
            break
    
    if not org_id:
        logger.error(f"Organization '{ORG_NAME}' not found")
        return {}
    
    logger.info(f"Found organization ID: {org_id}")
    
    # Get all devices
    devices_url = f"{BASE_URL}/organizations/{org_id}/devices"
    devices = make_api_request(devices_url)
    if "error" in devices:
        logger.error(f"Failed to get devices: {devices['error']}")
        return {}
    
    # Filter MX devices and get their notes
    mx_devices = [d for d in devices if d.get("model", "").startswith("MX")]
    logger.info(f"Found {len(mx_devices)} MX devices")
    
    current_notes = {}
    for i, device in enumerate(mx_devices):
        device_serial = device.get("serial")
        network_name = device.get("name", "")
        
        if not device_serial:
            continue
            
        # Get device details including notes
        device_url = f"{BASE_URL}/devices/{device_serial}"
        device_info = make_api_request(device_url)
        
        if "error" not in device_info:
            current_notes[device_serial] = {
                "network_name": network_name,
                "device_serial": device_serial,
                "device_model": device.get("model", ""),
                "raw_notes": device_info.get("notes", "") or "",
                "last_seen": device.get("lastSeen", "")
            }
        
        if (i + 1) % 50 == 0:
            logger.info(f"Downloaded notes for {i + 1}/{len(mx_devices)} devices...")
    
    logger.info(f"Downloaded notes for {len(current_notes)} MX devices")
    return current_notes

def get_historical_notes():
    """Get historical notes from June 24th git data"""
    logger.info("Retrieving historical notes from June 24th...")
    cmd = "git -C /var/www/html/meraki-data show 019677c:mx_inventory_live.json"
    json_content = subprocess.check_output(cmd, shell=True).decode()
    historical_data = json.loads(json_content)
    
    historical_notes = {}
    for device in historical_data:
        device_serial = device.get('device_serial', '')
        if device_serial and device.get('device_model', '').startswith('MX'):
            historical_notes[device_serial] = {
                "network_name": device.get('network_name', ''),
                "device_serial": device_serial,
                "device_model": device.get('device_model', ''),
                "raw_notes": device.get('raw_notes', '') or "",
            }
    
    logger.info(f"Found {len(historical_notes)} MX devices in historical data")
    return historical_notes

def get_database_data():
    """Get current database parsing results"""
    logger.info("Getting database parsing results...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT device_serial, network_name, device_model, device_notes,
               wan1_provider_label, wan1_speed_label,
               wan2_provider_label, wan2_speed_label
        FROM meraki_inventory
        WHERE device_model LIKE 'MX%'
    """)
    
    database_data = {}
    for row in cursor.fetchall():
        device_serial, network_name, device_model, device_notes, w1p, w1s, w2p, w2s = row
        database_data[device_serial] = {
            "network_name": network_name,
            "device_serial": device_serial,
            "device_model": device_model,
            "device_notes": device_notes or "",
            "wan1_provider_label": w1p or "",
            "wan1_speed_label": w1s or "",
            "wan2_provider_label": w2p or "",
            "wan2_speed_label": w2s or "",
        }
    
    cursor.close()
    conn.close()
    
    logger.info(f"Found {len(database_data)} MX devices in database")
    return database_data

def format_expected_notes(wan1_provider, wan1_speed, wan2_provider, wan2_speed):
    """Format notes in the expected format based on database data"""
    lines = []
    
    if wan1_provider and wan1_speed:
        lines.append("WAN 1")
        lines.append(wan1_provider)
        lines.append(wan1_speed)
    
    if wan2_provider and wan2_speed:
        lines.append("WAN 2") 
        lines.append(wan2_provider)
        lines.append(wan2_speed)
    
    return "\n".join(lines) if lines else ""

def analyze_notes_status():
    """Main analysis function"""
    logger.info("Starting comprehensive notes analysis...")
    
    # Get all data sources
    current_notes = get_current_device_notes()
    historical_notes = get_historical_notes()
    database_data = get_database_data()
    
    # Save current notes to temp file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_file = f"/tmp/current_meraki_notes_{timestamp}.json"
    with open(current_file, 'w') as f:
        json.dump(current_notes, f, indent=2)
    logger.info(f"Saved current notes to: {current_file}")
    
    # Analysis
    analysis_results = {
        "total_devices": len(database_data),
        "correct_notes": 0,
        "corrupted_notes": 0,
        "missing_notes": 0,
        "needs_restoration": [],
        "already_correct": [],
        "analysis_details": []
    }
    
    logger.info("Analyzing notes for each device...")
    
    for device_serial, db_data in database_data.items():
        network_name = db_data["network_name"]
        
        # Get current notes
        current = current_notes.get(device_serial, {}).get("raw_notes", "")
        
        # Get historical notes
        historical = historical_notes.get(device_serial, {}).get("raw_notes", "")
        
        # Get expected notes from database
        expected = format_expected_notes(
            db_data["wan1_provider_label"],
            db_data["wan1_speed_label"], 
            db_data["wan2_provider_label"],
            db_data["wan2_speed_label"]
        )
        
        # Parse current notes to see if they match database
        if current:
            try:
                w1p, w1s, w2p, w2s = parse_raw_notes_original(current)
                current_matches = (
                    w1p == db_data["wan1_provider_label"] and
                    w1s == db_data["wan1_speed_label"] and
                    w2p == db_data["wan2_provider_label"] and
                    w2s == db_data["wan2_speed_label"]
                )
            except:
                current_matches = False
        else:
            current_matches = False
        
        # Determine status
        if current_matches and current.strip():
            status = "CORRECT"
            analysis_results["correct_notes"] += 1
            analysis_results["already_correct"].append(device_serial)
        elif not current.strip():
            status = "MISSING"
            analysis_results["missing_notes"] += 1
            analysis_results["needs_restoration"].append(device_serial)
        else:
            status = "CORRUPTED"
            analysis_results["corrupted_notes"] += 1
            analysis_results["needs_restoration"].append(device_serial)
        
        # Store detailed analysis
        analysis_results["analysis_details"].append({
            "device_serial": device_serial,
            "network_name": network_name,
            "status": status,
            "current_notes": current[:100] + "..." if len(current) > 100 else current,
            "expected_notes": expected[:100] + "..." if len(expected) > 100 else expected,
            "historical_notes": historical[:100] + "..." if len(historical) > 100 else historical,
            "current_matches_db": current_matches
        })
    
    # Save analysis results
    analysis_file = f"/tmp/notes_analysis_{timestamp}.json"
    with open(analysis_file, 'w') as f:
        json.dump(analysis_results, f, indent=2)
    
    # Print summary
    logger.info("=== NOTES ANALYSIS SUMMARY ===")
    logger.info(f"Total MX Devices: {analysis_results['total_devices']}")
    logger.info(f"Correct Notes: {analysis_results['correct_notes']}")
    logger.info(f"Corrupted Notes: {analysis_results['corrupted_notes']}")
    logger.info(f"Missing Notes: {analysis_results['missing_notes']}")
    logger.info(f"Need Restoration: {len(analysis_results['needs_restoration'])}")
    logger.info(f"Analysis saved to: {analysis_file}")
    
    return analysis_results, current_file, analysis_file

if __name__ == "__main__":
    try:
        results, current_file, analysis_file = analyze_notes_status()
        print(f"\nCurrent notes saved to: {current_file}")
        print(f"Analysis results saved to: {analysis_file}")
        print(f"\nDevices needing restoration: {len(results['needs_restoration'])}")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise