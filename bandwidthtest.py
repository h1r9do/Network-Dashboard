import meraki
import datetime
import pytz
import pandas as pd
from tabulate import tabulate
import sys
import os
from dotenv import load_dotenv

# Load environment variables from meraki.env
load_dotenv('meraki.env')

# Configuration
API_KEY = os.getenv('MERAKI_API_KEY')
ORG_NAME = os.getenv('ORG_NAME')
NETWORK_ID = 'L_650207196201636678'  # ARL 05 network
DEVICE_SERIAL = 'Q2QN-L9J4-KK4A'     # MX65 device

# Validate environment variables
if not API_KEY or not ORG_NAME:
    print("Error: MERAKI_API_KEY or ORG_NAME not found in meraki.env")
    sys.exit(1)

# Initialize Meraki Dashboard API client
dashboard = meraki.DashboardAPI(api_key=API_KEY, suppress_logging=True)

def get_organization_id():
    """Retrieve organization ID by name."""
    try:
        orgs = dashboard.organizations.getOrganizations()
        for org in orgs:
            if org['name'].lower() == ORG_NAME.lower():
                return org['id']
        print(f"Error: Organization '{ORG_NAME}' not found.")
        sys.exit(1)
    except meraki.APIError as e:
        print(f"Error retrieving organizations: {e}")
        sys.exit(1)

def get_network_timezone():
    """Retrieve the timezone of the network from Meraki Dashboard."""
    try:
        network = dashboard.networks.getNetwork(NETWORK_ID)
        timezone = network.get('timeZone', 'UTC')
        return pytz.timezone(timezone)
    except meraki.APIError as e:
        print(f"Error retrieving network timezone: {e}")
        sys.exit(1)

def get_previous_workday(local_tz):
    """Determine the previous workday (Monday-Friday) in local timezone."""
    now = datetime.datetime.now(local_tz)
    # Move to previous day
    previous_day = now - datetime.timedelta(days=1)
    # If previous day is Saturday (weekday=5), move to Friday
    if previous_day.weekday() == 5:
        previous_day -= datetime.timedelta(days=1)
    # If previous day is Sunday (weekday=6), move to Friday
    elif previous_day.weekday() == 6:
        previous_day -= datetime.timedelta(days=2)
    return previous_day

def get_business_hours_intervals(local_tz, target_date):
    """Generate 5-minute intervals for business hours (8 AM - 6 PM) on the target date."""
    intervals = []
    start_hour = 8
    end_hour = 18
    interval_minutes = 5

    # Set start and end times for business hours
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
    # Convert bytes to bits (1 byte = 8 bits) and divide by seconds
    bits_per_second = (bytes_value * 8) / interval_seconds
    # Convert to Mbps (1 Mbps = 1,000,000 bits)
    mbps = bits_per_second / 1_000_000
    return round(mbps, 2)

def fetch_uplink_usage(start_time, end_time):
    """Fetch uplink usage history for the specified time range."""
    try:
        # Convert times to UTC for API query
        t0 = start_time.astimezone(pytz.UTC).isoformat()
        t1 = end_time.astimezone(pytz.UTC).isoformat()
        response = dashboard.appliance.getNetworkApplianceUplinksUsageHistory(
            NETWORK_ID,
            t0=t0,
            t1=t1
        )
        return response
    except meraki.APIError as e:
        print(f"Error fetching usage data for {start_time}: {e}")
        return []

def process_usage_data(intervals, local_tz):
    """Process usage data for each interval and calculate max/avg speeds."""
    results = []
    for start_time, end_time in intervals:
        usage_data = fetch_uplink_usage(start_time, end_time)
        max_upload = 0.0
        max_download = 0.0
        total_upload = 0.0
        total_download = 0.0
        count = 0

        for entry in usage_data:
            for interface in entry.get('byInterface', []):
                # Process data for wan1 (AT&T) and wan2 (Ritter Communications)
                if interface.get('interface') in ['wan1', 'wan2']:
                    sent_bytes = interface.get('sent', 0)
                    received_bytes = interface.get('received', 0)
                    upload_mbps = bytes_to_mbps(sent_bytes)
                    download_mbps = bytes_to_mbps(received_bytes)
                    max_upload = max(max_upload, upload_mbps)
                    max_download = max(max_download, download_mbps)
                    total_upload += upload_mbps
                    total_download += download_mbps
                    count += 1

        avg_upload = round(total_upload / count, 2) if count > 0 else 0.0
        avg_download = round(total_download / count, 2) if count > 0 else 0.0

        results.append({
            'Start Time': start_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'End Time': end_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'Max Upload (Mbps)': max_upload,
            'Max Download (Mbps)': max_download,
            'Avg Upload (Mbps)': avg_upload,
            'Avg Download (Mbps)': avg_download
        })

    return results

def save_to_csv(results, filename):
    """Save results to a CSV file."""
    df = pd.DataFrame(results)
    df.to_csv(filename, index=False)
    print(f"Results saved to {filename}")

def main():
    # Get organization ID
    org_id = get_organization_id()
    print(f"Organization: {ORG_NAME} (ID: {org_id})")

    # Get network's local timezone
    local_tz = get_network_timezone()
    print(f"Network timezone: {local_tz.zone}")

    # Determine previous workday
    previous_workday = get_previous_workday(local_tz)
    print(f"Analyzing business hours for: {previous_workday.strftime('%Y-%m-%d')}")

    # Generate 5-minute intervals for business hours
    intervals = get_business_hours_intervals(local_tz, previous_workday)
    print(f"Total intervals to process: {len(intervals)}")

    # Process usage data
    results = process_usage_data(intervals, local_tz)

    if not results:
        print("No data retrieved. Check API key, network ID, or connectivity.")
        return

    # Display results in a table
    df = pd.DataFrame(results)
    print("\nUplink Usage Summary for ARL 05 (Business Hours):")
    print(tabulate(df, headers='keys', tablefmt='psql', showindex=False))

    # Save to CSV
    output_file = f"uplink_usage_arl05_{previous_workday.strftime('%Y%m%d')}.csv"
    save_to_csv(results, output_file)

if __name__ == "__main__":
    main()