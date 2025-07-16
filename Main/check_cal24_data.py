#!/usr/bin/env python3
"""Check all database tables for CAL 24 data"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Add Flask extensions to path
sys.path.append('/usr/local/lib/python3.9/site-packages')
sys.path.append('/usr/lib/python3/dist-packages')

from flask import Flask
from sqlalchemy import create_engine, text, func
from config import config
from models import db, Circuit, MerakiInventory, EnrichedCircuit

app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)

def check_cal24():
    with app.app_context():
        print("=== Checking CAL 24 data in database ===\n")
        
        # Check circuits table
        print("1. Circuits table:")
        circuits = Circuit.query.filter(
            func.lower(Circuit.site_name) == 'cal 24'
        ).all()
        
        print(f"Found {len(circuits)} circuits for CAL 24")
        for circuit in circuits:
            print(f"  - Circuit ID: {circuit.id}")
            print(f"    Site Name: {circuit.site_name}")
            print(f"    Site ID: {circuit.site_id}")
            print(f"    WAN1 IP: {circuit.wan1_ip}")
            print(f"    WAN2 IP: {circuit.wan2_ip}")
            print(f"    Status: {circuit.status}")
            print(f"    Circuit Type: {circuit.circuit_type}")
            print()
        
        # Check meraki_inventory table
        print("\n2. Meraki Inventory table:")
        meraki_devices = MerakiInventory.query.filter(
            func.lower(MerakiInventory.network_name) == 'cal 24'
        ).all()
        
        print(f"Found {len(meraki_devices)} Meraki devices for CAL 24")
        for device in meraki_devices:
            print(f"  - Device Serial: {device.device_serial}")
            print(f"    Network Name: {device.network_name}")
            print(f"    Model: {device.model}")
            print(f"    WAN1 IP: {device.wan1_ip}")
            print(f"    WAN2 IP: {device.wan2_ip}")
            print(f"    WAN1 ARIN Provider: {device.wan1_arin_provider}")
            print(f"    WAN2 ARIN Provider: {device.wan2_arin_provider}")
            print(f"    Last Updated: {device.last_updated}")
            print()
        
        # Check enriched_circuits table
        print("\n3. Enriched Circuits table:")
        enriched = EnrichedCircuit.query.filter(
            func.lower(EnrichedCircuit.network_name) == 'cal 24'
        ).all()
        
        print(f"Found {len(enriched)} enriched circuits for CAL 24")
        for e in enriched:
            print(f"  - ID: {e.id}")
            print(f"    Network Name: {e.network_name}")
            print(f"    Site ID: {e.site_id}")
            print(f"    WAN1 IP: {e.wan1_ip}")
            print(f"    WAN2 IP: {e.wan2_ip}")
            print(f"    WAN1 ARIN Org: {e.wan1_arin_org}")
            print(f"    WAN2 ARIN Org: {e.wan2_arin_org}")
            print(f"    Last Updated: {e.last_updated}")
            print()
        
        # Check Meraki API directly
        print("\n4. Checking Meraki API for CAL 24:")
        print("Looking for any networks containing 'CAL'...")
        
        # Raw SQL to check all Meraki networks
        result = db.session.execute(text("""
            SELECT DISTINCT network_name 
            FROM meraki_inventory 
            WHERE network_name ILIKE '%cal%'
            ORDER BY network_name
        """))
        
        cal_networks = result.fetchall()
        print(f"\nFound {len(cal_networks)} networks with 'CAL' in the name:")
        for network in cal_networks:
            print(f"  - {network[0]}")

if __name__ == "__main__":
    check_cal24()