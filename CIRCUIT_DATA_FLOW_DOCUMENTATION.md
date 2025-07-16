# Circuit Data Flow Documentation

## Overview
This document explains the proper data flow for circuit information in the DSR Circuits system, specifically regarding the separation of DSR data (including costs) and Meraki enrichment data.

## Key Principle
**Cost data should ONLY come from DSR and should NEVER be modified by the Meraki edit modal.**

## Data Sources and Tables

### 1. DSR Data (`circuits` table)
- **Source**: DSR Global Portal CSV files via `nightly_dsr_pull_db_with_override.py`
- **Key Fields**:
  - `site_name`: Store identifier
  - `circuit_purpose`: Primary/Secondary
  - `provider_name`: ISP provider from DSR
  - `details_ordered_service_speed`: Circuit speed from DSR
  - `billing_monthly_cost`: **COST DATA - ONLY SOURCE OF TRUTH**
  - `status`: Circuit status (Enabled, etc.)
- **Update Frequency**: Nightly at 00:00

### 2. Meraki Enrichment (`enriched_circuits` table)
- **Source**: Meraki device notes and API data
- **Purpose**: Store Meraki-specific enrichment data
- **Key Fields**:
  - `network_name`: Meraki network name (matches site_name)
  - `wan1_provider`: Provider from Meraki notes or manual entry
  - `wan1_speed`: Speed from Meraki notes or manual entry
  - `wan2_provider`: Provider from Meraki notes or manual entry
  - `wan2_speed`: Speed from Meraki notes or manual entry
  - `wan1_confirmed`: Whether WAN1 data has been confirmed
  - `wan2_confirmed`: Whether WAN2 data has been confirmed
- **Should NOT contain**: Cost fields (wan1_monthly_cost, wan2_monthly_cost)

### 3. Meraki Inventory (`meraki_inventory` table)
- **Source**: Meraki Dashboard API
- **Purpose**: Store raw device information from Meraki
- **Key Fields**:
  - `device_notes`: Raw notes from Meraki device
  - `wan1_provider_label`: Parsed provider from notes
  - `wan1_speed_label`: Parsed speed from notes
  - IP addresses and ARIN data

## Proper Data Flow

### 1. Display Flow (dsrcircuits.html)
```
User loads page → dsrcircuits.py queries:
  - enriched_circuits for Meraki data (provider, speed)
  - circuits table for DSR data (COSTS)
  → Combines data for display
```

### 2. Edit Modal Flow
```
User clicks Edit → confirm_site() retrieves:
  - Meraki notes (current device notes)
  - DSR data (including costs for display only)
  - ARIN data
  → User modifies ONLY provider/speed
  → submit_confirmation() updates ONLY:
    - enriched_circuits.wan1_provider
    - enriched_circuits.wan1_speed
    - enriched_circuits.wan2_provider
    - enriched_circuits.wan2_speed
    - Push to Meraki device notes
  → NEVER touches cost fields
```

### 3. Nightly Update Flow
```
DSR Pull (00:00) → Updates circuits table with latest DSR data including costs
Meraki Pull (01:00) → Updates meraki_inventory with device data
Enrichment (03:00) → Updates enriched_circuits with Meraki data ONLY
```

## Current Issues to Fix

1. **enriched_circuits table has cost fields** - These should be removed as they duplicate DSR data
2. **Edit modal updates cost fields** - Fixed in dsrcircuits.py to not update costs
3. **Main page pulls costs from enriched_circuits** - Fixed to pull from circuits table
4. **Nightly enrichment updates costs** - Should be modified to not touch cost fields

## Recommended Architecture Changes

1. **Remove cost fields from enriched_circuits table**:
   ```sql
   ALTER TABLE enriched_circuits 
   DROP COLUMN wan1_monthly_cost,
   DROP COLUMN wan2_monthly_cost;
   ```

2. **Update nightly_meraki_enriched_db.py** to not process cost data

3. **Ensure all cost displays come from circuits table**

## Summary
- **DSR owns**: Site names, circuit purposes, providers, speeds, **COSTS**, status
- **Meraki owns**: Device notes, enriched provider/speed info for display
- **Edit modal**: Only updates Meraki notes (provider/speed), never costs
- **Display**: Combines DSR data (including costs) with Meraki enrichment

Last Updated: 2025-07-01