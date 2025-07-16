#!/usr/bin/env python3
"""Test the enhanced ARIN refresh function"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock Flask app context
from flask import Flask
from models import db, Circuit, MerakiInventory, EnrichedCircuit
from config import config

app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)

def test_arin_refresh_logic():
    """Test the ARIN refresh logic for CAL 24"""
    
    with app.app_context():
        site_name = "CAL 24"
        print(f"=== Testing ARIN refresh logic for {site_name} ===\n")
        
        # Strategy 1: Check Meraki device
        from sqlalchemy import func
        meraki_device = MerakiInventory.query.filter(
            func.lower(MerakiInventory.network_name) == func.lower(site_name)
        ).first()
        
        print(f"1. Meraki device check:")
        if meraki_device:
            print(f"   ✓ Found device: {meraki_device.device_serial}")
            print(f"   - WAN1 IP: {meraki_device.wan1_ip}")
            print(f"   - WAN2 IP: {meraki_device.wan2_ip}")
            print(f"   - WAN1 Provider: {meraki_device.wan1_arin_provider}")
            print(f"   - WAN2 Provider: {meraki_device.wan2_arin_provider}")
        else:
            print("   ✗ No Meraki device found")
        
        # Strategy 2: Check enriched circuits
        print(f"\n2. Enriched circuits check:")
        enriched = EnrichedCircuit.query.filter(
            func.lower(EnrichedCircuit.network_name) == func.lower(site_name)
        ).first()
        
        if enriched:
            print(f"   ✓ Found enriched circuit: ID {enriched.id}")
            print(f"   - WAN1 IP: {enriched.wan1_ip}")
            print(f"   - WAN2 IP: {enriched.wan2_ip}")
            print(f"   - WAN1 ARIN: {enriched.wan1_arin_org}")
            print(f"   - WAN2 ARIN: {enriched.wan2_arin_org}")
        else:
            print("   ✗ No enriched circuit found")
        
        # Strategy 3: Check circuits table
        print(f"\n3. Circuits table check:")
        circuits = Circuit.query.filter(
            func.lower(Circuit.site_name) == func.lower(site_name)
        ).all()
        
        print(f"   Found {len(circuits)} circuit(s)")
        for circuit in circuits:
            print(f"   - Circuit ID: {circuit.id}")
            print(f"   - Provider: {circuit.provider_name}")
            print(f"   - Status: {circuit.status}")
            
            # Check what IP columns exist
            if hasattr(circuit, 'ip_address_start'):
                print(f"   - IP Address Start: {circuit.ip_address_start}")
            if hasattr(circuit, 'wan1_ip'):
                print(f"   - WAN1 IP: {circuit.wan1_ip}")
            else:
                print("   - No wan1_ip column (this was the bug!)")
            if hasattr(circuit, 'wan2_ip'):
                print(f"   - WAN2 IP: {circuit.wan2_ip}")
            else:
                print("   - No wan2_ip column (this was the bug!)")
        
        # Summary
        print(f"\n4. Summary:")
        has_ip_data = False
        if meraki_device and (meraki_device.wan1_ip or meraki_device.wan2_ip):
            print("   ✓ IP data available from Meraki inventory")
            has_ip_data = True
        elif enriched and (enriched.wan1_ip or enriched.wan2_ip):
            print("   ✓ IP data available from enriched circuits")
            has_ip_data = True
        elif circuits:
            for circuit in circuits:
                if hasattr(circuit, 'ip_address_start') and circuit.ip_address_start:
                    print("   ✓ IP data available from circuits table (ip_address_start)")
                    has_ip_data = True
                    break
        
        if not has_ip_data:
            print("   ✗ No IP data found in any table")
            print("   → This is why ARIN refresh fails for CAL 24")
            print("   → Fixed version will provide detailed error message")
        
        # Test circuit count for error message
        circuit_count = Circuit.query.filter(func.lower(Circuit.site_name) == func.lower(site_name)).count()
        print(f"\n5. Error message components:")
        print(f"   - Meraki device: {'Found' if meraki_device else 'Not found'}")
        print(f"   - Circuit count: {circuit_count}")
        if meraki_device and not (meraki_device.wan1_ip or meraki_device.wan2_ip):
            print(f"   - Enhanced error: 'Meraki device found (serial: {meraki_device.device_serial}) but no IP addresses recorded'")

if __name__ == "__main__":
    test_arin_refresh_logic()