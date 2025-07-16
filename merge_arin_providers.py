#!/usr/bin/env python3
"""
Script to merge ARIN provider data with Meraki MX inventory and log 'no match' scenarios.
"""

import json
import ipaddress
from fuzzywuzzy import fuzz

# Configuration
MX_INVENTORY_FILE = "/var/www/html/meraki-data/meraki_mx_inventory.json"
LOG_FILE = "/var/www/html/meraki-data/no_matches.log"
FUZZY_MATCH_THRESHOLD = 80  # Threshold for fuzzy matching provider names

# Provider aliases to standardize names
PROVIDER_ALIASES = {
    "at&t": ["at&t", "at&t internet services", "at&t services, inc.", "att"],
    "charter": ["charter communications", "charter communications llc", "spectrum"],
    "comcast": ["comcast", "comcast cable communications, llc", "xfinity"],
    "verizon": ["verizon", "verizon business", "vz"],
    "cox": ["cox communications", "cox communications inc"],
    "lumen": ["lumen", "lumen technologies, inc", "centurylink"],
    "c spire": ["c spire", "dsr c spire"],
    "cogent": ["cogent communications"],
    "t-mobile": ["t-mobile", "t-mobile usa, inc"],
    # Add more aliases as needed
}

def load_json(file_path):
    """Load JSON data from a file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            print(f"Loaded {len(data)} entries from {file_path}")
            return data
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def standardize_provider_name(provider):
    """Standardize provider names using aliases."""
    if not provider:
        return ""
    provider_lower = provider.lower().strip()
    for standard, aliases in PROVIDER_ALIASES.items():
        if provider_lower in aliases or any(fuzz.partial_ratio(provider_lower, alias) > FUZZY_MATCH_THRESHOLD for alias in aliases):
            return standard
    return provider_lower

def compare_providers(label_provider, arin_provider):
    """Compare standardized provider names."""
    if not label_provider or not arin_provider:
        return "no match"
    label_standard = standardize_provider_name(label_provider)
    arin_standard = standardize_provider_name(arin_provider)
    if label_standard == arin_standard or fuzz.partial_ratio(label_standard, arin_standard) > FUZZY_MATCH_THRESHOLD:
        return "match"
    return "no match"

def is_private_ip(ip):
    """Check if the IP is private."""
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False

def evaluate_provider_matches(mx_data, log_file):
    with open(log_file, 'w') as f:
        for entry in mx_data:
            network_name = entry.get("network_name", "Unknown Network")
            for wan in ['wan1', 'wan2']:
                wan_data = entry.get(wan)
                if wan_data is None:
                    continue  # Skip if no data for this WAN

                ip = (wan_data.get('ip') or '').strip()
                if not ip or is_private_ip(ip):
                    continue  # Skip private or missing IPs

                label_provider = (wan_data.get('provider_label') or '').strip()
                arin_provider = (wan_data.get('provider') or '').strip()

                if not label_provider or not arin_provider:
                    continue  # Skip if no provider data

                comparison = compare_providers(label_provider, arin_provider)
                if comparison == "no match":
                    log_entry = f"{network_name}, {wan.upper()}, {ip}, {label_provider}, {arin_provider}\n"
                    f.write(log_entry)
                    print(log_entry.strip())  # Also print to screen

def main():
    """Main function to execute the evaluation and logging."""
    mx_data = load_json(MX_INVENTORY_FILE)
    if not mx_data:
        print("Failed to load MX inventory data. Exiting.")
        return

    evaluate_provider_matches(mx_data, LOG_FILE)
    print(f"No match scenarios have been logged to {LOG_FILE}")

if __name__ == "__main__":
    main()