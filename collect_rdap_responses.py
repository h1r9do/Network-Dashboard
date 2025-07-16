import json
import ipaddress
import requests
import time
from pathlib import Path
import os

# Configuration
JSON_FILE = "/var/www/html/meraki-data/mx_inventory_live.json"
OUTPUT_FILE = "/var/www/html/meraki-data/rdap_full_responses.json"
LOG_FILE = "/var/www/html/meraki-data/rdap_query.log"
RDAP_URL = "https://rdap.arin.net/registry/ip/{ip}"
RETRY_COUNT = 3  # Number of retries for RDAP API
RETRY_BACKOFF = 2  # Initial backoff in seconds
QUERY_DELAY = 1.0  # Delay between queries in seconds

def log_message(message):
    """Append a message to the log file."""
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {message}\n")
    except Exception as e:
        print(f"Error writing to log file {LOG_FILE}: {e}")

def load_json(file_path):
    """Read JSON from a file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        log_message(f"Error reading {file_path}: {e}")
        return []

def append_json(data, file_path):
    """Append a JSON object to an array in a file, maintaining valid JSON."""
    try:
        # Initialize file with empty array if it doesn't exist
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump([], f)
            log_message(f"Initialized {file_path} with empty array")

        # Read current content
        with open(file_path, 'r') as f:
            current_data = json.load(f)

        # Append new data
        current_data.append(data)

        # Write back to file
        with open(file_path, 'w') as f:
            json.dump(current_data, f, indent=2)
        log_message(f"Appended data to {file_path}")
    except Exception as e:
        log_message(f"Error appending to {file_path}: {e}")

def fetch_json(url, ip, retries=RETRY_COUNT, backoff=RETRY_BACKOFF):
    """Fetch JSON from a URL with retries, logging the IP being queried."""
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10, headers={"User-Agent": "Meraki-IP-Lookup/1.0"})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            log_message(f"Attempt {attempt + 1}/{retries} failed for IP {ip} at {url}: {e}")
            if 'response' in locals():
                log_message(f"Status Code: {response.status_code}, Response Text: {response.text[:100]}")
            if attempt < retries - 1:
                time.sleep(backoff * (2 ** attempt))
        except ValueError as e:
            log_message(f"Attempt {attempt + 1}/{retries} failed for IP {ip} at {url}: Invalid JSON - {e}")
            if 'response' in locals():
                log_message(f"Status Code: {response.status_code}, Response Text: {response.text[:100]}")
            if attempt < retries - 1:
                time.sleep(backoff * (2 ** attempt))
    log_message(f"Exhausted retries for IP {ip} at {url}")
    return None

def collect_rdap_responses(data):
    """Collect full RDAP responses for non-private IPs."""
    for entry in data:
        network_name = entry.get('network_name', 'Unknown')
        for wan in ['wan1', 'wan2']:
            wan_data = entry.get(wan, {})
            ip = wan_data.get('ip', '')
            if not ip:
                continue

            try:
                ip_addr = ipaddress.ip_address(ip)
                if ip_addr.is_private:
                    log_message(f"Skipping private IP {ip} in {network_name}")
                    continue
            except ValueError:
                log_message(f"Invalid IP {ip} in {network_name}")
                continue

            log_message(f"Querying ARIN RDAP for IP {ip}")
            url = RDAP_URL.format(ip=ip)
            response_data = fetch_json(url, ip)
            if response_data:
                # Create a record with IP and RDAP response
                record = {"ip": ip, "network_name": network_name, "rdap_response": response_data}
                append_json(record, OUTPUT_FILE)
                log_message(f"Retrieved and saved RDAP response for IP {ip}")
            else:
                log_message(f"No RDAP response for IP {ip}")
            time.sleep(QUERY_DELAY)  # Rate limit queries

def main():
    log_message("🔍 Collecting Full RDAP Responses")

    # Load JSON data
    data = load_json(JSON_FILE)
    if not data:
        log_message("No data to process. Exiting.")
        return

    # Ensure output file is initialized
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)  # Clear existing file to start fresh
    append_json([], OUTPUT_FILE)  # Initialize with empty array

    # Collect RDAP responses
    collect_rdap_responses(data)

    log_message("✅ RDAP Response Collection Complete")

if __name__ == "__main__":
    main()
