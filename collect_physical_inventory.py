#!/usr/bin/env python3
"""
Collect only physical devices with valid serial numbers from SNMP data
Filters out empty slots, sensors, and virtual components
"""
import json
import psycopg2
from datetime import datetime
import os

class PhysicalInventoryCollector:
    def __init__(self):
        self.db_connection = None
        
    def connect_db(self):
        """Connect to PostgreSQL database"""
        try:
            db_config = {
                'host': os.environ.get('DB_HOST', 'localhost'),
                'database': os.environ.get('DB_NAME', 'dsrcircuits'),
                'user': os.environ.get('DB_USER', 'dsruser'),
                'password': os.environ.get('DB_PASSWORD', 'dsruser'),
                'port': os.environ.get('DB_PORT', '5432')
            }
            self.db_connection = psycopg2.connect(**db_config)
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    def is_physical_component(self, entity):
        """Determine if an entity is a physical component worth tracking"""
        model = entity.get('model_name', '').strip()
        serial = entity.get('serial_number', '').strip()
        desc = entity.get('description', '').lower()
        entity_class = entity.get('class', '')
        
        # Must have a real model number (not empty or "")
        if not model or model == '""' or model == '':
            return False
        
        # Should have a serial number (but some valid components might not)
        has_serial = serial and serial != '""' and serial != ''
        
        # Entity class filters
        # Class 3: Chassis - Always physical
        # Class 6: Power Supply - Always physical
        # Class 7: Fan - Always physical
        # Class 9: Module - Physical if it has model/serial
        # Class 5: Container/Slot - Usually not physical unless it has serial
        # Class 8: Sensor - Never physical
        # Class 10: Port - Not physical (part of module)
        # Class 1: Processor - Usually virtual
        
        if entity_class == '8':  # Sensors
            return False
        
        if entity_class == '10':  # Ports
            return False
            
        if entity_class == '1':  # Processors
            return False
        
        # For transceivers/SFPs - must be populated (have model)
        if 'transceiver' in desc or 'sfp' in desc or 'qsfp' in desc:
            return bool(model and model != '""')
        
        # For modules, must have serial or be a known module type
        if entity_class == '9':
            # Known module patterns that are physical
            known_modules = ['SUP', 'FAB', 'N7K-', 'N5K-', 'N9K-', 'C8', 'WS-', 'C9']
            is_known = any(pattern in model for pattern in known_modules)
            return is_known or has_serial
        
        # For other classes, require serial number
        return has_serial
    
    def extract_physical_inventory(self, device_data):
        """Extract only physical components from device entity data"""
        physical_inventory = {
            'chassis': None,
            'modules': [],
            'power_supplies': [],
            'fans': [],
            'transceivers': []
        }
        
        for entity_id, entity in device_data.get('entity_data', {}).items():
            if not self.is_physical_component(entity):
                continue
            
            component = {
                'entity_id': entity_id,
                'description': entity.get('description', ''),
                'model': entity.get('model_name', '').strip(),
                'serial': entity.get('serial_number', '').strip(),
                'name': entity.get('name', ''),
                'class': entity.get('class', '')
            }
            
            # Remove empty serials from display
            if component['serial'] == '""':
                component['serial'] = ''
            
            # Categorize by type
            entity_class = entity.get('class', '')
            desc_lower = component['description'].lower()
            model = component['model']
            
            if entity_class == '3':  # Chassis
                physical_inventory['chassis'] = component
            elif entity_class == '6':  # Power Supply
                physical_inventory['power_supplies'].append(component)
            elif entity_class == '7':  # Fan
                physical_inventory['fans'].append(component)
            elif 'transceiver' in desc_lower or 'sfp' in desc_lower or any(x in model for x in ['GLC-', 'SFP-', 'QSFP-']):
                physical_inventory['transceivers'].append(component)
            elif entity_class == '9':  # Module
                physical_inventory['modules'].append(component)
            # Skip containers, sensors, ports, etc.
        
        return physical_inventory
    
    def process_all_devices(self, json_file):
        """Process all devices from JSON file and extract physical inventory"""
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        results = []
        
        for device in data['devices']:
            if device.get('status') != 'success':
                continue
            
            physical_inv = self.extract_physical_inventory(device)
            
            # Only include devices that have physical components
            if (physical_inv['chassis'] or physical_inv['modules'] or 
                physical_inv['power_supplies'] or physical_inv['fans'] or 
                physical_inv['transceivers']):
                
                result = {
                    'hostname': device.get('device_name', ''),
                    'ip': device.get('ip', ''),
                    'collection_timestamp': device.get('timestamp', ''),
                    'physical_inventory': physical_inv,
                    'summary': {
                        'chassis_model': physical_inv['chassis']['model'] if physical_inv['chassis'] else 'Unknown',
                        'chassis_serial': physical_inv['chassis']['serial'] if physical_inv['chassis'] else '',
                        'module_count': len(physical_inv['modules']),
                        'power_supply_count': len(physical_inv['power_supplies']),
                        'fan_count': len(physical_inv['fans']),
                        'transceiver_count': len(physical_inv['transceivers'])
                    }
                }
                results.append(result)
        
        return results
    
    def store_physical_inventory(self, inventory_data):
        """Store physical inventory in database"""
        if not self.db_connection:
            if not self.connect_db():
                return False
        
        cursor = self.db_connection.cursor()
        
        try:
            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS physical_device_inventory (
                    id SERIAL PRIMARY KEY,
                    hostname VARCHAR(255),
                    ip_address VARCHAR(45),
                    collection_timestamp TIMESTAMP,
                    chassis_model VARCHAR(100),
                    chassis_serial VARCHAR(100),
                    module_count INTEGER,
                    power_supply_count INTEGER,
                    fan_count INTEGER,
                    transceiver_count INTEGER,
                    physical_components JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(hostname, ip_address)
                )
            """)
            
            # Insert/update inventory
            for device in inventory_data:
                cursor.execute("""
                    INSERT INTO physical_device_inventory (
                        hostname, ip_address, collection_timestamp,
                        chassis_model, chassis_serial, module_count,
                        power_supply_count, fan_count, transceiver_count,
                        physical_components, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (hostname, ip_address) 
                    DO UPDATE SET
                        collection_timestamp = EXCLUDED.collection_timestamp,
                        chassis_model = EXCLUDED.chassis_model,
                        chassis_serial = EXCLUDED.chassis_serial,
                        module_count = EXCLUDED.module_count,
                        power_supply_count = EXCLUDED.power_supply_count,
                        fan_count = EXCLUDED.fan_count,
                        transceiver_count = EXCLUDED.transceiver_count,
                        physical_components = EXCLUDED.physical_components,
                        updated_at = EXCLUDED.updated_at
                """, (
                    device['hostname'],
                    device['ip'],
                    device['collection_timestamp'],
                    device['summary']['chassis_model'],
                    device['summary']['chassis_serial'],
                    device['summary']['module_count'],
                    device['summary']['power_supply_count'],
                    device['summary']['fan_count'],
                    device['summary']['transceiver_count'],
                    json.dumps(device['physical_inventory']),
                    datetime.now()
                ))
            
            self.db_connection.commit()
            print(f"Stored {len(inventory_data)} device inventories in database")
            return True
            
        except Exception as e:
            print(f"Database error: {e}")
            self.db_connection.rollback()
            return False
        finally:
            cursor.close()
    
    def generate_summary_report(self, inventory_data):
        """Generate summary report of physical inventory"""
        print("\n=== Physical Inventory Summary ===")
        print(f"Total devices with physical inventory: {len(inventory_data)}")
        
        # Group by chassis model
        by_model = {}
        for device in inventory_data:
            model = device['summary']['chassis_model']
            if model not in by_model:
                by_model[model] = []
            by_model[model].append(device)
        
        print("\nDevices by chassis model:")
        for model in sorted(by_model.keys()):
            print(f"\n{model}: {len(by_model[model])} devices")
            # Show first few examples
            for device in by_model[model][:3]:
                s = device['summary']
                print(f"  - {device['hostname']} ({device['ip']})")
                print(f"    Serial: {s['chassis_serial']}")
                print(f"    Modules: {s['module_count']}, PSUs: {s['power_supply_count']}, "
                      f"Fans: {s['fan_count']}, SFPs: {s['transceiver_count']}")
                
                # Show module models if any
                if device['physical_inventory']['modules']:
                    models = list(set([m['model'] for m in device['physical_inventory']['modules']]))
                    print(f"    Module models: {', '.join(models[:5])}")

def main():
    collector = PhysicalInventoryCollector()
    
    # Process latest collection
    json_file = '/var/www/html/network-data/nightly_snmp_collection_20250708_154906.json'
    
    print("Processing SNMP collection data...")
    inventory_data = collector.process_all_devices(json_file)
    
    # Generate report
    collector.generate_summary_report(inventory_data)
    
    # Store in database
    print("\nStoring in database...")
    if collector.store_physical_inventory(inventory_data):
        print("Successfully stored physical inventory in database")
    
    # Write JSON output for review
    output_file = '/usr/local/bin/physical_inventory_output.json'
    with open(output_file, 'w') as f:
        json.dump(inventory_data, f, indent=2)
    print(f"\nDetailed output written to: {output_file}")

if __name__ == "__main__":
    main()