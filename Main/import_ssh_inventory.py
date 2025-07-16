#!/usr/bin/env python3
"""
SSH Network Inventory Import Script
==================================

This script imports the comprehensive network inventory data collected via SSH
into the database, creating hierarchical device structures with master devices
and their associated components (chassis blades, SFP modules, hardware components).

Tables populated:
- network_devices (master devices)
- chassis_blades (line cards/modules)
- hardware_components (SFP modules on interfaces)
- sfp_modules (detailed SFP optics information)

Usage:
    python import_ssh_inventory.py

Data Source:
    /var/www/html/meraki-data/comprehensive_network_inventory.json
"""

import json
import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Add the current directory to the path so we can import models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, NetworkDevice, HardwareComponent, ChassisBlade, SfpModule
from config import Config

def get_database_session():
    """Create database session"""
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    return Session(), engine

def parse_timestamp(timestamp_str):
    """Parse timestamp string to datetime object"""
    if not timestamp_str:
        return None
    try:
        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except:
        return None

def import_device_data(device_data, ip_address, session):
    """Import a single device and its components"""
    
    # Extract basic info
    basic_info = device_data.get('basic_info', {})
    hostname = basic_info.get('hostname', '')
    collection_timestamp = parse_timestamp(basic_info.get('collection_timestamp'))
    
    # Determine device type - if it's a single device (no chassis/components), it's a master
    chassis_blades = device_data.get('chassis_blades', [])
    hardware_inventory = device_data.get('hardware_inventory', [])
    sfp_modules = device_data.get('sfp_modules', [])
    interfaces = device_data.get('interfaces', [])
    
    device_type = 'master'  # All devices are masters in this context
    
    # Create or update the network device
    device = session.query(NetworkDevice).filter_by(ip_address=ip_address).first()
    if not device:
        device = NetworkDevice(
            ip_address=ip_address,
            hostname=hostname,
            collection_timestamp=collection_timestamp,
            data_source='ssh_inventory',
            device_type=device_type,
            interfaces_count=len(interfaces)
        )
        session.add(device)
        session.flush()  # Get the ID
        print(f"Created new device: {hostname} ({ip_address})")
    else:
        # Update existing device
        device.hostname = hostname
        device.collection_timestamp = collection_timestamp
        device.interfaces_count = len(interfaces)
        device.updated_at = datetime.utcnow()
        print(f"Updated existing device: {hostname} ({ip_address})")
    
    # Clear existing components for this device
    session.query(HardwareComponent).filter_by(device_id=device.id).delete()
    session.query(ChassisBlade).filter_by(device_id=device.id).delete()
    session.query(SfpModule).filter_by(device_id=device.id).delete()
    
    # Import chassis blades
    for blade_data in chassis_blades:
        blade = ChassisBlade(
            device_id=device.id,
            module_number=blade_data.get('module_number', ''),
            ports=blade_data.get('ports', ''),
            card_type=blade_data.get('card_type', ''),
            model=blade_data.get('model', ''),
            serial_number=blade_data.get('serial_number', '')
        )
        session.add(blade)
    
    # Import hardware inventory (typically SFPs on interfaces)
    for hw_data in hardware_inventory:
        component = HardwareComponent(
            device_id=device.id,
            name=hw_data.get('name', ''),
            description=hw_data.get('description', ''),
            pid=hw_data.get('pid', '').strip(','),  # Remove commas
            vid=hw_data.get('vid', '').strip(','),  # Remove commas
            serial_number=hw_data.get('serial_number', ''),
            component_type='SFP'
        )
        session.add(component)
    
    # Import SFP modules
    for sfp_data in sfp_modules:
        sfp = SfpModule(
            device_id=device.id,
            interface=sfp_data.get('interface', ''),
            module_type=sfp_data.get('type', ''),
            status=sfp_data.get('status', ''),
            product_id=sfp_data.get('interface', '')  # Using interface as product_id fallback
        )
        session.add(sfp)
    
    return device

def create_tables_if_not_exist(engine):
    """Create the new tables if they don't exist"""
    with engine.connect() as conn:
        # Check if tables exist and create them if not
        tables_to_create = [
            """
            CREATE TABLE IF NOT EXISTS network_devices (
                id SERIAL PRIMARY KEY,
                ip_address VARCHAR(45) NOT NULL UNIQUE,
                hostname VARCHAR(100),
                collection_timestamp TIMESTAMP,
                data_source VARCHAR(50) DEFAULT 'ssh_inventory',
                device_type VARCHAR(50),
                interfaces_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS hardware_components (
                id SERIAL PRIMARY KEY,
                device_id INTEGER REFERENCES network_devices(id) ON DELETE CASCADE,
                name VARCHAR(100),
                description VARCHAR(255),
                pid VARCHAR(50),
                vid VARCHAR(50),
                serial_number VARCHAR(50),
                component_type VARCHAR(50) DEFAULT 'SFP',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS chassis_blades (
                id SERIAL PRIMARY KEY,
                device_id INTEGER REFERENCES network_devices(id) ON DELETE CASCADE,
                module_number VARCHAR(10),
                ports VARCHAR(10),
                card_type VARCHAR(255),
                model VARCHAR(100),
                serial_number VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sfp_modules (
                id SERIAL PRIMARY KEY,
                device_id INTEGER REFERENCES network_devices(id) ON DELETE CASCADE,
                interface VARCHAR(100),
                module_type VARCHAR(255),
                status VARCHAR(50),
                product_id VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        
        for table_sql in tables_to_create:
            try:
                conn.execute(text(table_sql))
                conn.commit()
            except Exception as e:
                print(f"Table creation warning: {e}")

def main():
    """Main import function"""
    print("Starting SSH Network Inventory Import...")
    print(f"Timestamp: {datetime.now()}")
    
    # Load the comprehensive inventory data
    inventory_file = '/var/www/html/meraki-data/comprehensive_network_inventory.json'
    
    if not os.path.exists(inventory_file):
        print(f"ERROR: Inventory file not found: {inventory_file}")
        return
    
    print(f"Loading data from: {inventory_file}")
    
    try:
        with open(inventory_file, 'r') as f:
            inventory_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in inventory file: {e}")
        return
    except Exception as e:
        print(f"ERROR: Could not read inventory file: {e}")
        return
    
    # Create database session
    session, engine = get_database_session()
    
    # Create tables if they don't exist
    create_tables_if_not_exist(engine)
    
    devices_processed = 0
    devices_with_components = 0
    total_chassis_blades = 0
    total_hardware_components = 0
    total_sfp_modules = 0
    
    try:
        # Process each device in the inventory
        for ip_address, device_info in inventory_data.items():
            # Skip entries that aren't device data
            if not isinstance(device_info, dict):
                continue
            
            # Extract SSH data
            ssh_data = device_info.get('ssh_data')
            if not ssh_data:
                continue
            
            # Import the device
            device = import_device_data(ssh_data, ip_address, session)
            devices_processed += 1
            
            # Count components
            chassis_count = len(ssh_data.get('chassis_blades', []))
            hardware_count = len(ssh_data.get('hardware_inventory', []))
            sfp_count = len(ssh_data.get('sfp_modules', []))
            
            if chassis_count > 0 or hardware_count > 0 or sfp_count > 0:
                devices_with_components += 1
                total_chassis_blades += chassis_count
                total_hardware_components += hardware_count
                total_sfp_modules += sfp_count
                
                print(f"  - {device.hostname}: {chassis_count} blades, {hardware_count} hw components, {sfp_count} SFPs")
            
            # Commit every 50 devices
            if devices_processed % 50 == 0:
                session.commit()
                print(f"Processed {devices_processed} devices...")
        
        # Final commit
        session.commit()
        
        print("\n" + "="*60)
        print("SSH NETWORK INVENTORY IMPORT COMPLETE")
        print("="*60)
        print(f"Total devices processed: {devices_processed}")
        print(f"Devices with components: {devices_with_components}")
        print(f"Total chassis blades: {total_chassis_blades}")
        print(f"Total hardware components: {total_hardware_components}")
        print(f"Total SFP modules: {total_sfp_modules}")
        print(f"Completed at: {datetime.now()}")
        
    except Exception as e:
        print(f"ERROR during import: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    main()