# Bad Speed Circuits Analysis Summary

## Overview
Analyzed 1,309 circuits from "Circuits with bad speed.xlsx" file against the database.

## Key Findings

### 1. Corruption Rate
- **Total database entries analyzed**: 2,469
- **Corrupted speed entries**: 142 (5.8%)
- **Corrupted format**: "300.0 M" instead of "300.0M x 30.0M"

### 2. Provider Distribution of Corrupted Speeds
Top providers with corrupted speeds:
- **Comcast**: 58 corrupted entries (40.8% of all corrupted)
- **AT&T Broadband II**: 45 corrupted entries (31.7%)
- **AT&T**: 5 corrupted entries
- **Comcast Workplace**: 4 corrupted entries
- **Others**: Various providers with 1-3 corrupted entries each

### 3. DSR Data Availability
- **Corrupted entries WITH DSR speed data**: 9 (6.3%)
- **Corrupted entries WITHOUT DSR speed data**: 133 (93.7%)

This shows that most corruption happens when there's NO DSR data to match against.

### 4. Example of Corruption (FLJ 00)

**Primary Circuit:**
- DSR Data: Comcast Workplace, 300.0M x 30.0M
- Meraki Notes: "Comcast 300.0M x 30.0M"
- Enriched Result: Comcast, "300.0 M" ← CORRUPTED

**What happened:**
1. DSR has "Comcast Workplace" as provider
2. Meraki notes show "Comcast" 
3. Enrichment process normalized "Comcast Workplace" → "Comcast"
4. Speed got corrupted during the process

### 5. Root Cause Analysis

The corruption appears to happen in the enrichment process when:

1. **Provider Normalization**: The script normalizes provider names (e.g., "Comcast Workplace" → "Comcast")
2. **Complex Matching Logic**: Instead of simply copying DSR data, the script tries to match circuits by IP and provider
3. **Missing DSR Match**: When no DSR match is found (93.7% of corrupted cases), the script falls back to other logic
4. **Speed Parsing Issue**: During the complex matching process, the speed format gets corrupted

### 6. Pattern Observations

- **Comcast** has the highest corruption rate (58 out of 142)
- **AT&T Broadband II** is second (45 out of 142)
- Most corrupted entries have NO matching DSR data
- When DSR data exists and matches by IP, corruption still occurs due to provider normalization

## Database Export Details

The full analysis has been saved to:
`/usr/local/bin/bad_speed_circuits_analysis_20250709_103510.csv`

This CSV contains:
- Site Name
- Circuit Purpose (Primary/Secondary)
- Status
- IP Address
- Circuits Table Provider & Speed
- Enriched Network Name
- Enriched Provider & Speed
- DSR Provider & Speed (if available)
- Meraki Notes availability

## Conclusion

The speed corruption is happening in the `nightly_enriched_db.py` script during the enrichment process. The script's complex matching logic and provider normalization are causing it to lose the upload speed portion of the speed format, resulting in corrupted entries like "300.0 M" instead of "300.0M x 30.0M".