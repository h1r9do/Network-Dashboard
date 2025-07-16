#!/usr/bin/env python3
import sys
sys.path.append('/usr/local/bin/Main')
from models import db, EnrichedCircuit
from dsrcircuits import app

with app.app_context():
    # Get all unique tags
    all_tags = set()
    circuits = db.session.query(EnrichedCircuit).filter(
        EnrichedCircuit.device_tags.isnot(None)
    ).limit(100).all()
    
    print(f"Found {len(circuits)} circuits with tags")
    print("\nSample circuit tags:")
    for i, circuit in enumerate(circuits[:5]):
        print(f"\n{i+1}. {circuit.network_name}:")
        if circuit.device_tags:
            print(f"   Tags: {circuit.device_tags}")
            for tag in circuit.device_tags:
                all_tags.add(tag)
    
    print("\n\nAll unique tags found:")
    for tag in sorted(all_tags):
        print(f"  - '{tag}'")
    
    # Check specifically for Discount-Tire variations
    print("\n\nChecking for Discount-Tire variations:")
    discount_variations = ['Discount-Tire', 'discount-tire', 'Discount Tire', 'discount tire', 'DiscountTire']
    for variation in discount_variations:
        count = db.session.query(EnrichedCircuit).filter(
            EnrichedCircuit.device_tags.any(variation)
        ).count()
        print(f"  '{variation}': {count} circuits")