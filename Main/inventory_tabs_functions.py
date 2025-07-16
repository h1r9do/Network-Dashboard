# Additional functions for Tab 2 and Tab 4 support
import psycopg2
import os
import sys
sys.path.append('/usr/local/bin/Main')

def get_corp_network_summary():
    """Get corporate network summary data for Tab 2"""
    try:
        # For now, return placeholder data since netdisco_devices table doesn't exist
        # This would normally fetch from your corporate network data source
        return {
            'status': 'success',
            'data': {
                'device_counts': {
                    'nexus_switches': 0,
                    'catalyst_switches': 0,
                    'routers': 0,
                    'firewalls': 0,
                    'total_devices': 0
                },
                'overall': {
                    'end_of_life': 0,
                    'end_of_sale': 0,
                    'active': 0,
                    'eol_percentage': 0,
                    'eos_percentage': 0,
                    'active_percentage': 0
                },
                'models': [],
                'by_device_type': [],
                'datacenter_alerts': {
                    'has_critical_risks': False,
                    'critical_risks': []
                },
                'critical_insights': {
                    'immediate_action': [],
                    'critical_years': [],
                    'major_refreshes': [],
                    'budget_planning': []
                }
            }
        }
    except Exception as e:
        print(f"Error getting corp network summary: {e}")
        return {'status': 'error', 'error': str(e)}

def get_datacenter_inventory():
    """Get datacenter inventory data for Tab 4"""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    try:
        # Database configuration
        DB_CONFIG = {
            'host': 'localhost',
            'database': 'dsrcircuits',
            'user': 'dsruser',
            'password': 'dsruser',
            'port': '5432'
        }
        
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        inventory = []
        
        # Get all data from inventory_web_format with EOL data from corporate_eol table
        cursor.execute("""
            SELECT i.site, i.hostname, i.parent_hostname, i.relationship, i.ip_address, i.position, 
                   i.model, i.serial_number, i.port_location, i.vendor, i.notes, i.row_order,
                   COALESCE(i.announcement_date, c.announcement_date) as end_of_sale,
                   COALESCE(i.end_of_support, c.end_of_support_date) as end_of_support,
                   c.end_of_sale_date as corporate_eos_date
            FROM inventory_web_format i
            LEFT JOIN corporate_eol c ON (
                -- Direct model match
                c.model = i.model 
                OR 
                -- Extract FEX model from descriptive text (e.g., "N2K-C2232PP-10GE" from "Fabric Extender Module: 32x10GE, 8x10GE-N2K-C2232PP-10GE")
                (i.model LIKE '%N2K-%' AND c.model = SUBSTRING(i.model FROM 'N2K-[A-Z0-9-]+'))
                OR
                -- Extract other Cisco models from descriptive text
                (i.model LIKE '%-%' AND c.model = SUBSTRING(i.model FROM '[A-Z0-9]+-[A-Z0-9-]+$'))
            )
            ORDER BY i.id
        """)
        
        all_rows = cursor.fetchall()
        
        # Process rows to create hierarchical structure
        current_parent = None
        for row in all_rows:
            # Check if this is a master/parent device
            # Master devices have hostname but empty parent_hostname (CSV structure)
            if row['hostname'] and not row['parent_hostname']:
                # This is a master device
                current_parent = row['hostname']
                inventory.append({
                    'site': row['site'] or '',
                    'hostname': row['hostname'] or '',
                    'parent_hostname': row['parent_hostname'] or '',
                    'relationship': row['relationship'] or '',
                    'ip_address': row['ip_address'] or '',
                    'position': row['position'] or '',
                    'model': row['model'] or '',
                    'serial_number': row['serial_number'] or '',
                    'port_location': row['port_location'] or '',
                    'vendor': row['vendor'] or '',
                    'notes': row['notes'] or '',
                    'end_of_sale': str(row['corporate_eos_date'] or row['end_of_sale']) if (row['corporate_eos_date'] or row['end_of_sale']) else '',
                    'end_of_support': str(row['end_of_support']) if row['end_of_support'] else ''
                })
            else:
                # This is a component - no hostname, but has parent_hostname
                inventory.append({
                    'site': row['site'] or '',
                    'hostname': '',  # Components don't have their own hostname
                    'parent_hostname': row['parent_hostname'] or '',
                    'relationship': row['relationship'] or '',
                    'ip_address': row['ip_address'] or '',
                    'position': row['position'] or '',
                    'model': row['model'] or '',
                    'serial_number': row['serial_number'] or '',
                    'port_location': row['port_location'] or '',
                    'vendor': row['vendor'] or '',
                    'notes': row['notes'] or '',
                    'end_of_sale': str(row['corporate_eos_date'] or row['end_of_sale']) if (row['corporate_eos_date'] or row['end_of_sale']) else '',
                    'end_of_support': str(row['end_of_support']) if row['end_of_support'] else ''
                })
        
        # Get counts
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT CASE WHEN hostname = parent_hostname THEN hostname END) as total_devices,
                COUNT(CASE WHEN hostname != parent_hostname OR hostname IS NULL THEN 1 END) as total_components,
                COUNT(*) as total_rows
            FROM inventory_web_format
        """)
        
        counts = cursor.fetchone()
        
        # No additional SNMP devices - only CSV data
        snmp_count = 0
        
        cursor.close()
        conn.close()
        
        return {
            'summary': {
                'total_rows': len(inventory),
                'total_devices': counts['total_devices'] + snmp_count,
                'total_components': counts['total_components'],
                'ssh_devices': counts['total_devices'],
                'snmp_devices': snmp_count,
                'total_modules': counts['total_components']
            },
            'inventory': inventory
        }
        
    except Exception as e:
        print(f"Error getting datacenter inventory: {e}")
        import traceback
        traceback.print_exc()
        return {'summary': {'total_rows': 0}, 'inventory': []}