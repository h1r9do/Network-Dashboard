#!/usr/bin/env python3
"""
Check CAL 24 circuits in the database to identify DSR vs Non-DSR circuits
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, Circuit
from config import get_db_uri
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def check_cal24_circuits():
    """Check all circuits for CAL 24 site"""
    # Create database connection
    engine = create_engine(get_db_uri())
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("Checking CAL 24 circuits in database...")
    print("="*80)
    
    # Query all circuits for CAL 24, regardless of status
    circuits = session.query(Circuit).filter(
        Circuit.site_name == 'CAL 24'
    ).all()
    
    print(f"\nTotal circuits found for CAL 24: {len(circuits)}")
    print("-"*80)
    
    # Group by status
    status_groups = {}
    for circuit in circuits:
        status = circuit.status or 'Unknown'
        if status not in status_groups:
            status_groups[status] = []
        status_groups[status].append(circuit)
    
    # Display circuits grouped by status
    for status, status_circuits in status_groups.items():
        print(f"\n{status} circuits: {len(status_circuits)}")
        for circuit in status_circuits:
            print(f"  - Site ID: {circuit.site_id}")
            print(f"    Circuit Purpose: {circuit.circuit_purpose}")
            print(f"    Provider: {circuit.provider_name}")
            print(f"    Speed: {circuit.details_ordered_service_speed}")
            print(f"    Cost: ${circuit.billing_monthly_cost or 0}")
            print(f"    Record Number: {circuit.record_number}")
            print()
    
    # Check for Non-DSR indicators
    print("\nChecking for Non-DSR indicators...")
    print("-"*80)
    
    non_dsr_indicators = [
        "Non-DSR",
        "non-dsr",
        "NonDSR",
        "Store provided",
        "Store Provided",
        "Customer provided",
        "Customer Provided"
    ]
    
    for circuit in circuits:
        # Check circuit_purpose field
        if circuit.circuit_purpose:
            for indicator in non_dsr_indicators:
                if indicator.lower() in circuit.circuit_purpose.lower():
                    print(f"\n⚠️  Possible Non-DSR circuit found:")
                    print(f"   Site ID: {circuit.site_id}")
                    print(f"   Purpose: {circuit.circuit_purpose}")
                    print(f"   Status: {circuit.status}")
                    print(f"   Provider: {circuit.provider_name}")
                    
        # Check if it's a store-provided circuit based on cost
        if circuit.billing_monthly_cost == 0 and circuit.status == 'Enabled':
            print(f"\n⚠️  Zero-cost enabled circuit (possible store-provided):")
            print(f"   Site ID: {circuit.site_id}")
            print(f"   Purpose: {circuit.circuit_purpose}")
            print(f"   Provider: {circuit.provider_name}")
    
    # Show only enabled circuits (what would appear in dsrallcircuits)
    enabled_circuits = [c for c in circuits if c.status == 'Enabled']
    print(f"\n\nEnabled circuits that appear in dsrallcircuits: {len(enabled_circuits)}")
    print("-"*80)
    for circuit in enabled_circuits:
        print(f"Site ID: {circuit.site_id}, Purpose: {circuit.circuit_purpose}, Provider: {circuit.provider_name}")
    
    session.close()

if __name__ == "__main__":
    check_cal24_circuits()