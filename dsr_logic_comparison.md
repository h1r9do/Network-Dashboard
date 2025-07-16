# DSR Circuit Logic Comparison: Legacy vs Current Scripts

## Overview
This document compares the circuit processing logic between:
1. **Legacy Scripts**: `meraki_mx.py` + `nightly_enriched.py`
2. **Current Fixed Script**: `automated_notes_restoration_fixed.py`
3. **Correct Implementation**: `automated_notes_restoration_correct.py`
4. **Nightly Database Script**: `nightly_enriched_db.py`

## Step-by-Step Logic Comparison

### Step 1: Initial Data Collection

#### Legacy (`meraki_mx.py`)
```python
# 1. Get WAN IP addresses from Meraki uplink status
wan1_ip = uplink_dict.get(serial, {}).get('wan1', {}).get('ip', '')
wan2_ip = uplink_dict.get(serial, {}).get('wan2', {}).get('ip', '')

# 2. Parse device notes
wan1_label, wan1_speed, wan2_label, wan2_speed = parse_raw_notes(raw_notes)

# 3. Perform ARIN lookups
wan1_provider = get_provider_for_ip(wan1_ip)  # ARIN RDAP lookup
wan2_provider = get_provider_for_ip(wan2_ip)  # ARIN RDAP lookup

# 4. Compare ARIN vs notes
wan1_comparison = compare_providers(wan1_provider, wan1_label)  # "Match" or "No match"
wan2_comparison = compare_providers(wan2_provider, wan2_label)  # "Match" or "No match"
```

#### Current Fixed Script
❌ **INCORRECT**: Normalizes all providers, including DSR names

#### Correct Implementation  
✅ **CORRECT**: Preserves exact source data, including comparisons

### Step 2: DSR Circuit Matching

#### Legacy (`nightly_enriched.py`)
```python
# Priority 1: Match by IP address
ip_matches = valid_matches[valid_matches["ip_address_start"] == wan_ip]
if ip_matches:
    return {
        "provider": row["provider_name"],  # DSR name used EXACTLY
        "role": row["Circuit Purpose"]      # Primary/Secondary preserved
    }

# Priority 2: Match by provider name (fuzzy)
score = fuzz.ratio(normalized_wan_provider, tracking_provider)
if score > 60:
    return {
        "provider": row["provider_name"],  # DSR name used EXACTLY
        "role": row["Circuit Purpose"]
    }
```

#### Current Fixed Script
❌ **INCORRECT**: 
```python
# Normalizes DSR providers
wan1_provider = normalize_provider_original(wan1_provider_raw)  # AT&T Broadband II → AT&T
```

#### Correct Implementation
✅ **CORRECT**:
```python
# DSR providers preserved exactly
if dsr_match:
    return circuit['provider'], True  # "AT&T Broadband II" stays as-is
```

### Step 3: Fallback Logic (No DSR Match)

#### Legacy (`nightly_enriched.py`)
```python
# Line 374-378: Fallback logic
if site["wan1"].get("provider_comparison") == "No match":
    wan1_provider_raw = site["wan1"].get("provider_label")  # Use notes
else:
    wan1_provider_raw = site["wan1"].get("provider")  # Use ARIN
```

#### Current Fixed Script
❌ **INCORRECT**: Always normalizes providers

#### Correct Implementation
✅ **CORRECT**: Matches legacy exactly
```python
if comparison == "No match":
    return notes_provider, False  # Trust notes over ARIN
else:
    return arin_provider, False   # Trust ARIN when match
```

### Step 4: WAN Assignment Logic

#### Legacy
- **IP-based assignment**: Circuit goes to whichever WAN has matching IP
- **DSR Primary/Secondary**: Stored but doesn't control WAN slot
```python
# DSR Circuit with IP 1.2.3.4 marked "Secondary"
# If WAN1 has IP 1.2.3.4, the circuit goes to WAN1
```

#### All Current Scripts
✅ **CORRECT**: All follow IP-based assignment

### Step 5: Provider Normalization

#### Legacy
```python
# Only normalize non-DSR providers
if not is_dsr:
    provider = normalize_provider(provider)  # Charter → Charter Communications
```

#### Current Fixed Script  
❌ **INCORRECT**: Normalizes everything

#### Correct Implementation
✅ **CORRECT**: Only normalizes when no DSR match

## Key Differences Summary

| Aspect | Legacy | Current Fixed | Correct Implementation |
|--------|--------|---------------|----------------------|
| DSR Provider Names | Preserved exactly | ❌ Normalized | ✅ Preserved exactly |
| Provider Comparison | Used for fallback | ❌ Ignored | ✅ Used for fallback |
| WAN Assignment | IP-based | ✅ IP-based | ✅ IP-based |
| Primary/Secondary | Stored only | ✅ Stored only | ✅ Stored only |
| Normalization | Only non-DSR | ❌ All providers | ✅ Only non-DSR |

## Required Changes to Current Scripts

### 1. `automated_notes_restoration_fixed.py`
- **Line 307-308**: Remove normalization of DSR providers
- **Lines 372-378**: Add comparison-based fallback logic
- **Lines 464-468**: Don't normalize DSR providers in database update

### 2. `nightly_enriched_db.py`
- Add provider comparison logic from `meraki_mx.py`
- Preserve DSR provider names exactly when matched
- Only normalize when no DSR match exists
- Use comparison result for fallback decisions

### 3. `nightly_meraki_db.py`
- Should perform ARIN lookups and provider comparisons
- Store comparison results ("Match"/"No match")
- Keep both ARIN provider and notes provider

## Correct Logic Flow

1. **Collect Data** (meraki_mx.py):
   - Get WAN IPs
   - Parse notes for provider labels
   - Lookup ARIN providers
   - Compare ARIN vs notes → "Match" or "No match"

2. **Match DSR Circuits** (nightly_enriched.py):
   - Try IP match first (best)
   - Try provider name match (fallback)
   - If match found → use DSR provider name EXACTLY

3. **No DSR Match - Use Comparison**:
   - If "No match" → trust notes provider
   - If "Match" → trust ARIN provider
   - Only normalize at this stage

4. **Store Results**:
   - `confirmed = True` if DSR match
   - `confirmed = False` if no DSR match
   - Provider name preserved exactly for DSR

This ensures DSR data integrity while maintaining proper fallback logic for non-DSR sites.