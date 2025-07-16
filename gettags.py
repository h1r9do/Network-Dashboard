#!/usr/bin/env python3
import os
import time
import json
import requests
from dotenv import load_dotenv

# ─── Load env vars ─────────────────────────────────────────────────────────────
load_dotenv('/usr/local/bin/meraki.env')
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
ORG_NAME       = os.getenv("ORG_NAME")

if not MERAKI_API_KEY:
    raise RuntimeError("MERAKI_API_KEY not set in /usr/local/bin/meraki.env")
if not ORG_NAME:
    raise RuntimeError("ORG_NAME not set in /usr/local/bin/meraki.env")

BASE_URL = "https://api.meraki.com/api/v1"

def make_api_request(url, api_key, params=None):
    headers = {
        "X-Cisco-Meraki-API-Key": api_key,
        "Content-Type": "application/json"
    }
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()

def get_organization_id():
    """Look up the Meraki organization ID by name."""
    url = f"{BASE_URL}/organizations"
    for org in make_api_request(url, MERAKI_API_KEY):
        if org.get("name") == ORG_NAME:
            return org.get("id")
    raise ValueError(f"Organization '{ORG_NAME}' not found")

def get_all_networks(org_id):
    """Retrieve all networks in the organization (paginated)."""
    all_nets = []
    url = f"{BASE_URL}/organizations/{org_id}/networks"
    params = {'perPage': 1000, 'startingAfter': None}
    while True:
        batch = make_api_request(url, MERAKI_API_KEY, params=params)
        if not batch:
            break
        all_nets.extend(batch)
        if len(batch) < params['perPage']:
            break
        params['startingAfter'] = batch[-1]['id']
        print(f"Fetched {len(batch)} networks (total {len(all_nets)})")
    return all_nets

def get_devices(network_id):
    """Retrieve all devices for a given network."""
    url = f"{BASE_URL}/networks/{network_id}/devices"
    return make_api_request(url, MERAKI_API_KEY)

def get_device_details(serial):
    """Retrieve the device record (including its tags)."""
    url = f"{BASE_URL}/devices/{serial}"
    return make_api_request(url, MERAKI_API_KEY)

def main():
    org_id = get_organization_id()
    print(f"Using Organization ID: {org_id}\n")

    networks = get_all_networks(org_id)
    print(f"\nTotal networks retrieved: {len(networks)}\n")

    mx_entries = []

    for net in networks:
        net_id   = net['id']
        net_name = net.get('name')

        devices = get_devices(net_id)
        for dev in devices:
            model = dev.get('model', '').upper()
            if model.startswith('MX'):
                serial = dev['serial']
                # pull the device record to get its tags
                details     = get_device_details(serial)
                device_tags = details.get('tags', [])

                # print each MX’s tags as we go
                print(f"MX {serial} ({dev.get('name')}) tags: {device_tags}")

                mx_entries.append({
                    "network_id":    net_id,
                    "network_name":  net_name,
                    "device_serial": serial,
                    "device_model":  dev.get('model'),
                    "device_name":   dev.get('name'),
                    "device_tags":   device_tags
                })

                # rate-limit courtesy
                time.sleep(0.2)

    out_file = "/var/www/html/meraki-data/mx_inventory_full.json"
    with open(out_file, 'w') as f:
        json.dump(mx_entries, f, indent=2)

    print(f"\nSaved {len(mx_entries)} MX devices (with their tags) to {out_file}")

if __name__ == "__main__":
    main()
