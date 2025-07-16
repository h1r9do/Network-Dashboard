import json
import csv
import os
from fuzzywuzzy import fuzz
from datetime import datetime

# File paths
MX_INVENTORY_FILE = "/var/www/html/meraki-data/meraki_mx_inventory.json"
TRACKING_DATA_DIR = "/var/www/html/circuitinfo/"
OUTPUT_MERGED_FILE = "/var/www/html/merged_circuits.json"
FUZZY_MATCH_THRESHOLD = 80  # Threshold for fuzzy matching provider names

# Provider aliases to standardize names (same as in the original script)
PROVIDER_ALIASES = {
    "at&t": ["at&t", "at&t internet services", "att", "at&t broadband"],
    "charter": ["charter", "spectrum"],
    # Add more provider aliases here as needed
}

def standardize_provider_name(provider):
    """Standardize provider names using aliases."""
    if not provider:
        return ""
    provider_lower = provider.lower().strip()
    for standard, aliases in PROVIDER_ALIASES.items():
        if provider_lower in aliases or any(fuzz.partial_ratio(provider_lower, alias) > FUZZY_MATCH_THRESHOLD for alias in aliases):
            return standard
    return provider_lower

def compare_providers(provider1, provider2):
    """Compare standardized provider names."""
    if not provider1 or not provider2:
        return "no match"
    standard1 = standardize_provider_name(provider1)
    standard2 = standardize_provider_name(provider2)
    if standard1 == standard2 or fuzz.partial_ratio(standard1, standard2) > FUZZY_MATCH_THRESHOLD:
        return "match"
    return "no match"

def load_json(file_path):
    """Load JSON data from a file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            return data
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def load_tracking_data(file_path):
    """Load circuit data from a CSV file."""
    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def match_interface(circuit, meraki_data):
    """Match a circuit to a WAN interface based on provider."""
    circuit_provider = (circuit.get('provider_name') or '').strip()
    site_name = (circuit.get('Site Name') or '').strip()

    if not circuit_provider or not site_name:
        return 'N/A'

    for device in meraki_data:
        json_network_name = (device.get('network_name') or '').strip()
        if site_name.lower() == json_network_name.lower():
            for wan in ['wan1', 'wan2']:
                wan_data = device.get(wan)
                if wan_data:
                    label_provider = (wan_data.get('provider_label') or '').strip()
                    arin_provider = (wan_data.get('provider') or '').strip()
                    if (compare_providers(circuit_provider, label_provider) == 'match' or 
                        compare_providers(circuit_provider, arin_provider) == 'match'):
                        return wan.upper()
    return 'N/A'

def build_merged_json():
    """Build and save a merged JSON file."""
    # Load Meraki inventory
    meraki_data = load_json(MX_INVENTORY_FILE)

    # Find the most recent CSV file and load its data
    latest_file = max([f for f in os.listdir(TRACKING_DATA_DIR) if f.endswith('.csv')], key=lambda f: os.path.getctime(os.path.join(TRACKING_DATA_DIR, f)))
    tracking_data = load_tracking_data(os.path.join(TRACKING_DATA_DIR, latest_file))

    merged_data = []

    for circuit in tracking_data:
        site_name = (circuit.get('Site Name') or '').strip()
        if site_name:
            interface = match_interface(circuit, meraki_data)
            circuit['interface'] = interface  # Add interface data to the circuit
            merged_data.append(circuit)

    # Save the merged data to a JSON file
    with open(OUTPUT_MERGED_FILE, 'w') as f:
        json.dump(merged_data, f)

    print(f"Merged data saved to {OUTPUT_MERGED_FILE}")

if __name__ == '__main__':
    build_merged_json()

