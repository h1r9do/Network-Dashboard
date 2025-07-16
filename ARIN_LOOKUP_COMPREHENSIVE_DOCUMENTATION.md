# Comprehensive ARIN Lookup Functionality Documentation

This document captures all ARIN lookup implementations across the DSR Circuits system, showing the logic that was working correctly before any modifications.

## Table of Contents
1. [Core ARIN Functions](#core-arin-functions)
2. [Company Name Normalization](#company-name-normalization)
3. [Special IP Range Handling](#special-ip-range-handling)
4. [KNOWN_IPS Mappings](#known_ips-mappings)
5. [Provider Keywords Mapping](#provider-keywords-mapping)
6. [RDAP Response Parsing](#rdap-response-parsing)
7. [Provider Comparison Logic](#provider-comparison-logic)

## Core ARIN Functions

### 1. get_provider_for_ip() - Main Function
Found in: `/usr/local/bin/meraki_mx.py`, `/usr/local/bin/Main/nightly_meraki_db.py`

```python
def get_provider_for_ip(ip, cache, missing_set):
    """Determine the ISP provider name for a given IP address using cache or RDAP."""
    # 1. Check cache first
    if ip in cache:
        return cache[ip]
    
    # 2. Special handling for 166.80.0.0/16 range (Verizon Business)
    try:
        ip_addr = ipaddress.ip_address(ip)
        if ipaddress.IPv4Address("166.80.0.0") <= ip_addr <= ipaddress.IPv4Address("166.80.255.255"):
            provider = "Verizon Business"
            cache[ip] = provider
            return provider
    except ValueError:
        logger.warning(f"Invalid IP address format: {ip}")
        missing_set.add(ip)
        return "Unknown"
    
    # 3. Check KNOWN_IPS mapping
    if ip in KNOWN_IPS:
        provider = KNOWN_IPS[ip]
        cache[ip] = provider
        return provider
    
    # 4. Skip private IPs
    if ip_addr.is_private:
        return "Unknown"
    
    # 5. Query ARIN RDAP API
    rdap_url = f"https://rdap.arin.net/registry/ip/{ip}"
    rdap_data = fetch_json(rdap_url, ip)
    if not rdap_data:
        missing_set.add(ip)
        return "Unknown"
    
    # 6. Parse response and cache result
    provider = parse_arin_response(rdap_data)
    cache[ip] = provider
    return provider
```

### 2. parse_arin_response() - Response Parser
Found in: `/usr/local/bin/Main/nightly_meraki_db.py` (most comprehensive version)

```python
def parse_arin_response(rdap_data):
    """Parse the ARIN RDAP response to extract the provider name."""
    
    # Define the nested function to collect org entities
    def collect_org_entities(entities):
        """Recursively collect organization names from entities"""
        org_names = []
        for entity in entities:
            vcard = entity.get("vcardArray", [])
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
                    # Skip personal names
                    if not any(keyword in name for keyword in ["Mr.", "Ms.", "Dr.", "Mrs.", "Miss"]):
                        org_names.append(name)
            
            # Check sub-entities
            sub_entities = entity.get("entities", [])
            if sub_entities:
                org_names.extend(collect_org_entities(sub_entities))
        
        return org_names
    
    # First try network name directly in response
    network_name = rdap_data.get('name')
    
    # Get organization entities
    entities = rdap_data.get('entities', [])
    org_names = []
    if entities:
        org_names = collect_org_entities(entities)
    
    # Special handling for CABLEONE - prefer the full company name from entities
    if network_name == 'CABLEONE' and org_names:
        for name in org_names:
            if 'cable one' in name.lower():
                return "Cable One, Inc."  # Return normalized version
    
    # If we have org names, use the first one (they're already filtered for org type)
    if org_names:
        # Clean the name first
        clean_name = org_names[0]
        clean_name = re.sub(r"^Private Customer -\s*", "", clean_name).strip()
        
        # Apply known company normalizations
        company_map = {
            "AT&T": ["AT&T", "AT&T Internet Services", "AT&T Enterprises, LLC", "AT&T Broadband", 
                     "IPAdmin-ATT Internet Services", "AT&T Communications", "AT&T Business"],
            "Charter Communications": ["Charter Communications LLC", "Charter Communications Inc", 
                                     "Charter Communications, LLC", "Charter Communications"],
            "Comcast": ["Comcast Cable Communications, LLC", "Comcast Communications", 
                        "Comcast Cable", "Comcast Corporation"],
            "Cox Communications": ["Cox Communications Inc.", "Cox Communications", "Cox Communications Group"],
            "CenturyLink": ["CenturyLink Communications", "CenturyLink", "Lumen Technologies", 
                            "Level 3 Parent, LLC", "Level 3 Communications", "Level3"],
            "Frontier Communications": ["Frontier Communications Corporation", "Frontier Communications", 
                                      "Frontier Communications Inc."],
            "Verizon": ["Verizon Communications", "Verizon Internet", "Verizon Business", "Verizon Wireless"],
            "Optimum": ["Optimum", "Altice USA", "Suddenlink Communications"],
            "Crown Castle": ["Crown Castle", "CROWN CASTLE"],
            "Cable One, Inc.": ["CABLE ONE, INC.", "Cable One, Inc.", "Cable One"],
        }
        
        for company, variations in company_map.items():
            for variant in variations:
                if variant.lower() in clean_name.lower():
                    return company
        
        return clean_name
    
    # If no org entities found, try to normalize the network name
    if network_name:
        # Check if it's an AT&T network (SBC-*)
        if network_name.startswith('SBC-'):
            return 'AT&T'
        # Check for other patterns
        elif 'CHARTER' in network_name.upper():
            return 'Charter Communications'
        elif 'COMCAST' in network_name.upper():
            return 'Comcast'
        elif 'COX' in network_name.upper():
            return 'Cox Communications'
        elif 'VERIZON' in network_name.upper():
            return 'Verizon'
        elif 'CENTURYLINK' in network_name.upper():
            return 'CenturyLink'
        elif 'FRONTIER' in network_name.upper():
            return 'Frontier Communications'
        elif 'CC04' in network_name:  # Charter network code
            return 'Charter Communications'
        else:
            # Return the network name as-is if no pattern matches
            return network_name
    
    return "Unknown"
```

## Company Name Normalization

### normalize_company_name() Function
Found in: `/usr/local/bin/clean_ip_network_cache.py`, `/usr/local/bin/Main/test_arin_lookup_with_normalization.py`

```python
# Company normalization map
COMPANY_NAME_MAP = {
    "AT&T": ["AT&T", "AT&T Internet Services", "AT&T Enterprises, LLC", "AT&T Broadband", 
             "IPAdmin-ATT Internet Services", "AT&T Communications", "AT&T Business"],
    "Charter Communications": ["Charter Communications LLC", "Charter Communications Inc", 
                             "Charter Communications, LLC"],
    "Comcast": ["Comcast Cable Communications, LLC", "Comcast Communications", 
                "Comcast Cable", "Comcast Corporation"],
    "Cox Communications": ["Cox Communications Inc.", "Cox Communications", "Cox Communications Group"],
    "CenturyLink": ["CenturyLink Communications", "CenturyLink", "Lumen Technologies",
                    "Level 3 Parent, LLC", "Level 3 Communications", "Level3"],
    "Frontier Communications": ["Frontier Communications Corporation", "Frontier Communications", 
                              "Frontier Communications Inc."],
    "Verizon": ["Verizon Communications", "Verizon Internet", "Verizon Business", "Verizon Wireless"],
    "Metronet": ["Metronet", "Metronet Fiber"],
    "AT&T Internet": ["AT&T Internet"],
    "Optimum": ["Optimum", "Altice USA", "Suddenlink Communications"],
    "Crown Castle": ["Crown Castle", "CROWN CASTLE"],
    "Cable One, Inc.": ["CABLE ONE, INC.", "Cable One, Inc.", "Cable One"]
}

def normalize_company_name(name: str) -> str:
    """Normalize company names using known variations"""
    for company, variations in COMPANY_NAME_MAP.items():
        for variant in variations:
            if variant.lower() in name.lower():
                return company
    return name  # If no match, return the name as-is
```

## Special IP Range Handling

### 166.80.0.0/16 Range (Verizon Business)
This special case is handled in get_provider_for_ip():

```python
# Special handling for 166.80.0.0/16 range
try:
    ip_addr = ipaddress.ip_address(ip)
    # Check if IP falls within the 166.80.0.0/16 range
    if ipaddress.IPv4Address("166.80.0.0") <= ip_addr <= ipaddress.IPv4Address("166.80.255.255"):
        provider = "Verizon Business"
        cache[ip] = provider
        return provider
except ValueError:
    print(f"⚠️ Invalid IP address format: {ip}")
    missing_set.add(ip)
    return "Unknown"
```

## KNOWN_IPS Mappings

### Static IP-to-Provider Mappings
Found in: `/usr/local/bin/meraki_mx.py`, `/usr/local/bin/Main/nightly_meraki_db.py`

```python
KNOWN_IPS = {
    "63.228.128.81": "CenturyLink",
    "24.101.188.52": "Charter Communications",
    "198.99.82.203": "AT&T",
    "206.222.219.64": "Cogent Communications",
    "208.83.9.194": "CenturyLink",
    "195.252.240.66": "Deutsche Telekom",
    "209.66.104.34": "Verizon",
    "65.100.99.25": "CenturyLink",
    "69.130.234.114": "Comcast",
    "184.61.190.6": "Frontier Communications",
    "72.166.76.98": "Cox Communications",
    "98.6.198.210": "Charter Communications",
    "65.103.195.249": "CenturyLink",
    "100.88.182.60": "Verizon",
    "66.76.161.89": "Suddenlink Communications",
    "66.152.135.50": "EarthLink",
    "216.164.196.131": "RCN",
    "209.124.218.134": "IBM Cloud",
    "67.199.174.137": "Google",
    "184.60.134.66": "Frontier Communications",
    "24.144.4.162": "Conway Corporation",
    "199.38.125.142": "Ritter Communications",
    "69.195.29.6": "Ritter Communications",
    "69.171.123.138": "FAIRNET LLC",
    "63.226.59.241": "CenturyLink Communications, LLC",
    "24.124.116.54": "Midcontinent Communications",
    "50.37.227.70": "Ziply Fiber",
    "24.220.46.162": "Midcontinent Communications",
    "76.14.161.29": "Wave Broadband",
    "71.186.165.101": "Verizon Business",
    "192.190.112.119": "Lrm-Com, Inc.",
    "149.97.243.90": "Equinix, Inc.",
    "162.247.42.4": "HUNTER COMMUNICATIONS",
}
```

## Provider Keywords Mapping

### Keywords for Device Notes Normalization
Found in: `/usr/local/bin/meraki_mx.py`, `/usr/local/bin/Main/nightly_meraki_db.py`

```python
PROVIDER_KEYWORDS = {
    'spectrum': 'charter communications',
    'charter': 'charter communications',
    'at&t': 'at&t',
    'att': 'at&t',
    'comcast': 'comcast',
    'verizon': 'verizon business',
    'vz': 'verizon business',
    'cox': 'cox communications',
    'yelcot': 'yelcot telephone company',
    'ritter': 'ritter communications',
    'conway': 'conway corporation',
    'altice': 'optimum',
    'brightspeed': 'level 3',
    'clink': 'centurylink',
    'lumen': 'centurylink',
    'c spire': 'c spire fiber',
    'orbitelcomm': 'orbitel communications, llc',
    'sparklight': 'cable one, inc.',
    'lightpath': 'optimum',
    'vzg': 'verizon business',
    'digi': 'verizon business',  # Maps 'DIGI' to 'verizon business'
    'centurylink': 'centurylink',
    'mediacom': 'mediacom communications corporation',
    'frontier': 'frontier communications',
    'cable one': 'cable one, inc.',
    'qwest': 'centurylink',
    'cox business': 'cox communications',
    'consolidatedcomm': 'consolidated communications, inc.',  # Maps 'DSR ConsolidatedComm' to ARIN provider
    'consolidated': 'consolidated communications, inc.'  # Handles variations
}
```

## RDAP Response Parsing

### Entity Collection Logic
The recursive collection of organization entities from RDAP responses:

```python
def collect_org_entities(entity_list):
    """Recursively collect all org entities and their latest event date"""
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
                    # Add to candidates
                    org_candidates.append(name)
        # Check sub-entities
        sub_entities = entity.get("entities", [])
        if sub_entities:
            org_candidates.extend(collect_org_entities(sub_entities))
    return org_candidates
```

## Provider Comparison Logic

### compare_providers() Function
Found in: `/usr/local/bin/Main/nightly_meraki_db.py`

```python
def compare_providers(arin_provider, label_provider):
    """Compare ARIN provider with device notes provider using fuzzy matching"""
    if not arin_provider or not label_provider:
        return None
    
    if arin_provider == "Unknown":
        return None
    
    # Normalize both providers
    arin_normalized = arin_provider.lower().strip()
    label_normalized = label_provider.lower().strip()
    
    # Use fuzzy matching
    score = fuzz.ratio(arin_normalized, label_normalized)
    
    # Check against known mappings
    for keyword, canonical in PROVIDER_KEYWORDS.items():
        if keyword in label_normalized:
            if canonical.lower() in arin_normalized:
                return "Match"
    
    # If fuzzy score is high enough, consider it a match
    if score >= 80:
        return "Match"
    else:
        return "No match"
```

## Key Implementation Details

1. **Cache Management**: All implementations use an IP cache to avoid redundant RDAP queries
2. **Private IP Handling**: Private IPs are immediately returned as "Unknown" without API calls
3. **Error Handling**: Invalid IPs are logged and added to a missing_set for tracking
4. **Company Normalization**: Multiple variations of company names are normalized to canonical forms
5. **Special Cases**: 
   - 166.80.0.0/16 range is hardcoded as "Verizon Business"
   - SBC-* networks are recognized as "AT&T"
   - CABLEONE network names are normalized to "Cable One, Inc."

## Database Storage

The ARIN provider data is stored in two locations:
1. **meraki_inventory table**: wan1_arin_provider, wan2_arin_provider columns
2. **rdap_cache table**: Caches IP-to-provider mappings for performance

## Usage Pattern

1. Check cache first (database or in-memory)
2. Apply special IP range rules
3. Check KNOWN_IPS mapping
4. Skip private IPs
5. Query ARIN RDAP API if needed
6. Parse response with entity extraction
7. Normalize company names
8. Cache and return result

This comprehensive logic ensures accurate provider identification across the system while minimizing API calls through effective caching and special case handling.