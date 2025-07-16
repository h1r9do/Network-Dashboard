#!/usr/bin/env python3
"""
Update Meraki DEVICE tags from CSV file
This version updates tags at the device level to match where we read them from
"""

import csv
import json
import os
import requests
import time
import re
import argparse
from datetime import datetime
from dotenv import load_dotenv
import collections

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
LIVE_JSON = "/var/www/html/meraki-data/mx_inventory_live.json"
DATA_DIRECTORY = "/var/www/html/meraki-data/"

# API limits (Meraki allows ~1000 requests per 5 minutes)
MAX_REQUESTS = 900  # Buffer below 1000 to be safe
REQUEST_WINDOW = 300  # 5 minutes in seconds
REQUESTS = []  # Track timestamps of requests

def log_message(message, log_file):
    print(message)
    with open(log_file, 'a') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def get_headers():
    return {
        "X-Cisco-Meraki-API-Key": os.getenv("MERAKI_API_KEY"),
        "Content-Type": "application/json"
    }

def clean_request_timestamps():
    global REQUESTS
    current_time = time.time()
    REQUESTS = [t for t in REQUESTS if current_time - t < REQUEST_WINDOW]

def make_api_update(url, data, max_retries=5, backoff_factor=1, log_file=None):
    headers = get_headers()
    for attempt in range(max_retries):
        clean_request_timestamps()
        if len(REQUESTS) >= MAX_REQUESTS:
            time.sleep(REQUEST_WINDOW / MAX_REQUESTS)  # Simple rate limit adjustment
            clean_request_timestamps()
        
        try:
            response = requests.put(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            REQUESTS.append(time.time())
            return {"success": True}
        except requests.exceptions.RequestException as e:
            if response.status_code == 429:  # Too Many Requests
                wait_time = backoff_factor * (2 ** attempt) + (attempt * 0.1)  # Exponential backoff with jitter
                log_message(f"Rate limit hit, backing off for {wait_time} seconds (attempt {attempt + 1}/{max_retries})", log_file)
                time.sleep(wait_time)
            elif attempt == max_retries - 1:
                return {"error": str(e)}
            else:
                time.sleep(backoff_factor * (2 ** attempt))  # Backoff for other errors
    return {"error": "Max retries exceeded"}

def make_api_get(url, max_retries=3, backoff_factor=1, log_file=None):
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
                if log_file:
                    log_message(f"Failed to GET {url}: {str(e)}", log_file)
                return None
            time.sleep(backoff_factor * (2 ** attempt))
    return None

def normalize_string(s):
    if not s:
        return "UNKNOWN"
    return re.sub(r'\s+', ' ', s.strip()).upper()

def update_device_tags_from_csv(csv_filename):
    # Construct full paths
    input_csv = os.path.join(DATA_DIRECTORY, csv_filename)
    csv_basename = os.path.splitext(csv_filename)[0]
    log_file = os.path.join(DATA_DIRECTORY, f"device_tags_update_log_{csv_basename}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt")
    
    # Check if files exist
    if not os.path.exists(LIVE_JSON):
        print(f"Error: Missing {LIVE_JSON}")
        return
    
    if not os.path.exists(input_csv):
        print(f"Error: CSV file not found: {input_csv}")
        print(f"Make sure {csv_filename} is in the {DATA_DIRECTORY} directory")
        return

    log_message(f"Starting DEVICE tag update from {csv_filename}", log_file)
    log_message(f"Full CSV path: {input_csv}", log_file)
    log_message(f"Log file: {log_file}", log_file)
    
    try:
        with open(LIVE_JSON, 'r') as f:
            live_data = json.load(f)
    except Exception as e:
        log_message(f"Error reading {LIVE_JSON}: {str(e)}", log_file)
        return

    # Load CSV data into a dictionary, deduplicating by network name
    csv_data = {}
    try:
        with open(input_csv, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
            reader = csv.DictReader(f)
            log_message(f"CSV columns found: {reader.fieldnames}", log_file)
            
            # Find the Network column (handle BOM and case variations)
            network_column = None
            for col in reader.fieldnames:
                if col.strip().lower() in ['network', 'network name']:
                    network_column = col
                    break
            
            if not network_column:
                log_message(f"Error: Could not find 'Network' column in CSV. Available columns: {reader.fieldnames}", log_file)
                return
            
            log_message(f"Using column '{network_column}' for network names", log_file)
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 since row 1 is headers
                network_name = row.get(network_column, '').strip()
                if not network_name:
                    continue
                    
                normalized_name = normalize_string(network_name)
                if normalized_name not in csv_data:
                    discount_tire = row.get('Discount-Tire', '').strip().lower() == 'yes'
                    tags = [tag.strip() for tag in [
                        row.get('Tag 1', ''), 
                        row.get('Tag 2', ''), 
                        row.get('Tag 3', ''), 
                        row.get('Tag 4', ''), 
                        row.get('Tag 5', '')
                    ] if tag and tag.strip()]
                    
                    if discount_tire:
                        tags.append("Discount-Tire")
                    # Remove underscores from tags for Meraki compatibility
                    tags = [tag.replace('_', '-') for tag in tags]
                    csv_data[normalized_name] = tags
                    log_message(f"Loaded network: {network_name} -> Tags: {', '.join(tags) if tags else 'No tags'}", log_file)
                else:
                    log_message(f"Duplicate entry for {network_name} in row {row_num}, using first occurrence", log_file)
                    
    except Exception as e:
        log_message(f"Error reading {input_csv}: {str(e)}", log_file)
        return

    log_message(f"Loaded {len(csv_data)} unique networks from CSV", log_file)

    # Create a mapping of network_name to device_serial(s) from live data
    network_to_devices = {}
    for entry in live_data:
        network_name = normalize_string(entry.get('network_name', 'UNKNOWN'))
        device_serial = entry.get('device_serial')
        if network_name != 'UNKNOWN' and device_serial:
            if network_name not in network_to_devices:
                network_to_devices[network_name] = []
            if device_serial not in network_to_devices[network_name]:
                network_to_devices[network_name].append(device_serial)
    
    log_message(f"Live inventory contains {len(network_to_devices)} networks with devices", log_file)

    # Update Meraki device tags
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for network_name, tags in csv_data.items():
        if network_name == 'UNKNOWN' or network_name not in network_to_devices:
            log_message(f"Skipping {network_name}: No matching devices in live inventory", log_file)
            skipped_count += 1
            continue

        device_serials = network_to_devices[network_name]
        log_message(f"\nProcessing {network_name} with {len(device_serials)} device(s)", log_file)
        
        for device_serial in device_serials:
            # Fetch current device details to compare tags
            url = f"https://api.meraki.com/api/v1/devices/{device_serial}"
            try:
                current_data = make_api_get(url, log_file=log_file)
                if not current_data:
                    log_message(f"Error fetching device {device_serial}", log_file)
                    error_count += 1
                    continue
                    
                current_tags = current_data.get('tags', [])
                
                # Compare tag lists directly (Meraki expects array format)
                if set(current_tags) != set(tags):  # Update only if tags differ
                    log_message(f"  Tags differ for device {device_serial}. Current: {current_tags} -> New: {tags}", log_file)
                    update_data = {"tags": tags}  # Send as array
                    result = make_api_update(url, update_data, log_file=log_file)
                    if result.get('success'):
                        log_message(f"  ✓ Successfully updated device {device_serial} tags to: {tags}", log_file)
                        updated_count += 1
                    else:
                        log_message(f"  ✗ Failed to update device {device_serial}: {result.get('error')}", log_file)
                        error_count += 1
                else:
                    log_message(f"  No change needed for device {device_serial} - tags already match", log_file)
                    
            except Exception as e:
                log_message(f"  Error processing device {device_serial}: {str(e)}", log_file)
                error_count += 1

    log_message(f"\n=== SUMMARY ===", log_file)
    log_message(f"Device tag update completed for {csv_filename}", log_file)
    log_message(f"Devices successfully updated: {updated_count}", log_file)
    log_message(f"Networks skipped (no devices): {skipped_count}", log_file)
    log_message(f"Devices with errors: {error_count}", log_file)
    log_message(f"Total networks processed from CSV: {len(csv_data)}", log_file)
    log_message(f"Log saved to: {log_file}", log_file)

def main():
    parser = argparse.ArgumentParser(
        description="Update Meraki DEVICE tags from a CSV file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 update_device_tags_from_csv.py tags_other.csv
  python3 update_device_tags_from_csv.py my_network_tags.csv

CSV file must be located in: /var/www/html/meraki-data/

Required CSV columns:
  - Network: Network name
  - Discount-Tire: "yes" or "no" 
  - Tag 1, Tag 2, Tag 3, Tag 4, Tag 5: Tag values (optional)

This script updates tags at the DEVICE level, not network level.
        """
    )
    
    parser.add_argument(
        'csv_file',
        help='CSV filename (must be in /var/www/html/meraki-data/ directory)'
    )
    
    args = parser.parse_args()
    
    # Validate that it's just a filename, not a path
    if '/' in args.csv_file or '\\' in args.csv_file:
        print("Error: Please provide just the filename, not a full path.")
        print(f"The file should be located in: {DATA_DIRECTORY}")
        return
    
    # Validate file extension
    if not args.csv_file.lower().endswith('.csv'):
        print("Warning: File doesn't have .csv extension, but proceeding anyway...")
    
    print(f"Looking for CSV file: {os.path.join(DATA_DIRECTORY, args.csv_file)}")
    print("This script will make LIVE changes to your Meraki DEVICES!")
    print("Press Ctrl+C now if you want to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return
    
    update_device_tags_from_csv(args.csv_file)

if __name__ == "__main__":
    main()