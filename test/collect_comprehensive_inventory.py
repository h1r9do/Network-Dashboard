#!/usr/bin/env python3
"""
Collect comprehensive inventory from all devices using connection information
"""

import json
import paramiko
import psycopg2
import time
import re
import logging
from datetime import datetime
from pysnmp.hlapi import *

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsrpass123'
}

class InventoryCollector:
    def __init__(self, connection_file):
        """Initialize with connection information"""
        with open(connection_file, 'r') as f:
            self.connection_info = json.load(f)
        
        self.collected_inventory = {
            'collection_date': datetime.now().isoformat(),
            'devices': {}
        }
    
    def collect_ssh_inventory(self, hostname, ip, username, password):
        """Collect comprehensive inventory via SSH"""
        inventory = {
            'chassis': [],
            'modules': [],
            'power_supplies': [],
            'fans': [],
            'interfaces': [],
            'sfps': [],
            'fex_modules': []
        }
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Handle username@ip format
            if '@' not in username:
                connect_username = username
            else:
                connect_username = f"{username}@{ip}"
            
            ssh.connect(
                hostname=ip,
                username=connect_username,
                password=password,
                timeout=10,
                allow_agent=False,
                look_for_keys=False
            )
            
            # Determine device type and run appropriate commands
            commands = self._get_inventory_commands(hostname)
            
            for cmd_info in commands:
                cmd = cmd_info['command']
                parser = cmd_info['parser']
                
                try:
                    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
                    output = stdout.read().decode('utf-8', errors='ignore')
                    
                    # Parse output based on command type
                    parsed_data = parser(output, hostname)
                    
                    # Merge parsed data into inventory
                    for key, value in parsed_data.items():
                        if isinstance(value, list):
                            inventory[key].extend(value)
                        else:
                            inventory[key] = value
                            
                except Exception as e:
                    logging.warning(f"Error running command '{cmd}' on {hostname}: {e}")
            
            ssh.close()
            return True, inventory
            
        except Exception as e:
            logging.error(f"SSH collection failed for {hostname}: {e}")
            return False, inventory
    
    def _get_inventory_commands(self, hostname):
        """Get appropriate inventory commands based on device type"""
        commands = []
        
        # Cisco Nexus commands
        if '5000' in hostname or '5K' in hostname or '7000' in hostname or '7K' in hostname:
            commands = [
                {
                    'command': 'show inventory',
                    'parser': self._parse_nexus_inventory
                },
                {
                    'command': 'show module',
                    'parser': self._parse_nexus_modules
                },
                {
                    'command': 'show interface transceiver',
                    'parser': self._parse_nexus_transceivers
                },
                {
                    'command': 'show fex',
                    'parser': self._parse_nexus_fex
                },
                {
                    'command': 'show fex detail',
                    'parser': self._parse_nexus_fex_detail
                }
            ]
        
        # Cisco ASA/Firewall commands
        elif 'ASA' in hostname or 'FW' in hostname:
            commands = [
                {
                    'command': 'show inventory',
                    'parser': self._parse_cisco_inventory
                },
                {
                    'command': 'show module',
                    'parser': self._parse_asa_modules
                }
            ]
        
        # Generic Cisco commands
        else:
            commands = [
                {
                    'command': 'show inventory',
                    'parser': self._parse_cisco_inventory
                },
                {
                    'command': 'show module',
                    'parser': self._parse_cisco_modules
                },
                {
                    'command': 'show interfaces transceiver',
                    'parser': self._parse_cisco_transceivers
                }
            ]
        
        return commands
    
    def _parse_nexus_inventory(self, output, hostname):
        """Parse Nexus show inventory output"""
        inventory = {
            'chassis': [],
            'modules': [],
            'power_supplies': [],
            'fans': []
        }
        
        current_item = None
        
        for line in output.split('\n'):
            line = line.strip()
            
            if line.startswith('NAME:'):
                # Extract name, description
                name_match = re.search(r'NAME:\s+"([^"]+)"', line)
                desc_match = re.search(r'DESCR:\s+"([^"]+)"', line)
                
                if name_match:
                    current_item = {
                        'name': name_match.group(1),
                        'description': desc_match.group(1) if desc_match else '',
                        'hostname': hostname
                    }
            
            elif line.startswith('PID:') and current_item:
                # Extract PID, VID, SN
                pid_match = re.search(r'PID:\s+(\S+)', line)
                vid_match = re.search(r'VID:\s+(\S+)', line)
                sn_match = re.search(r'SN:\s+(\S+)', line)
                
                if pid_match:
                    current_item['pid'] = pid_match.group(1)
                    current_item['vid'] = vid_match.group(1) if vid_match else ''
                    current_item['serial_number'] = sn_match.group(1) if sn_match else ''
                    
                    # Categorize based on name/description
                    if 'Chassis' in current_item['name'] or 'chassis' in current_item['description'].lower():
                        inventory['chassis'].append(current_item)
                    elif 'Module' in current_item['name'] or 'module' in current_item['description'].lower():
                        inventory['modules'].append(current_item)
                    elif 'Power' in current_item['name'] or 'power' in current_item['description'].lower():
                        inventory['power_supplies'].append(current_item)
                    elif 'Fan' in current_item['name'] or 'fan' in current_item['description'].lower():
                        inventory['fans'].append(current_item)
                    
                    current_item = None
        
        return inventory
    
    def _parse_nexus_modules(self, output, hostname):
        """Parse Nexus show module output"""
        modules = []
        
        in_module_section = False
        for line in output.split('\n'):
            line = line.strip()
            
            # Look for module section
            if 'Mod' in line and 'Ports' in line:
                in_module_section = True
                continue
            
            if in_module_section and line and not line.startswith('-'):
                parts = line.split()
                if len(parts) >= 4 and parts[0].isdigit():
                    module = {
                        'module_number': parts[0],
                        'ports': parts[1],
                        'module_type': parts[2],
                        'model': parts[3] if len(parts) > 3 else '',
                        'status': parts[4] if len(parts) > 4 else '',
                        'hostname': hostname
                    }
                    modules.append(module)
        
        return {'modules': modules}
    
    def _parse_nexus_transceivers(self, output, hostname):
        """Parse Nexus transceiver information"""
        sfps = []
        
        current_interface = None
        for line in output.split('\n'):
            if line.startswith('Ethernet') or line.startswith('fc'):
                current_interface = line.split()[0]
            elif current_interface and 'transceiver is present' in line:
                sfp = {'interface': current_interface, 'hostname': hostname}
            elif current_interface and line.strip():
                # Parse SFP details
                if 'type is' in line:
                    sfp['type'] = line.split('type is')[-1].strip()
                elif 'name is' in line:
                    sfp['vendor'] = line.split('name is')[-1].strip()
                elif 'part number is' in line:
                    sfp['part_number'] = line.split('part number is')[-1].strip()
                elif 'serial number is' in line:
                    sfp['serial_number'] = line.split('serial number is')[-1].strip()
                    sfps.append(sfp)
                    current_interface = None
        
        return {'sfps': sfps}
    
    def _parse_nexus_fex(self, output, hostname):
        """Parse Nexus FEX information"""
        fex_modules = []
        
        for line in output.split('\n'):
            if 'FEX' in line and 'Online' in line:
                parts = line.split()
                if len(parts) >= 4:
                    fex = {
                        'fex_number': parts[0],
                        'description': parts[1],
                        'state': parts[2],
                        'model': parts[3] if len(parts) > 3 else '',
                        'hostname': hostname,
                        'parent_hostname': hostname  # Parent Nexus 5K
                    }
                    fex_modules.append(fex)
        
        return {'fex_modules': fex_modules}
    
    def _parse_nexus_fex_detail(self, output, hostname):
        """Parse detailed Nexus FEX information"""
        fex_details = []
        
        current_fex = None
        for line in output.split('\n'):
            if line.startswith('FEX:'):
                if current_fex:
                    fex_details.append(current_fex)
                
                fex_num = line.split()[1]
                current_fex = {
                    'fex_number': fex_num,
                    'parent_hostname': hostname
                }
            elif current_fex:
                if 'Description:' in line:
                    current_fex['description'] = line.split('Description:')[-1].strip()
                elif 'state:' in line:
                    current_fex['state'] = line.split('state:')[-1].strip()
                elif 'Model:' in line:
                    current_fex['model'] = line.split('Model:')[-1].strip()
                elif 'Serial number:' in line:
                    current_fex['serial_number'] = line.split('Serial number:')[-1].strip()
                elif 'Extender Serial:' in line:
                    current_fex['extender_serial'] = line.split('Extender Serial:')[-1].strip()
        
        if current_fex:
            fex_details.append(current_fex)
        
        return {'fex_modules': fex_details}
    
    def _parse_cisco_inventory(self, output, hostname):
        """Parse generic Cisco inventory"""
        return self._parse_nexus_inventory(output, hostname)  # Similar format
    
    def _parse_cisco_modules(self, output, hostname):
        """Parse generic Cisco modules"""
        modules = []
        
        # Simple parsing for now
        for line in output.split('\n'):
            if 'Module' in line or 'Slot' in line:
                # Parse module info
                pass
        
        return {'modules': modules}
    
    def _parse_cisco_transceivers(self, output, hostname):
        """Parse generic Cisco transceivers"""
        return self._parse_nexus_transceivers(output, hostname)  # Similar format
    
    def _parse_asa_modules(self, output, hostname):
        """Parse ASA module information"""
        modules = []
        
        # ASA specific parsing
        for line in output.split('\n'):
            if 'Module' in line or 'slot' in line.lower():
                # Parse ASA module info
                pass
        
        return {'modules': modules}
    
    def collect_all_inventory(self):
        """Collect inventory from all devices"""
        devices = self.connection_info.get('devices', {})
        
        total = len(devices)
        success_count = 0
        
        for i, (hostname, device_info) in enumerate(devices.items()):
            logging.info(f"[{i+1}/{total}] Collecting inventory from {hostname}")
            
            # Find working SSH connection
            ssh_connection = None
            for conn in device_info.get('connections', []):
                if conn['method'] == 'ssh' and conn['status'] == 'success':
                    ssh_connection = conn
                    break
            
            if ssh_connection:
                success, inventory = self.collect_ssh_inventory(
                    hostname,
                    device_info['ip'],
                    ssh_connection['username'],
                    ssh_connection['password']
                )
                
                if success:
                    success_count += 1
                    self.collected_inventory['devices'][hostname] = {
                        'ip': device_info['ip'],
                        'collection_method': 'ssh',
                        'collection_time': datetime.now().isoformat(),
                        'inventory': inventory
                    }
                    logging.info(f"  ✅ Collected inventory via SSH")
                else:
                    logging.warning(f"  ❌ Failed to collect inventory")
            else:
                logging.warning(f"  ⚠️  No SSH connection available")
            
            # Be nice to devices
            if i < total - 1:
                time.sleep(1)
        
        # Summary
        self.collected_inventory['summary'] = {
            'total_devices': total,
            'successful_collections': success_count,
            'success_rate': round((success_count / total * 100), 2) if total else 0
        }
        
        logging.info(f"\n📊 Collection Summary:")
        logging.info(f"   Total devices: {total}")
        logging.info(f"   Successful: {success_count}")
        logging.info(f"   Success rate: {self.collected_inventory['summary']['success_rate']}%")
        
        return self.collected_inventory
    
    def save_to_database(self):
        """Save collected inventory to database"""
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        try:
            # Create collection record
            cursor.execute("""
                INSERT INTO inventory_collections 
                (collection_date, total_devices, successful_devices, collection_type)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (
                datetime.now(),
                self.collected_inventory['summary']['total_devices'],
                self.collected_inventory['summary']['successful_collections'],
                'comprehensive'
            ))
            
            collection_id = cursor.fetchone()[0]
            
            # Process each device
            for hostname, device_data in self.collected_inventory['devices'].items():
                inventory = device_data['inventory']
                
                # Save chassis info
                for chassis in inventory.get('chassis', []):
                    cursor.execute("""
                        INSERT INTO collected_chassis 
                        (collection_id, hostname, name, description, pid, serial_number)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        collection_id,
                        hostname,
                        chassis.get('name'),
                        chassis.get('description'),
                        chassis.get('pid'),
                        chassis.get('serial_number')
                    ))
                
                # Save modules
                for module in inventory.get('modules', []):
                    cursor.execute("""
                        INSERT INTO collected_modules
                        (collection_id, hostname, module_name, module_type, model, 
                         serial_number, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        collection_id,
                        hostname,
                        module.get('name'),
                        module.get('module_type'),
                        module.get('model'),
                        module.get('serial_number'),
                        module.get('status')
                    ))
                
                # Save SFPs
                for sfp in inventory.get('sfps', []):
                    cursor.execute("""
                        INSERT INTO collected_sfps
                        (collection_id, hostname, interface, sfp_type, vendor, 
                         part_number, serial_number)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        collection_id,
                        hostname,
                        sfp.get('interface'),
                        sfp.get('type'),
                        sfp.get('vendor'),
                        sfp.get('part_number'),
                        sfp.get('serial_number')
                    ))
                
                # Save FEX modules
                for fex in inventory.get('fex_modules', []):
                    cursor.execute("""
                        INSERT INTO collected_fex_modules
                        (collection_id, parent_hostname, fex_number, description, 
                         model, serial_number, state)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        collection_id,
                        hostname,
                        fex.get('fex_number'),
                        fex.get('description'),
                        fex.get('model'),
                        fex.get('serial_number'),
                        fex.get('state')
                    ))
            
            conn.commit()
            logging.info(f"✅ Saved inventory to database (collection_id: {collection_id})")
            
            return collection_id
            
        except Exception as e:
            logging.error(f"Database save failed: {e}")
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()
    
    def save_to_json(self, filename):
        """Save collected inventory to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.collected_inventory, f, indent=2)
        logging.info(f"✅ Saved inventory to {filename}")


def main():
    """Main execution"""
    import sys
    
    # Determine which connection file to use
    if len(sys.argv) > 1:
        connection_file = sys.argv[1]
    else:
        # Check for existing connection files
        import os
        if os.path.exists('/var/www/html/meraki-data/device_connections_with_snmp.json'):
            connection_file = '/var/www/html/meraki-data/device_connections_with_snmp.json'
        elif os.path.exists('/var/www/html/meraki-data/device_connections.json'):
            connection_file = '/var/www/html/meraki-data/device_connections.json'
        else:
            logging.error("No connection file found. Run test_all_connections.py first.")
            sys.exit(1)
    
    logging.info(f"Using connection file: {connection_file}")
    
    # Create collector
    collector = InventoryCollector(connection_file)
    
    # Collect inventory
    collector.collect_all_inventory()
    
    # Save results
    output_file = '/var/www/html/meraki-data/comprehensive_inventory_collected.json'
    collector.save_to_json(output_file)
    
    # Save to database
    try:
        collection_id = collector.save_to_database()
        logging.info(f"✅ Inventory collection complete! Collection ID: {collection_id}")
    except Exception as e:
        logging.error(f"Failed to save to database: {e}")


if __name__ == "__main__":
    main()