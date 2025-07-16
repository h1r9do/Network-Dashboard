import meraki
import datetime
import pytz
import pandas as pd
import sys
import os
import time
import requests
import json
import logging
from dotenv import load_dotenv
from filelock import FileLock

# Set up logging
logging.basicConfig(
    filename='/var/log/meraki_bandwidth.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables from meraki.env
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
API_KEY = os.getenv('MERAKI_API_KEY')
ORG_NAME = os.getenv('ORG_NAME', 'DTC-Store-Inventory-All')
INVENTORY_FILE = '/var/www/html/meraki-data/mx_inventory_live.json'
BANDWIDTH_DIR = '/var/www/html/meraki-data/bandwidth'
PEAK_JSONL = os.path.join(BANDWIDTH_DIR, 'peak_bandwidth_history.jsonl')

# Ensure bandwidth directory exists
try:
    os.makedirs(BANDWIDTH_DIR, exist_ok=True)
except PermissionError:
    logging.error(f"Permission denied creating directory {BANDWIDTH_DIR}")
    print(f"Error: Permission denied creating directory {BANDWIDTH_DIR}")
    sys.exit(1)

# Validate environment variables
if not API_KEY:
    logging.error("MERAKI_API_KEY not found in meraki.env")
    print("Error: MERAKI_API_KEY not found in meraki.env")
    sys.exit(1)
if not ORG_NAME:
    logging.warning("ORG_NAME not found in meraki.env, defaulting to 'DTC-Store-Inventory-All'")
    print("Warning: ORG_NAME not found in meraki.env, defaulting to 'DTC-Store-Inventory-All'")

# Initialize Meraki Dashboard API client
try:
    dashboard = meraki.DashboardAPI(api_key=API_KEY, suppress_logging=True)
except Exception as e:
    logging.error(f"Failed to initialize Meraki API client: {e}")
    print(f"Error: Failed to initialize Meraki API client: {e}")
    sys.exit(1)

def load_vision_networks():
    """Load networks with 'Vision' or 'vision' tag from the inventory file."""
    try:
        with open(INVENTORY_FILE, 'r') as f:
            data = json.load(f)
        vision_networks = [
            entry for entry in data
            if any(tag.lower() == 'vision' for tag in entry.get('device_tags', []))
        ]
        logging.info(f"Found {len(vision_networks)} networks with 'Vision' tag")
        print(f"Found {len(vision_networks)} networks with 'Vision' tag")
        return vision_networks
    except FileNotFoundError:
        logging.error(f"Inventory file {INVENTORY_FILE} not found")
        print(f"Error: Inventory file {INVENTORY_FILE} not found")
        sys.exit(1)
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in {INVENTORY_FILE}")
        print(f"Error: Invalid JSON in {INVENTORY_FILE}")
        sys.exit(1)
    except PermissionError:
        logging.error(f"Permission denied accessing {INVENTORY_FILE}")
        print(f"Error: Permission denied accessing {INVENTORY_FILE}")
        sys.exit(1)

def get_organization_id():
    """Retrieve organization ID by name."""
    try:
        orgs = dashboard.organizations.getOrganizations()
        for org in orgs:
            if org['name'].lower() == ORG_NAME.lower():
                return org['id']
        logging.error(f"Organization '{ORG_NAME}' not found")
        print(f"Error: Organization '{ORG_NAME}' not found")
        sys.exit(1)
    except meraki.APIError as e:
        logging.error(f"Error retrieving organizations: {e}")
        print(f"Error retrieving organizations: {e}")
        sys.exit(1)

def get_network_timezone(network_id):
    """Retrieve the timezone of the network from Meraki Dashboard."""
    try:
        network = dashboard.networks.getNetwork(network_id)
        timezone = network.get('timeZone', 'UTC')
        return pytz.timezone(timezone)
    except meraki.APIError as e:
        logging.warning(f"Error retrieving network timezone for network {network_id}: {e}. Defaulting to UTC")
        print(f"Error retrieving network timezone for network {network_id}: {e}. Defaulting to UTC")
        return pytz.UTC

def get_previous_workday(local_tz):
    """Determine the previous workday (Monday-Saturday) in local timezone."""
    now = datetime.datetime.now(local_tz).date()
    previous_day = now - datetime.timedelta(days=1)
    if previous_day.weekday() == 6:  # Sunday
        previous_day -= datetime.timedelta(days=1)  # Move to Saturday
    return previous_day

def get_business_hours_intervals(local_tz, target_date):
    """Generate 5-minute intervals for business hours (8 AM - 6 PM) on the target date."""
    intervals = []
    start_hour = 8
    end_hour = 18
    interval_minutes = 5

    start_time = local_tz.localize(
        datetime.datetime(target_date.year, target_date.month, target_date.day, start_hour, 0)
    )
    end_time = local_tz.localize(
        datetime.datetime(target_date.year, target_date.month, target_date.day, end_hour, 0)
    )

    current_time = start_time
    while current_time < end_time:
        interval_end = current_time + datetime.timedelta(minutes=interval_minutes)
        intervals.append((current_time, interval_end))
        current_time = interval_end

    return intervals

def bytes_to_mbps(bytes_value, interval_seconds=300):
    """Convert bytes to Mbps (bits per second, considering the 5-minute interval)."""
    if bytes_value is None:
        return 0.0
    bits_per_second = (bytes_value * 8) / interval_seconds
    mbps = bits_per_second / 1_000_000
    return round(mbps, 2)

def fetch_uplink_usage(network_id, start_time, end_time):
    """Fetch uplink usage history with rate limiting."""
    max_retries = 2
    backoff_times = [1, 2, 4]
    retry_count = 0
    backoff_index = 0

    t0 = start_time.astimezone(pytz.UTC).isoformat()
    t1 = end_time.astimezone(pytz.UTC).isoformat()

    while True:
        try:
            logging.info(f"Requesting uplink usage for network {network_id} at {start_time}")
            print(f"🔑 Requesting uplink usage for network {network_id} at {start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            response = dashboard.appliance.getNetworkApplianceUplinksUsageHistory(
                network_id,
                t0=t0,
                t1=t1,
                resolution=300  # Set to 5-minute intervals
            )
            time.sleep(1)  # Ensure 1 request per second
            return response
        except meraki.APIError as e:
            if e.status == 429:
                if retry_count < max_retries:
                    retry_count += 1
                    logging.warning(f"Rate limited. Retry {retry_count}/{max_retries} after 1s")
                    print(f"⏳ Rate limited. Retry {retry_count}/{max_retries} after 1s...")
                    time.sleep(1)
                    continue
                elif backoff_index < len(backoff_times):
                    delay = backoff_times[backoff_index]
                    logging.warning(f"Rate limited. Backing off for {delay}s")
                    print(f"⏳ Rate limited. Backing off for {delay}s...")
                    time.sleep(delay)
                    backoff_index += 1
                    continue
                else:
                    logging.error(f"Max retries exceeded for {start_time}")
                    print(f"⚠️ Max retries exceeded for {start_time}")
                    return []
            else:
                logging.error(f"API error for network {network_id} at {start_time}: {e}")
                print(f"⚠️ API error for network {network_id} at {start_time}: {e}")
                return []

def process_usage_data(network_id, network_name, intervals, local_tz, target_date):
    """Process usage data and extract peak speeds for wan1 and wan2 separately."""
    results = []
    peak_upload_wan1 = {'value': 0.0, 'start_time': None, 'end_time': None}
    peak_download_wan1 = {'value': 0.0, 'start_time': None, 'end_time': None}
    peak_upload_wan2 = {'value': 0.0, 'start_time': None, 'end_time': None}
    peak_download_wan2 = {'value': 0.0, 'start_time': None, 'end_time': None}

    for start_time, end_time in intervals:
        usage_data = fetch_uplink_usage(network_id, start_time, end_time)
        max_upload_wan1 = 0.0
        max_download_wan1 = 0.0
        total_upload_wan1 = 0.0
        total_download_wan1 = 0.0
        count_wan1 = 0
        max_upload_wan2 = 0.0
        max_download_wan2 = 0.0
        total_upload_wan2 = 0.0
        total_download_wan2 = 0.0
        count_wan2 = 0

        for entry in usage_data:
            for interface in entry.get('byInterface', []):
                sent_bytes = interface.get('sent', 0)
                received_bytes = interface.get('received', 0)
                if sent_bytes is None or received_bytes is None:
                    logging.warning(f"Null data for {network_id} at {start_time}, interface {interface.get('interface')}")
                upload_mbps = min(bytes_to_mbps(sent_bytes), 500.0)  # Cap at 500 Mbps
                download_mbps = min(bytes_to_mbps(received_bytes), 500.0)  # Cap at 500 Mbps
                if interface.get('interface') == 'wan1':
                    max_upload_wan1 = max(max_upload_wan1, upload_mbps)
                    max_download_wan1 = max(max_download_wan1, download_mbps)
                    total_upload_wan1 += upload_mbps
                    total_download_wan1 += download_mbps
                    count_wan1 += 1
                elif interface.get('interface') == 'wan2':
                    max_upload_wan2 = max(max_upload_wan2, upload_mbps)
                    max_download_wan2 = max(max_download_wan2, download_mbps)
                    total_upload_wan2 += upload_mbps
                    total_download_wan2 += download_mbps
                    count_wan2 += 1

        avg_upload_wan1 = round(total_upload_wan1 / count_wan1, 2) if count_wan1 > 0 else 0.0
        avg_download_wan1 = round(total_download_wan1 / count_wan1, 2) if count_wan1 > 0 else 0.0
        avg_upload_wan2 = round(total_upload_wan2 / count_wan2, 2) if count_wan2 > 0 else 0.0
        avg_download_wan2 = round(total_download_wan2 / count_wan2, 2) if count_wan2 > 0 else 0.0

        if max_upload_wan1 > peak_upload_wan1['value']:
            peak_upload_wan1 = {
                'value': max_upload_wan1,
                'start_time': start_time,
                'end_time': end_time
            }
        if max_download_wan1 > peak_download_wan1['value']:
            peak_download_wan1 = {
                'value': max_download_wan1,
                'start_time': start_time,
                'end_time': end_time
            }
        if max_upload_wan2 > peak_upload_wan2['value']:
            peak_upload_wan2 = {
                'value': max_upload_wan2,
                'start_time': start_time,
                'end_time': end_time
            }
        if max_download_wan2 > peak_download_wan2['value']:
            peak_download_wan2 = {
                'value': max_download_wan2,
                'start_time': start_time,
                'end_time': end_time
            }

        results.append({
            'Start Time': start_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'End Time': end_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'Max Upload WAN1 (Mbps)': max_upload_wan1,
            'Max Download WAN1 (Mbps)': max_download_wan1,
            'Avg Upload WAN1 (Mbps)': avg_upload_wan1,
            'Avg Download WAN1 (Mbps)': avg_download_wan1,
            'Max Upload WAN2 (Mbps)': max_upload_wan2,
            'Max Download WAN2 (Mbps)': max_download_wan2,
            'Avg Upload WAN2 (Mbps)': avg_upload_wan2,
            'Avg Download WAN2 (Mbps)': avg_download_wan2
        })

    # Prepare peak data for JSONL (one entry per interface)
    peak_data_list = []
    if peak_upload_wan1['value'] > 0 or peak_download_wan1['value'] > 0:
        peak_data_list.append({
            'store_name': network_name,
            'network_id': network_id,
            'interface': 'wan1',
            'date': target_date.strftime('%Y-%m-%d'),
            'peak_upload_mbps': peak_upload_wan1['value'],
            'peak_upload_time': peak_upload_wan1['start_time'].strftime('%Y-%m-%d %H:%M:%S %Z') if peak_upload_wan1['start_time'] else '',
            'peak_download_mbps': peak_download_wan1['value'],
            'peak_download_time': peak_download_wan1['start_time'].strftime('%Y-%m-%d %H:%M:%S %Z') if peak_download_wan1['start_time'] else ''
        })
    if peak_upload_wan2['value'] > 0 or peak_download_wan2['value'] > 0:
        peak_data_list.append({
            'store_name': network_name,
            'network_id': network_id,
            'interface': 'wan2',
            'date': target_date.strftime('%Y-%m-%d'),
            'peak_upload_mbps': peak_upload_wan2['value'],
            'peak_upload_time': peak_upload_wan2['start_time'].strftime('%Y-%m-%d %H:%M:%S %Z') if peak_upload_wan2['start_time'] else '',
            'peak_download_mbps': peak_download_wan2['value'],
            'peak_download_time': peak_download_wan2['start_time'].strftime('%Y-%m-%d %H:%M:%S %Z') if peak_download_wan2['start_time'] else ''
        })

    return results, peak_data_list

def save_to_csv(results, filename):
    """Save full results to a CSV file."""
    try:
        df = pd.DataFrame(results)
        df.to_csv(filename, index=False)
        logging.info(f"Full results saved to {filename}")
        print(f"Full results saved to {filename}")
    except PermissionError:
        logging.error(f"Permission denied writing to {filename}")
        print(f"Error: Permission denied writing to {filename}")
        raise
    except Exception as e:
        logging.error(f"Error saving CSV {filename}: {e}")
        print(f"Error saving CSV {filename}: {e}")
        raise

def append_peak_to_jsonl(peak_data_list):
    """Append peak data to the JSONL file with file locking."""
    lock = FileLock(PEAK_JSONL + ".lock")
    with lock:
        try:
            with open(PEAK_JSONL, 'a') as f:
                for peak_data in peak_data_list:
                    json.dump(peak_data, f)
                    f.write('\n')
            logging.info(f"Peak data appended to {PEAK_JSONL}")
            print(f"Peak data appended to {PEAK_JSONL}")
        except PermissionError:
            logging.error(f"Permission denied writing to {PEAK_JSONL}")
            print(f"Error: Permission denied writing to {PEAK_JSONL}")
            raise
        except Exception as e:
            logging.error(f"Error appending to {PEAK_JSONL}: {e}")
            print(f"Error appending to {PEAK_JSONL}: {e}")
            raise

def main():
    logging.info("Starting Meraki bandwidth data collection")
    print("Starting Meraki bandwidth data collection")

    # Get organization ID
    org_id = get_organization_id()
    logging.info(f"Organization: {ORG_NAME} (ID: {org_id})")
    print(f"Organization: {ORG_NAME} (ID: {org_id})")

    # Load Vision networks
    vision_networks = load_vision_networks()
    logging.info(f"Processing {len(vision_networks)} Vision networks for previous workday")
    print(f"Processing {len(vision_networks)} Vision networks for previous workday")

    # Initialize list to store peak data
    peak_data_list = []

    for net_index, network in enumerate(vision_networks):
        network_id = network['network_id']
        network_name = network['network_name']
        logging.info(f"Processing network {network_name} (ID: {network_id}) ({net_index + 1}/{len(vision_networks)})")
        print(f"\nProcessing network {network_name} (ID: {network_id}) ({net_index + 1}/{len(vision_networks)})")

        # Get network's local timezone
        local_tz = get_network_timezone(network_id)
        logging.info(f"Network timezone: {local_tz.zone}")
        print(f"Network timezone: {local_tz.zone}")

        # Get the previous workday
        target_date = get_previous_workday(local_tz)
        logging.info(f"Analyzing business hours for: {target_date}")
        print(f"Analyzing business hours for: {target_date.strftime('%Y-%m-%d')}")

        # Generate 5-minute intervals for business hours
        intervals = get_business_hours_intervals(local_tz, target_date)
        logging.info(f"Total intervals to process: {len(intervals)}")
        print(f"Total intervals to process: {len(intervals)}")

        # Process usage data
        try:
            results, network_peak_data = process_usage_data(network_id, network_name, intervals, local_tz, target_date)
        except Exception as e:
            logging.error(f"Error processing data for {network_name}: {e}")
            print(f"Error processing data for {network_name}: {e}")
            continue

        if not results:
            logging.warning(f"No data retrieved for {network_name}")
            print(f"No data retrieved for {network_name}. Check API key, network ID, or connectivity.")
            continue

        # Save full results to individual CSV
        output_file = os.path.join(BANDWIDTH_DIR, f"uplink_usage_{network_name.replace(' ', '_')}_{target_date.strftime('%Y%m%d')}.csv")
        try:
            save_to_csv(results, output_file)
        except Exception as e:
            logging.error(f"Failed to save CSV for {network_name}: {e}")
            print(f"Failed to save CSV for {network_name}: {e}")
            continue

        # Add peak data to list
        peak_data_list.extend(network_peak_data)

    # Append all peak data to the JSONL file
    if peak_data_list:
        try:
            append_peak_to_jsonl(peak_data_list)
        except Exception as e:
            logging.error(f"Failed to append peak data to JSONL: {e}")
            print(f"Failed to append peak data to JSONL: {e}")

    logging.info("Completed Meraki bandwidth data collection")
    print("Completed Meraki bandwidth data collection")

if __name__ == "__main__":
    main()