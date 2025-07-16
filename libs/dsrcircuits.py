#!/usr/bin/env python3

from flask import Flask, render_template, send_from_directory
import csv
import os
import glob

# Initialize Flask app
app = Flask(
    __name__,
    template_folder='/usr/local/bin/templates',
    static_folder='/usr/local/bin/static'
)

# Configuration
INVENTORY_DIR = "/var/www/html/meraki-data"

def clean_csv(file_path):
    with open(file_path, 'rb') as file:
        data = file.read()
    cleaned_data = data.decode('utf-8', errors='replace')
    cleaned_file_path = file_path + '.cleaned'
    with open(cleaned_file_path, 'w', encoding='utf-8') as file:
        file.write(cleaned_data)
    return cleaned_file_path

@app.route('/circuitinfo/<filename>')
def serve_csv(filename):
    csv_dir = '/var/www/html/circuitinfo/'
    return send_from_directory(csv_dir, filename)

@app.route('/dsrcircuits')
def dsrcircuits():
    csv_dir = '/var/www/html/circuitinfo/'
    csv_files = glob.glob(os.path.join(csv_dir, 'tracking_data_*.csv'))
    if not csv_files:
        print("No CSV files found")
        return render_template('dsrcircuits.html', error="No CSV files found.")
    csv_file_path = max(csv_files, key=os.path.getmtime)
    cleaned_file_path = clean_csv(csv_file_path)
    data = []
    try:
        with open(cleaned_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            data = list(reader)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return render_template('dsrcircuits.html', error="Failed to load data from CSV.")
    enabled_data = [row for row in data if row.get('status', '').lower() == 'enabled']
    grouped_data = {}
    for row in enabled_data:
        site_name = row.get('Site Name', '').strip()
        if not site_name:
            continue
        if site_name not in grouped_data:
            grouped_data[site_name] = []
        grouped_data[site_name].append(row)
    return render_template('dsrcircuits.html', grouped_data=grouped_data)

if __name__ == '__main__':
    app.run(host='localhost', port=5052, debug=True)
