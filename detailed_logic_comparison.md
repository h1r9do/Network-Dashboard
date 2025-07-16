# Detailed Line-by-Line Logic Comparison

## My Current Recovery Script Logic vs Original Scripts

### Current Recovery Script Flow (recover_with_correct_logic.py)

**Lines 311-312: Step 1 - Parse Raw Notes**
```python
wan1_label, wan1_speed_label, wan2_label, wan2_speed_label = parse_raw_notes_original(raw_notes)
```
- ✅ **CORRECT**: Uses exact `parse_raw_notes()` from `meraki_mx.py`
- ✅ **CORRECT**: Returns 4 values: wan1_provider, wan1_speed, wan2_provider, wan2_speed

**Lines 314-316: Step 2 - Normalize Providers**
```python
wan1_normalized = normalize_provider_original(wan1_label, is_dsr=False) if wan1_label else ""
wan2_normalized = normalize_provider_original(wan2_label, is_dsr=False) if wan2_label else ""
```
- ✅ **CORRECT**: Uses exact `normalize_provider()` from `nightly_enriched.py`
- ✅ **CORRECT**: Handles VZG → VZW Cell mapping
- ✅ **CORRECT**: Removes IMEI, DSR prefixes

**Lines 318-324: Step 3 - Get IPs and ARIN Lookups**
```python
wan1_ip = device.get('wan1', {}).get('ip', '')
wan2_ip = device.get('wan2', {}).get('ip', '')
wan1_arin = get_provider_for_ip(wan1_ip, ip_cache, missing_ips) if wan1_ip else "Unknown"
wan2_arin = get_provider_for_ip(wan2_ip, ip_cache, missing_ips) if wan2_ip else "Unknown"
```
- ✅ **CORRECT**: Gets IPs from historical data
- ✅ **CORRECT**: Uses RDAP lookup with caching

**Lines 326-328: Step 4 - Compare Providers**
```python
wan1_comparison = compare_providers(wan1_arin, wan1_normalized) if wan1_normalized else None
wan2_comparison = compare_providers(wan2_arin, wan2_normalized) if wan2_normalized else None
```
- ✅ **CORRECT**: Compares ARIN vs normalized notes
- ✅ **CORRECT**: Returns "Match" or "No match"

**Lines 330-337: Step 5 - Get DSR Data and Final Provider Selection**
```python
site_enabled = network_name in enabled_circuits
wan1_dsr = enabled_circuits.get(network_name, {}).get('wan1', '')
wan2_dsr = enabled_circuits.get(network_name, {}).get('wan2', '')
wan1_final = determine_final_provider_original(wan1_normalized, wan1_arin, wan1_comparison, wan1_dsr, site_enabled)
wan2_final = determine_final_provider_original(wan2_normalized, wan2_arin, wan2_comparison, wan2_dsr, site_enabled)
```
- ✅ **CORRECT**: Gets DSR data for enabled circuits only
- ✅ **CORRECT**: Applies hierarchy: DSR > Notes (if no match) > ARIN

**Lines 339-341: Step 6 - Speed Formatting**
```python
wan1_speed_final = reformat_speed_original(wan1_speed_label, wan1_final)
wan2_speed_final = reformat_speed_original(wan2_speed_label, wan2_final)
```
- ✅ **CORRECT**: Uses exact `reformat_speed()` logic from `nightly_enriched.py`
- ✅ **CORRECT**: Provider-specific speed overrides (Cell, Satellite)

**Lines 343-364: Step 7 - Update meraki_inventory**
```python
cursor.execute("""
    UPDATE meraki_inventory
    SET device_notes = %s,
        wan1_provider_label = %s,    # wan1_normalized
        wan1_speed_label = %s,       # wan1_speed_label (raw parsed)
        wan2_provider_label = %s,    # wan2_normalized  
        wan2_speed_label = %s,       # wan2_speed_label (raw parsed)
        wan1_provider_comparison = %s,
        wan2_provider_comparison = %s,
        last_updated = NOW()
    WHERE device_serial = %s
""", (
    raw_notes,
    wan1_normalized,  # NORMALIZED provider
    wan1_speed_label, # RAW parsed speed
    wan2_normalized,  # NORMALIZED provider
    wan2_speed_label, # RAW parsed speed
    wan1_comparison,
    wan2_comparison,
    device_serial
))
```
- ✅ **CORRECT**: Stores NORMALIZED providers in provider_label fields
- ✅ **CORRECT**: Stores RAW parsed speeds in speed_label fields
- ✅ **CORRECT**: Stores comparison results

**Lines 368-382: Step 8 - Update enriched_circuits**
```python
cursor.execute("""
    UPDATE enriched_circuits
    SET wan1_provider = %s,    # wan1_final (after hierarchy)
        wan1_speed = %s,       # wan1_speed_final (formatted)
        wan2_provider = %s,    # wan2_final (after hierarchy)
        wan2_speed = %s,       # wan2_speed_final (formatted)
        last_updated = NOW()
    WHERE network_name = %s
""", (
    wan1_final,      # Final provider after hierarchy
    wan1_speed_final, # Formatted speed (Cell/Satellite/regular)
    wan2_final,      # Final provider after hierarchy
    wan2_speed_final, # Formatted speed (Cell/Satellite/regular)
    network_name
))
```
- ✅ **CORRECT**: Stores final providers after hierarchy logic
- ✅ **CORRECT**: Stores formatted speeds with Cell/Satellite overrides

---

## Comparison Against Original Scripts

### Original Logic from `/usr/local/bin/nightly_enriched.py`

**Original Provider Normalization:**
```python
def normalize_provider(provider, is_dsr=False):
    # ... exact cleaning logic ...
    if provider_lower.startswith('digi'):
        return "Digi"
    if provider_lower.startswith('starlink') or 'starlink' in provider_lower:
        return "Starlink"
    if provider_lower.startswith('inseego') or 'inseego' in provider_lower:
        return "Inseego"
    if provider_lower.startswith(('vz', 'vzw', 'vzn', 'verizon', 'vzm')) and not is_dsr:
        return "VZW Cell"
```
- ✅ **MY SCRIPT MATCHES**: `normalize_provider_original()` has identical logic

**Original Speed Formatting:**
```python
def reformat_speed(speed, provider):
    if provider in ["Inseego", "VZW Cell", "Digi", ""]:
        return "Cell"
    if provider == "Starlink":
        return "Satellite"
    # ... rest of speed formatting ...
```
- ✅ **MY SCRIPT MATCHES**: `reformat_speed_original()` has identical logic

**Original Parsing from `/usr/local/bin/meraki_mx.py`:**
```python
def parse_raw_notes(raw_notes):
    # ... exact regex and splitting logic ...
```
- ✅ **MY SCRIPT MATCHES**: `parse_raw_notes_original()` has identical logic

---

## What Data Should Be Stored Where

### meraki_inventory Table (Raw Processing Results)
- `device_notes`: Raw notes from Meraki API
- `wan1_provider_label`: **NORMALIZED** provider from Step 2 (e.g., "VZW Cell")
- `wan1_speed_label`: **RAW PARSED** speed from Step 1 (e.g., "500.0M x 500.0M")
- `wan2_provider_label`: **NORMALIZED** provider from Step 2 (e.g., "VZW Cell")  
- `wan2_speed_label`: **RAW PARSED** speed from Step 1 (e.g., "")
- `wan1_provider_comparison`: Comparison result ("Match"/"No match")
- `wan2_provider_comparison`: Comparison result ("Match"/"No match")

### enriched_circuits Table (Final Results)
- `wan1_provider`: **FINAL** provider after hierarchy (e.g., "Frontier Communications")
- `wan1_speed`: **FORMATTED** speed with overrides (e.g., "500.0M x 500.0M") 
- `wan2_provider`: **FINAL** provider after hierarchy (e.g., "VZW Cell")
- `wan2_speed`: **FORMATTED** speed with overrides (e.g., "Cell")

---

## CAL 17 Example with Current Logic

**Input**: 
```
Raw Notes: "WAN1 NOT DSR Frontier Fiber 500.0M x 500.0M ... WAN2 VZG IMEI: 356405432462415"
WAN1 IP: 47.176.201.18
WAN2 IP: 192.168.0.151
```

**Processing**:
1. **Parse**: wan1_label="NOT DSR Frontier Fiber", wan2_label="VZG IMEI 356405432462415"
2. **Normalize**: wan1_normalized="Frontier", wan2_normalized="VZW Cell"
3. **ARIN**: wan1_arin="Frontier Communications", wan2_arin="Private IP"
4. **Compare**: wan1_comparison="No match", wan2_comparison=None
5. **Final**: wan1_final="Frontier", wan2_final="VZW Cell"
6. **Speed**: wan1_speed_final="500.0M x 500.0M", wan2_speed_final="Cell"

**Expected Storage**:

**meraki_inventory**:
- wan1_provider_label: "Frontier" (normalized)
- wan1_speed_label: "500.0M x 500.0M" (raw parsed)
- wan2_provider_label: "VZW Cell" (normalized)
- wan2_speed_label: "" (raw parsed)

**enriched_circuits**:
- wan1_provider: "Frontier" (final after hierarchy)
- wan1_speed: "500.0M x 500.0M" (formatted)
- wan2_provider: "VZW Cell" (final after hierarchy)  
- wan2_speed: "Cell" (formatted override)

---

## VERDICT: LOGIC IS CORRECT

✅ **ALL STEPS MATCH ORIGINAL LOGIC**
✅ **DATABASE STORAGE IS CORRECT**
✅ **SPEED FORMATTING IS CORRECT**
✅ **PROVIDER NORMALIZATION IS CORRECT**
✅ **HIERARCHY LOGIC IS CORRECT**

**The recovery script logic is implementing the original logic correctly.**