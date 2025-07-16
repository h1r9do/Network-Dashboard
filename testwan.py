#!/usr/bin/env python3

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Fetch API key and organization name from the environment
API_KEY = os.getenv("MERAKI_API_KEY")
ORG_NAME = os.getenv("ORG_NAME")
BASE_URL = "https://api.meraki.com/api/v1"

# Setup headers for the API request
def get_headers(api_key):
    return {
        "X-Cisco-Meraki-API-Key": api_key,
        "Content-Type": "application/json"
    }

# Make the API request and handle response
def make_api_request(url, api_key):
    headers = get_headers(api_key)
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check for request errors
        return response.json()  # Return the JSON data if successful
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error: {e}")
        return {}

# Fetch organization ID by name
def get_organization_id(org_name, api_key):
    url = f"{BASE_URL}/organizations"
    organizations = make_api_request(url, api_key)
    for org in organizations:
        if org["name"] == org_name:
            return org["id"]
    return None

# Fetch uplink statuses for a specific network
def get_uplink_statuses(network_id, api_key):
    url = f"{BASE_URL}/networks/{network_id}/appliance/uplinkStatuses"
    return make_api_request(url, api_key)

def main():
    if not API_KEY or not ORG_NAME:
        print("API Key or Organization Name is missing. Please check your environment variables.")
        return

    # Fetch organization ID based on the ORG_NAME
    org_id = get_organization_id(ORG_NAME, API_KEY)

    if not org_id:
        print(f"Organization '{ORG_NAME}' not found.")
        return

    print(f"Using Organization ID: {org_id}")

    # Specify the network ID you want to query
    network_id = 'L_650207196201636678'  # Replace with your specific network ID

    # Fetch uplink statuses for this network
    uplink_statuses = get_uplink_statuses(network_id, API_KEY)
    
    if uplink_statuses:
        print(f"Uplink Statuses for Network {network_id}:")
        for uplink in uplink_statuses:
            interface = uplink.get("interface", "N/A")
            ip_address = uplink.get("ip", "N/A")
            ip_assignment = uplink.get("ipAssignedBy", "N/A")

            # Print the uplink details
            print(f"Interface: {interface}")
            print(f"IP Address: {ip_address}")
            print(f"IP Assignment: {ip_assignment}")
            print("-" * 40)
    else:
        print("No uplink status data found for this network.")

if __name__ == "__main__":
    main()

