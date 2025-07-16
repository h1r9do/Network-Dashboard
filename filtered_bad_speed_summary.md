# Filtered Bad Speed Circuits Analysis - Complete Summary

## Overview
Analyzed 147 unique circuits from the filtered "Circuits with bad speed.xlsx" file, which resulted in 251 database records (includes multiple entries per site for Primary/Secondary circuits).

## Key Findings

### 1. Corruption Statistics
- **Total records analyzed**: 251
- **Corrupted speed format**: 132 (52.6%)
- **Corruption pattern**: Speed shows as "500.0 M" instead of "500.0M x 500.0M"

### 2. Root Cause Analysis

#### A. Provider Mismatches (25% of corrupted entries)
Examples where the enrichment process chose a different provider:
- **CAN 16**: Spectrum (in circuits table) → Frontier Communications (in enriched)
- **CAN 35**: Comcast Workplace → AT&T Broadband II
- **CAS 35**: Spectrum → Frontier Communications

#### B. Missing DSR Data (93.2% of corrupted entries)
- Only 9 corrupted entries have DSR reference data
- 123 corrupted entries have NO DSR data to match against
- When DSR data is missing, the enrichment falls back to complex matching logic

#### C. Provider-Specific Corruption Rates
- **Frontier Communications**: 100% corruption rate (4 out of 4)
- **AT&T**: 100% corruption rate (4 out of 4)
- **AT&T Broadband II**: 72.1% corruption rate (44 out of 61)
- **Comcast**: 62.4% corruption rate (58 out of 93)

### 3. Data Flow Analysis

For each corrupted entry, the pattern is:
1. **Meraki notes have correct format**: "500.0M x 500.0M"
2. **DSR tracking (if exists) has correct format**: "300.0M x 30.0M"
3. **Enrichment process corrupts it to**: "500.0 M" (missing upload speed)

### 4. Example Case Study: CAN 25

- **Circuits Table**: No provider, no speed (NaN)
- **Meraki Notes**: "WAN 1 Comcast 300.0M x 30.0M"
- **ARIN Lookup**: Unknown provider
- **Enriched Result**: Comcast, "300.0 M" ← CORRUPTED

What happened:
1. No DSR data available
2. Enrichment parsed Meraki notes and found "Comcast"
3. Speed got corrupted during the parsing/storage process

## Database Export Details

The complete analysis has been saved to:
- **CSV Export**: `/usr/local/bin/bad_speed_circuits_analysis_20250709_104339.csv`
- Contains all 251 records with full details including:
  - Circuits table provider/speed
  - Enriched table provider/speed
  - DSR provider/speed (when available)
  - Meraki notes preview
  - IP addresses and network names

## Conclusion

The filtered data confirms that speed corruption is happening systematically in the enrichment process. The key issues are:

1. **93.2% of corrupted entries have no DSR data** - the enrichment script falls back to parsing Meraki notes
2. **Provider normalization** - the script changes provider names during enrichment
3. **Speed parsing bug** - when processing speeds, the upload portion gets lost

The corruption is NOT random - it follows specific patterns based on provider matching logic and data availability.