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

# Analyze patterns
print("=== ANALYSIS OF 127 NO-MATCH CASES ===\n")

# 1. DSR Provider Distribution
dsr_providers = defaultdict(int)
for nm in no_matches:
    dsr_providers[nm['dsr_provider']] += 1

print("1. DSR PROVIDER DISTRIBUTION:")
for provider, count in sorted(dsr_providers.items(), key=lambda x: x[1], reverse=True):
    print(f"   {provider}: {count} cases")

# 2. Cases with ARIN/Notes data but still no match
has_arin_or_notes = []
for nm in no_matches:
    if nm['arin_provider'] or nm['notes_provider']:
        has_arin_or_notes.append(nm)

print(f"\n2. CASES WITH ARIN/NOTES DATA: {len(has_arin_or_notes)} out of 127")

# Group by pattern
patterns = defaultdict(list)
for nm in has_arin_or_notes:
    key = f"DSR: {nm['dsr_provider']}  < /dev/null |  ARIN: {nm['arin_provider']} | Notes: {nm['notes_provider']}"
    patterns[key].append(nm)

print("\n   Pattern Analysis:")
for pattern, cases in sorted(patterns.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"   - {pattern}: {len(cases)} cases")

# 3. Primary vs Secondary distribution
primary = sum(1 for nm in no_matches if nm['purpose'] == 'Primary')
secondary = sum(1 for nm in no_matches if nm['purpose'] == 'Secondary')
print(f"\n3. CIRCUIT PURPOSE DISTRIBUTION:")
print(f"   Primary: {primary}")
print(f"   Secondary: {secondary}")

# 4. Special cases analysis
print("\n4. SPECIAL CASES:")

# Comcast variants
comcast_variants = [nm for nm in no_matches if 'Comcast' in nm['dsr_provider']]
print(f"\n   Comcast Variants ({len(comcast_variants)} total):")
comcast_types = defaultdict(int)
for cv in comcast_variants:
    comcast_types[cv['dsr_provider']] += 1
for ct, count in sorted(comcast_types.items()):
    print(f"   - {ct}: {count}")

# AT&T variants
att_variants = [nm for nm in no_matches if 'AT&T' in nm['dsr_provider']]
print(f"\n   AT&T Variants ({len(att_variants)} total):")
att_types = defaultdict(int)
for av in att_variants:
    att_types[av['dsr_provider']] += 1
for at, count in sorted(att_types.items()):
    print(f"   - {at}: {count}")

# 5. Problematic patterns
print("\n5. KEY PROBLEMATIC PATTERNS:")
print("\n   a) Comcast with AT&T in ARIN/Notes:")
comcast_att = [nm for nm in no_matches if nm['dsr_provider'] == 'Comcast' and 'AT&T' in nm['arin_provider']]
print(f"      - {len(comcast_att)} cases where DSR shows Comcast but ARIN shows AT&T")

print("\n   b) Missing ARIN/Notes data entirely:")
no_data = [nm for nm in no_matches if not nm['arin_provider'] and not nm['notes_provider']]
print(f"      - {len(no_data)} cases with no ARIN or Notes data")

print("\n   c) Provider variants needing mapping:")
print("      - 'Comcast Workplace' (26 cases) - needs mapping")
print("      - 'Cox Business/BOI' (7 cases) - needs mapping")
print("      - 'VZW Cell' (6 cases) - cellular provider")
print("      - Provider names with quotes/special chars")

# 6. Recommendations
print("\n6. RECOMMENDATIONS FOR RESOLUTION:")
print("   1. Add mappings for 'Comcast Workplace' → 'Comcast'")
print("   2. Add mappings for 'Cox Business/BOI' → 'Cox Communications'")
print("   3. Handle cases where DSR=Comcast but ARIN=AT&T (likely incorrect ARIN data)")
print("   4. Clean provider names (remove quotes, normalize LLC/Inc variations)")
print("   5. Consider cellular providers (VZW Cell) as special case")
print("   6. Add mappings for smaller providers (Brightspeed, Ziply, etc.)")
