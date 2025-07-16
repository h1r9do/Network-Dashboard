# Actionable Circuit Analysis Report

**Generated:** July 13, 2025  
**Total Sites Analyzed:** 1,433  
**Sites with <2 Circuits:** 102

## Executive Summary

Of the 102 sites with only 1 circuit:
- **27 sites** need immediate attention (active stores with single broadband)
- **10 sites** have wireless backup (Cell/Satellite) - lower priority
- **31 sites** are marked "Not Installed" - need status verification  
- **30 sites** are secondary locations (-B suffix) - need business review
- **4 sites** appear to be test/special entries

## IMMEDIATE ACTION REQUIRED (27 Active Stores)

These stores have active broadband service but no redundancy:

### High-Speed Sites (≥300M) - Priority 1
1. **CAL 13N** - Spectrum 300.0M x 20.0M
2. **FLP 26** - CityNet 1000.0M x 1000.0M  
3. **FLP 38** - Blue Stream 300.0M x 300.0M
4. **FLP 47** - Spectrum 300.0M x 20.0M
5. **ILR 17** - Metronet 1000.0M x 1000.0M
6. **INI 06** - AT&T 1000.0M x 1000.0M
7. **MDD 15** - Verizon 300.0M x 300.0M
8. **NJM 02** - Comcast 300.0M x 35.0M
9. **OHC 36** - Charter Communications 300.0M x 10.0M
10. **OHC 44** - Spectrum 600.0M x 35.0M
11. **OHD 28** - Spectrum 600.0M x 35.0M
12. **OHY 13** - Suddenlink 300.0M x 35.0M
13. **PAP 35** - Comcast 300.0M x 35.0M
14. **TND 17** - Comcast 300.0M x 35.0M
15. **TNM 08** - Comcast 300.0M x 35.0M
16. **TXS 55** - AT&T 1000.0M x 1000.0M
17. **TXS 90** - AT&T 1000.0M x 1000.0M

### Medium-Speed Sites (50-299M) - Priority 2
1. **CAL 25** - Cox Business/BOI 50.0M x 10.0M
2. **COL 37** - Comcast 100.0M x 35.0M
3. **CSP 10** - Comcast 50.0M x 10.0M
4. **FLP 06** - Mediacom 200.0M x 15.0M
5. **GAD 02** - Comcast 200.0M x 35.0M
6. **ILP 45** - Suddenlink 300.0M x 35.0M
7. **MII 15** - AT&T 100.0M x 100.0M
8. **MNM 02** - Frontier 200.0M x 10.0M
9. **NCA 25** - AT&T 100.0M x 100.0M
10. **OHC 48** - AT&T 50.0M x 50.0M
11. **SCG 05** - Cox Business/BOI 300.0M x 20.0M
12. **TNA 19** - AT&T 50.0M x 10.0M
13. **TXA 81** - Frontier 100.0M x 100.0M
14. **VAA02** - Cox Business/BOI 100.0M x 10.0M
15. **VAR 13** - Verizon 100.0M x 100.0M

### Low-Speed Sites (<50M) - Priority 3
1. **CAL W01** - Frontier 30.0M x 5.0M
2. **IDD 01** - Allstream 45.0M x 4.0M

## SITES WITH WIRELESS BACKUP (10 Sites) - Lower Priority

These sites already have Cell or Satellite connectivity:
- **AZPB 20** - AT&T Cell
- **AZP_00** - AT&T Cell
- **CAN 08** - Starlink Satellite
- **COC 10** - Verizon Wireless Cell
- **IDH01 -B** - Verizon Wireless Cell
- **MNM 05** - Starlink Satellite
- **NEW 15** - Starlink Satellite
- **TXD 92** - Starlink Satellite
- **UTH 11** - AT&T Cell
- **WAC 29** - Starlink Satellite

## SITES NEEDING VERIFICATION (31 "Not Installed")

These sites show "Not Installed" status and need verification:
COL 23, FLP 05 -B, FLP 27, FLP 39, FLP 42, FLP 43, FLP 45, FLP 46, FLP 49, FLP 50, FLP 51, MNB 09, NJP 15, NYA 17, OHT 20, OKO 13, OKT 05, PAP 32, PAP 37, SCA 17, TND02-B, TNK 13, TNM 18, TNM 19, TXH135, TXH137, TXH141, TXH142, TXS128, TXS136, UTS 18, VAF 12, WIP 08, WIP 09, WVH 08

## RECOMMENDATIONS

### Immediate Actions (This Week)
1. **Add secondary circuits** to the 17 Priority 1 sites (high-speed, active stores)
2. **Contact providers** for quotes on redundant circuits at these locations
3. **Prioritize** stores with 1Gbps primary circuits for fastest redundancy

### Short-term Actions (Next 2 Weeks)  
1. **Complete secondary circuits** for Priority 2 sites (15 medium-speed stores)
2. **Verify status** of 31 "Not Installed" sites - are these future stores?
3. **Review business requirements** for 30 secondary (-B) locations

### Long-term Actions (Next Month)
1. **Evaluate** Priority 3 sites for circuit upgrades along with redundancy
2. **Consider** wired backup for wireless-only sites if transitioning to Vision
3. **Database cleanup** - remove or flag test entries (AMERICA's TIRE, etc.)

## Files Generated
- **Full JSON Report:** `/usr/local/bin/Main/circuit_analysis_report.json`
- **CSV Export:** `/usr/local/bin/Main/sites_needing_circuits.csv`
- **Summary Report:** `/usr/local/bin/Main/circuit_analysis_summary.md`
- **This Report:** `/usr/local/bin/Main/circuit_analysis_actionable_report.md`

## Note on Excel Analysis
The master circuit info Excel file (`master circuit info cleaned.xlsx`) could not be accessed due to file permissions. Once accessible, it should be cross-referenced to identify:
- Available non-DSR circuit options
- Provider alternatives at each location
- Cost information for budgeting
- Speed options for redundancy planning