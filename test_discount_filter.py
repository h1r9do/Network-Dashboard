#!/usr/bin/env python3
import sys
sys.path.append('/usr/local/bin/Main')
from models import db, EnrichedCircuit, MerakiInventory
from dsrcircuits import app

with app.app_context():
    # Count total enriched circuits
    total = db.session.query(EnrichedCircuit).count()
    print(f"Total enriched circuits: {total}")
    
    # Count circuits with Discount-Tire tag
    query = db.session.query(EnrichedCircuit).join(
        MerakiInventory,
        EnrichedCircuit.network_name == MerakiInventory.network_name
    ).filter(
        db.text("meraki_inventory.device_tags @> ARRAY['Discount-Tire']")
    )
    
    discount_count = query.count()
    print(f"Circuits with Discount-Tire tag: {discount_count}")
    
    # Show first 5 examples
    if discount_count > 0:
        print("\nFirst 5 examples:")
        for circuit in query.limit(5):
            meraki = MerakiInventory.query.filter_by(network_name=circuit.network_name).first()
            print(f"  - {circuit.network_name}: tags = {meraki.device_tags if meraki else 'No meraki record'}")
    
    # Check if there's a mismatch in network names
    print("\n\nChecking for network name mismatches...")
    
    # Get some Meraki devices with Discount-Tire tag
    meraki_with_tag = db.session.query(MerakiInventory).filter(
        db.text("device_tags @> ARRAY['Discount-Tire']")
    ).limit(5).all()
    
    print(f"\nMeraki devices with Discount-Tire tag:")
    for m in meraki_with_tag:
        print(f"  - {m.network_name}")
        # Check if there's a matching enriched circuit
        ec = EnrichedCircuit.query.filter_by(network_name=m.network_name).first()
        if not ec:
            print(f"    WARNING: No enriched circuit found for this network!")