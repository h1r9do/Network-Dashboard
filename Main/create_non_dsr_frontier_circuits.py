#!/usr/bin/env python3
"""
Create Non-DSR circuit records for Frontier sites from master circuit info Excel file
"""

import sys
import os
sys.path.append('/usr/local/bin/Main')

import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Circuit, db
from config import Config

def get_next_circuit_id(session):
    """Get the next available circuit ID"""
    result = session.execute(text("SELECT MAX(id) FROM circuits")).scalar()
    return (result or 0) + 1

def circuit_exists(session, site_name, provider_name, circuit_purpose):
    """Check if a circuit already exists for this site/provider/purpose combo"""
    existing = session.query(Circuit).filter(
        Circuit.site_name == site_name,
        Circuit.provider_name == provider_name,
        Circuit.circuit_purpose == circuit_purpose,
        Circuit.status == 'Enabled'
    ).first()
    return existing is not None

def create_non_dsr_circuit(session, site_name, provider_name, speed, cost, circuit_purpose):
    """Create a non-DSR circuit record"""
    
    # Skip if circuit already exists
    if circuit_exists(session, site_name, provider_name, circuit_purpose):
        print(f"  → Circuit already exists for {site_name} {circuit_purpose} {provider_name}")
        return False
    
    # Get next ID
    next_id = get_next_circuit_id(session)
    
    # Create the circuit
    new_circuit = Circuit(
        id=next_id,
        site_name=site_name,
        site_id=None,  # Non-DSR circuits typically don't have site_id
        circuit_purpose=circuit_purpose,
        status='Enabled',
        provider_name=provider_name,
        details_ordered_service_speed=speed if speed != 'Cell' else None,
        billing_monthly_cost=float(cost) if pd.notna(cost) else 0.0,
        data_source='Non-DSR',
        record_number=None,  # Critical: NULL for Non-DSR
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    session.add(new_circuit)
    print(f"  ✓ Created {circuit_purpose} circuit: {provider_name} ({speed}) ${cost}")
    return True

def main():
    # Read the Excel file
    print("Reading master circuit info Excel file...")
    df = pd.read_excel('/usr/local/bin/Main/master circuit info cleaned.xlsx')
    
    # Target Frontier sites that are failing to match
    target_sites = ['CAL 13', 'CAL 17', 'CAL 20', 'CAL 24', 'CAN 16', 'CAS 35', 'CAS 40', 'CAS 41', 'CAS 48']
    
    # Create database session
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("\n=== Creating Non-DSR Circuits for Frontier Sites ===\n")
    
    created_count = 0
    
    for site in target_sites:
        site_data = df[df['Store'] == site]
        
        if site_data.empty:
            print(f"\n{site}: Not found in Excel file")
            continue
        
        row = site_data.iloc[0]
        print(f"\n{site}:")
        
        # Check existing circuits first
        existing_circuits = session.query(Circuit).filter(
            Circuit.site_name == site,
            Circuit.status == 'Enabled'
        ).all()
        
        if existing_circuits:
            print(f"  Existing circuits found:")
            for circ in existing_circuits:
                print(f"    - {circ.circuit_purpose}: {circ.provider_name} (data_source: {circ.data_source})")
        
        # Create Primary circuit if WAN1 exists
        wan1_provider = row['WAN 1 Provider']
        wan1_speed = row['WAN 1 Speed']
        wan1_cost = row['WAN 1 Cost']
        
        if pd.notna(wan1_provider) and wan1_provider:
            if create_non_dsr_circuit(session, site, wan1_provider, wan1_speed, wan1_cost, 'Primary'):
                created_count += 1
        
        # Create Secondary circuit if WAN2 exists and not just "Cell"
        wan2_provider = row['WAN 2 Provider']
        wan2_speed = row['WAN 2 Speed']
        wan2_cost = row['Wan 2 Cost']
        
        if pd.notna(wan2_provider) and wan2_provider and wan2_provider != 'Cell':
            if create_non_dsr_circuit(session, site, wan2_provider, wan2_speed, wan2_cost, 'Secondary'):
                created_count += 1
    
    print(f"\n\n=== Summary ===")
    print(f"Total circuits created: {created_count}")
    
    # Show what would be committed
    print("\n=== Circuits to be committed ===")
    for circuit in session.new:
        print(f"{circuit.site_name} - {circuit.circuit_purpose}: {circuit.provider_name}")
    
    # Auto-commit for non-interactive execution
    if created_count > 0:
        session.commit()
        print("✓ Changes committed successfully!")
    else:
        session.rollback()
        print("✗ No changes to commit")
    
    session.close()

if __name__ == "__main__":
    main()