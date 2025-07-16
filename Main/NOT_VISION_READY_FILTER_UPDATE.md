# Not Vision Ready Filter Update - July 14, 2025

## Overview
Updated the "Not Vision Ready" filter on the dsrcircuits page to capture sites that are not ready for Vision technology implementation.

## Filter Criteria
The filter now identifies sites matching these criteria:

### Scenario 1: Both Circuits Cellular
- Sites where BOTH WAN1 and WAN2 have cellular service
- Includes sites where:
  - Speed field shows "Cell"
  - Provider name contains AT&T, Verizon, VZW, Cell, Cellular, or Wireless

### Scenario 2: Low Speed + Cellular
- Sites with speeds under 100.0M x 10.0M on one circuit AND cellular service on the other
- Low speed defined as:
  - Download speed < 100.0 Mbps OR
  - Upload speed ≤ 10.0 Mbps
- Cellular detection same as Scenario 1

### Additional Filters
- Only includes Discount-Tire tagged stores
- Excludes satellite services
- Excludes hub/lab/voice/test sites
- Excludes sites without IP addresses

## Files Updated

### 1. `/usr/local/bin/Main/templates/dsrcircuits.html`
- Updated JavaScript filter logic in the DataTables custom search function
- Added `isCellularProvider()` function to check provider names for cellular indicators
- Modified filter to check both scenarios (both cellular OR low speed + cellular)

### 2. `/usr/local/bin/Main/sql/not_vision_ready_query.sql`
- Updated SQL query to match new filter criteria
- Added comprehensive WHERE clause to handle both scenarios
- Enhanced result columns to show reason for being "not vision ready"

## Test Results
Running the filter on production data shows:
- **Both cellular**: Sites where both circuits are cellular (e.g., CAL 07, CAL 12, CAN 02)
- **Low speed + cellular**: Sites with low speed on one circuit and cellular on the other (e.g., AZP 44, AZP 49, CAN 12)

## Example Sites

### Both Cellular Examples:
- **CAL 07**: AT&T Broadband II (300M) + VZW Cell
- **CAN 02**: AT&T Broadband II (1000M) + AT&T Cell
- **AZN 04**: AT&T (20M) + AT&T (20M)

### Low Speed + Cellular Examples:
- **AZP 44**: CenturyLink (100M x 10M) + AT&T Cell
- **AZP 56**: Comcast (10M x 10M) + AT&T Cell
- **COD 06**: Lumen (100M x 10M) + AT&T Cell

## Usage
1. Navigate to the DSR Circuits page
2. Click the "📡 Not Vision Ready" button to filter
3. Only sites matching the above criteria will be displayed
4. Click "Show All" to remove the filter

## Technical Notes
- Filter is applied client-side using DataTables custom search
- Cellular detection is case-insensitive
- Speed parsing handles various formats (e.g., "100.0M x 10.0M")
- Provider text is extracted from HTML if needed