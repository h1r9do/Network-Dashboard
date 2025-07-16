import json
import re
import ipaddress
from datetime import datetime

# File paths
INPUT_FILE = "/var/www/html/meraki-data/rdap_full_responses.json"
OUTPUT_FILE = "/var/www/html/meraki-data/ip_lookup_cache.json"
LOG_FILE = "/var/www/html/meraki-data/missing_data_log.txt"

# Known IP-to-ISP mappings (static list provided by the user)
KNOWN_IPS = {
    "63.228.128.81": "CenturyLink",
    "24.101.188.52": "Charter Communications",
    "198.99.82.203": "AT&T",
    "206.222.219.64": "Cogent Communications",
    "208.83.9.194": "CenturyLink",
    "195.252.240.66": "Deutsche Telekom",
    "209.66.104.34": "Verizon",
    "65.140.77.202": "CenturyLink",
    "69.130.234.114": "Comcast",
    "184.61.190.6": "Frontier Communications",
    "72.166.76.98": "Cox Communications",
    "98.6.198.210": "Charter Communications",
    "65.100.99.25": "CenturyLink",
    "100.88.182.60": "Verizon",
    "66.76.161.89": "Suddenlink Communications",
    "66.152.135.50": "EarthLink",
    "216.164.196.131": "RCN",
    "209.124.218.134": "IBM Cloud",
    "67.199.174.137": "Google",
    "65.103.195.249": "CenturyLink",
    "184.60.134.66": "Frontier Communications"
}

# Company normalization map (known variations)
COMPANY_NAME_MAP = {
    "AT&T": ["AT&T", "AT&T Internet Services", "AT&T Enterprises, LLC", "AT&T Broadband", "IPAdmin-ATT Internet Services", "AT&T Communications", "AT&T Business"],
    "Charter Communications": ["Charter Communications LLC", "Charter Communications Inc", "Charter Communications, LLC"],
    "Comcast": ["Comcast Cable Communications, LLC", "Comcast Communications", "Comcast Cable", "Comcast Corporation"],
    "Cox Communications": ["Cox Communications Inc.", "Cox Communications", "Cox Communications Group"],
    "CenturyLink": ["CenturyLink Communications", "CenturyLink", "Lumen Technologies"],
    "Frontier Communications": ["Frontier Communications Corporation", "Frontier Communications", "Frontier Communications Inc."],
    "Level 3": ["Level 3 Parent, LLC", "Level 3 Communications", "Level3"],
    "Verizon": ["Verizon Communications", "Verizon Internet", "Verizon Business", "Verizon Wireless"],
    "Metronet": ["Metronet", "Metronet Fiber"],
    "AT&T Internet": ["AT&T Internet"]
}

# Anomaly keywords for non-network providers (e.g., CPA, hardware store)
ANOMALIES = [
    "CPA", "Certified Public Accountant", "Hardware Store", "Electrician", "Plumbing", "Legal Services"
]

# Helper function to normalize company names
def normalize_company_name(name: str) -> str:
    for company, variations in COMPANY_NAME_MAP.items():
        for variant in variations:
            if variant.lower() in name.lower():
                return company
    return name  # If no match, return the name as-is

# Helper function to check for anomalies
def check_for_anomalies(name: str) -> bool:
    for anomaly in ANOMALIES:
        if anomaly.lower() in name.lower():
            return True
    return False

# Helper function to clean the company name by removing unwanted prefixes or substrings
def clean_company_name(name: str) -> str:
    return re.sub(r"^Private Customer -\s*", "", name).strip()

# Function to determine if the name looks like a personal name
def looks_like_personal(name: str) -> bool:
    personal_keywords = ["Mr.", "Ms.", "Dr.", "Mrs.", "Miss"]
    if any(keyword in name for keyword in personal_keywords):
        return True
    if len(name.split()) == 2:
        return True
    return False

# Recursive function to collect all org entities and their latest event date
def collect_org_entities(entity_list: list) -> list:
    org_candidates = []
    for entity in entity_list:
        vcard = entity.get("vcardArray")
        if vcard and isinstance(vcard, list) and len(vcard) > 1:
            vcard_props = vcard[1]
            name = None
            kind = None
            for prop in vcard_props:
                if len(prop) >= 4:
                    label = prop[0]
                    value = prop[3]
                    if label == "fn":
                        name = value
                    elif label == "kind":
                        kind = value
            if kind and kind.lower() == "org" and name:
                if not looks_like_personal(name):
                    latest_date = None
                    for event in entity.get("events", []):
                        action = event.get("eventAction", "").lower()
                        if action in ("registration", "last changed"):
                            date_str = event.get("eventDate")
                            if date_str:
                                try:
                                    dt = datetime.fromisoformat(date_str)
                                except Exception:
                                    try:
                                        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
                                    except Exception:
                                        continue
                                if latest_date is None or dt > latest_date:
                                    latest_date = dt
                    if latest_date is None:
                        latest_date = datetime.min
                    org_candidates.append((name, latest_date))
        sub_entities = entity.get("entities", [])
        if sub_entities:
            org_candidates.extend(collect_org_entities(sub_entities))
    return org_candidates

# Main processing function
def main():
    with open(INPUT_FILE, "r") as f:
        data = json.load(f)

    data = [entry for entry in data if entry]

    ip_to_company = {}
    missing_ips = []
    anomalies = []

    for entry in data:
        if isinstance(entry, dict):
            ip = entry.get("ip")
            rdap = entry.get("rdap_response", {})
            entities = rdap.get("entities", [])
            if not ip or not entities:
                continue
            # Check if the IP is in the known list
            if ip in KNOWN_IPS:
                ip_to_company[ip] = KNOWN_IPS[ip]
            else:
                orgs = collect_org_entities(entities)
                if not orgs:
                    missing_ips.append(ip)
                else:
                    orgs.sort(key=lambda x: x[1], reverse=True)
                    best_name = orgs[0][0]
                    clean_name = clean_company_name(best_name)
                    normalized_name = normalize_company_name(clean_name)
                    if check_for_anomalies(normalized_name):
                        anomalies.append(f"Anomaly found for IP {ip}: {normalized_name}")
                    ip_to_company[ip] = normalized_name
    
    # Write the IP-to-company mapping as JSON
    with open(OUTPUT_FILE, "w") as out_f:
        json.dump(ip_to_company, out_f, indent=2)

    # Write missing IPs to log file
    with open(LOG_FILE, "w") as log_f:
        for ip in missing_ips:
            log_f.write(f"{ip}\n")

    # Log anomalies found
    with open("/var/www/html/meraki-data/anomalies_log.txt", "w") as anomaly_log:
        for anomaly in anomalies:
            anomaly_log.write(f"{anomaly}\n")

# Execute the main function
if __name__ == "__main__":
    main()
