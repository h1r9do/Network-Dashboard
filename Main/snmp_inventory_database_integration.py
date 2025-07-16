#!/usr/bin/env python3
"""
SNMP Inventory Database Integration
Stores collected SNMP inventory data in PostgreSQL database tables
"""
import json
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from datetime import datetime
import os
import sys

class SNMPInventoryDB:
    def __init__(self):
        """Initialize database connection"""
        self.connection = None
        
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
            
            self.connection = psycopg2.connect(**db_config)
            return True
            
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    def close_db(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
    
    def process_entity_data(self, entity_data):
        """Process raw entity data into structured format"""
        chassis = []
        modules = []
        power_supplies = []
        fans = []
        transceivers = []
        fex_units = []
        other_components = []
        
        for entity_idx, entity in entity_data.items():
            entity_class = entity.get('class', '')
            description = entity.get('description', '').lower()
            model = entity.get('model_name', '')
            serial = entity.get('serial_number', '')
            name = entity.get('name', '')
            
            component = {
                'entity_index': entity_idx,
                'description': entity.get('description', ''),
                'class': entity_class,
                'name': name,
                'serial_number': serial,
                'model_name': model
            }
            
            # Classify components
            if entity_class == '3':  # Chassis
                if 'fex-' in description or 'fabric extender' in description:
                    fex_units.append(component)
                else:
                    chassis.append(component)
            elif entity_class == '9':  # Module
                if any(t in model.lower() for t in ['sfp', 'qsfp', 'x2', 'xfp']):
                    transceivers.append(component)
                else:
                    modules.append(component)
            elif 'power' in description or 'psu' in description:
                power_supplies.append(component)
            elif 'fan' in description and 'fan-' in model:
                fans.append(component)
            elif any(t in model.lower() for t in ['sfp', 'qsfp']) or any(t in description for t in ['transceiver', '1000base', '10gbase']):
                transceivers.append(component)
            else:
                other_components.append(component)
        
        return {
            'chassis': chassis,
            'modules': modules,
            'power_supplies': power_supplies,
            'fans': fans,
            'transceivers': transceivers,
            'fex_units': fex_units,
            'other_components': other_components
        }
    
    def extract_system_info(self, device_data):
        """Extract system information from device data"""
        sys_desc = device_data.get('system_description', '')
        
        # Extract version info
        version = ''
        if 'Version' in sys_desc:
            try:
                version_part = sys_desc.split('Version')[1].split(',')[0].strip()
                version = version_part
            except:
                pass
        
        # Extract model from system description
        model = ''
        if 'Cisco' in sys_desc:
            # Look for Nexus models
            import re
            model_match = re.search(r'(N[0-9]+K?-[A-Z0-9-]+|C[0-9]+-[A-Z0-9-]+)', sys_desc)
            if model_match:
                model = model_match.group(1)
        
        return {
            'system_description': sys_desc,
            'software_version': version,
            'detected_model': model,
            'collection_method': device_data.get('collection_method', 'standard'),
            'entity_count': device_data.get('entity_count', 0),
            'collection_time': device_data.get('collection_time_seconds', 0)
        }
    
    def store_device_inventory(self, device_data):
        """Store device inventory in comprehensive_device_inventory table"""
        if not self.connection:
            if not self.connect_db():
                return False
        
        try:
            hostname = device_data.get('device_name', '')
            ip_address = device_data.get('ip', '')
            collection_timestamp = device_data.get('timestamp', datetime.now().isoformat())
            
            # Parse timestamp
            if isinstance(collection_timestamp, str):
                try:
                    collection_timestamp = datetime.fromisoformat(collection_timestamp.replace('Z', '+00:00'))
                except:
                    collection_timestamp = datetime.now()
            
            # Extract system info
            system_info = self.extract_system_info(device_data)
            
            # Process entity data
            entity_data = device_data.get('entity_data', {})
            physical_components = self.process_entity_data(entity_data)
            
            # Create summary
            summary = {
                'status': device_data.get('status', 'unknown'),
                'credential_used': device_data.get('credential', ''),
                'device_type': device_data.get('device_type', ''),
                'total_entities': len(entity_data),
                'component_counts': {
                    'chassis': len(physical_components['chassis']),
                    'modules': len(physical_components['modules']),
                    'power_supplies': len(physical_components['power_supplies']),
                    'fans': len(physical_components['fans']),
                    'transceivers': len(physical_components['transceivers']),
                    'fex_units': len(physical_components['fex_units']),
                    'other_components': len(physical_components['other_components'])
                }
            }
            
            # If device failed, store error info
            if device_data.get('status') == 'failed':
                summary['error'] = device_data.get('error', 'Unknown error')
                physical_components = {}
                system_info['error'] = device_data.get('error', 'Unknown error')
            
            with self.connection.cursor() as cursor:
                # Use INSERT ... ON CONFLICT to handle updates
                cursor.execute("""
                    INSERT INTO comprehensive_device_inventory (
                        hostname, ip_address, collection_timestamp, 
                        system_info, physical_components, summary,
                        created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (hostname, ip_address) 
                    DO UPDATE SET
                        collection_timestamp = EXCLUDED.collection_timestamp,
                        system_info = EXCLUDED.system_info,
                        physical_components = EXCLUDED.physical_components,
                        summary = EXCLUDED.summary,
                        updated_at = EXCLUDED.updated_at
                """, (
                    hostname, ip_address, collection_timestamp,
                    Json(system_info), Json(physical_components), Json(summary),
                    datetime.now(), datetime.now()
                ))
                
                self.connection.commit()
                return True
                
        except Exception as e:
            print(f"Error storing device inventory for {hostname}: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def update_inventory_summary(self):
        """Update inventory_summary table with model counts"""
        if not self.connection:
            if not self.connect_db():
                return False
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get model counts from stored inventory
                cursor.execute("""
                    SELECT 
                        system_info->>'detected_model' as model,
                        COUNT(*) as count
                    FROM comprehensive_device_inventory 
                    WHERE system_info->>'detected_model' IS NOT NULL
                    AND system_info->>'detected_model' != ''
                    AND summary->>'status' = 'success'
                    GROUP BY system_info->>'detected_model'
                    ORDER BY count DESC
                """)
                
                model_counts = cursor.fetchall()
                
                print(f"Updating inventory summary for {len(model_counts)} models...")
                
                for row in model_counts:
                    model = row['model']
                    count = row['count']
                    
                    # Skip non-Meraki models (Cisco switches)
                    # Meraki models typically start with M (MR, MS, MX, MV, MT) or are VMX/Z series
                    if not (model.startswith(('MR', 'MS', 'MX', 'MV', 'MT', 'VMX', 'Z3', 'Z1'))):
                        print(f"Skipping non-Meraki model: {model}")
                        continue
                    
                    # Insert or update model count
                    cursor.execute("""
                        INSERT INTO inventory_summary (model, total_count, org_counts)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (model)
                        DO UPDATE SET
                            total_count = EXCLUDED.total_count,
                            org_counts = EXCLUDED.org_counts
                    """, (model, count, f"SNMP: {count}"))
                
                self.connection.commit()
                print(f"Updated inventory summary for {len(model_counts)} models")
                return True
                
        except Exception as e:
            print(f"Error updating inventory summary: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def get_inventory_stats(self):
        """Get inventory statistics"""
        if not self.connection:
            if not self.connect_db():
                return None
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_devices,
                        COUNT(*) FILTER (WHERE summary->>'status' = 'success') as successful_devices,
                        COUNT(*) FILTER (WHERE summary->>'status' = 'failed') as failed_devices,
                        COUNT(*) FILTER (WHERE summary->>'status' = 'pending_friday') as pending_devices,
                        SUM((summary->'component_counts'->>'transceivers')::int) as total_transceivers,
                        SUM((summary->'component_counts'->>'power_supplies')::int) as total_power_supplies,
                        SUM((summary->'component_counts'->>'modules')::int) as total_modules,
                        SUM((summary->'component_counts'->>'fex_units')::int) as total_fex_units
                    FROM comprehensive_device_inventory
                """)
                
                return dict(cursor.fetchone())
                
        except Exception as e:
            print(f"Error getting inventory stats: {e}")
            return None

def process_collection_file(file_path, db_manager):
    """Process a collection JSON file and store in database"""
    print(f"Processing collection file: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            collection_data = json.load(f)
        
        devices = collection_data.get('devices', [])
        print(f"Found {len(devices)} devices in collection file")
        
        successful_imports = 0
        failed_imports = 0
        
        for device in devices:
            if db_manager.store_device_inventory(device):
                successful_imports += 1
            else:
                failed_imports += 1
        
        print(f"Import complete: {successful_imports} successful, {failed_imports} failed")
        
        # Update inventory summary
        print("Updating inventory summary...")
        db_manager.update_inventory_summary()
        
        # Show stats
        stats = db_manager.get_inventory_stats()
        if stats:
            print("\nInventory Statistics:")
            print(f"  Total devices: {stats['total_devices']}")
            print(f"  Successful: {stats['successful_devices']}")
            print(f"  Failed: {stats['failed_devices']}")
            print(f"  Pending: {stats['pending_devices']}")
            print(f"  Total transceivers: {stats['total_transceivers']}")
            print(f"  Total power supplies: {stats['total_power_supplies']}")
            print(f"  Total modules: {stats['total_modules']}")
            print(f"  Total FEX units: {stats['total_fex_units']}")
        
        return True
        
    except Exception as e:
        print(f"Error processing collection file: {e}")
        return False

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SNMP Inventory Database Integration')
    parser.add_argument('--import-file', help='Import collection JSON file to database')
    parser.add_argument('--stats', action='store_true', help='Show inventory statistics')
    parser.add_argument('--update-summary', action='store_true', help='Update inventory summary table')
    
    args = parser.parse_args()
    
    db_manager = SNMPInventoryDB()
    
    try:
        if args.import_file:
            if not os.path.exists(args.import_file):
                print(f"File not found: {args.import_file}")
                sys.exit(1)
            
            process_collection_file(args.import_file, db_manager)
            
        elif args.stats:
            stats = db_manager.get_inventory_stats()
            if stats:
                print("Inventory Statistics:")
                for key, value in stats.items():
                    print(f"  {key.replace('_', ' ').title()}: {value}")
            
        elif args.update_summary:
            db_manager.update_inventory_summary()
            
        else:
            parser.print_help()
            
    finally:
        db_manager.close_db()

if __name__ == "__main__":
    main()