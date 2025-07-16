import os
import json
import requests
import csv
import time
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration constants
BASE_URL = "https://api.meraki.com/api/v1"
DATA_DIR = "/var/www/html/meraki-data"
INVENTORY_FILE = os.path.join(DATA_DIR, 'mx_inventory_live.json')

# Load API key from environment
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
if not MERAKI_API_KEY:
    raise RuntimeError("MERAKI_API_KEY not set in /usr/local/bin/meraki.env")

def update_network_tags(network_id, tags):
    """Update the tags for a given network ID."""
    url = f"{BASE_URL}/networks/{network_id}"
    headers = {
        "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
        "Content-Type": "application/json"
    }
    data = {"tags": tags}
    try:
        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()
        print(f"Updated tags for network {network_id}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to update tags for network {network_id}: {e}")

def main(csv_file):
    # Load the inventory JSON to map network names to IDs
    with open(INVENTORY_FILE, 'r') as f:
        inventory = json.load(f)
    
    # Create a mapping of network_name to network_id
    network_map = {}
    for entry in inventory:
        name = entry['network_name']
        net_id = entry['network_id']
        if name not in network_map:
            network_map[name] = net_id
        elif network_map[name] != net_id:
            print(f"Warning: Duplicate network name '{name}' with different IDs")
    
    # Read the CSV file and update tags
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            network_name = row[0].strip()
            new_tags = [tag.strip() for tag in row[1:] if tag.strip()]  # All columns after network_name are tags
            if network_name not in network_map:
                print(f"Network '{network_name}' not found in inventory")
                continue
            network_id = network_map[network_name]
            print(f"Updating network '{network_name}' to tags {new_tags}")
            update_network_tags(network_id, new_tags)
            time.sleep(0.2)  # Avoid hitting API rate limits

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_network_tags.py <csv_file>")
        sys.exit(1)
    csv_file = sys.argv[1]
    if not os.path.exists(csv_file):
        print(f"CSV file '{csv_file}' does not exist")
        sys.exit(1)
    main(csv_file)