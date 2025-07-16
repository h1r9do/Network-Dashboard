#!/usr/bin/env python3

import json
import csv
import re
import os

# Define the regex pattern for circuit speed (e.g., "600.0M x 200.0M")
speed_pattern = r"(\d+(?:\.\d+)?M x \d+(?:\.\d+)?M)$"

def parse_label(label):
    """
    Parse a WAN label to extract the circuit provider and speed.
    
    Args:
        label (str): The WAN label string.
    
    Returns:
        tuple: (circuit provider, circuit speed)
    """
    if not label:
        return "", ""
    match = re.search(speed_pattern, label)
    if match:
        speed = match.group(1)
        provider = label[:match.start()].strip()
        return provider, speed
    else:
        return label.strip(), ""

def main():
    # Define file paths
    json_file_path = '/var/www/html/meraki-data/mx_inventory_live.json'
    csv_file_path = '/var/www/html/meraki-data/mx_inventory_live.csv'
    
    # Check if JSON file exists
    if not os.path.exists(json_file_path):
        print(f"Error: JSON file not found at {json_file_path}")
        return
    
    # Load JSON data
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return
    
    # Open CSV file for writing
    with open(csv_file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write headers
        writer.writerow([
            "Site Name",
            "WAN1 Circuit Provider",
            "WAN1 Circuit Speed",
            "WAN1 IP Type",
            "WAN1 ARIN Provider",
            "WAN2 Circuit Provider",
            "WAN2 Circuit Speed",
            "WAN2 IP Type",
            "WAN2 ARIN Provider"
        ])
        
        # Write data rows
        for network in data:
            site_name = network.get("network_name", "")
            wan1_label = network.get("wan1_label", "")
            wan1_provider, wan1_speed = parse_label(wan1_label)
            wan1_ip_type = network.get("wan1_assignment", "")
            wan1_arin_provider = network.get("wan1_provider", "")
            wan2_label = network.get("wan2_label", "")
            wan2_provider, wan2_speed = parse_label(wan2_label)
            wan2_ip_type = network.get("wan2_assignment", "")
            wan2_arin_provider = network.get("wan2_provider", "")
            
            writer.writerow([
                site_name,
                wan1_provider,
                wan1_speed,
                wan1_ip_type,
                wan1_arin_provider,
                wan2_provider,
                wan2_speed,
                wan2_ip_type,
                wan2_arin_provider
            ])

if __name__ == "__main__":
    main()
