# DSR Circuits - Complete Logic Documentation

## Overview
This document defines the complete step-by-step logic for processing Meraki device notes and enriching circuit data. This logic is implemented across multiple scripts and is the authoritative source for how provider information is parsed, normalized, and enriched.

## Complete Step-by-Step Logic for Notes Processing

### Step 1: Raw Notes Parsing (`meraki_mx.py` - `parse_raw_notes()`)

**Input**: Raw device notes from Meraki API
**Function**: Extract WAN1 and WAN2 provider/speed labels

#### 1.1 Text Preprocessing
- Strip whitespace and normalize spaces: `re.sub(r'\s+', ' ', raw_notes.strip())`

#### 1.2 Pattern Definitions
- WAN1: `r'(?:WAN1|WAN\s*1)\s*:?\s*'` (case insensitive)
- WAN2: `r'(?:WAN2|WAN\s*2)\s*:?\s*'` (case insensitive) 
- Speed: `r'(\d+(?:\.\d+)?)\s*([MG]B?)\s*x\s*(\d+(?:\.\d+)?)\s*([MG]B?)'`

#### 1.3 Text Splitting Logic
- First, try to split on WAN1 pattern
- If WAN1 found: take remainder and split on WAN2 pattern
- If no WAN1: try splitting on WAN2 pattern only
- Fallback: treat entire text as WAN1

#### 1.4 Provider/Speed Extraction (for each WAN segment)
- Search for speed pattern in segment
- If speed found:
  - Extract up/down speeds and units
  - Convert G/GB to M (multiply by 1000)
  - Format as: `"{up_speed:.1f}{up_unit} x {down_speed:.1f}{down_unit}"`
  - Provider = text before speed match
- If no speed: entire segment is provider
- Clean provider: `re.sub(r'[^\w\s.&|-]', ' ', provider_name)`

**Output**: `wan1_provider, wan1_speed, wan2_provider, wan2_speed` (raw labels)

### Step 2: Provider Normalization (`nightly_enriched.py` - `normalize_provider()`)

**Input**: Raw provider label from Step 1
**Function**: Normalize to canonical provider names

#### 2.1 Initial Cleaning
```python
# Remove IMEI, serial numbers, location info, etc.
provider_clean = re.sub(
    r'\s*(?:##.*##|\s*imei.*$|\s*kitp.*$|\s*sn.*$|\s*port.*$|\s*location.*$|\s*in\s+the\s+bay.*$|\s*up\s+front.*$|\s*under\s+.*$|\s*wireless\s+gateway.*$|\s*serial.*$|\s*poe\s+injector.*$|\s*supported\s+through.*$|\s*static\s+ip.*$|\s*subnet\s+mask.*$|\s*gateway\s+ip.*$|\s*service\s+id.*$|\s*circuit\s+id.*$|\s*ip\s+address.*$|\s*5g.*$|\s*currently.*$)',
    '', str(provider), flags=re.IGNORECASE
).strip()
```

#### 2.2 Prefix Removal
```python
# Remove DSR, AGG, NOT DSR prefixes and suffixes like "extended cable"
provider_clean = re.sub(
    r'^\s*(?:dsr|agg|comcastagg|clink|not\s*dsr|--|-)\s+|\s*(?:extended\s+cable|dsl|fiber|adi|workpace)\s*',
    '', provider_clean, flags=re.IGNORECASE
).strip()
```

#### 2.3 Special Provider Detection (in order)
- `provider_lower.startswith('digi')` → "Digi"
- `provider_lower.startswith('starlink') or 'starlink' in provider_lower` → "Starlink"  
- `provider_lower.startswith('inseego') or 'inseego' in provider_lower` → "Inseego"
- `provider_lower.startswith(('vz', 'vzw', 'vzn', 'verizon', 'vzm')) and not is_dsr` → "VZW Cell"

#### 2.4 Fuzzy Matching
Use provider_mapping dictionary with `fuzz.ratio(key, provider_lower) > 70`:
```python
provider_mapping = {
    "vzg": "VZW Cell",
    "spectrum": "Charter Communications", 
    "cox business": "Cox Communications",
    "comcast workplace": "Comcast",
    "at&t broadband ii": "AT&T",
    "frontier fiber": "Frontier Communications",
    # ... complete mapping from nightly_enriched.py
}
```

**Output**: Normalized provider name (e.g., "VZW Cell", "Charter Communications")

### Step 3: ARIN Provider Lookup

**Input**: WAN IP addresses
**Function**: Get ISP information via RDAP API

#### 3.1 IP Processing
1. **IP Validation**: Check if private IP → return "Private IP"
2. **Cache Check**: Look in existing IP cache first
3. **RDAP Query**: Query ARIN RDAP API for public IPs
4. **Response Parsing**: Extract organization name with date-based sorting (newest first)

**Output**: ARIN provider name (e.g., "Frontier Communications")

### Step 4: Provider Comparison Logic

**Input**: Normalized notes provider vs ARIN provider
**Function**: Determine if they match

#### 4.1 Comparison Rules
1. **Exact Match**: Normalized provider == ARIN provider → "Match"
2. **Fuzzy Match**: Use fuzzywuzzy for similarity → "Match" if > threshold
3. **No Match**: Different providers → "No match" 

**Output**: "Match" or "No match"

### Step 5: Final Provider Selection (Enrichment Hierarchy)

**Input**: Notes provider, ARIN provider, comparison result, DSR data
**Function**: Apply business logic hierarchy with DSR priority and IP-based WAN assignment

#### 5.1 WAN Assignment Logic
**IP Address Matching determines WAN assignments**: 
- DSR circuits are matched to WAN ports by IP address
- If DSR Circuit A's IP matches WAN1's IP → Circuit A data goes to WAN1
- If DSR Circuit B's IP matches WAN2's IP → Circuit B data goes to WAN2
- DSR Primary/Secondary roles are preserved but don't control WAN assignment

#### 5.2 DSR Matching Priority
1. **IP Address Match (Highest Priority)**:
   - If WAN IP matches DSR circuit's ip_address_start → use that DSR circuit
   - Provider name used exactly as in DSR (no normalization)
   - Circuit Purpose (Primary/Secondary) preserved as circuit_role

2. **Provider Name Match (Second Priority)**:
   - If no IP match, try fuzzy matching (>60% threshold) on provider names
   - Matches DSR provider_name against normalized notes provider
   - Provider name used exactly as in DSR (no normalization)

#### 5.3 Fallback Provider Selection (No DSR Match)
When no DSR circuit matches by IP or provider name:

1. **Check provider_comparison from meraki_mx.py**:
   - If "No match" → use provider_label (from notes)
   - If "Match" → use provider (from ARIN)
   - If no comparison → use provider_label if exists, else provider

2. **Normalize the selected provider** (only for non-DSR):
   - Apply normalize_provider() function
   - Set confirmed = False (not from DSR)

**Key Rules**: 
- DSR provider names are NEVER normalized (e.g., "AT&T Broadband II" stays as-is)
- Only non-DSR providers get normalized
- The confirmed flag indicates if data came from DSR (True) or not (False)

**Output**: Final enriched provider for display with correct WAN assignments

## Example Walkthrough: CAL 17

**Raw Notes**: `"WAN1 NOT DSR Frontier Fiber 500.0M x 500.0M ... WAN2 VZG IMEI: 356405432462415"`

### Step 1 - Parsing:
- WAN1 segment: `"NOT DSR Frontier Fiber 500.0M x 500.0M"`
- WAN2 segment: `"VZG IMEI: 356405432462415"`
- **Result**: wan1_provider="NOT DSR Frontier Fiber", wan1_speed="500.0M x 500.0M", wan2_provider="VZG IMEI: 356405432462415", wan2_speed=""

### Step 2 - Normalization:
- WAN1: "NOT DSR Frontier Fiber" → remove "NOT DSR" → "Frontier Fiber"
- WAN2: "VZG IMEI: 356405432462415" → remove IMEI suffix → "VZG" → matches "vzg" mapping → **"VZW Cell"**

### Step 3 - ARIN:
- WAN1 IP: 47.176.201.18 → **"Frontier Communications"**
- WAN2 IP: 192.168.0.151 → **"Private IP"**

### Step 4 - Comparison:
- WAN1: "Frontier Fiber" vs "Frontier Communications" → fuzzy match → **"Match"**
- WAN2: "VZW Cell" vs "Private IP" → **"No match"**

### Step 5 - Final Selection:
- WAN1: Match found → use ARIN → **"Frontier Communications"**
- WAN2: No match → use normalized notes → **"VZW Cell"**

**Expected Final Result**: WAN1="Frontier Communications", WAN2="VZW Cell"

## Implementation Files

### Primary Scripts
- `/usr/local/bin/meraki_mx.py` - Original parsing logic (Step 1)
- `/usr/local/bin/nightly_enriched.py` - Original normalization logic (Step 2)
- `/usr/local/bin/Main/nightly_meraki_db.py` - Database-integrated implementation
- `/usr/local/bin/Main/recover_all_from_historical.py` - Recovery script using historical data

### Database Tables
- `meraki_inventory` - Raw parsing results (wan1_provider_label, wan2_provider_label, etc.)
- `enriched_circuits` - Final enriched results (wan1_provider, wan2_provider)
- `rdap_cache` - ARIN lookup cache

## Key Business Rules

1. **Enabled Circuits Only**: Only process circuits with status='enabled' from DSR data
2. **VZG/VZW Normalization**: All VZG variants become "VZW Cell" regardless of IMEI
3. **DSR Takes Priority**: Enabled DSR data overrides notes/ARIN when available
4. **Comparison Logic**: When notes don't match ARIN, trust the notes
5. **Private IP Handling**: Private IPs return "Private IP" for ARIN lookups

## Version History
- **Original Logic**: `/usr/local/bin/meraki_mx.py` + `/usr/local/bin/nightly_enriched.py`
- **Database Migration**: Combined logic in `/usr/local/bin/Main/nightly_meraki_db.py`
- **Recovery Implementation**: June 24, 2025 - Historical data restoration
- **Logic Correction**: June 30, 2025 - Fixed to preserve DSR provider names exactly

## Critical Implementation Notes

### DSR Provider Name Preservation
- **DSR Matched Circuits**: Provider names MUST be preserved exactly as they appear in DSR
  - "AT&T Broadband II" stays as "AT&T Broadband II" (NOT normalized to "AT&T")
  - "Comcast Workplace" stays as "Comcast Workplace" (NOT normalized to "Comcast")
- **Non-DSR Circuits**: Only these get normalized using the provider mapping

### Confirmed Flag Usage
- `confirmed = True`: Circuit matched from DSR data (by IP or provider name)
- `confirmed = False`: No DSR match, using ARIN/notes fallback
- This flag should only change when DSR circuit changes occur

### WAN Assignment by IP
- DSR Primary/Secondary labels are stored but don't control WAN assignment
- Actual WAN port is determined by IP address matching
- Example: DSR Secondary circuit goes to WAN1 if its IP matches WAN1's IP

---

**Last Updated**: June 30, 2025  
**Status**: Authoritative Documentation - Use this as source of truth for all implementations