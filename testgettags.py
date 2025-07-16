import requests
import json
import os

BASE_URL = "https://api.meraki.com/api/v1"
MERAKI_API_KEY = os.environ.get("MERAKI_API_KEY")

def make_api_request(url, api_key, max_retries=5):
    headers = {"X-Cisco-Meraki-API-Key": api_key}
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                print(f"Failed to fetch {url} after {max_retries} attempts: {e}")
                return []
            time.sleep(2 ** attempt)  # Exponential backoff
    return []

def get_device_details(serial):
    """Retrieve the device record (including its tags)."""
    url = f"{BASE_URL}/devices/{serial}"
    return make_api_request(url, MERAKI_API_KEY)

def append_to_json_file(filename, device_entry):
    """Append device entry to JSON file, ensuring proper formatting."""
    data = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            data = []
    data.append(device_entry)
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

# Example main loop (adjust based on your full script)
organizations = make_api_request(f"{BASE_URL}/organizations", MERAKI_API_KEY)
for org in organizations:
    networks = make_api_request(f"{BASE_URL}/organizations/{org['id']}/networks", MERAKI_API_KEY)
    for net in networks:
        net_id = net["id"]
        net_name = net.get("name", "")
        devices = make_api_request(f"{BASE_URL}/networks/{net_id}/devices", MERAKI_API_KEY)
        for device in devices:
            if device["model"].startswith("MX"):
                serial = device["serial"]
                model = device["model"]
                device_details = get_device_details(serial)
                tags = device_details.get("tags", []) if device_details else []
                
                # Debug statement to verify tags
                print(f"Device {serial} tags: {tags}")
                
                device_entry = {
                    "network_id": net_id,
                    "device_tags": tags,  # Renamed to clarify these are device tags
                    "network_name": net_name,
                    "device_serial": serial,
                    "device_model": model,
                    "device_name": device.get("name", "")
                }
                append_to_json_file("/var/www/html/meraki-data/mx_inventory_live.json", device_entry)
