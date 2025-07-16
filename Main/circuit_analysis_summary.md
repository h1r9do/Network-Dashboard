# Circuit Analysis Report - Sites with Less Than 2 Circuits

**Analysis Date:** July 13, 2025  
**Total Sites in Database:** 1,433  
**Sites with <2 Circuits:** 102 (7.1%)

## Summary

Found 102 sites that currently have only 1 circuit in the database. These sites may need a secondary circuit for redundancy.

## Key Categories of Sites

### 1. Cell/Satellite Only Sites (Non-DSR)
These sites already have wireless connectivity and may not need traditional broadband:
- **AZPB 20** - AT&T Cell (Non-DSR)
- **AZP_00** - AT&T Cell (Non-DSR)  
- **CAN 08** - Starlink Satellite (Non-DSR)
- **COC 10** - Verizon Wireless Cell (Non-DSR)
- **IDH01 -B** - Verizon Wireless Cell (Non-DSR)
- **MNM 05** - Starlink Satellite (Non-DSR)
- **NEW 15** - Starlink Satellite (Non-DSR)
- **TXD 92** - Starlink Satellite (Non-DSR)
- **UTH 11** - AT&T Cell (Non-DSR)
- **WAC 29** - Starlink Satellite (Non-DSR)

### 2. Test/Special Sites
- **AZP 00**, **AZP 00 NEW** - Appear to be test/special locations
- **AMERICA's TIRE**, **AMERICAS TIRE CO** - Generic names, possibly test entries
- Various "-B" suffixed sites (secondary location indicators)

### 3. Regular Store Sites with Single Circuit
These are standard store locations with only one broadband circuit:
- **CAL 13N** - Spectrum 300.0M x 20.0M
- **CAL 25** - Cox Business/BOI 50.0M x 10.0M  
- **CSP 10** - Comcast 50.0M x 10.0M
- **FLP 06** - Mediacom 200.0M x 15.0M
- **GAD 02** - Comcast 200.0M x 35.0M
- **INI 06** - AT&T 1000.0M x 1000.0M
- **NCA 25** - AT&T 100.0M x 100.0M
- **NJM 02** - Comcast 300.0M x 35.0M
- **OHC 48** - AT&T 50.0M x 50.0M
- **SCG 05** - Cox Business/BOI 300.0M x 20.0M
- **TXS 55** - AT&T 1000.0M x 1000.0M
- **VAA02** - Cox Business/BOI 100.0M x 10.0M

### 4. Secondary (-B) Locations
Many sites are marked with "-B" suffix indicating they are secondary locations which may have different circuit requirements:
- CAN 33 -B, CAN 34 -B, CAN 39 -B, etc.
- FLP 10 -B, FLP 17 -B
- GAD 06 -B, IDD 04 -B
- MII 19 -B, NCG 12 -B
- And many others

## Recommendations

1. **Cell/Satellite Sites (10 sites):** These already have wireless backup and may not need additional circuits unless transitioning to Vision.

2. **Test/Special Sites (4 sites):** Verify if these are actual store locations before adding circuits.

3. **Regular Stores (30+ sites):** These are prime candidates for secondary circuit addition for redundancy.

4. **Secondary Locations (50+ sites):** Review business requirements as secondary locations may have different connectivity needs.

## Excel File Access Issue

The master circuit info Excel file exists at `/usr/local/bin/Main/master circuit info cleaned.xlsx` but has restricted permissions (root ownership). To complete the analysis with potential non-DSR circuit information from the Excel file, the file permissions need to be updated or the file needs to be copied to an accessible location.

## Next Steps

1. **Immediate Action:** Add secondary circuits to the 30+ regular store sites that currently have only one broadband circuit.

2. **Review Required:** Examine the 50+ secondary (-B) locations to determine their circuit requirements.

3. **Excel Analysis:** Once file access is resolved, cross-reference with Excel data to identify available non-DSR circuit information including provider, speed, and cost details.

4. **Database Update:** After review and approval, update the circuits table with new circuit entries for sites requiring redundancy.