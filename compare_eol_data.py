#!/usr/bin/env python3
"""
Compare EOL data from ANM PowerPoint with our database
Generate a comparison table for boss
"""

import psycopg2
from config import Config
import re
from datetime import datetime
from tabulate import tabulate

def get_db_connection():
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
    user, password, host, port, database = match.groups()
    return psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)

def parse_date(date_str):
    """Parse date string to date object"""
    if not date_str or date_str == '' or date_str == 'None':
        return None
    try:
        # Try different formats
        for fmt in ['%b %d, %Y', '%B %d, %Y', '%Y-%m-%d']:
            try:
                return datetime.strptime(str(date_str), fmt).date()
            except:
                continue
    except:
        pass
    return None

def format_date_meraki(date_obj):
    """Format date in Meraki style: Mar 28, 2025"""
    if not date_obj:
        return ''
    return date_obj.strftime('%b %d, %Y')

# PowerPoint data from slides 4, 5, and 6
ppt_data = {
    # Slide 4
    'MX400': {'qty': 2, 'ann': 'Feb 28, 2018', 'eos': 'May 20, 2018', 'eol': 'May 20, 2025'},
    'MS220-48FP': {'qty': 11, 'ann': 'Mar 16, 2017', 'eos': 'Jul 29, 2017', 'eol': 'Jul 29, 2024'},
    'MS220-8P': {'qty': 4, 'ann': 'Feb 28, 2018', 'eos': 'May 20, 2018', 'eol': 'May 20, 2025'},  # Note: includes 8LP
    'MS220-24P': {'qty': 1, 'ann': 'Mar 16, 2017', 'eos': 'Jul 29, 2017', 'eol': 'Jul 29, 2024'},
    'MR66': {'qty': 8, 'ann': 'Jun 7, 2017', 'eos': 'Jun 9, 2017', 'eol': 'Jun 9, 2024'},
    'MR16': {'qty': 2072, 'ann': 'Feb 27, 2014', 'eos': 'May 31, 2014', 'eol': 'May 31, 2021'},
    'MR18': {'qty': 194, 'ann': 'Dec 8, 2016', 'eos': 'Feb 13, 2017', 'eol': 'Mar 31, 2024'},
    'MR34': {'qty': 21, 'ann': 'Aug 1, 2016', 'eos': 'Oct 31, 2016', 'eol': 'Oct 31, 2023'},
    
    # Slide 5
    'MR20': {'qty': 4, 'ann': 'Dec 19, 2022', 'eos': 'Jun 1, 2023', 'eol': 'Jun 13, 2028'},
    'MR33': {'qty': 1575, 'ann': 'Jan 27, 2021', 'eos': 'Jul 14, 2022', 'eol': 'Jul 21, 2026'},
    'MR36': {'qty': 69, 'ann': '', 'eos': '', 'eol': ''},
    'MR42': {'qty': 51, 'ann': 'Jan 27, 2021', 'eos': 'Jul 14, 2022', 'eol': 'Jul 21, 2026'},
    'MR44': {'qty': 488, 'ann': '', 'eos': '', 'eol': ''},
    'MR86': {'qty': 2495, 'ann': '', 'eos': '', 'eol': ''},
    'MR46': {'qty': 31, 'ann': '', 'eos': '', 'eol': ''},  # Note: includes MR46E
    'MX100': {'qty': 8, 'ann': 'Aug 10, 2021', 'eos': 'Feb 1, 2022', 'eol': 'Feb 1, 2027'},
    'MR52': {'qty': 15, 'ann': 'Jan 27, 2021', 'eos': 'Apr 7, 2022', 'eol': 'Jul 21, 2026'},
    'MS120-48LP': {'qty': 7, 'ann': 'Mar 28, 2024', 'eos': 'Mar 28, 2025', 'eol': 'Mar 28, 2030'},  # Note: includes 48FP
    'MS120-8': {'qty': 7, 'ann': 'Mar 28, 2024', 'eos': 'Mar 28, 2025', 'eol': 'Mar 28, 2030'},  # Note: includes 8LP
    'MS125-24P': {'qty': 3162, 'ann': 'Mar 28, 2024', 'eos': 'Mar 28, 2025', 'eol': 'Mar 28, 2030'},
    'MS225-24': {'qty': 1, 'ann': '', 'eos': '', 'eol': ''},
    'MS225-48': {'qty': 6, 'ann': '', 'eos': '', 'eol': ''},  # Note: includes 48FP
    
    # Slide 6
    'MR74': {'qty': 63, 'ann': 'Jan 27, 2021', 'eos': 'Jul 21, 2021', 'eol': 'Jul 21, 2026'},
    'MS210-48FP': {'qty': 5, 'ann': '', 'eos': '', 'eol': ''},
    'MX450': {'qty': 9, 'ann': '', 'eos': '', 'eol': ''},
    'MS250-48': {'qty': 16, 'ann': 'Aug 28, 2024', 'eos': 'Aug 8, 2025', 'eol': 'Aug 8, 2030'},  # Note: includes 48FP
    'MX105': {'qty': 4, 'ann': '', 'eos': '', 'eol': ''},
    'MX250': {'qty': 1, 'ann': '', 'eos': '', 'eol': ''},
    'MX65': {'qty': 1062, 'ann': 'Nov 20, 2018', 'eos': 'May 28, 2019', 'eol': 'May 28, 2026'},
    'MX67C-NA': {'qty': 2, 'ann': '', 'eos': '', 'eol': ''},
    'MX68': {'qty': 238, 'ann': '', 'eos': '', 'eol': ''},
    'MX75': {'qty': 2, 'ann': '', 'eos': '', 'eol': ''},
    'MX95': {'qty': 2, 'ann': '', 'eos': '', 'eol': ''},
    'VMX-L': {'qty': 6, 'ann': '', 'eos': '', 'eol': ''},
    'Z3': {'qty': 2, 'ann': '', 'eos': '', 'eol': ''},
}

# Get our database data
conn = get_db_connection()
cursor = conn.cursor()

# Get EOL data for these models
cursor.execute("""
    SELECT model, announcement_date, end_of_sale, end_of_support
    FROM meraki_eol_enhanced
    WHERE model IN %s
    ORDER BY model
""", (tuple(ppt_data.keys()),))

db_data = {}
for row in cursor.fetchall():
    model, ann, eos, eol = row
    db_data[model] = {
        'ann': format_date_meraki(ann),
        'eos': format_date_meraki(eos),
        'eol': format_date_meraki(eol)
    }

# Also check variants (e.g., MS220-8P for MS220-8)
cursor.execute("""
    SELECT model, announcement_date, end_of_sale, end_of_support
    FROM meraki_eol_enhanced
    WHERE model LIKE 'MS220-8%' OR model LIKE 'MS120-8%' OR model LIKE 'MS120-48%'
       OR model LIKE 'MS250-48%' OR model LIKE 'MS225-48%' OR model LIKE 'MR46%'
    ORDER BY model
""")

for row in cursor.fetchall():
    model, ann, eos, eol = row
    # Map variants to base models in PPT
    base_model = model
    if model in ['MS220-8P', 'MS220-8LP']:
        base_model = 'MS220-8P'  # PPT groups these
    elif model in ['MS120-8', 'MS120-8LP']:
        base_model = 'MS120-8'  # PPT groups these
    elif model in ['MS120-48LP', 'MS120-48FP']:
        base_model = 'MS120-48LP'  # PPT groups these
    elif model in ['MS250-48', 'MS250-48FP']:
        base_model = 'MS250-48'  # PPT groups these
    elif model in ['MS225-48', 'MS225-48FP']:
        base_model = 'MS225-48'  # PPT groups these
    elif model in ['MR46', 'MR46E']:
        base_model = 'MR46'  # PPT groups these
    
    if base_model not in db_data:
        db_data[base_model] = {
            'ann': format_date_meraki(ann),
            'eos': format_date_meraki(eos),
            'eol': format_date_meraki(eol)
        }

cursor.close()
conn.close()

# Compare and generate table
comparison_table = []
discrepancies = []

for model, ppt_info in sorted(ppt_data.items()):
    db_info = db_data.get(model, {'ann': '', 'eos': '', 'eol': ''})
    
    # Check for discrepancies
    issues = []
    
    # Parse dates for comparison
    ppt_ann = parse_date(ppt_info['ann'])
    ppt_eos = parse_date(ppt_info['eos'])
    ppt_eol = parse_date(ppt_info['eol'])
    
    db_ann = parse_date(db_info['ann'])
    db_eos = parse_date(db_info['eos'])
    db_eol = parse_date(db_info['eol'])
    
    # Compare dates
    if ppt_info['ann'] and db_ann != ppt_ann:
        issues.append('Ann')
    if ppt_info['eos'] and db_eos != ppt_eos:
        issues.append('EOS')
    if ppt_info['eol'] and db_eol != ppt_eol:
        issues.append('EOL')
    
    # If PPT has dates but DB doesn't
    if ppt_info['eos'] and not db_info['eos']:
        issues.append('Missing')
    
    status = '❌ ' + ','.join(issues) if issues else '✅ Match' if ppt_info['eos'] else '➖ No PPT Data'
    
    comparison_table.append([
        model,
        ppt_info['qty'],
        ppt_info['ann'] or '-',
        ppt_info['eos'] or '-',
        ppt_info['eol'] or '-',
        db_info['ann'] or '-',
        db_info['eos'] or '-',
        db_info['eol'] or '-',
        status
    ])
    
    if issues:
        discrepancies.append({
            'model': model,
            'issues': issues,
            'ppt': ppt_info,
            'db': db_info
        })

# Print comparison table
headers = ['Model', 'Qty', 'PPT Ann', 'PPT EOS', 'PPT EOL', 'DB Ann', 'DB EOS', 'DB EOL', 'Status']
print("\n=== EOL Data Comparison: ANM PowerPoint vs Our Database ===\n")
print(tabulate(comparison_table, headers=headers, tablefmt='grid'))

# Summary of discrepancies
print(f"\n=== Summary ===")
print(f"Total models in PowerPoint: {len(ppt_data)}")
print(f"Models with matching data: {len([r for r in comparison_table if '✅' in r[-1]])}")
print(f"Models with discrepancies: {len(discrepancies)}")
print(f"Models with no PPT EOL data: {len([r for r in comparison_table if '➖' in r[-1]])}")

if discrepancies:
    print(f"\n=== Discrepancies Requiring Attention ===")
    for disc in discrepancies:
        print(f"\n{disc['model']} - Issues: {', '.join(disc['issues'])}")
        print(f"  PPT: Ann={disc['ppt']['ann']}, EOS={disc['ppt']['eos']}, EOL={disc['ppt']['eol']}")
        print(f"  DB:  Ann={disc['db']['ann']}, EOS={disc['db']['eos']}, EOL={disc['db']['eol']}")

# Special notes
print("\n=== Notes ===")
print("1. MS220-8P/LP are grouped together in the PowerPoint")
print("2. MS120-8/LP, MS120-48LP/FP are grouped in the PowerPoint")
print("3. MS250-48/FP, MS225-48/FP are grouped in the PowerPoint")
print("4. MR46/MR46E are grouped in the PowerPoint")
print("5. Models with blank EOL dates in PPT are not yet announced for EOL")