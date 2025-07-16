# Legacy Data Flow Documentation

## Overview
The legacy system used two separate scripts to collect and enrich Meraki data with DSR tracking information, producing a JSON file with 1,296 networks that included complete WAN1 and WAN2 information.

## Step 1: Meraki Data Collection (meraki_mx.py)
**Runtime**: 1:00 AM daily
**Output**: `/var/www/html/meraki-data/mx_inventory_live.json`

### Process:
1. **Fetch Organization Data**
   - Connect to Meraki API using API key from `/usr/local/bin/meraki.env`
   - Get organization ID for "DTC-Store-Inventory-All"

2. **Get All Networks**
   - Fetch all networks in the organization (paginated)
   - Sort by network name

3. **Get Uplink Status**
   - Call `/organizations/{org_id}/appliances/uplinks/statuses` 
   - Build dictionary of WAN1/WAN2 IP addresses and assignment methods per device serial

4. **Process Each Network**
   - Get all devices in network
   - Filter for MX models only
   - For each MX device:
     a. Get device details to fetch tags
     b. Get WAN1/WAN2 IPs from uplink status
     c. Parse device notes for provider labels and speeds
     d. Lookup provider by IP using ARIN RDAP API
     e. Compare ARIN provider with notes provider

5. **Note Parsing Logic**
   - Look for patterns: "WAN1: Provider 100M x 100M"
   - Extract provider name and speed
   - Handle various speed formats (M/MB/G/GB)
   - Normalize speed to "X.XM x X.XM" format

6. **IP Provider Lookup**
   - Check static KNOWN_IPS mapping first
   - Skip private IPs
   - Query ARIN RDAP: `https://rdap.arin.net/registry/ip/{ip}`
   - Extract provider name from response
   - Cache results to avoid duplicate lookups

7. **Output Structure** (per network):
```json
{
  "network_id": "L_1234",
  "network_name": "CAL 01",
  "device_serial": "Q2XX-XXXX",
  "device_model": "MX67",
  "device_name": "CAL 01",
  "device_tags": ["Discount-Tire", "America's"],
  "wan1": {
    "provider_label": "Spectrum",
    "speed": "940.0M x 35.0M",
    "ip": "24.29.106.73",
    "assignment": "dhcp",
    "provider": "Charter Communications",
    "provider_comparison": "Match"
  },
  "wan2": {
    "provider_label": "AT&T",
    "speed": "25.0M x 3.0M",
    "ip": "104.13.199.26",
    "assignment": "dhcp", 
    "provider": "AT&T",
    "provider_comparison": "Match"
  },
  "raw_notes": "WAN1: Spectrum 940M x 35M\nWAN2: AT&T 25M x 3M",
  "last_updated": "2025-06-20T08:00:00Z"
}
```

## Step 2: Enrichment Process (nightly_enriched.py)
**Runtime**: 3:00 AM daily
**Input**: 
- `/var/www/html/meraki-data/mx_inventory_live.json`
- `/var/www/html/circuitinfo/tracking_data_*.csv` (latest)
**Output**: `/var/www/html/meraki-data/mx_inventory_enriched_YYYY-MM-DD.json`

### Process:
1. **Load Live Meraki Data**
   - Read mx_inventory_live.json
   - Filter out networks with tags: HUB, LAB, VOICE
   - Result: ~1,296 networks

2. **Load DSR Tracking Data**
   - Find latest tracking_data_*.csv
   - Load into pandas DataFrame
   - Filter for status = "Enabled" only
   - Remove entries with $0 monthly cost

3. **Provider Normalization**
   - Apply extensive provider mapping (100+ mappings)
   - Examples:
     - "spectrum" → "Charter Communications"
     - "verizon cell" → "Verizon"
     - "at&t adi" → "AT&T"

4. **Matching Logic (per network)**
   ```
   For WAN1 and WAN2:
   1. Try IP address match first:
      - Find tracking entries where IP matches exactly
      - If found, use that provider/speed/cost/role
   
   2. If no IP match, try fuzzy provider matching:
      - Normalize both provider names
      - Use fuzzywuzzy for similarity scoring
      - Accept matches with score > 60
      - Pick highest scoring match
   
   3. If no match at all:
      - Use Meraki live data
      - Set cost to $0.00
      - Set role to Primary/Secondary by default
   ```

5. **Speed Reformatting**
   - Starlink → "Satellite"
   - Normalize all speeds to "X.XM x X.XM" format
   - Handle special cases (DSL, Satellite, etc.)

6. **Output Structure** (per network):
```json
{
  "network_name": "CAL 01",
  "device_tags": ["Discount-Tire", "America's"],
  "wan1": {
    "provider": "Charter Communications",
    "speed": "940.0M x 35.0M",
    "monthly_cost": "$95.00",
    "circuit_role": "Primary",
    "confirmed": true
  },
  "wan2": {
    "provider": "AT&T", 
    "speed": "25.0M x 3.0M",
    "monthly_cost": "$65.00",
    "circuit_role": "Secondary",
    "confirmed": true
  }
}
```

## Step 3: Display (dsrcircuits.py)
- Load latest `mx_inventory_enriched_*.json`
- Pass entire JSON array to template
- Template displays all 1,296 networks with complete WAN1/WAN2 data

## Key Points:
1. **All MX devices are included** (1,296 total after filtering tags)
2. **Enrichment adds cost/role data** but doesn't filter networks
3. **Networks without tracking matches** still appear with $0 cost
4. **IP matching takes precedence** over fuzzy name matching
5. **Both WAN1 and WAN2** are fully populated from Meraki data