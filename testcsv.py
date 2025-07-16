import csv
with open('/var/www/html/circuitinfo/tracking_data_2025-04-28.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    print("Headers:", reader.fieldnames)
    for i, row in enumerate(reader):
        if i < 3:  # Print first 3 rows
            print(row)
        if i > 10:  # Don't print everything
            break
