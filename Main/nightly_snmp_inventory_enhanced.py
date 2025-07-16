#!/usr/bin/env python3
"""
Enhanced Nightly SNMP Inventory Collection Script
Includes FEX model extraction and SFP identification
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

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InventoryEnhancer:
    """Handles model identification enhancements"""
    
    def __init__(self):
        # FEX patterns for model extraction
        self.fex_patterns = {
            r'48x1GE.*4x10GE.*N2K-C2248TP': 'N2K-C2248TP-1GE',
            r'32x10GE.*8x10GE.*N2K-C2232PP': 'N2K-C2232PP-10GE',
            r'16x10GE.*8x10GE.*N2K-B22': 'N2K-B22DELL-P',
            r'48x1GE.*4x10GE.*N2K-C2148T': 'N2K-C2148T-1GE',
            r'48x1GE.*4x10GE': 'N2K-C2248TP-1GE',  # Default for 48x1G
            r'32x10GE.*8x10GE': 'N2K-C2232PP-10GE', # Default for 32x10G
            r'16x10GE.*8x10GE': 'N2K-B22DELL-P',    # Default for 16x10G
        }
        
        # SFP description to model mapping
        self.sfp_description_map = {
            '1000BaseSX SFP': 'GLC-SX-MMD',
            '1000BaseLX SFP': 'GLC-LX-SMD',
            '10/100/1000BaseTX SFP': 'GLC-T',
            '1000BaseT SFP': 'GLC-T',
            'SFP-10Gbase-SR': 'SFP-10G-SR',
            'SFP-10Gbase-LR': 'SFP-10G-LR',
            'SFP+ 10GBASE-SR': 'SFP-10G-SR',
            'SFP+ 10GBASE-LR': 'SFP-10G-LR',
        }
        
        # SFP vendor identification by serial prefix
        self.sfp_vendor_patterns = {
            'AGM': 'Avago',
            'AGS': 'Avago',
            'FNS': 'Finisar',
            'OPM': 'OptoSpan',
            'AVD': 'Avago',
            'ECL': 'Eoptolink',
            'MTC': 'MikroTik',
        }
    
    def extract_fex_model(self, description: str, current_model: str) -> str:
        """Extract actual FEX model from description"""
        if '-N2K-' in current_model:
            match = re.search(r'(N2K-[A-Z0-9\-]+)', current_model)
            if match:
                return match.group(1)
        
        full_text = f"{description} {current_model}"
        
        for pattern, model in self.fex_patterns.items():
            if re.search(pattern, full_text, re.IGNORECASE):
                return model
        
        if 'Fabric Extender' in description:
            port_match = re.search(r'(\d+x\d+G[BE].*\d+x\d+G[BE])', description)
            if port_match:
                return f"FEX-{port_match.group(1)}"
        
        return current_model
    
    def identify_sfp_model(self, description: str, model_name: str, serial_number: str) -> Tuple[str, Optional[str]]:
        """Identify SFP model and vendor"""
        if model_name and model_name not in ['Unspecified', '""', '']:
            return model_name, None
        
        serial = serial_number.strip()
        
        # Identify vendor from serial prefix
        vendor = None
        for prefix, vendor_name in self.sfp_vendor_patterns.items():
            if serial.startswith(prefix):
                vendor = vendor_name
                break
        
        # Map description to standard model
        for desc_pattern, model in self.sfp_description_map.items():
            if desc_pattern.lower() in description.lower():
                return model, vendor
        
        # Try to extract from description
        if 'sfp' in description.lower():
            if '10g' in description.lower():
                if 'sr' in description.lower():
                    return 'SFP-10G-SR', vendor
                elif 'lr' in description.lower():
                    return 'SFP-10G-LR', vendor
            elif '1g' in description.lower() or '1000' in description:
                if 'sx' in description.lower():
                    return 'GLC-SX-MMD', vendor
                elif 'lx' in description.lower():
                    return 'GLC-LX-SMD', vendor
                elif 'tx' in description.lower() or 'baset' in description.lower():
                    return 'GLC-T', vendor
        
        return model_name, vendor

class SNMPInventoryCollector:
    """Enhanced SNMP inventory collector with model identification"""
    
    def __init__(self):
        self.enhancer = InventoryEnhancer()
        self.entity_oids = {
            'description': '1.3.6.1.2.1.47.1.1.1.1.2',
            'class': '1.3.6.1.2.1.47.1.1.1.1.5',
            'name': '1.3.6.1.2.1.47.1.1.1.1.7',
            'model_name': '1.3.6.1.2.1.47.1.1.1.1.13',
            'serial_number': '1.3.6.1.2.1.47.1.1.1.1.11',
            'parent_relative_pos': '1.3.6.1.2.1.47.1.1.1.1.6',
            'contained_in': '1.3.6.1.2.1.47.1.1.1.1.4'
        }
    
    def get_snmp_credentials(self, device_name: str) -> Dict[str, Any]:
        """Get SNMP credentials from database"""
        conn = get_db_connection()
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
        """Determine if entity is a physical component worth tracking"""
        entity_class = entity.get('class', '')
        model = entity.get('model_name', '').strip()
        serial = entity.get('serial_number', '').strip()
        
        # Must have model and serial
        if not model or model == '""' or not serial or serial == '""':
            return False
        
        # Entity class filters
        if entity_class == '8':  # Sensors
            return False
        if entity_class == '10' and 'sensor' in entity.get('description', '').lower():
            return False
        
        # Description filters
        desc_lower = entity.get('description', '').lower()
        skip_keywords = ['sensor', 'empty', 'blank', 'temperature', 'voltage', 'current draw']
        if any(keyword in desc_lower for keyword in skip_keywords):
            return False
        
        return True
    
    def process_entity_data(self, entity_data: Dict[str, Dict]) -> Dict[str, List[Dict]]:
        """Process raw entity data into structured physical inventory"""
        physical_inventory = {
            'chassis': [],
            'modules': [],
            'power_supplies': [],
            'fans': [],
            'transceivers': []
        }
        
        # Build parent-child relationships
        parent_map = {}
        for entity_id, entity in entity_data.items():
            parent_id = entity.get('contained_in', '0')
            if parent_id not in parent_map:
                parent_map[parent_id] = []
            parent_map[parent_id].append((entity_id, entity))
        
        # Process entities
        for entity_id, entity in entity_data.items():
            if not self.is_physical_component(entity):
                continue
            
            entity_class = entity.get('class', '')
            description = entity.get('description', '')
            model = entity.get('model_name', '').strip()
            
            # Create component entry
            component = {
                'name': entity.get('name', ''),
                'description': description,
                'model': model,
                'serial': entity.get('serial_number', '').strip(),
                'entity_id': entity_id
            }
            
            # Chassis (class 3)
            if entity_class == '3':
                # Check if it's a FEX
                if 'Fabric Extender' in description or 'Fabric Extender' in model:
                    component['model'] = self.enhancer.extract_fex_model(description, model)
                physical_inventory['chassis'].append(component)
            
            # Modules (class 9)
            elif entity_class == '9':
                # Check if it's a FEX module
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
                # Enhance SFP identification
                enhanced_model, vendor = self.enhancer.identify_sfp_model(
                    description, model, component['serial']
                )
                component['model'] = enhanced_model
                if vendor:
                    component['vendor'] = vendor
                physical_inventory['transceivers'].append(component)
        
        # Sort chassis by entity ID to maintain stack order
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
            
            # Collect entity data
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
            
            # Process into physical inventory
            physical_inventory = self.process_entity_data(entity_data)
            
            # Create summary
            summary = {
                'chassis_count': len(physical_inventory['chassis']),
                'module_count': len(physical_inventory['modules']),
                'transceiver_count': len(physical_inventory['transceivers']),
                'collection_time': datetime.now().isoformat()
            }
            
            # Add model/serial lists for quick reference
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
    
    def store_to_database(self, device_data: Dict):
        """Store enhanced inventory data to database"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Store in comprehensive_device_inventory table
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
            logger.info(f"Stored inventory for {device_data['device_name']}")
            
        except Exception as e:
            logger.error(f"Database error for {device_data['device_name']}: {str(e)}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

def main():
    """Main execution function"""
    logger.info("Starting enhanced SNMP inventory collection")
    
    # Get device list from database
    conn = get_db_connection()
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
    
    # Process devices in parallel
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
                    collector.store_to_database(result)
                    success_count += 1
            except Exception as e:
                logger.error(f"Failed to process {device[0]}: {str(e)}")
    
    logger.info(f"Collection complete. Successfully processed {success_count}/{len(devices)} devices")
    
    # Save summary file
    summary_file = f"/var/www/html/network-data/nightly_snmp_enhanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w') as f:
        json.dump({
            'collection_time': datetime.now().isoformat(),
            'total_devices': len(devices),
            'successful_collections': success_count,
            'enhancements': {
                'fex_model_extraction': True,
                'sfp_identification': True,
                'stack_support': True
            }
        }, f, indent=2)
    
    logger.info(f"Summary saved to {summary_file}")

if __name__ == "__main__":
    main()