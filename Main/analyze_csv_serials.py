#!/usr/bin/env python3
import csv
from collections import Counter

with open('inventory_ultimate_final.csv', 'r') as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    
    rows = list(reader)
    total = len(rows)
    
    # Count serials
    serials = []
    empty_serials = 0
    for row in rows:
        if len(row) > 5:
            serial = row[5]
            if serial and serial != '""""""':
                serials.append(serial)
            else:
                empty_serials += 1
    
    unique_serials = set(serials)
    
    print(f'Total rows: {total}')
    print(f'Rows with serial numbers: {len(serials)}')
    print(f'Rows with empty serials: {empty_serials}')
    print(f'Unique serial numbers: {len(unique_serials)}')
    
    # Check for duplicates
    serial_counts = Counter(serials)
    duplicates = {s: c for s, c in serial_counts.items() if c > 1}
    print(f'Duplicate serials in CSV: {len(duplicates)}')
    
    if duplicates:
        print('\nTop duplicates in CSV:')
        for serial, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f'  {serial}: appears {count} times')