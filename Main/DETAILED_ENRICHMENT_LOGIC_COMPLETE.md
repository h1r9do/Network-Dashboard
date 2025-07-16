# Complete Detailed Enrichment Logic - Step by Step

## Phase 1: Data Loading

### Step 1.1: Load DSR Circuits from Database
```python
cursor.execute("""
    SELECT site_name, site_id, circuit_id, circuit_purpose, status,
           provider_name, details_ordered_service_speed, 
           billing_monthly_cost, ip_address_start
    FROM circuits
    WHERE status = 'Enabled'
""")
```
- Only loads ENABLED circuits
- Groups by site_name into dictionary
- Each site has list of circuits with provider, speed, cost, IP

### Step 1.2: Load Current Enriched Data
```python
cursor.execute("""
    SELECT network_name, wan1_provider, wan1_speed, wan1_circuit_role, wan1_confirmed,
           wan2_provider, wan2_speed, wan2_circuit_role, wan2_confirmed
    FROM enriched_circuits
""")
```
- Loads previous enrichment results
- Used for preservation logic (don't overwrite confirmed data)

### Step 1.3: Load Meraki Data
```python
cursor.execute("""
    SELECT network_name, device_serial, device_notes, 
           wan1_ip, wan2_ip, wan1_public_ip, wan2_public_ip,
           wan1_gateway, wan2_gateway, wan1_vlan, wan2_vlan
    FROM meraki_mx_uplink_data
    WHERE wan1_ip IS NOT NULL OR wan2_ip IS NOT NULL
""")
```
- Gets all sites with at least one IP
- Includes device notes for provider parsing

### Step 1.4: Load ARIN Provider Data
```python
cursor.execute("""
    SELECT network_name, wan1_provider, wan2_provider
    FROM meraki_mx_arin_data  
""")
```
- Pre-calculated ARIN RDAP lookups
- Maps IP addresses to ISP names

## Phase 2: Main Processing Loop

### For Each Meraki Site:

### Step 2.1: Extract Basic Data
```python
network_name = row['network_name']
device_notes = row['device_notes']
wan1_ip = row['wan1_ip']
wan2_ip = row['wan2_ip']
wan1_arin = arin_data.get(network_name, {}).get('wan1_provider', '')
wan2_arin = arin_data.get(network_name, {}).get('wan2_provider', '')
```

### Step 2.2: Skip Offline Sites
```python
# Skip sites with no IP addresses (offline)
if not wan1_ip and not wan2_ip:
    logger.info(f"{network_name}: Skipping - no IP addresses (offline)")
    continue
```

### Step 2.3: Parse Device Notes
```python
wan1_notes, wan1_speed, wan2_notes, wan2_speed = parse_device_notes(device_notes)
```

**Device Notes Parser Logic:**
```
Example Input:
"WAN 1
Cox Communications
1000M x 50M
WAN 2  
Verizon
Cell"

Parsing Steps:
1. Split on "WAN 2" pattern
2. Extract WAN1 section and WAN2 section
3. For each section:
   - Skip the "WAN X" line
   - Next non-empty line = Provider
   - If next line matches speed pattern = Speed
4. Return: wan1_provider="Cox Communications", wan1_speed="1000M x 50M"
          wan2_provider="Verizon", wan2_speed="Cell"
```

### Step 2.4: Get DSR Circuits for Site
```python
dsr_circuits = dsr_circuits_by_site.get(network_name, [])
```
- List of all enabled DSR circuits for this site
- Each has: provider, speed, cost, purpose (Primary/Secondary), IP

### Step 2.5: Compare ARIN vs Device Notes
```python
wan1_comparison = compare_providers(wan1_arin, wan1_notes)
wan2_comparison = compare_providers(wan2_arin, wan2_notes)
```

**Provider Comparison Logic:**
```python
def compare_providers(arin_provider, notes_provider):
    # Normalize both providers
    norm_arin = normalize_provider_for_comparison(arin_provider)
    norm_notes = normalize_provider_for_comparison(notes_provider)
    
    # Exact match
    if norm_notes == norm_arin:
        return "Match"
    
    # Fuzzy match
    similarity = fuzz.ratio(norm_notes, norm_arin)
    return "Match" if similarity >= 80 else "No match"
```

### Step 2.6: Check for Non-DSR Circuit Preservation
```python
if not dsr_circuits and current_record:
    if not has_source_data_changed(current_record, device_notes, wan1_ip, wan2_ip, wan1_arin, wan2_arin):
        # Non-DSR circuit with no changes - preserve completely
        non_dsr_preserved += 1
        continue
```

### Step 2.7: Detect WAN Flip
```python
is_flipped = False
if len(dsr_circuits) >= 2:
    is_flipped, confidence = detect_wan_flip(dsr_circuits, wan1_ip, wan2_ip, wan1_arin, wan2_arin)
```

**WAN Flip Detection Logic:**
```python
def detect_wan_flip(dsr_circuits, wan1_ip, wan2_ip, wan1_arin, wan2_arin):
    # Find Primary and Secondary circuits
    primary_circuit = None
    secondary_circuit = None
    
    for circuit in dsr_circuits:
        if circuit['purpose'] == 'Primary':
            primary_circuit = circuit
        elif circuit['purpose'] == 'Secondary':
            secondary_circuit = circuit
    
    # Check multiple indicators
    flip_indicators = 0
    
    # 1. Check IP addresses
    if primary_circuit.get('ip') == wan2_ip:
        flip_indicators += 1
    if secondary_circuit.get('ip') == wan1_ip:
        flip_indicators += 1
    
    # 2. Check ARIN providers
    if providers_match_for_sync(primary_circuit['provider'], wan2_arin):
        flip_indicators += 1
    if providers_match_for_sync(secondary_circuit['provider'], wan1_arin):
        flip_indicators += 1
    
    # Need at least 2 indicators to confirm flip
    return flip_indicators >= 2
```

### Step 2.8: Match Circuits to WANs

#### If Flipped:
```python
# Look for Secondary circuit for WAN1
for circuit in dsr_circuits:
    if circuit['purpose'] == 'Secondary':
        if circuit.get('ip') == wan1_ip:
            wan1_dsr = circuit
            break
        elif not wan1_dsr and providers_match_for_sync(circuit['provider'], wan1_arin):
            wan1_dsr = circuit

# Look for Primary circuit for WAN2
for circuit in dsr_circuits:
    if circuit['purpose'] == 'Primary':
        if circuit.get('ip') == wan2_ip:
            wan2_dsr = circuit
            break
        elif not wan2_dsr and providers_match_for_sync(circuit['provider'], wan2_arin):
            wan2_dsr = circuit
```

#### If Normal (ENHANCED):
```python
# Match WAN1
wan1_dsr = match_dsr_circuit_by_ip(dsr_circuits, wan1_ip)
if not wan1_dsr:
    wan1_dsr = match_dsr_circuit_by_provider(dsr_circuits, wan1_notes)
# NEW: Try ARIN provider if device notes fail
if not wan1_dsr and wan1_arin:
    wan1_dsr = match_dsr_circuit_by_provider(dsr_circuits, wan1_arin)
    if wan1_dsr:
        logger.info(f"{network_name}: WAN1 matched via ARIN fallback")

# Match WAN2
wan2_dsr = match_dsr_circuit_by_ip(dsr_circuits, wan2_ip)
if not wan2_dsr:
    wan2_dsr = match_dsr_circuit_by_provider(dsr_circuits, wan2_notes)
# NEW: Try ARIN provider if device notes fail
if not wan2_dsr and wan2_arin:
    wan2_dsr = match_dsr_circuit_by_provider(dsr_circuits, wan2_arin)
    if wan2_dsr:
        logger.info(f"{network_name}: WAN2 matched via ARIN fallback")
```

### Step 2.9: Check Preservation Logic
```python
# For WAN1: Check if we should preserve existing DSR data
wan1_preserve = False
if current_record.get('wan1_confirmed') and current_record.get('wan1_provider'):
    # Check if current WAN1 matches either ARIN provider (considering flips)
    if wan1_arin and providers_match_for_sync(current_record.get('wan1_provider'), wan1_arin):
        wan1_preserve = True
    elif wan2_arin and providers_match_for_sync(current_record.get('wan1_provider'), wan2_arin):
        # Current WAN1 matches WAN2 ARIN - possible flip scenario
        wan1_preserve = True

# Same logic for WAN2...
```

### Step 2.10: Build Final Enriched Record

#### For WAN1:
```python
if wan1_preserve and current_record.get('wan1_provider'):
    # Preserve existing confirmed data
    wan1_provider = current_record.get('wan1_provider')
    wan1_speed = current_record.get('wan1_speed')
    wan1_cost = extract_monthly_cost(current_record.get('wan1_monthly_cost'))
    wan1_role = current_record.get('wan1_circuit_role') or 'Primary'
    wan1_confirmed = True
    preserved_count += 1
elif wan1_dsr:
    # Use matched DSR data
    wan1_provider = wan1_dsr['provider']
    wan1_speed = reformat_speed(wan1_dsr['speed'], wan1_provider)
    wan1_cost = wan1_dsr['cost']
    wan1_role = 'Secondary' if is_flipped else 'Primary'
    wan1_confirmed = False
else:
    # Use device notes or ARIN data
    wan1_provider = wan1_notes or wan1_arin or ""
    wan1_speed = wan1_speed or ""
    wan1_cost = 0
    wan1_role = 'Primary'
    wan1_confirmed = False
```

### Step 2.11: Format Monthly Cost
```python
wan1_monthly_cost = f"${wan1_cost:.2f}" if wan1_cost else "$0.00"
wan2_monthly_cost = f"${wan2_cost:.2f}" if wan2_cost else "$0.00"
```

### Step 2.12: Determine Circuit Source
```python
circuit_source = determine_circuit_source(
    wan1_dsr is not None,
    wan2_dsr is not None,
    wan1_arin,
    wan2_arin,
    wan1_comparison,
    wan2_comparison
)
```

### Step 2.13: Insert/Update Enriched Record
```python
INSERT INTO enriched_circuits (
    network_name, 
    wan1_provider, wan1_speed, wan1_monthly_cost, wan1_circuit_role,
    wan2_provider, wan2_speed, wan2_monthly_cost, wan2_circuit_role,
    wan1_public_ip, wan2_public_ip,
    wan1_arin_org, wan2_arin_org,
    circuit_source, last_updated
) VALUES (...)
ON CONFLICT (network_name) DO UPDATE SET ...
```

### Step 2.14: Track Changes (if any)
```python
if has_changes:
    INSERT INTO enrichment_change_tracking (
        network_name, change_type, field_name,
        old_value, new_value, change_timestamp
    ) VALUES (...)
```

## Phase 3: Update DSR-Matched Records

### Step 3.1: Sync Confirmed Data Back to Circuits Table
```python
UPDATE circuits 
SET ip_address_start = %s,
    ip_address_end = %s,
    last_enrichment_sync = CURRENT_TIMESTAMP
WHERE site_name = %s 
AND provider_name = %s 
AND circuit_purpose = %s
AND status = 'Enabled'
```

## Key Functions Detail

### Provider Matching Function (ENHANCED):
```python
def match_dsr_circuit_by_provider(dsr_circuits, notes_provider):
    if not notes_provider or not dsr_circuits:
        return None
    
    notes_norm = normalize_provider_for_comparison(notes_provider)
    best_match = None
    best_score = 0
    
    for circuit in dsr_circuits:
        dsr_norm = normalize_provider_for_comparison(circuit['provider'])
        
        # Exact match after normalization
        if notes_norm == dsr_norm:
            return circuit
        
        # Fuzzy match
        score = max(
            fuzz.ratio(notes_norm, dsr_norm),
            fuzz.partial_ratio(notes_norm, dsr_norm)
        )
        
        # NEW: 70% threshold (was 60%)
        if score > 70 and score > best_score:
            best_match = circuit
            best_score = score
    
    return best_match
```

### Provider Normalization:
```python
def normalize_provider_for_comparison(provider):
    if not provider:
        return ""
    
    provider_lower = provider.lower().strip()
    
    # Remove common prefixes/suffixes
    provider_clean = re.sub(
        r'^\s*(?:dsr|agg|comcastagg|clink|not\s*dsr|--|-)\\s+|\s*(?:extended\s+cable|dsl|fiber|adi|workpace)\s*',
        '', provider_lower
    ).strip()
    
    # Apply provider mapping
    for key, mapped_value in PROVIDER_MAPPING.items():
        if key in provider_clean:
            return mapped_value.lower()
    
    return provider_clean
```

## Summary Statistics Tracking

Throughout the process, these counters are maintained:
- `total_processed`: Total sites processed
- `matched_both`: Sites with both WAN1 and WAN2 matched
- `matched_wan1_only`: Sites with only WAN1 matched
- `matched_wan2_only`: Sites with only WAN2 matched
- `no_matches`: Sites with no matches
- `preserved_count`: Confirmed records preserved
- `non_dsr_preserved`: Non-DSR circuits preserved
- `updated_count`: Records with changes