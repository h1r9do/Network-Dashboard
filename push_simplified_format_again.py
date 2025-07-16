#!/usr/bin/env python3
"""
Export confirmed sites from database and push to Meraki separately
This avoids holding database locks during the slow Meraki API operations
"""
import os
import sys
import json
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

# Add the script directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config
from models import db, EnrichedCircuit, MerakiInventory
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"

def export_confirmed_sites():
    """Export the 654 sites from the list"""
    print("=== Loading 654 sites to push simplified format ===")
    
    # Load the 654 sites
    sites_to_push = []
    with open('/tmp/sites_to_revert.txt', 'r') as f:
        site_names = [line.strip() for line in f.readlines() if line.strip()]
    
    # Create database session
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Query only the 654 sites
        query = session.query(
            EnrichedCircuit.network_name,
            EnrichedCircuit.wan1_provider,
            EnrichedCircuit.wan1_speed,
            EnrichedCircuit.wan1_confirmed,
            EnrichedCircuit.wan2_provider, 
            EnrichedCircuit.wan2_speed,
            EnrichedCircuit.wan2_confirmed,
            MerakiInventory.device_serial,
            MerakiInventory.network_id
        ).join(
            MerakiInventory, 
            EnrichedCircuit.network_name == MerakiInventory.network_name
        ).filter(
            EnrichedCircuit.network_name.in_(site_names),
            MerakiInventory.device_model.like('MX%')
        ).order_by(EnrichedCircuit.network_name)
        
        sites_to_push = []
        for row in query.all():
            network_name = row[0]
            wan1_provider = row[1] or ""
            wan1_speed = row[2] or ""
            wan1_confirmed = row[3]
            wan2_provider = row[4] or ""
            wan2_speed = row[5] or ""
            wan2_confirmed = row[6]
            device_serial = row[7]
            network_id = row[8]
            
            # Build notes string in correct format
            notes_parts = []
            if wan1_confirmed and wan1_provider and wan1_speed:
                notes_parts.extend([
                    "WAN 1",
                    wan1_provider,
                    wan1_speed
                ])
            
            if wan2_confirmed and wan2_provider and wan2_speed:
                notes_parts.extend([
                    "WAN 2",
                    wan2_provider, 
                    wan2_speed
                ])
            
            if notes_parts:
                notes = "\n".join(notes_parts)
                sites_to_push.append({
                    'network_name': network_name,
                    'device_serial': device_serial,
                    'network_id': network_id,
                    'notes': notes,
                    'wan1_confirmed': wan1_confirmed,
                    'wan2_confirmed': wan2_confirmed
                })
        
        print(f"✅ Loaded {len(sites_to_push)} sites to push simplified format")
        return sites_to_push
        
    finally:
        session.close()

def update_device_notes(device_serial, notes):
    """Update device notes via Meraki API"""
    url = f"{BASE_URL}/devices/{device_serial}"
    headers = {
        "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
        "Content-Type": "application/json"
    }
    
    data = {"notes": notes}
    
    try:
        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 200:
            return True
        else:
            print(f"❌ Error updating device {device_serial}: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception updating device {device_serial}: {e}")
        return False

def mark_sites_as_pushed(sites_pushed):
    """Mark successful sites as pushed in database"""
    print(f"\n=== Marking {len(sites_pushed)} sites as pushed in database ===")
    
    # Create database session
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        for site in sites_pushed:
            circuit = session.query(EnrichedCircuit).filter_by(
                network_name=site['network_name']
            ).first()
            
            if circuit:
                circuit.pushed_to_meraki = True
                circuit.pushed_date = datetime.utcnow()
        
        session.commit()
        print("✅ Database updated successfully")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error updating database: {e}")
    finally:
        session.close()

def main():
    """Main function"""
    print("=== Push Simplified Format to 654 Sites ===")
    start_time = time.time()
    
    # Step 1: Export confirmed sites from database (fast)
    sites_to_push = export_confirmed_sites()
    if not sites_to_push:
        print("No confirmed sites to push")
        return
    
    print(f"\n=== Pushing {len(sites_to_push)} sites to Meraki ===")
    
    # Step 2: Push to Meraki (slow, but no database locks)
    success_count = 0
    error_count = 0
    sites_pushed = []
    
    for i, site in enumerate(sites_to_push, 1):
        network_name = site['network_name']
        device_serial = site['device_serial'] 
        notes = site['notes']
        
        print(f"[{i}/{len(sites_to_push)}] Processing {network_name} ({device_serial})")
        print(f"  Notes format:")
        for line in notes.split('\n'):
            print(f"    {line}")
        
        if update_device_notes(device_serial, notes):
            print(f"  ✓ Successfully updated {network_name}")
            success_count += 1
            sites_pushed.append(site)
        else:
            print(f"  ✗ Failed to update {network_name}")
            error_count += 1
        
        # Rate limiting
        time.sleep(0.3)
        
        # Progress update every 50 sites
        if i % 50 == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed * 60  # sites per minute
            remaining = len(sites_to_push) - i
            eta_minutes = remaining / (rate / 60) if rate > 0 else 0
            print(f"\n📊 Progress: {i}/{len(sites_to_push)} ({i/len(sites_to_push)*100:.1f}%)")
            print(f"   Rate: {rate:.1f} sites/min, ETA: {eta_minutes:.1f} minutes\n")
    
    # Step 3: Mark successful sites as pushed (fast)
    if sites_pushed:
        mark_sites_as_pushed(sites_pushed)
    
    # Summary
    elapsed = time.time() - start_time
    print(f"\n=== Summary ===")
    print(f"Total sites processed: {len(sites_to_push)}")
    print(f"Successful pushes: {success_count}")
    print(f"Failed pushes: {error_count}")
    print(f"Total time: {elapsed/60:.1f} minutes")
    print(f"Average rate: {len(sites_to_push)/(elapsed/60):.1f} sites/min")
    print(f"✅ Push operation complete!")

if __name__ == "__main__":
    main()