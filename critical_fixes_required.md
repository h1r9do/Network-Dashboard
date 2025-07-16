# Critical Fixes Required for Database Script

## 1. CRITICAL BUG - Missing Function

### Issue
The script calls `get_organization_uplink_statuses()` on line 412 but this function is NOT defined in the file.

### Fix Required
Add this function from `meraki_mx.py` (lines 203-217):
```python
def get_organization_uplink_statuses(org_id):
    """Retrieve WAN uplink statuses for all appliances in the organization."""
    all_statuses = []
    url = f"{BASE_URL}/organizations/{org_id}/appliance/uplink/statuses"
    params = {'perPage': 1000, 'startingAfter': None}
    while True:
        statuses = make_api_request(url, MERAKI_API_KEY, params)
        if not statuses:
            break
        all_statuses.extend(statuses)
        if len(statuses) < 1000:
            break
        params['startingAfter'] = statuses[-1]['serial']
        logging.info(f"Fetched {len(statuses)} devices, total so far: {len(all_statuses)}")
    return all_statuses
```

## 2. Missing Provider Mappings

### Issue
Missing 73 provider mappings from the enrichment script, which will cause incorrect provider normalization.

### Fix Required
Add all missing mappings to PROVIDER_MAPPING dictionary (see missing_provider_mappings.md for complete list).

## 3. Incorrect Speed Formatting

### Issue
The `reformat_speed()` function is missing critical logic for cellular and satellite providers.

### Current Code (Incorrect)
```python
def reformat_speed(speed, provider):
    if provider and provider.lower() == "starlink":
        return "Satellite"
    # Missing Cell logic
```

### Fix Required
```python
def reformat_speed(speed, provider):
    # Override speed for specific providers
    if provider in ["Inseego", "VZW Cell", "Digi", ""]:
        return "Cell"
    if provider == "Starlink":
        return "Satellite"
    if not speed or str(speed).lower() in ['cell', 'satellite', 'tbd', 'unknown', 'nan']:
        return str(speed) or "Unknown"
    # ... rest of logic
```

## 4. Missing parse_raw_notes Logic

### Issue
The new script is missing the specific format parsing that handles:
```
WAN 1
Provider
Speed
WAN 2
Provider
Speed
```

### Fix Required
Add the specific pattern matching from `nightly_enriched.py` lines 216-225.

## 5. Missing Provider Normalization Logic

### Issue
The `normalize_provider()` function is missing:
1. The `is_dsr` parameter
2. Special handling for Digi, Starlink, Inseego
3. VZW/Verizon normalization logic
4. Extensive regex cleaning

### Fix Required
Implement the full logic from `nightly_enriched.py` lines 146-167.

## 6. Incorrect Provider Comparison

### Issue
Lines 472-473 use simple string comparison instead of fuzzy matching.

### Current Code (Incorrect)
```python
wan1_comparison = "Match" if wan1_provider and wan1_label and wan1_provider.lower() in wan1_label.lower() else "No match"
```

### Fix Required
Implement the `compare_providers()` function from `meraki_mx.py` lines 180-193 with fuzzy matching.

## 7. Missing WAN Provider Priority Logic

### Issue
The enrichment process doesn't prioritize provider_label when provider_comparison is "No match".

### Fix Required
When collecting data, check provider_comparison and prioritize accordingly (see `nightly_enriched.py` lines 373-380).

## 8. Missing Data Persistence

### Issues
1. No IP cache persistence (should save/load from file)
2. No missing data logging
3. No backup creation before updates
4. No change tracking/reporting

### Fix Required
Implement these features for production reliability.

## Priority Order

1. **Fix missing function** - Script won't run without this
2. **Add provider mappings** - Critical for data quality
3. **Fix speed formatting** - Important for correct data
4. **Fix provider normalization** - Important for matching
5. **Add parse_raw_notes logic** - Important for some networks
6. **Fix provider comparison** - Important for accuracy
7. **Add data persistence** - Important for production
8. **Add WAN provider priority** - Nice to have

## Testing Recommendations

After fixes:
1. Compare output with old scripts on same data
2. Verify all 1,296 networks are processed correctly
3. Check provider normalization for known test cases
4. Validate speed formatting for Cell/Satellite providers
5. Ensure database records match expected JSON structure