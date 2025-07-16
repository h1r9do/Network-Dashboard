# Recovery Script Logic vs Original Scripts - Line by Line Comparison

## My Recovery Script Logic (recover_with_correct_logic.py)

### Step 1: Parse Raw Notes
```python
wan1_label, wan1_speed_label, wan2_label, wan2_speed_label = parse_raw_notes_original(raw_notes)
```
**What it does**: Parses "WAN1 NOT DSR Frontier Fiber 500.0M x 500.0M ... WAN2 VZG IMEI: 356405432462415"
**Result**: wan1_label="NOT DSR Frontier Fiber", wan2_label="VZG IMEI 356405432462415"

### Step 2: Normalize Providers
```python
wan1_normalized = normalize_provider_original(wan1_label, is_dsr=False) if wan1_label else ""
wan2_normalized = normalize_provider_original(wan2_label, is_dsr=False) if wan2_label else ""
```
**What it does**: Applies normalization (remove IMEI, DSR prefixes, VZG→VZW Cell mapping)
**Result**: wan1_normalized="Frontier", wan2_normalized="VZW Cell"

### Step 3: ARIN Lookups
```python
wan1_arin = get_provider_for_ip(wan1_ip, ip_cache, missing_ips) if wan1_ip else "Unknown"
wan2_arin = get_provider_for_ip(wan2_ip, ip_cache, missing_ips) if wan2_ip else "Unknown"
```
**What it does**: Looks up IP providers via RDAP
**Result**: wan1_arin="Frontier Communications", wan2_arin="Private IP"

### Step 4: Compare Providers
```python
wan1_comparison = compare_providers(wan1_arin, wan1_normalized) if wan1_normalized else None
wan2_comparison = compare_providers(wan2_arin, wan2_normalized) if wan2_normalized else None
```
**What it does**: Compares ARIN vs normalized notes
**Result**: wan1_comparison="No match", wan2_comparison=None

### Step 5: Final Provider Selection
```python
wan1_final = determine_final_provider_original(wan1_normalized, wan1_arin, wan1_comparison, wan1_dsr, site_enabled)
wan2_final = determine_final_provider_original(wan2_normalized, wan2_arin, wan2_comparison, wan2_dsr, site_enabled)
```
**What it does**: Applies hierarchy (DSR > Notes if no match > ARIN)
**Result**: wan1_final="Frontier", wan2_final="VZW Cell"

### Step 6: Speed Assignment (MY CURRENT LOGIC)
```python
if wan1_final and any(x in wan1_final.lower() for x in ['cell', 'digi', 'vzw', 'vzg', 'inseego']):
    wan1_speed_final = 'Cell'
elif 'starlink' in wan1_final.lower():
    wan1_speed_final = 'Satellite'
else:
    wan1_speed_final = wan1_speed_label or '0.0M x 0.0M'
```
**What it does**: Checks provider name for cell/satellite keywords
**Issues**: ❌ Uses loose keyword matching instead of exact provider names

### Step 7: Database Storage (MY CURRENT LOGIC)
```python
# meraki_inventory
wan1_provider_label = wan1_normalized  # "Frontier"
wan2_provider_label = wan2_normalized  # "VZW Cell"

# enriched_circuits  
wan1_provider = wan1_final  # "Frontier"
wan2_provider = wan2_final  # "VZW Cell"
```

---

## Original Scripts Logic (meraki_mx.py + nightly_enriched.py)

### Step 1: Parse Raw Notes ✅ SAME
From `meraki_mx.py` parse_raw_notes() - EXACT SAME LOGIC

### Step 2: Normalize Providers ✅ SAME  
From `nightly_enriched.py` normalize_provider() - EXACT SAME LOGIC

### Step 3: ARIN Lookups ✅ SAME
Standard RDAP lookup - SAME LOGIC

### Step 4: Compare Providers ✅ SAME
Fuzzy matching logic - SAME LOGIC

### Step 5: Final Provider Selection ✅ SAME
Hierarchy logic - SAME LOGIC

### Step 6: Speed Assignment (ORIGINAL LOGIC)
From `nightly_enriched.py` reformat_speed() function:
```python
def reformat_speed(speed, provider):
    # Override speed for specific providers
    if provider in ["Inseego", "VZW Cell", "Digi", ""]:
        return "Cell"
    if provider == "Starlink":
        return "Satellite"
    if not speed or str(speed).lower() in ['cell', 'satellite', 'tbd', 'unknown', 'nan']:
        return str(speed) or "Unknown"
    # ... rest of speed formatting logic
```

---

## COMPARISON: What I'm Missing

### ❌ MISSING #1: Exact Provider Name Matching for Speed
**Original Logic**: `if provider in ["Inseego", "VZW Cell", "Digi", ""]:`
**My Logic**: `if any(x in wan1_final.lower() for x in ['cell', 'digi', 'vzw', 'vzg', 'inseego']):`
**Problem**: I'm using keyword matching instead of exact provider name matching

### ❌ MISSING #2: Speed Formatting Logic
**Original Logic**: Has complete speed formatting with regex parsing, unit conversion
**My Logic**: Just assigns "Cell" or "Satellite", doesn't handle regular speeds properly
**Problem**: Not implementing the full reformat_speed function

### ❌ MISSING #3: Empty Provider Handling
**Original Logic**: `if provider in ["Inseego", "VZW Cell", "Digi", ""]:`
**My Logic**: Doesn't check for empty provider
**Problem**: Missing empty string case

### ❌ MISSING #4: Original Speed Preservation
**Original Logic**: Uses original parsed speed if not cell/satellite
**My Logic**: Uses `wan1_speed_label or '0.0M x 0.0M'`
**Problem**: Should preserve original speed, not default to 0.0M

## CORRECT IMPLEMENTATION NEEDED

### Fix #1: Exact Provider Matching
```python
def reformat_speed_original(speed, provider):
    """EXACT logic from nightly_enriched.py"""
    # Override speed for specific providers
    if provider in ["Inseego", "VZW Cell", "Digi", ""]:
        return "Cell"
    if provider == "Starlink":
        return "Satellite"
    if not speed or str(speed).lower() in ['cell', 'satellite', 'tbd', 'unknown', 'nan']:
        return str(speed) or "Unknown"
    
    # Format regular speeds
    match = re.match(r'^([\d.]+)\s*(M|G|MB)\s*[xX]\s*([\d.]+)\s*(M|G|MB)$', str(speed), re.IGNORECASE)
    if match:
        download, d_unit, upload, u_unit = match.groups()
        try:
            download = float(download)
            upload = float(upload)
            return f"{download:.1f}{d_unit} x {upload:.1f}{u_unit}"
        except:
            return str(speed)
    return str(speed)
```

### Fix #2: Use Original Function
```python
# Instead of my current logic:
wan1_speed_final = reformat_speed_original(wan1_speed_label, wan1_final)
wan2_speed_final = reformat_speed_original(wan2_speed_label, wan2_final)
```

### Expected Results with Correct Logic:
- **CAL 17 WAN1**: provider="Frontier", speed="500.0M x 500.0M" (formatted, not "Cell")
- **CAL 17 WAN2**: provider="VZW Cell", speed="Cell" (because provider="VZW Cell")

## Summary of Missing Logic:
1. ❌ Not using exact provider name matching for speed assignment
2. ❌ Missing complete speed formatting function  
3. ❌ Not handling empty provider case
4. ❌ Not preserving original speeds for non-cellular providers
5. ❌ Using keyword matching instead of exact string matching

**ACTION NEEDED**: Implement the exact `reformat_speed()` function from `nightly_enriched.py`