import json
import ipaddress
import requests
import time
from pathlib import Path
from datetime import datetime
import os

# Configuration
JSON_FILE = "/var/www/html/meraki-data/mx_inventory_live.json"
CACHE_FILE = "/var/www/html/meraki-data/ip_lookup_cache.json"
RDAP_URL = "https://rdap.arin.net/registry/ip/{ip}"
RETRY_COUNT = 3  # Number of retries for RDAP API
RETRY_BACKOFF = 2  # Initial backoff in seconds
QUERY_DELAY = 1.0  # Delay between queries in seconds
LOG_FILE = "/var/www/html/meraki-data/rdap_query.log"
RDAP_RESPONSE_DIR = "/var/www/html/meraki-data/rdap_responses/"

def log_message(message):
    """Append a message to the log file."""
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(f"{datetime.now()}: {message}\n")
    except Exception as e:
        print(f"Error writing to log file {LOG_FILE}: {e}")

def load_json(file_path):
    """Read JSON from a file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        log_message(f"Error reading {file_path}: {e}")
        return []  # Return empty list for JSON file

def save_json(data, file_path):
    """Save JSON to a file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        log_message(f"Saved data to {file_path}")
    except Exception as e:
        log_message(f"Error saving {file_path}: {e}")

def save_rdap_response(ip, data):
    """Save the full RDAP response to a file."""
    try:
        os.makedirs(RDAP_RESPONSE_DIR, exist_ok=True)
        response_file = os.path.join(RDAP_RESPONSE_DIR, f"{ip.replace('/', '_')}.json")
        save_json(data, response_file)
    except Exception as e:
        log_message(f"Error saving RDAP response for IP {ip}: {e}")

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

def parse_timestamp(timestamp):
    """Parse RDAP timestamp to datetime object."""
    if not timestamp:
        return datetime.min
    try:
        # Handle format like "2025-03-21T15:19:04-04:00"
        return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        try:
            # Handle format like "Fri, 21 Mar 2025 19:19:04 GMT"
            return datetime.strptime(timestamp, "%a, %d %b %Y %H:%M:%S GMT")
        except ValueError:
            try:
                # Handle ISO format without timezone
                return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                log_message(f"Failed to parse timestamp: {timestamp}")
                return datetime.min

def get_provider_from_rdap(ip):
    """Retrieve the latest organization from ARIN RDAP based on Last Changed date."""
    log_message(f"Querying ARIN RDAP for IP {ip}")
    url = RDAP_URL.format(ip=ip)
    data = fetch_json(url, ip)
    if not data:
        log_message(f"No data returned from RDAP for IP {ip}")
        return None

    # Save the full RDAP response
    save_rdap_response(ip, data)

    def get_entity_info(entity):
        """Extract Full Name and Last Changed timestamp from an entity."""
        name = None
        last_changed = datetime.min
        vcard_array = entity.get('vcardArray', [])
        if len(vcard_array) > 1 and isinstance(vcard_array[1], list):
            for vcard in vcard_array[1]:
                if vcard[0] == 'fn' and len(vcard) > 3 and isinstance(vcard[3], str):
                    name = vcard[3].strip()
        for event in entity.get('events', []):
            if event.get('eventAction') == 'last changed':
                last_changed = parse_timestamp(event.get('eventDate'))
        return name, last_changed

    # Log the entire entities array for debugging
    entities = data.get('entities', [])
    log_message(f"Entities found for IP {ip}: {json.dumps(entities, indent=2)}")

    # Collect all organization entities
    org_entities = []
    for entity in entities:
        if entity.get('kind') == 'org':
            name, last_changed = get_entity_info(entity)
            if name:
                org_entities.append((name, last_changed))
            else:
                log_message(f"Entity with kind=org missing name: {json.dumps(entity, indent=2)}")
        else:
            log_message(f"Skipping non-org entity: {json.dumps(entity, indent=2)}")

    # Check related entities via links
    for entity in entities:
        for link in entity.get('links', []):
            if link.get('rel') == 'related' and 'href' in link:
                related_url = link['href']
                log_message(f"Fetching related entity for IP {ip} from {related_url}")
                related_data = fetch_json(related_url, ip)
                if related_data:
                    save_rdap_response(f"{ip}_related_{related_url.replace('/', '_')}", related_data)
                    for related_entity in related_data.get('entities', []):
                        if related_entity.get('kind') == 'org':
                            name, last_changed = get_entity_info(related_entity)
                            if name:
                                org_entities.append((name, last_changed))
                            else:
                                log_message(f"Related entity with kind=org missing name: {json.dumps(related_entity, indent=2)}")
                        else:
                            log_message(f"Skipping non-org related entity: {json.dumps(related_entity, indent=2)}")

    # Select the organization with the latest Last Changed timestamp
    if org_entities:
        latest_org = max(org_entities, key=lambda x: x[1])
        org_name = latest_org[0]
        if org_name.startswith("Private Customer - "):
            org_name = org_name.replace("Private Customer - ", "", 1).strip()
        log_message(f"RDAP latest org name for IP {ip}: {org_name} (Last Changed: {latest_org[1]})")
        return org_name
    else:
        log_message(f"No organization entities found in RDAP response for IP {ip}")
        return None

def update_ip_providers(data, cache):
    """Update provider fields in the JSON data, querying RDAP fresh for all IPs."""
    updated = False
    for entry in data:
        for wan in ['wan1', 'wan2']:
            wan_data = entry.get(wan, {})
            ip = wan_data.get('ip', '')
            provider_label = wan_data.get('provider_label', '')

            if not ip:
                continue

            try:
                ip_addr = ipaddress.ip_address(ip)
                if ip_addr.is_private:
                    log_message(f"Skipping private IP {ip} in {entry['network_name']}")
                    continue
            except ValueError:
                log_message(f"Invalid IP {ip} in {entry['network_name']}")
                continue

            # Always query RDAP fresh
            org_name = get_provider_from_rdap(ip)
            cache[ip] = org_name
            log_message(f"Queried RDAP for IP {ip}: {org_name}")
            time.sleep(QUERY_DELAY)  # Rate limit queries

            if org_name:
                wan_data['provider'] = org_name
                wan_data['provider_comparison'] = (
                    "match" if provider_label and org_name.lower() in provider_label.lower() else "no match"
                )
                updated = True
            else:
                wan_data['provider'] = "Unknown"
                wan_data['provider_comparison'] = "unknown/private"
                updated = True

    return updated, cache

def main():
    log_message("🔍 Updating IP Providers in mx_inventory_live.json")

    # Load JSON data
    data = load_json(JSON_FILE)
    if not data:
        log_message("No data to process. Exiting.")
        return

    # Start with empty cache to query all data fresh
    cache = {}

    # Update providers
    updated, cache = update_ip_providers(data, cache)

    # Save updated JSON if changes were made
    if updated:
        save_json(data, JSON_FILE)

    # Save new cache
    save_json(cache, CACHE_FILE)

    log_message("✅ IP Provider Update Complete")

if __name__ == "__main__":
    main()