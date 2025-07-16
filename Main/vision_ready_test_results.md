# "Not Vision Ready" Filter Test Results

## Test Date: July 14, 2025

## Summary
- **Total Discount-Tire circuits tested**: 28
- **Sites found by "Not Vision Ready" filter**: 0
- **Expected result**: This appears to be correct based on the data

## Filter Criteria Applied
1. **BOTH circuits are cellular (cell/cell)**, OR
2. **One circuit has low speed (under 100M x 10M) AND the other is cellular**
3. **Exclude satellite services**
4. **Only for Discount-Tire tagged stores**

## Detailed Analysis

### Sites with Cellular Connections
The following sites have at least one cellular connection:

1. **ALB 03**: 600M x 35M (Spectrum) + Cell (VZW Cell)
   - Does NOT qualify: 35M upload > 10M threshold

2. **FLO 13**: 600M x 35M (Spectrum) + Cell (VZW Cell)
   - Does NOT qualify: 35M upload > 10M threshold

3. **MOS 07**: 1000M x 200M (AT&T Broadband II) + Cell (VZW Cell)
   - Does NOT qualify: Neither circuit is low speed

4. **NCC 48**: 300M x 300M (Brightspeed) + Cell (VZW Cell)
   - Does NOT qualify: Neither circuit is low speed

5. **TXA 24**: 750M x 35M (Charter Communications) + Cell (AT&T)
   - Does NOT qualify: 35M upload > 10M threshold

6. **TXG 02**: 300M x 300M (Consolidated Communications) + Cell (VZW Cell)
   - Does NOT qualify: Neither circuit is low speed

7. **WAS 29**: 600M x 35M (Comcast Workplace) + Cell (VZW Cell)
   - Does NOT qualify: 35M upload > 10M threshold

### Key Finding
**No sites meet the "Not Vision Ready" criteria** because:
- No sites have both circuits as cellular (cell/cell)
- Sites with cellular connections have their other circuit with upload speeds ≥ 30M, which exceeds the 10M threshold for "low speed"

## Cellular Provider Detection Fix
Fixed issue where "AT&T Broadband II" was incorrectly detected as cellular:
- **Before**: Any provider containing "AT&T" was considered cellular
- **After**: Only providers explicitly containing "Cell" along with "AT&T" or "Verizon" are considered cellular
- **Examples of corrected classifications**:
  - "AT&T Broadband II" → NOT cellular (correct)
  - "VZW Cell" → cellular (correct)
  - "AT&T Cell" → cellular (would be correct if found)

## Specific Sites Searched
The following specific sites were not found in Discount-Tire circuits:
- CAL 07
- AZP 56  
- WAS 23
- CAN 12
- AZP 49

## Recommendations
1. **Verify filter criteria**: The current criteria may be too strict
2. **Check data source**: Confirm if the web interface uses different data or criteria
3. **Consider adjusting thresholds**: The 10M upload threshold for "low speed" may need adjustment
4. **Validate against actual web filter**: Test the web interface directly to compare results

## Data Source
- **Table**: enriched_circuits
- **Tag Filter**: 'Discount-Tire' = ANY(device_tags)
- **Total Records**: 28 circuits
- **Connection**: Direct PostgreSQL database query