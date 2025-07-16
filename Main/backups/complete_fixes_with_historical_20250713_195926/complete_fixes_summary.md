# Complete DSR Circuits Fixes - July 13, 2025 19:43 MST

## Overview
This backup contains all fixes implemented during this session, including filter buttons, Not Vision Ready filter, and ARIN refresh functionality.

## 1. Filter Button Fixes

### Discount-Tire Filter
- **Issue**: Page already filters for Discount-Tire by default, button logic was backwards
- **Solution**: Changed to use URL parameter `?filter=all` for server-side filtering
- **Behavior**: 
  - Default: Shows ~1200 Discount-Tire tagged networks
  - Clicked: Reloads page with all 1300+ networks

### Not Vision Ready Filter
- **Issue**: Wasn't properly detecting wireless/satellite only sites
- **Solution**: Checks speed columns for "Cell", "Satellite", or "N/A"
- **Shows**: Sites where BOTH connections are wireless/satellite (no broadband)

### 1 Circuit Filter
- **Function**: Shows sites with only one active circuit (WAN1 or WAN2 is N/A)

### Export Buttons
- **Excel Export**: Downloads filtered data as CSV
- **PDF Export**: Triggers browser print dialog

## 2. ARIN Refresh Fixes

### Real-time DDNS/Public IP Query
- Queries Meraki API uplink statuses in real-time
- Prefers `publicIp` field over interface IPs
- Falls back to DDNS hostname resolution if no publicIp
- Filters out private/loopback/link-local IPs

### Enhanced RDAP Parsing
- **Recursive Entity Collection**: Searches all nested entities
- **Organization Filter**: Only considers entities with `kind: org`
- **Role Prioritization**: registrant > ISP > others
- **Company Normalization**:
  - CCCS → Comcast Cable Communications, LLC
  - MCICS → Verizon Business
  - OREGON-19 → Comcast Cable Communications, LLC
  - AT&T variations → AT&T
  - Charter variations → Charter Communications

### Special IP Handling
- 166.80.x.x → "Verizon Business" (hardcoded)
- Private IPs → "Private IP"
- Invalid/0.0.0.0 → "Unknown"

## 3. JavaScript/UI Updates

### DataTable Initialization
- Proper column mapping (WAN1 Speed = col 2, WAN2 Speed = col 5)
- Row count updates dynamically
- Filter state management

### Modal Response Handling
- Changed from `wan1_arin_provider` to `wan1_provider`
- Changed from `wan2_arin_provider` to `wan2_provider`
- Displays IP addresses and provider names

## Files Modified

1. **dsrcircuits_blueprint.py**
   - Complete rewrite of `refresh_arin_data()` function
   - Real-time Meraki API queries
   - Enhanced RDAP parsing with organization entity collection
   - Company name normalization

2. **dsrcircuits.html** (Main and Flask templates)
   - Fixed Discount-Tire filter to use URL parameter
   - Fixed Not Vision Ready filter to check speed columns
   - Added export functionality
   - Fixed JavaScript response field names
   - Removed duplicate filter code

## Testing Results

### Filter Testing
- ✅ Discount-Tire filter toggles between filtered/all networks
- ✅ Not Vision Ready shows Cell/Satellite only sites
- ✅ 1 Circuit filter shows sites with single connection
- ✅ Export buttons functional

### ARIN Refresh Testing
- ✅ 71.236.222.207 → Comcast Cable Communications, LLC (was OREGON-19)
- ✅ 166.253.100.68 → Verizon Business (was MCICS)
- ✅ Real-time IP lookups working
- ✅ DDNS resolution fallback working

## Known Limitations

1. **No Persistent RDAP Cache**: Uses in-memory cache only for the request duration
2. **Server-side Filtering**: Discount-Tire filter requires page reload
3. **Modal Load Time**: May take a moment when opening sites with complex data

## Backup Contents

- `dsrcircuits_blueprint.py` - Flask blueprint with all API endpoints
- `dsrcircuits.html` - Main template with all UI fixes
- `dsrcircuits_flask_template.html` - Flask template directory copy
- `dsrcircuits.py` - Main application file

## Previous Backups Referenced

1. `/usr/local/bin/Main/backups/arin_refresh_working_20250713_112339/` - Working ARIN implementation
2. `/usr/local/bin/Main/backups/filter_buttons_working_20250713_160719/` - Working filter buttons
3. `/usr/local/bin/Main/backups/broken_state_20250713_155743/` - Modal functionality source
4. `/usr/local/bin/Main/backups/arin_refresh_fix_20250713_192830/` - ARIN fix attempt

---
All functionality tested and working as of 19:43 MST on July 13, 2025.# Historical Data Fix - Added Sun Jul 13 19:59:39 MST 2025

## DSR Historical Fix
- **Issue**: Circuit history table was empty, foreign key constraint preventing inserts
- **Root Cause**: nightly_circuit_history.py was looking up circuits by site_name only
- **Solution**: Modified to match on both site_name AND site_id for exact circuit match
- **Result**: Successfully populated 60 historical records from July 7-11
- **Files Modified**: nightly_circuit_history.py
- **Helper Script**: populate_historical_data.py (for manual population)
