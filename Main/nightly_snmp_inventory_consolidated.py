#!/usr/bin/env python3
"""
Enhanced Nightly SNMP Inventory Collection with VDC Consolidation
- Consolidates Nexus 7K VDCs into single device entries
- Removes duplicate serials across devices
- Enhances FEX and SFP model identification
"""
import json
import re
import psycopg2
from psycopg2.extras import Json
from datetime import datetime
import concurrent.futures
from pysnmp.hlapi import *
import sys
import os
import logging
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InventoryEnhancer:
    """Handles all inventory enhancements"""
    
    def __init__(self):
        # FEX patterns
        self.fex_patterns = {
            r'48x1GE.*4x10GE.*N2K-C2248TP': 'N2K-C2248TP-1GE',
            r'32x10GE.*8x10GE.*N2K-C2232PP': 'N2K-C2232PP-10GE',
            r'16x10GE.*8x10GE.*N2K-B22': 'N2K-B22DELL-P',
            r'48x1GE.*4x10GE': 'N2K-C2248TP-1GE',
            r'32x10GE.*8x10GE': 'N2K-C2232PP-10GE',
            r'16x10GE.*8x10GE': 'N2K-B22DELL-P',
        }
        
        # SFP mappings
        self.sfp_description_map = {
            '1000BaseSX SFP': 'GLC-SX-MMD',
            '1000BaseLX SFP': 'GLC-LX-SMD',
            '10/100/1000BaseTX SFP': 'GLC-T',
            '1000BaseT SFP': 'GLC-T',
            'SFP-10Gbase-SR': 'SFP-10G-SR',
            'SFP-10Gbase-LR': 'SFP-10G-LR',
        }
        
        self.sfp_vendor_patterns = {
            'AGM': 'Avago',
            'AGS': 'Avago',
            'FNS': 'Finisar',
            'MTC': 'MikroTik',
        }
    
    def extract_fex_model(self, description: str, current_model: str) -> str:
        """Extract FEX model from description"""
        if '-N2K-' in current_model:
            match = re.search(r'(N2K-[A-Z0-9\-]+)', current_model)
            if match:
                return match.group(1)
        
        full_text = f"{description} {current_model}"
        
        for pattern, model in self.fex_patterns.items():
            if re.search(pattern, full_text, re.IGNORECASE):
                return model
        
        if 'Nexus2232' in description:
            return 'N2K-C2232PP-10GE'
        elif 'Nexus2248' in description:
            return 'N2K-C2248TP-1GE'
        elif 'Nexus2200DELL' in description:
            return 'N2K-B22DELL-P'
        
        return current_model
    
    def identify_sfp_model(self, description: str, model_name: str, serial_number: str) -> Tuple[str, Optional[str]]:
        """Identify SFP model and vendor"""
        if model_name and model_name not in ['Unspecified', '""', '']:
            return model_name, None
        
        serial = serial_number.strip()
        vendor = None
        
        for prefix, vendor_name in self.sfp_vendor_patterns.items():
            if serial.startswith(prefix):
                vendor = vendor_name
                break
        
        for desc_pattern, model in self.sfp_description_map.items():
            if desc_pattern.lower() in description.lower():
                return model, vendor
        
        return model_name, vendor

class VDCConsolidator:
    """Handles VDC consolidation logic"""
    
    def consolidate_devices(self, devices: List[Dict]) -> List[Dict]:
        """Consolidate VDC devices into single entries"""
        logger.info(f"Starting VDC consolidation for {len(devices)} devices")
        
        # Group devices by base name
        device_groups = defaultdict(list)
        standalone_devices = []
        
        for device in devices:
            hostname = device['device_name']
            
            # Check if this is a 7K VDC device
            if '7000' in hostname and any(vdc in hostname for vdc in ['CORE', 'ADMIN', 'EDGE', 'PCI']):
                base_match = re.match(r'(.*-7000-\d+)', hostname)
                if base_match:
                    base_name = base_match.group(1)
                    device_groups[base_name].append(device)
                else:
                    standalone_devices.append(device)
            else:
                standalone_devices.append(device)
        
        logger.info(f"Found {len(device_groups)} 7K device groups with VDCs")
        
        # Consolidate each VDC group
        consolidated_devices = []
        
        for base_name, vdc_devices in device_groups.items():
            # Find CORE VDC or use first
            core_device = next((d for d in vdc_devices if 'CORE' in d['device_name']), vdc_devices[0])
            
            # Collect all unique components by serial
            all_components = defaultdict(dict)
            vdc_names = []
            
            for device in vdc_devices:
                vdc_names.append(device['device_name'])
                physical_inv = device['physical_inventory']
                
                for comp_type in ['chassis', 'modules', 'power_supplies', 'fans', 'transceivers']:
                    for component in physical_inv.get(comp_type, []):
                        serial = component.get('serial', '').strip()
                        if serial and serial not in all_components[comp_type]:
                            all_components[comp_type][serial] = component
            
            # Build consolidated device
            consolidated_physical_inv = {}
            for comp_type, components in all_components.items():
                consolidated_physical_inv[comp_type] = list(components.values())
            
            # Update core device
            core_device['physical_inventory'] = consolidated_physical_inv
            core_device['summary']['consolidated_vdcs'] = vdc_names
            core_device['summary']['vdc_count'] = len(vdc_names)
            
            # Extract VDC types
            vdc_types = set()
            for vdc in vdc_names:
                if '-ADMIN' in vdc:
                    vdc_types.add('ADMIN')
                elif '-CORE' in vdc:
                    vdc_types.add('CORE')
                elif '-EDGE' in vdc:
                    vdc_types.add('EDGE')
                elif '-PCI' in vdc:
                    vdc_types.add('PCI')
            
            core_device['summary']['vdc_types'] = list(vdc_types)
            
            consolidated_devices.append(core_device)
            
            logger.info(f"Consolidated {base_name}: {len(vdc_names)} VDCs -> 1 device")
        
        # Add standalone devices
        consolidated_devices.extend(standalone_devices)
        
        return consolidated_devices

class SNMPInventoryCollector:
    """Main SNMP collection class with all enhancements"""
    
    def __init__(self):
        self.enhancer = InventoryEnhancer()
        self.consolidator = VDCConsolidator()
        self.entity_oids = {
            'description': '1.3.6.1.2.1.47.1.1.1.1.2',
            'class': '1.3.6.1.2.1.47.1.1.1.1.5',
            'name': '1.3.6.1.2.1.47.1.1.1.1.7',
            'model_name': '1.3.6.1.2.1.47.1.1.1.1.13',
            'serial_number': '1.3.6.1.2.1.47.1.1.1.1.11',
            'parent_relative_pos': '1.3.6.1.2.1.47.1.1.1.1.6',
            'contained_in': '1.3.6.1.2.1.47.1.1.1.1.4'
        }
        
        # Track global serials for deduplication
        self.global_serials = {}
    
    def get_snmp_credentials(self, device_name: str) -> Dict[str, Any]:
        """Get SNMP credentials from database"""
        conn = psycopg2.connect(
            host="localhost",
            database="network_inventory",
            user="postgres",
            password="postgres"
        )
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT snmp_version, snmp_community, 
                       snmpv3_username, snmpv3_auth_password, 
                       snmpv3_priv_password, snmpv3_auth_protocol,
                       snmpv3_priv_protocol
                FROM snmp_credentials 
                WHERE device_name = %s
            """, (device_name,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'version': result[0],
                    'community': result[1],
                    'username': result[2],
                    'auth_password': result[3],
                    'priv_password': result[4],
                    'auth_protocol': result[5],
                    'priv_protocol': result[6]
                }
        finally:
            cursor.close()
            conn.close()
        
        return None
    
    def is_physical_component(self, entity: Dict[str, str]) -> bool:
        """Determine if entity is a physical component"""
        entity_class = entity.get('class', '')
        model = entity.get('model_name', '').strip()
        serial = entity.get('serial_number', '').strip()
        
        if not model or model == '""' or not serial or serial == '""':
            return False
        
        if entity_class == '8':  # Sensors
            return False
        if entity_class == '10' and 'sensor' in entity.get('description', '').lower():
            return False
        
        desc_lower = entity.get('description', '').lower()
        skip_keywords = ['sensor', 'empty', 'blank', 'temperature', 'voltage']
        if any(keyword in desc_lower for keyword in skip_keywords):
            return False
        
        return True
    
    def process_entity_data(self, entity_data: Dict[str, Dict]) -> Dict[str, List[Dict]]:
        """Process raw entity data with enhancements"""
        physical_inventory = {
            'chassis': [],
            'modules': [],
            'power_supplies': [],
            'fans': [],
            'transceivers': []
        }
        
        for entity_id, entity in entity_data.items():
            if not self.is_physical_component(entity):
                continue
            
            entity_class = entity.get('class', '')
            description = entity.get('description', '')
            model = entity.get('model_name', '').strip()
            
            component = {
                'name': entity.get('name', ''),
                'description': description,
                'model': model,
                'serial': entity.get('serial_number', '').strip(),
                'entity_id': entity_id
            }
            
            # Chassis (class 3)
            if entity_class == '3':
                if 'Fabric Extender' in description or 'Fabric Extender' in model:
                    component['model'] = self.enhancer.extract_fex_model(description, model)
                physical_inventory['chassis'].append(component)
            
            # Modules (class 9)
            elif entity_class == '9':
                if 'Fabric Extender' in description or 'Fabric Extender' in model:
                    component['model'] = self.enhancer.extract_fex_model(description, model)
                physical_inventory['modules'].append(component)
            
            # Power supplies (class 6)
            elif entity_class == '6':
                physical_inventory['power_supplies'].append(component)
            
            # Fans (class 7)  
            elif entity_class == '7':
                physical_inventory['fans'].append(component)
            
            # Transceivers/SFPs (class 10)
            elif entity_class == '10' and ('sfp' in description.lower() or 
                                          'transceiver' in description.lower() or
                                          'base' in description.lower()):
                enhanced_model, vendor = self.enhancer.identify_sfp_model(
                    description, model, component['serial']
                )
                component['model'] = enhanced_model
                if vendor:
                    component['vendor'] = vendor
                physical_inventory['transceivers'].append(component)
        
        # Sort chassis by entity ID
        physical_inventory['chassis'].sort(key=lambda x: int(x['entity_id']))
        
        return physical_inventory
    
    def collect_device_inventory(self, device_name: str, ip_address: str) -> Optional[Dict]:
        """Collect inventory from a single device"""
        credentials = self.get_snmp_credentials(device_name)
        if not credentials:
            logger.warning(f"No SNMP credentials found for {device_name}")
            return None
        
        try:
            entity_data = {}
            
            # Collect entity data via SNMP
            for oid_name, base_oid in self.entity_oids.items():
                if credentials['version'] == 'v3':
                    iterator = bulkCmd(
                        SnmpEngine(),
                        UsmUserData(
                            credentials['username'],
                            credentials['auth_password'],
                            credentials['priv_password'],
                            authProtocol=getattr(usmHMACSHAAuthProtocol, 'HMACSHA256AuthProtocol', usmHMACSHAAuthProtocol),
                            privProtocol=usmAesCfb128Protocol
                        ),
                        UdpTransportTarget((ip_address, 161)),
                        ContextData(),
                        0, 25,
                        ObjectType(ObjectIdentity(base_oid))
                    )
                else:
                    iterator = bulkCmd(
                        SnmpEngine(),
                        CommunityData(credentials['community']),
                        UdpTransportTarget((ip_address, 161)),
                        ContextData(),
                        0, 25,
                        ObjectType(ObjectIdentity(base_oid))
                    )
                
                for errorIndication, errorStatus, errorIndex, varBinds in iterator:
                    if errorIndication or errorStatus:
                        break
                    
                    for varBind in varBinds:
                        oid_str = str(varBind[0])
                        if not oid_str.startswith(base_oid + '.'):
                            break
                        
                        entity_index = oid_str.split('.')[-1]
                        value = str(varBind[1])
                        
                        if entity_index not in entity_data:
                            entity_data[entity_index] = {}
                        entity_data[entity_index][oid_name] = value
            
            # Process with enhancements
            physical_inventory = self.process_entity_data(entity_data)
            
            # Create summary
            summary = {
                'chassis_count': len(physical_inventory['chassis']),
                'module_count': len(physical_inventory['modules']),
                'transceiver_count': len(physical_inventory['transceivers']),
                'collection_time': datetime.now().isoformat()
            }
            
            if physical_inventory['chassis']:
                summary['chassis_models'] = ', '.join(c['model'] for c in physical_inventory['chassis'])
                summary['chassis_serials'] = ', '.join(c['serial'] for c in physical_inventory['chassis'])
            
            return {
                'device_name': device_name,
                'ip_address': ip_address,
                'entity_data': entity_data,
                'physical_inventory': physical_inventory,
                'summary': summary,
                'collection_timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error collecting from {device_name}: {str(e)}")
            return None
    
    def remove_cross_device_duplicates(self, all_devices: List[Dict]) -> List[Dict]:
        """Remove duplicate serials across devices (for N5K FEX sharing)"""
        # Find all duplicate serials
        serial_to_devices = defaultdict(list)
        
        for device in all_devices:
            device_name = device['device_name']
            
            for comp_type in ['chassis', 'modules', 'transceivers']:
                for component in device['physical_inventory'].get(comp_type, []):
                    serial = component.get('serial', '').strip()
                    if serial:
                        serial_to_devices[serial].append({
                            'device': device_name,
                            'component': component
                        })
        
        # For each duplicate, assign to primary device
        duplicates_removed = 0
        
        for serial, occurrences in serial_to_devices.items():
            if len(occurrences) > 1:
                # Determine primary device (prefer -01)
                devices = [occ['device'] for occ in occurrences]
                primary = next((d for d in devices if '-01' in d), devices[0])
                
                # Mark components on non-primary devices for removal
                for occ in occurrences:
                    if occ['device'] != primary:
                        occ['component']['_remove'] = True
                        duplicates_removed += 1
        
        # Remove marked components
        for device in all_devices:
            for comp_type in ['chassis', 'modules', 'transceivers']:
                if comp_type in device['physical_inventory']:
                    device['physical_inventory'][comp_type] = [
                        c for c in device['physical_inventory'][comp_type]
                        if not c.get('_remove', False)
                    ]
        
        logger.info(f"Removed {duplicates_removed} duplicate components across devices")
        
        return all_devices
    
    def store_to_database(self, device_data: Dict):
        """Store enhanced inventory to database"""
        conn = psycopg2.connect(
            host="localhost",
            database="network_inventory",
            user="postgres",
            password="postgres"
        )
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO comprehensive_device_inventory 
                (device_name, ip_address, entity_data, physical_inventory, 
                 summary, collection_timestamp)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (device_name) DO UPDATE SET
                    ip_address = EXCLUDED.ip_address,
                    entity_data = EXCLUDED.entity_data,
                    physical_inventory = EXCLUDED.physical_inventory,
                    summary = EXCLUDED.summary,
                    collection_timestamp = EXCLUDED.collection_timestamp
            """, (
                device_data['device_name'],
                device_data['ip_address'],
                Json(device_data['entity_data']),
                Json(device_data['physical_inventory']),
                Json(device_data['summary']),
                device_data['collection_timestamp']
            ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Database error for {device_data['device_name']}: {str(e)}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    
    def update_web_format_table(self, all_devices: List[Dict]):
        """Update the web format table for display"""
        conn = psycopg2.connect(
            host="localhost",
            database="network_inventory",
            user="postgres",
            password="postgres"
        )
        cursor = conn.cursor()
        
        try:
            # Clear existing data
            cursor.execute("TRUNCATE TABLE inventory_web_format")
            
            # Insert consolidated data
            for device in all_devices:
                hostname = device['device_name']
                ip = device['ip_address']
                physical_inv = device['physical_inventory']
                
                # Get VDC info if available
                notes = ""
                if device.get('summary', {}).get('vdc_types'):
                    notes = f"VDCs: {', '.join(device['summary']['vdc_types'])}"
                
                # Insert chassis
                chassis_list = physical_inv.get('chassis', [])
                if chassis_list:
                    # Main chassis
                    main_chassis = chassis_list[0]
                    position = 'Standalone'
                    if len(chassis_list) > 1:
                        if 'N5K' in main_chassis['model'] or 'N56' in main_chassis['model']:
                            position = 'Parent Switch'
                        else:
                            position = 'Master'
                    
                    cursor.execute("""
                        INSERT INTO inventory_web_format 
                        (hostname, ip_address, position, model, serial_number, 
                         port_location, vendor, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        hostname,
                        str(ip),
                        position,
                        main_chassis['model'],
                        main_chassis['serial'],
                        '',
                        'Cisco' if position == 'Parent Switch' else '',
                        notes
                    ))
                    
                    # Additional chassis (FEX or stack members)
                    for i in range(1, len(chassis_list)):
                        chassis = chassis_list[i]
                        if 'Fex-' in chassis.get('name', ''):
                            fex_id = re.search(r'Fex-(\d+)', chassis['name'])
                            fex_num = fex_id.group(1) if fex_id else str(100 + i)
                            position = f'FEX-{fex_num}'
                        else:
                            position = 'Slave'
                        
                        cursor.execute("""
                            INSERT INTO inventory_web_format 
                            (hostname, ip_address, position, model, serial_number, 
                             port_location, vendor, notes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            '',
                            '',
                            position,
                            chassis['model'],
                            chassis['serial'],
                            chassis['name'],
                            'Cisco' if 'FEX' in position else '',
                            ''
                        ))
                
                # Insert modules (limited)
                module_count = 0
                for module in physical_inv.get('modules', []):
                    if module_count < 20:  # Limit modules per device
                        cursor.execute("""
                            INSERT INTO inventory_web_format 
                            (hostname, ip_address, position, model, serial_number, 
                             port_location, vendor, notes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            '',
                            '',
                            'Module',
                            module['model'],
                            module['serial'],
                            module['name'],
                            '',
                            ''
                        ))
                        module_count += 1
                
                # Insert SFPs (limited)
                sfp_count = 0
                for sfp in physical_inv.get('transceivers', []):
                    if sfp_count < 10:  # Limit SFPs per device
                        cursor.execute("""
                            INSERT INTO inventory_web_format 
                            (hostname, ip_address, position, model, serial_number, 
                             port_location, vendor, notes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            '',
                            '',
                            'SFP',
                            sfp.get('model', 'Unknown'),
                            sfp['serial'],
                            sfp['name'],
                            sfp.get('vendor', ''),
                            ''
                        ))
                        sfp_count += 1
            
            conn.commit()
            logger.info("Updated inventory_web_format table")
            
        except Exception as e:
            logger.error(f"Error updating web format table: {str(e)}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

def main():
    """Main execution function"""
    logger.info("Starting consolidated SNMP inventory collection")
    
    # Get device list
    conn = psycopg2.connect(
        host="localhost",
        database="network_inventory",
        user="postgres",
        password="postgres"
    )
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT device_name, ip_address 
        FROM snmp_credentials 
        WHERE snmp_enabled = true
        ORDER BY device_name
    """)
    
    devices = cursor.fetchall()
    cursor.close()
    conn.close()
    
    logger.info(f"Found {len(devices)} devices to collect from")
    
    # Initialize collector
    collector = SNMPInventoryCollector()
    
    # Collect from all devices
    all_device_data = []
    success_count = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_device = {
            executor.submit(collector.collect_device_inventory, device[0], device[1]): device
            for device in devices
        }
        
        for future in concurrent.futures.as_completed(future_to_device):
            device = future_to_device[future]
            try:
                result = future.result()
                if result:
                    all_device_data.append(result)
                    success_count += 1
            except Exception as e:
                logger.error(f"Failed to process {device[0]}: {str(e)}")
    
    logger.info(f"Collected from {success_count}/{len(devices)} devices")
    
    # Consolidate VDCs
    all_device_data = collector.consolidator.consolidate_devices(all_device_data)
    
    # Remove cross-device duplicates
    all_device_data = collector.remove_cross_device_duplicates(all_device_data)
    
    # Store to database
    for device_data in all_device_data:
        collector.store_to_database(device_data)
    
    # Update web format table
    collector.update_web_format_table(all_device_data)
    
    logger.info(f"Collection complete. Final device count: {len(all_device_data)}")
    
    # Save summary
    summary_file = f"/var/www/html/network-data/nightly_snmp_consolidated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w') as f:
        json.dump({
            'collection_time': datetime.now().isoformat(),
            'original_devices': len(devices),
            'consolidated_devices': len(all_device_data),
            'successful_collections': success_count,
            'features': {
                'vdc_consolidation': True,
                'duplicate_removal': True,
                'fex_enhancement': True,
                'sfp_identification': True
            }
        }, f, indent=2)
    
    logger.info(f"Summary saved to {summary_file}")

if __name__ == "__main__":
    main()