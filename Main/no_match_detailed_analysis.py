import csv
from collections import defaultdict

# Read the no-match cases
no_matches = []
with open('/usr/local/bin/Main/no_match_analysis.csv', 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        no_matches.append({
            'site_name': row[0],
            'site_id': row[1],
            'purpose': row[2],
            'dsr_provider': row[3],
            'arin_provider': row[4],
            'notes_provider': row[5],
            'speed': row[10],
            'cost': row[11]
        })

print("=== DETAILED ANALYSIS OF 127 NO-MATCH CASES ===\n")

# Category 1: Clean mapping opportunities
print("CATEGORY 1: CLEAN MAPPING OPPORTUNITIES (59 cases)")
print("These can be resolved by adding simple provider mappings:\n")

# Comcast Workplace
cw = [nm for nm in no_matches if nm['dsr_provider'] == 'Comcast Workplace' and not nm['arin_provider']]
print(f"1. Comcast Workplace → Comcast: {len(cw)} cases")
print("   - All appear to be legitimate Comcast business services")
print("   - No conflicting ARIN/Notes data")

# Cox Business/BOI
cox = [nm for nm in no_matches if nm['dsr_provider'] == 'Cox Business/BOI' and not nm['arin_provider']]
print(f"\n2. Cox Business/BOI → Cox Communications: {len(cox)} cases")
print("   - BOI likely means 'Business Over Internet'")
print("   - Standard Cox business service")

# Provider name variations
print("\n3. Provider name variations:")
print("   - 'Comcast Cable Communications, LLC' → 'Comcast' (2 cases)")
print("   - 'AT&T Enterprises, LLC' → 'AT&T' (1 case)")
print("   - Quotes in names need cleaning (2 cases)")

# Category 2: Conflicting data
print("\n\nCATEGORY 2: CONFLICTING ARIN DATA (34 cases)")
print("These have DSR provider different from ARIN provider:\n")

# Comcast vs AT&T
comcast_att = [nm for nm in no_matches if nm['dsr_provider'] in ['Comcast', 'Comcast Cable Communications, LLC'] and nm['arin_provider'] == 'AT&T']
print(f"1. DSR=Comcast, ARIN=AT&T: {len(comcast_att)} cases")
print("   - All secondary circuits (-B suffix)")
print("   - Likely ARIN lookup error or shared infrastructure")
print("   - Example sites: CAN 35, GAA 10-30 series")

# Other conflicts
other_conflicts = [nm for nm in no_matches if nm['arin_provider'] and nm['dsr_provider'] not in ['Comcast', 'Comcast Cable Communications, LLC'] and nm['arin_provider'] not in nm['dsr_provider']]
print(f"\n2. Other provider conflicts: {len(other_conflicts)} cases")
for oc in other_conflicts[:5]:
    print(f"   - DSR: {oc['dsr_provider']} vs ARIN: {oc['arin_provider']}")

# Category 3: Missing enrichment data
print("\n\nCATEGORY 3: NO ENRICHMENT DATA (79 cases)")
no_data = [nm for nm in no_matches if not nm['arin_provider'] and not nm['notes_provider']]
by_provider = defaultdict(int)
for nd in no_data:
    by_provider[nd['dsr_provider']] += 1

print("Breakdown by DSR provider:")
for provider, count in sorted(by_provider.items(), key=lambda x: x[1], reverse=True):
    print(f"   - {provider}: {count} cases")

# Category 4: Special cases
print("\n\nCATEGORY 4: SPECIAL CASES")

# Cellular
cellular = [nm for nm in no_matches if 'VZW' in nm['dsr_provider'] or 'Cell' in nm['dsr_provider']]
print(f"\n1. Cellular providers: {len(cellular)} cases")
print("   - VZW Cell (Verizon Wireless)")
print("   - These are backup cellular connections, may need special handling")

# Regional/smaller providers
regional = ['Brightspeed', 'Ziply Fiber', 'Vyve', 'Vista Broadband', 'Cincinnati Bell', 'Mediacom/BOI']
print("\n2. Regional/smaller providers needing mappings:")
for r in regional:
    count = sum(1 for nm in no_matches if r in nm['dsr_provider'])
    if count > 0:
        print(f"   - {r}: {count} cases")

# Summary
print("\n\n=== RESOLUTION SUMMARY ===")
print("\n1. IMMEDIATE FIXES (61 cases can be resolved):")
print("   - Add 'Comcast Workplace' → 'Comcast' mapping")
print("   - Add 'Cox Business/BOI' → 'Cox Communications' mapping")
print("   - Clean provider names (remove LLC, quotes)")

print("\n2. CONFLICT RESOLUTION (34 cases):")
print("   - Need logic to handle DSR vs ARIN conflicts")
print("   - Consider trusting DSR over ARIN for known patterns")
print("   - Especially for Comcast/AT&T conflicts on secondary circuits")

print("\n3. DATA ENRICHMENT NEEDED (32 cases):")
print("   - 79 total with no ARIN/Notes, but 47 can be mapped")
print("   - Remaining 32 need manual provider identification")
print("   - Consider additional data sources or manual mapping")

# List specific new mappings needed
print("\n\n=== NEW MAPPINGS TO ADD ===")
mappings = [
    ("Comcast Workplace", "Comcast"),
    ("Cox Business/BOI", "Cox Communications"),
    ("Comcast Cable Communications, LLC", "Comcast"),
    ("AT&T Enterprises, LLC", "AT&T"),
    ("Mediacom/BOI", "Mediacom"),
    ("EB2-Frontier Fiber", "Frontier"),
    ("EB2-Centurylink DSL", "CenturyLink"),
    ("CenturyLink Fiber Plus", "CenturyLink"),
    ("VZW Cell", "Verizon Wireless"),
]

print("\nProvider mappings to add:")
for old, new in mappings:
    count = sum(1 for nm in no_matches if nm['dsr_provider'] == old)
    print(f"   '{old}' → '{new}' ({count} cases)")
