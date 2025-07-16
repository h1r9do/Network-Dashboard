#!/usr/bin/env python3
import sys
sys.path.insert(0, '/usr/local/bin/Main')
from config import Config
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
from models import Circuit, EnrichedCircuit

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

# Simulate what dsrcircuits.py does for AZN 03
circuit = session.query(EnrichedCircuit).filter(
    func.lower(EnrichedCircuit.network_name) == 'azn 03'
).first()

if circuit:
    print(f'Found enriched circuit for AZN 03')
    print(f'WAN1 Provider: {circuit.wan1_provider}')
    print(f'WAN2 Provider: {circuit.wan2_provider}')
    
    # Get cost data from circuits table
    wan1_cost = '$0.00'
    wan2_cost = '$0.00'
    
    # Get ALL enabled circuits for this site
    site_circuits = session.query(Circuit).filter(
        func.lower(Circuit.site_name) == func.lower(circuit.network_name),
        Circuit.status == 'Enabled'
    ).all()
    
    print(f'\nFound {len(site_circuits)} enabled circuits')
    
    for dsr_circuit in site_circuits:
        print(f'\nDSR Circuit: {dsr_circuit.circuit_purpose} - {dsr_circuit.provider_name}')
        print(f'  Cost: {dsr_circuit.billing_monthly_cost}')
        
        if not dsr_circuit.billing_monthly_cost:
            print('  Skipping - no cost')
            continue
            
        # Normalize provider names
        dsr_provider = (dsr_circuit.provider_name or '').upper().strip()
        wan1_provider = (circuit.wan1_provider or '').upper().strip()
        
        print(f'  Comparing: DSR="{dsr_provider}" vs WAN1="{wan1_provider}"')
        
        if wan1_provider and dsr_provider:
            if dsr_provider in wan1_provider or wan1_provider in dsr_provider:
                print('  MATCH!')
                wan1_cost = f'${float(dsr_circuit.billing_monthly_cost):.2f}'
    
    print(f'\nFinal costs: WAN1={wan1_cost}, WAN2={wan2_cost}')

session.close()