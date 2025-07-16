#!/usr/bin/env python3
"""
Corporate Network Data from Database with SNMP Integration for Tab 4
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime, date
import os

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'database': os.environ.get('DB_NAME', 'dsrcircuits'),
    'user': os.environ.get('DB_USER', 'dsruser'),
    'password': os.environ.get('DB_PASSWORD', 'dsruser'),
    'port': os.environ.get('DB_PORT', '5432')
}

def get_comprehensive_datacenter_inventory_db():
    """Get comprehensive datacenter inventory including SNMP collected data"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # First get the SSH collected inventory (existing logic)
        cursor.execute("""
            SELECT site, hostname, vendor, mgmt_ip, device_type, model, 
                   software_version, serial_number,
                   announcement_date, end_of_sale, end_of_support
            FROM netdisco_devices
            WHERE mgmt_ip IS NOT NULL
            ORDER BY site, hostname
        """)
        ssh_devices = cursor.fetchall()
        
        # Get chassis blades and hardware components for SSH devices
        cursor.execute("""
            SELECT nd.hostname, nd.mgmt_ip, cb.module_number, cb.ports, 
                   cb.card_type, cb.model, cb.serial_number
            FROM netdisco_devices nd
            JOIN chassis_blades cb ON nd.id = cb.device_id
            ORDER BY nd.hostname, 
                CASE 
                    WHEN cb.module_number ~ '^[0-9]+$' THEN CAST(cb.module_number AS INTEGER)
                    ELSE 999
                END, cb.module_number
        """)
        chassis_blades = cursor.fetchall()
        
        cursor.execute("""
            SELECT nd.hostname, nd.mgmt_ip, hc.name, hc.description, 
                   hc.pid, hc.vid, hc.serial_number, hc.component_type
            FROM netdisco_devices nd
            JOIN hardware_components hc ON nd.id = hc.device_id
            ORDER BY nd.hostname, hc.name
        """)
        hardware_components = cursor.fetchall()
        
        cursor.execute("""
            SELECT nd.hostname, nd.mgmt_ip, sm.interface, sm.module_type, 
                   sm.status, sm.product_id
            FROM netdisco_devices nd
            JOIN sfp_modules sm ON nd.id = sm.device_id
            ORDER BY nd.hostname, sm.interface
        """)
        sfp_modules = cursor.fetchall()
        
        # Now get SNMP collected inventory data
        cursor.execute("""
            SELECT 
                hostname,
                ip_address,
                collection_timestamp,
                system_info->>'detected_model' as model,
                system_info->>'software_version' as software_version,
                system_info->>'system_description' as system_description,
                system_info->>'collection_method' as collection_method,
                physical_components,
                summary->'component_counts' as component_counts,
                summary->>'status' as status
            FROM comprehensive_device_inventory
            WHERE summary->>'status' = 'success'
            ORDER BY hostname
        """)
        snmp_devices = cursor.fetchall()
        
        # Process SSH devices first (existing logic)
        devices_dict = {}
        
        for device in ssh_devices:
            hostname = device['hostname']
            mgmt_ip = device['mgmt_ip']
            
            if hostname not in devices_dict:
                devices_dict[hostname] = {
                    'master': {
                        'site': device['site'],
                        'hostname': hostname,
                        'vendor': device['vendor'],
                        'mgmt_ip': mgmt_ip,
                        'device_type': device['device_type'],
                        'model': device['model'],
                        'software_version': device['software_version'],
                        'serial_number': device['serial_number'],
                        'announcement_date': str(device['announcement_date']) if device['announcement_date'] else '',
                        'end_of_sale': str(device['end_of_sale']) if device['end_of_sale'] else '',
                        'end_of_support': str(device['end_of_support']) if device['end_of_support'] else '',
                        'collection_method': 'SSH'
                    },
                    'modules': []
                }
        
        # Add SSH collected modules
        for blade in chassis_blades:
            hostname = blade['hostname']
            if hostname in devices_dict:
                devices_dict[hostname]['modules'].append({
                    'type': 'Chassis Blade',
                    'module_number': blade['module_number'],
                    'ports': blade['ports'],
                    'description': blade['card_type'],
                    'model': blade['model'],
                    'serial_number': blade['serial_number']
                })
        
        for component in hardware_components:
            hostname = component['hostname']
            if hostname in devices_dict:
                devices_dict[hostname]['modules'].append({
                    'type': component['component_type'] or 'Hardware Component',
                    'interface': component['name'],
                    'description': component['description'],
                    'pid': component['pid'],
                    'vid': component['vid'],
                    'serial_number': component['serial_number']
                })
        
        for sfp in sfp_modules:
            hostname = sfp['hostname']
            if hostname in devices_dict:
                devices_dict[hostname]['modules'].append({
                    'type': 'SFP Module',
                    'interface': sfp['interface'],
                    'module_type': sfp['module_type'],
                    'status': sfp['status'],
                    'product_id': sfp['product_id']
                })
        
        # Add SNMP collected devices
        for device in snmp_devices:
            hostname = device['hostname']
            
            # Skip if already collected via SSH
            if hostname in devices_dict:
                continue
                
            # Create master device entry
            devices_dict[hostname] = {
                'master': {
                    'site': 'SNMP Collection',  # No site info in SNMP data
                    'hostname': hostname,
                    'vendor': 'Cisco',  # Most are Cisco based on data
                    'mgmt_ip': str(device['ip_address']),
                    'device_type': device['model'] or 'Network Device',
                    'model': device['model'] or '',
                    'software_version': device['software_version'] or '',
                    'serial_number': '',  # Will be populated from components
                    'announcement_date': '',
                    'end_of_sale': '',
                    'end_of_support': '',
                    'collection_method': device['collection_method'] or 'SNMP',
                    'system_description': device['system_description'] or ''
                },
                'modules': []
            }
            
            # Process physical components from SNMP data
            if device['physical_components']:
                components = device['physical_components']
                
                # Extract chassis serial number if available
                if components.get('chassis'):
                    for chassis in components['chassis']:
                        if chassis.get('serial_number'):
                            devices_dict[hostname]['master']['serial_number'] = chassis['serial_number']
                            break
                
                # Add modules/blades
                if components.get('modules'):
                    for module in components['modules']:
                        if module.get('serial_number'):  # Only show modules with serial numbers
                            devices_dict[hostname]['modules'].append({
                                'type': 'Module',
                                'name': module.get('name', ''),
                                'description': module.get('description', ''),
                                'model': module.get('model_name', ''),
                                'serial_number': module.get('serial_number', '')
                            })
                
                # Add FEX units
                if components.get('fex_units'):
                    for fex in components['fex_units']:
                        if fex.get('serial_number'):
                            devices_dict[hostname]['modules'].append({
                                'type': 'FEX',
                                'name': fex.get('name', ''),
                                'description': fex.get('description', ''),
                                'model': fex.get('model_name', ''),
                                'serial_number': fex.get('serial_number', '')
                            })
                
                # Add transceivers (SFPs)
                if components.get('transceivers'):
                    for transceiver in components['transceivers']:
                        if transceiver.get('serial_number'):
                            devices_dict[hostname]['modules'].append({
                                'type': 'Transceiver',
                                'name': transceiver.get('name', ''),
                                'description': transceiver.get('description', ''),
                                'model': transceiver.get('model_name', ''),
                                'serial_number': transceiver.get('serial_number', '')
                            })
                
                # Add power supplies
                if components.get('power_supplies'):
                    for ps in components['power_supplies']:
                        if ps.get('serial_number'):
                            devices_dict[hostname]['modules'].append({
                                'type': 'Power Supply',
                                'name': ps.get('name', ''),
                                'description': ps.get('description', ''),
                                'model': ps.get('model_name', ''),
                                'serial_number': ps.get('serial_number', '')
                            })
        
        # Convert to list and calculate summary
        inventory_list = []
        total_devices = 0
        total_modules = 0
        ssh_devices_count = 0
        snmp_devices_count = 0
        
        for hostname, device_data in devices_dict.items():
            # Add master device
            inventory_list.append({
                'is_master': True,
                'level': 0,
                'hostname': device_data['master']['hostname'],
                'vendor': device_data['master']['vendor'],
                'mgmt_ip': device_data['master']['mgmt_ip'],
                'device_type': device_data['master']['device_type'],
                'model': device_data['master']['model'],
                'software_version': device_data['master']['software_version'],
                'serial_number': device_data['master']['serial_number'],
                'announcement_date': device_data['master']['announcement_date'],
                'end_of_sale': device_data['master']['end_of_sale'],
                'end_of_support': device_data['master']['end_of_support'],
                'collection_method': device_data['master']['collection_method'],
                'module_count': len(device_data['modules'])
            })
            total_devices += 1
            
            if device_data['master']['collection_method'] == 'SSH':
                ssh_devices_count += 1
            else:
                snmp_devices_count += 1
            
            # Add modules under the master
            for module in device_data['modules']:
                module_entry = {
                    'is_master': False,
                    'level': 1,
                    'hostname': f"  └─ {module.get('type', 'Module')}",
                    'vendor': '',
                    'mgmt_ip': module.get('interface', module.get('module_number', '')),
                    'device_type': module.get('type', ''),
                    'model': module.get('model', module.get('pid', module.get('product_id', ''))),
                    'software_version': module.get('vid', ''),
                    'serial_number': module.get('serial_number', ''),
                    'announcement_date': '',
                    'end_of_sale': '',
                    'end_of_support': '',
                    'description': module.get('description', module.get('module_type', ''))
                }
                inventory_list.append(module_entry)
                total_modules += 1
        
        # Sort inventory list
        inventory_list.sort(key=lambda x: (x['hostname'].lower() if x['is_master'] else ''))
        
        # Get total counts from database for summary
        cursor.execute("""
            SELECT COUNT(*) FROM netdisco_devices WHERE mgmt_ip IS NOT NULL
        """)
        ssh_total = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT COUNT(*) FROM comprehensive_device_inventory WHERE summary->>'status' = 'success'
        """)
        snmp_total = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM chassis_blades")
        total_chassis_blades = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM hardware_components")
        total_hardware_components = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM sfp_modules")
        total_sfp_modules = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT 
                SUM((summary->'component_counts'->>'modules')::int) as modules,
                SUM((summary->'component_counts'->>'transceivers')::int) as transceivers,
                SUM((summary->'component_counts'->>'power_supplies')::int) as power_supplies,
                SUM((summary->'component_counts'->>'fex_units')::int) as fex_units
            FROM comprehensive_device_inventory 
            WHERE summary->>'status' = 'success'
        """)
        snmp_components = cursor.fetchone()
        
        conn.close()
        
        return {
            'inventory': inventory_list,
            'summary': {
                'total_devices': total_devices,
                'ssh_devices': ssh_devices_count,
                'snmp_devices': snmp_devices_count,
                'total_modules': total_modules,
                'total_chassis_blades': total_chassis_blades,
                'total_hardware_components': total_hardware_components,
                'total_sfp_modules': total_sfp_modules,
                'snmp_modules': snmp_components['modules'] or 0,
                'snmp_transceivers': snmp_components['transceivers'] or 0,
                'snmp_power_supplies': snmp_components['power_supplies'] or 0,
                'snmp_fex_units': snmp_components['fex_units'] or 0,
                'collection_methods': {
                    'SSH': ssh_devices_count,
                    'SNMP': snmp_devices_count
                }
            }
        }
        
    except Exception as e:
        print(f"Error getting comprehensive datacenter inventory: {e}")
        import traceback
        traceback.print_exc()
        return {'inventory': [], 'summary': {}}
    finally:
        if conn:
            conn.close()

# Keep all other existing functions unchanged
def get_corp_executive_summary_db():
    """Get corporate network executive summary from database"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get device counts by type
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT CASE WHEN vendor ILIKE '%cisco%' AND model ILIKE '%nexus%' THEN hostname END) as nexus_switches,
                COUNT(DISTINCT CASE WHEN vendor ILIKE '%cisco%' AND model ILIKE '%catalyst%' THEN hostname END) as catalyst_switches,
                COUNT(DISTINCT CASE WHEN vendor ILIKE '%cisco%' AND (model ILIKE '%asr%' OR model ILIKE '%isr%') THEN hostname END) as routers,
                COUNT(DISTINCT CASE WHEN vendor ILIKE '%cisco%' AND model ILIKE '%asa%' THEN hostname END) as firewalls,
                COUNT(DISTINCT hostname) as total_devices
            FROM netdisco_devices
            WHERE mgmt_ip IS NOT NULL
        """)
        
        device_counts = cursor.fetchone()
        
        # Get model summary
        cursor.execute("""
            SELECT model, COUNT(*) as count,
                   MIN(announcement_date) as announcement_date,
                   MIN(end_of_sale) as end_of_sale,
                   MIN(end_of_support) as end_of_support
            FROM netdisco_devices
            WHERE mgmt_ip IS NOT NULL AND model IS NOT NULL
            GROUP BY model
            ORDER BY count DESC
        """)
        
        models = cursor.fetchall()
        
        # Calculate EOL summary
        today = date.today()
        eol_summary = {
            'total_devices': device_counts['total_devices'],
            'end_of_life': 0,
            'end_of_sale': 0,
            'active': 0
        }
        
        for model in models:
            if model['end_of_support'] and model['end_of_support'] <= today:
                eol_summary['end_of_life'] += model['count']
            elif model['end_of_sale'] and model['end_of_sale'] <= today:
                eol_summary['end_of_sale'] += model['count']
            else:
                eol_summary['active'] += model['count']
        
        # Calculate percentages
        if eol_summary['total_devices'] > 0:
            eol_summary['eol_percentage'] = round((eol_summary['end_of_life'] / eol_summary['total_devices']) * 100, 1)
            eol_summary['eos_percentage'] = round((eol_summary['end_of_sale'] / eol_summary['total_devices']) * 100, 1)
            eol_summary['active_percentage'] = round((eol_summary['active'] / eol_summary['total_devices']) * 100, 1)
        else:
            eol_summary['eol_percentage'] = 0
            eol_summary['eos_percentage'] = 0
            eol_summary['active_percentage'] = 0
        
        conn.close()
        
        return {
            'device_counts': device_counts,
            'models': models,
            'overall': eol_summary,
            'by_device_type': []  # This would need more complex logic
        }
        
    except Exception as e:
        print(f"Error getting corp executive summary: {e}")
        return {
            'device_counts': {},
            'models': [],
            'overall': {},
            'by_device_type': []
        }
    finally:
        if conn:
            conn.close()

def get_datacenter_inventory_with_eol_db():
    """Get datacenter inventory with EOL data from database"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT site, hostname, vendor, mgmt_ip, device_type, model, 
                   software_version, serial_number,
                   announcement_date, end_of_sale, end_of_support
            FROM netdisco_devices
            WHERE mgmt_ip IS NOT NULL
            ORDER BY site, hostname
        """)
        
        devices = cursor.fetchall()
        
        # Format dates
        for device in devices:
            for date_field in ['announcement_date', 'end_of_sale', 'end_of_support']:
                if device[date_field]:
                    device[date_field] = str(device[date_field])
                else:
                    device[date_field] = ''
        
        conn.close()
        
        return {
            'devices': devices,
            'total_count': len(devices)
        }
        
    except Exception as e:
        print(f"Error getting datacenter inventory: {e}")
        return {'devices': [], 'total_count': 0}
    finally:
        if conn:
            conn.close()

def get_collected_inventory_db():
    """Get collected inventory from SSH collections database (Tabs 6&7)"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get all collected inventory items with device info
        cursor.execute("""
            SELECT 
                nd.hostname,
                nd.mgmt_ip as ip,
                cb.module_number,
                cb.ports,
                cb.card_type,
                cb.model,
                cb.serial_number,
                'chassis_blade' as component_type
            FROM netdisco_devices nd
            JOIN chassis_blades cb ON nd.id = cb.device_id
            
            UNION ALL
            
            SELECT 
                nd.hostname,
                nd.mgmt_ip as ip,
                hc.name as module_number,
                '' as ports,
                hc.description as card_type,
                hc.pid as model,
                hc.serial_number,
                'hardware_component' as component_type
            FROM netdisco_devices nd
            JOIN hardware_components hc ON nd.id = hc.device_id
            
            UNION ALL
            
            SELECT 
                nd.hostname,
                nd.mgmt_ip as ip,
                sm.interface as module_number,
                '' as ports,
                sm.module_type as card_type,
                sm.product_id as model,
                '' as serial_number,
                'sfp_module' as component_type
            FROM netdisco_devices nd
            JOIN sfp_modules sm ON nd.id = sm.device_id
            
            ORDER BY hostname, component_type, module_number
        """)
        
        inventory = cursor.fetchall()
        
        # Get summary counts
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM chassis_blades) as chassis_blades,
                (SELECT COUNT(*) FROM hardware_components) as hardware_components,
                (SELECT COUNT(*) FROM sfp_modules) as sfp_modules,
                (SELECT COUNT(DISTINCT device_id) FROM chassis_blades
                 UNION SELECT device_id FROM hardware_components
                 UNION SELECT device_id FROM sfp_modules) as total_devices
        """)
        
        summary = cursor.fetchone()
        
        conn.close()
        
        return {
            'inventory': inventory,
            'summary': summary
        }
        
    except Exception as e:
        print(f"Error getting collected inventory: {e}")
        import traceback
        traceback.print_exc()
        return {'inventory': [], 'summary': {}}
    finally:
        if conn:
            conn.close()