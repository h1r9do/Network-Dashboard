#!/usr/bin/env python
import time
import requests
import json
from datetime import datetime
from splunklib.modularinput import Script, EventWriter

MERAKI_API_KEY = "your_api_key"
NETWORK_IDS = ["L_123456789", "L_987654321"]  # Your Meraki network IDs
SPLUNK_HEC_URL = "https://your-splunk-server:8088/services/collector"
SPLUNK_HEC_TOKEN = "your-hec-token"
MAX_REQUESTS_PER_SECOND = 1

def get_air_marshal_data(network_id):
    url = f"https://api.meraki.com/api/v1/networks/{network_id}/wireless/airMarshal"
    headers = {
        "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    return response.json()

def send_to_splunk(events):
    headers = {
        "Authorization": f"Splunk {SPLUNK_HEC_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(SPLUNK_HEC_URL, headers=headers, data=json.dumps(events), verify=False)
    return response.status_code

def process_network(network_id):
    time.sleep(1/MAX_REQUESTS_PER_SECOND)  # Strict rate limiting
    
    try:
        air_marshal_data = get_air_marshal_data(network_id)
        events = []
        
        for rogue_network in air_marshal_data:
            event = {
                "time": datetime.utcnow().isoformat() + "Z",
                "event": "rogue_ssid_detected",
                "sourcetype": "meraki:airmarshal",
                "source": f"meraki:{network_id}",
                "fields": {
                    "network_id": network_id,
                    "ssid": rogue_network.get('ssid', 'unknown'),
                    "bssid": rogue_network.get('bssid', 'unknown'),
                    "channel": rogue_network.get('channel', 'unknown'),
                    "rssi": rogue_network.get('rssi', 'unknown'),
                    "first_seen": rogue_network.get('firstSeen', 'unknown'),
                    "last_seen": rogue_network.get('lastSeen', 'unknown'),
                    "encryption": rogue_network.get('encryption', 'unknown'),
                    "vendor": rogue_network.get('vendor', 'unknown'),
                    "is_meraki_network": rogue_network.get('isMerakiNetwork', False)
                }
            }
            events.append(event)
        
        if events:
            send_to_splunk(events)
    
    except Exception as e:
        error_event = {
            "time": datetime.utcnow().isoformat() + "Z",
            "event": f"error_processing_network {network_id}: {str(e)}",
            "sourcetype": "meraki:error",
            "source": "meraki_airmarshal_check"
        }
        send_to_splunk([error_event])

if __name__ == "__main__":
    for network_id in NETWORK_IDS:
        process_network(network_id)
