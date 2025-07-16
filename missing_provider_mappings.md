# Missing Provider Mappings in New Database Script

## Provider Mappings Present in Old Script but Missing in New

The following provider mappings from `nightly_enriched.py` (lines 29-132) are **NOT** present in `nightly_meraki_enriched_db.py`:

### Missing Entries (73 mappings):

1. **"yelcot telephone company"**: "Yelcot Communications"
2. **"yelcot communications"**: "Yelcot Communications"
3. **"ritter communications"**: "Ritter Communications"
4. **"- ritter comm"**: "Ritter Communications"
5. **"conway corporation"**: "Conway Corporation"
6. **"conway extended cable"**: "Conway Corporation"
7. **"dsr conway extended cable"**: "Conway Corporation"
8. **"altice"**: "Optimum"
9. **"altice west"**: "Optimum"
10. **"optimum"**: "Optimum"
11. **"frontier fios"**: "Frontier"
12. **"frontier metrofiber"**: "Frontier"
13. **"allo communications"**: "Allo Communications"
14. **"segra"**: "Segra"
15. **"mountain west technologies"**: "Mountain West Technologies"
16. **"c spire"**: "C Spire"
17. **"brightspeed"**: "Brightspeed"
18. **"century link"**: "CenturyLink"
19. **"clink fiber"**: "CenturyLink"
20. **"eb2-frontier fiber"**: "Frontier"
21. **"one ring networks"**: "One Ring Networks"
22. **"gtt ethernet"**: "GTT"
23. **"vexus"**: "Vexus"
24. **"sparklight"**: "Sparklight"
25. **"vista broadband"**: "Vista Broadband"
26. **"metronet"**: "Metronet"
27. **"rise broadband"**: "Rise Broadband"
28. **"lumos networks"**: "Lumos Networks"
29. **"point broadband"**: "Point Broadband"
30. **"gvtc communications"**: "GVTC Communications"
31. **"harris broadband"**: "Harris Broadband"
32. **"unite private networks"**: "Unite Private Networks"
33. **"pocketinet communications"**: "Pocketinet Communications"
34. **"eb2-ziply fiber"**: "Ziply Fiber"
35. **"astound"**: "Astound"
36. **"consolidated communications"**: "Consolidated Communications"
37. **"etheric networks"**: "Etheric Networks"
38. **"saddleback communications"**: "Saddleback Communications"
39. **"orbitel communications"**: "Orbitel Communications"
40. **"eb2-cableone cable"**: "Cable One"
41. **"cable one"**: "Cable One"
42. **"cableone"**: "Cable One"
43. **"transworld"**: "TransWorld"
44. **"mediacom/boi"**: "Mediacom"
45. **"mediacom"**: "Mediacom"
46. **"login"**: "Login"
47. **"livcom"**: "Livcom"
48. **"tds cable"**: "TDS Cable"
49. **"first digital"**: "Digi"
50. **"spanish fork community network"**: "Spanish Fork Community Network"
51. **"centracom"**: "Centracom"
52. **"eb2-lumen dsl"**: "Lumen"
53. **"lumen dsl"**: "Lumen"
54. **"eb2-centurylink dsl"**: "CenturyLink"
55. **"centurylink/qwest"**: "CenturyLink"
56. **"centurylink fiber plus"**: "CenturyLink"
57. **"lightpath"**: "Lightpath"
58. **"localtel"**: "LocalTel"
59. **"infowest inc"**: "Infowest"
60. **"eb2-windstream fiber"**: "Windstream"
61. **"gtt/esa2 adsl"**: "GTT"
62. **"zerooutages"**: "ZeroOutages"
63. **"fuse internet access"**: "Fuse Internet Access"
64. **"windstream communications llc"**: "Windstream"
65. **"frontier communications"**: "Frontier"
66. **"glenwood springs community broadband network"**: "Glenwood Springs Community Broadband Network"
67. **"unknown"**: ""
68. **"uniti fiber"**: "Uniti Fiber"
69. **"wideopenwest"**: "WideOpenWest"
70. **"wide open west"**: "WideOpenWest"
71. **"level 3"**: "Lumen"
72. **"plateau telecommunications"**: "Plateau Telecommunications"
73. **"d & p communications"**: "D&P Communications"
74. **"vzg"**: "VZW Cell"

## Provider Keywords Comparison

### Old Script PROVIDER_KEYWORDS (meraki_mx.py lines 71-101)
Has 30 entries including special mappings for:
- 'yelcot': 'yelcot telephone company'
- 'ritter': 'ritter communications'
- 'conway': 'conway corporation'
- 'altice': 'optimum'
- 'brightspeed': 'level 3'
- 'clink': 'centurylink'
- 'lumen': 'centurylink'
- 'c spire': 'c spire fiber'
- 'orbitelcomm': 'orbitel communications, llc'
- 'sparklight': 'cable one, inc.'
- 'lightpath': 'optimum'
- 'vzg': 'verizon business'
- 'digi': 'verizon business'
- 'mediacom': 'mediacom communications corporation'
- 'cable one': 'cable one, inc.'
- 'qwest': 'centurylink'
- 'cox business': 'cox communications'
- 'consolidatedcomm': 'consolidated communications, inc.'
- 'consolidated': 'consolidated communications, inc.'

### New Script PROVIDER_KEYWORDS (lines 124-135)
Only has 10 basic entries - missing 20 keyword mappings

## Impact Analysis

1. **Data Quality**: Without these mappings, many providers will not be normalized correctly
2. **Matching Accuracy**: Fuzzy matching will fail for these providers
3. **Cost Attribution**: Circuits may not match correctly between Meraki and DSR data
4. **Reporting**: Provider reports will show inconsistent naming

## Recommendation

All 73 missing provider mappings and 20 missing keyword mappings should be added to the new database script to ensure data continuity and quality.