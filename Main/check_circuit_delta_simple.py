#!/usr/bin/env python3
"""Check the delta between CSV enabled circuits and database circuits"""

import csv
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, Circuit, EnrichedCircuit, MerakiInventory
from config import config
from sqlalchemy import func, text

# Create Flask app context
app = Flask(__name__)
app.config.from_object(config['production'])
db.init_app(app)

with app.app_context():
    # Read CSV file and count enabled circuits
    csv_count = 0
    csv_sites = set()
    with open('/var/www/html/circuitinfo/tracking_data_2025-07-11.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['status'] == 'Enabled':
                csv_count += 1
                csv_sites.add(row['Site Name'].strip())
    
    print(f"CSV Analysis:")
    print(f"- Total enabled circuits in CSV: {csv_count}")
    print(f"- Unique sites with enabled circuits: {len(csv_sites)}")
    
    # Database counts
    db_enabled_count = Circuit.query.filter_by(status='Enabled').count()
    print(f"\nDatabase Analysis:")
    print(f"- Total enabled circuits in database: {db_enabled_count}")
    
    # What the test page shows (with Discount-Tire tag filter)
    test_page_query = db.session.query(EnrichedCircuit).join(
        MerakiInventory,
        EnrichedCircuit.network_name == MerakiInventory.network_name
    ).filter(
        text("meraki_inventory.device_tags @> ARRAY['Discount-Tire']"),
        ~(
            EnrichedCircuit.network_name.ilike('%hub%') |
            EnrichedCircuit.network_name.ilike('%lab%') |
            EnrichedCircuit.network_name.ilike('%voice%') |
            EnrichedCircuit.network_name.ilike('%test%')
        ),
        ((MerakiInventory.wan1_ip.is_(None)) | (MerakiInventory.wan1_ip == '') | (MerakiInventory.wan1_ip == 'None')) &
        ((MerakiInventory.wan2_ip.is_(None)) | (MerakiInventory.wan2_ip == '') | (MerakiInventory.wan2_ip == 'None'))
    )
    
    test_page_sites = test_page_query.all()
    test_page_count = 0
    
    for circuit in test_page_sites:
        # Count enabled circuits for each site
        site_enabled = Circuit.query.filter(
            func.lower(Circuit.site_name) == func.lower(circuit.network_name),
            Circuit.status == 'Enabled'
        ).count()
        test_page_count += site_enabled
    
    print(f"\nTest Page Analysis:")
    print(f"- Sites shown on test page: {len(test_page_sites)}")
    print(f"- Total enabled circuits on test page: {test_page_count}")
    
    # The delta
    print(f"\nDelta Summary:")
    print(f"- CSV shows: {csv_count} enabled circuits")
    print(f"- Test page shows: {test_page_count} enabled circuits")
    print(f"- Difference: {csv_count - test_page_count} circuits")
    
    # Find sites missing from test page
    test_page_site_names = {circuit.network_name.lower() for circuit in test_page_sites}
    missing_from_test = []
    
    for site in csv_sites:
        if site.lower() not in test_page_site_names:
            missing_from_test.append(site)
    
    print(f"\nSites in CSV but not on test page: {len(missing_from_test)}")
    if missing_from_test:
        print("Examples (first 10):")
        for site in sorted(missing_from_test)[:10]:
            # Check why it's missing
            has_meraki = MerakiInventory.query.filter(
                func.lower(MerakiInventory.network_name) == func.lower(site)
            ).first()
            
            if not has_meraki:
                reason = "No Meraki device"
            elif has_meraki and 'Discount-Tire' not in (has_meraki.device_tags or []):
                reason = "No Discount-Tire tag"
            else:
                reason = "Excluded (hub/lab/test) or has IPs"
            
            print(f"  - {site}: {reason}")