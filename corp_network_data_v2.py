#!/usr/bin/env python3
"""
Corporate Network Data Functions - Excel Based (Row 62+ only)
"""
import pandas as pd
from datetime import datetime, date
from collections import defaultdict

def parse_date(date_str):
    """Parse various date formats from Excel"""
    if pd.isna(date_str) or date_str == '' or str(date_str).strip() == '' or str(date_str) == '-':
        return None
    
    date_str = str(date_str).strip()
    
    # Handle datetime objects
    if isinstance(date_str, pd.Timestamp):
        return date_str.date()
    
    # Handle "Not publicly available"
    if 'not publicly available' in date_str.lower():
        return None
    
    # Try parsing string formats
    try:
        # If it's already a datetime string from pandas
        if ' ' in date_str and ':' in date_str:
            return pd.to_datetime(date_str).date()
        
        # Try different date formats
        formats = [
            '%b %d, %Y',    # Oct 24, 2015
            '%B %d, %Y',    # October 24, 2015
            '%m/%d/%Y',     # 10/24/2015
            '%Y-%m-%d',     # 2015-10-24
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
    except:
        pass
    
    return None

def get_device_type_from_model(model, category=None):
    """Determine device type from model name and category"""
    if not model:
        return 'Unknown'
    
    model = str(model).upper()
    
    # Use category hints if available
    if category:
        category = str(category).upper()
        if 'ROUTER' in category or 'WAN' in category:
            return 'Router'
        elif 'SWITCH' in category:
            return 'Switch'
        elif 'FIREWALL' in category:
            return 'Firewall'
    
    # Model-based detection
    if any(pattern in model for pattern in ['ASR', 'ISR', 'C1000']):
        return 'Router'
    elif any(pattern in model for pattern in ['WS-', 'C3750', 'C3560', 'C2960', 'N2K', 'N5K', 'N7K', 'N9K', 'C9410']):
        return 'Switch'
    elif any(pattern in model for pattern in ['PA-', 'ASA', 'FPR']):
        return 'Firewall'
    
    return 'Other'

def generate_corp_critical_insights(processed_data, by_device_type, eol_timeline, today):
    """Generate critical insights for corporate network"""
    insights = {
        'immediate_action': [],
        'critical_years': [],
        'major_refreshes': [],
        'budget_planning': []
    }
    
    # Immediate action - devices already EOL
    eol_devices = [d for d in processed_data if d['status'] == 'EOL']
    if eol_devices:
        total_eol = sum(d['total_devices'] for d in eol_devices)
        insights['immediate_action'].append({
            'message': f'{total_eol} devices across {len(eol_devices)} models are past End-of-Support and pose security/operational risks',
            'priority': 'HIGHEST'
        })
        
        # Check for critical EOL devices
        critical_eol = [d for d in eol_devices if d['device_type'] in ['Router', 'Firewall', 'Switch'] and d['total_devices'] >= 5]
        if critical_eol:
            for device in critical_eol[:3]:  # Top 3
                insights['immediate_action'].append({
                    'message': f'{device["total_devices"]} {device["model"]} {device["device_type"]}s - EOL since {device["end_of_support"].strftime("%Y-%m-%d")}',
                    'priority': 'CRITICAL'
                })
    
    # Critical years analysis
    current_year = today.year
    for year_data in eol_timeline:
        if year_data['year'] >= current_year and year_data['year'] <= current_year + 2:
            if year_data['total_devices'] >= 20:
                insights['critical_years'].append({
                    'message': f'{year_data["year"]}: {year_data["total_devices"]} devices reaching EOL - Plan replacement budget',
                    'priority': 'HIGH'
                })
    
    # Major device refreshes needed
    for dt in by_device_type:
        if dt['end_of_life'] >= 3 or dt['end_of_sale'] >= 5:
            refresh_needed = dt['end_of_life'] + dt['end_of_sale']
            percent_affected = round((refresh_needed / dt['model_count'] * 100) if dt['model_count'] > 0 else 0)
            insights['major_refreshes'].append({
                'message': f'{dt["device_type"]}: {refresh_needed} models ({percent_affected}%) require refresh - {dt["total_devices"]} devices',
                'priority': 'MODERATE'
            })
    
    # Budget planning
    eos_devices = [d for d in processed_data if d['status'] == 'EOS']
    if eos_devices:
        total_eos = sum(d['total_devices'] for d in eos_devices)
        insights['budget_planning'].append({
            'message': f'{total_eos} devices are End-of-Sale but still supported - Plan phased replacement',
            'priority': 'MODERATE'
        })
    
    # Data center specific risks
    dc_switches = [d for d in processed_data if 'N7K' in d['model'] or 'N5K' in d['model'] or 'N9K' in d['model']]
    if dc_switches:
        eol_dc = [d for d in dc_switches if d['status'] in ['EOL', 'EOS']]
        if eol_dc:
            total_dc = sum(d['total_devices'] for d in eol_dc)
            insights['budget_planning'].append({
                'message': f'{total_dc} data center core switches approaching/past EOL - Critical infrastructure at risk',
                'priority': 'HIGHEST'
            })
    
    return insights

def generate_datacenter_alerts(processed_data, today):
    """Generate datacenter-specific security and operational alerts"""
    
    # Find critical datacenter infrastructure
    nexus_switches = [d for d in processed_data if any(x in d['model'] for x in ['N7K', 'N5K', 'N9K'])]
    firewalls = [d for d in processed_data if d['device_type'] == 'Firewall']
    routers = [d for d in processed_data if d['device_type'] == 'Router']
    
    # Calculate EOL statistics for critical infrastructure
    nexus_eol = sum(d['total_devices'] for d in nexus_switches if d['status'] == 'EOL')
    nexus_eos = sum(d['total_devices'] for d in nexus_switches if d['status'] == 'EOS')
    nexus_total = sum(d['total_devices'] for d in nexus_switches)
    
    firewall_eol = sum(d['total_devices'] for d in firewalls if d['status'] == 'EOL')
    firewall_total = sum(d['total_devices'] for d in firewalls)
    
    # Find specific critical models
    n7k_devices = next((d for d in processed_data if d['model'] == 'N7K-C7010'), None)
    
    return {
        'nexus_stats': {
            'total': nexus_total,
            'eol': nexus_eol,
            'eos': nexus_eos,
            'eol_percentage': round((nexus_eol / nexus_total * 100) if nexus_total > 0 else 0),
            'critical_model': 'N7K-C7010 (16 devices)' if n7k_devices else None
        },
        'firewall_stats': {
            'total': firewall_total,
            'eol': firewall_eol,
            'models_affected': len([d for d in firewalls if d['status'] in ['EOL', 'EOS']])
        },
        'has_critical_risks': nexus_eol > 0 or firewall_eol > 0
    }

def get_corp_executive_summary():
    """Generate executive summary for corporate network from Excel row 62+"""
    try:
        # Read EOL data
        eol_df = pd.read_excel('/var/www/html/meraki-data/Discount Tire Network Inventory.xlsx', 
                              sheet_name='End of LIfe Summary Counts')
        
        # Get only corporate data (row 62 onwards)
        corp_df = eol_df.iloc[61:].copy()  # Row 62 in Excel = index 61
        
        # Clean data - remove rows without model
        corp_df = corp_df[corp_df['Model'].notna()]
        
        # Process data
        today = date.today()
        processed_data = []
        
        for _, row in corp_df.iterrows():
            model = row.get('Model')
            total = row.get('Total', 0) if not pd.isna(row.get('Total')) else 0
            if total <= 0:
                continue
                
            category = row.get('Unnamed: 0', '')  # Category column
            end_of_sale = parse_date(row.get('End of Sale Date'))
            end_of_support = parse_date(row.get('End of Support Date'))
            device_type = get_device_type_from_model(model, category)
            
            # Determine status
            status = 'Active'
            if end_of_support and end_of_support <= today:
                status = 'EOL'
            elif end_of_sale and end_of_sale <= today:
                status = 'EOS'
            
            processed_data.append({
                'model': model,
                'total_devices': total,
                'device_type': device_type,
                'category': category if not pd.isna(category) else '',
                'end_of_sale': end_of_sale,
                'end_of_support': end_of_support,
                'status': status
            })
        
        # Calculate overall stats
        total_models = len(processed_data)
        total_devices = sum(item['total_devices'] for item in processed_data)
        eol_models = sum(1 for item in processed_data if item['status'] == 'EOL')
        eos_models = sum(1 for item in processed_data if item['status'] == 'EOS')
        active_models = total_models - eol_models - eos_models
        
        eol_devices = sum(item['total_devices'] for item in processed_data if item['status'] == 'EOL')
        eos_devices = sum(item['total_devices'] for item in processed_data if item['status'] == 'EOS')
        active_devices = total_devices - eol_devices - eos_devices
        
        # By device type summary
        device_type_stats = defaultdict(lambda: {'models': 0, 'devices': 0, 'eol': 0, 'eos': 0, 'active': 0})
        
        for item in processed_data:
            dt = item['device_type']
            device_type_stats[dt]['models'] += 1
            device_type_stats[dt]['devices'] += item['total_devices']
            
            if item['status'] == 'EOL':
                device_type_stats[dt]['eol'] += 1
            elif item['status'] == 'EOS':
                device_type_stats[dt]['eos'] += 1
            else:
                device_type_stats[dt]['active'] += 1
        
        by_device_type = []
        for device_type, stats in device_type_stats.items():
            total_models = stats['models']
            by_device_type.append({
                'device_type': device_type,
                'total_devices': stats['devices'],
                'model_count': total_models,
                'active': stats['active'],
                'end_of_sale': stats['eos'],
                'end_of_life': stats['eol'],
                'active_percentage': round((stats['active'] / total_models * 100) if total_models > 0 else 0),
                'eos_percentage': round((stats['eos'] / total_models * 100) if total_models > 0 else 0),
                'eol_percentage': round((stats['eol'] / total_models * 100) if total_models > 0 else 0)
            })
        
        # Sort by total devices
        by_device_type.sort(key=lambda x: x['total_devices'], reverse=True)
        
        # EOL Timeline
        timeline_data = defaultdict(lambda: {'total_devices': 0, 'by_device_type': defaultdict(int)})
        current_year = today.year
        
        for item in processed_data:
            if item['end_of_support']:
                year = item['end_of_support'].year
                timeline_data[year]['total_devices'] += item['total_devices']
                timeline_data[year]['by_device_type'][item['device_type']] += item['total_devices']
        
        eol_timeline = []
        for year in sorted(timeline_data.keys()):
            eol_timeline.append({
                'year': year,
                'total_devices': timeline_data[year]['total_devices'],
                'by_device_type': dict(timeline_data[year]['by_device_type']),
                'is_past': year < current_year,
                'is_current': year == current_year
            })
        
        # Generate critical insights for corporate network
        critical_insights = generate_corp_critical_insights(processed_data, by_device_type, eol_timeline, today)
        
        # Generate datacenter-specific alerts
        datacenter_alerts = generate_datacenter_alerts(processed_data, today)
        
        return {
            'overall': {
                'total_models': total_models,
                'total_devices': total_devices,
                'active': active_models,
                'end_of_sale': eos_models,
                'end_of_life': eol_models,
                'active_percentage': round((active_models / total_models * 100) if total_models > 0 else 0),
                'eos_percentage': round((eos_models / total_models * 100) if total_models > 0 else 0),
                'eol_percentage': round((eol_models / total_models * 100) if total_models > 0 else 0),
                'active_devices': active_devices,
                'eos_devices': eos_devices,
                'eol_devices': eol_devices
            },
            'by_device_type': by_device_type,
            'eol_timeline': eol_timeline,
            'models_data': processed_data,
            'critical_insights': critical_insights,
            'datacenter_alerts': datacenter_alerts
        }
        
    except Exception as e:
        print(f"❌ Error generating corp executive summary: {e}")
        return {'overall': {}, 'by_device_type': [], 'eol_timeline': [], 'models_data': []}

def get_datacenter_inventory_with_eol():
    """Get All Data Centers inventory with EOL dates merged"""
    try:
        # Read All Data Centers sheet
        dc_df = pd.read_excel('/var/www/html/meraki-data/Discount Tire Network Inventory.xlsx', 
                             sheet_name='All Data Centers')
        
        # Read EOL data (corporate only - row 62+)
        eol_df = pd.read_excel('/var/www/html/meraki-data/Discount Tire Network Inventory.xlsx', 
                              sheet_name='End of LIfe Summary Counts')
        corp_eol = eol_df.iloc[61:].copy()
        corp_eol = corp_eol[corp_eol['Model'].notna()]
        
        # Create EOL lookup dictionary
        eol_lookup = {}
        for _, row in corp_eol.iterrows():
            model = row['Model']
            eol_lookup[model] = {
                'end_of_sale': parse_date(row.get('End of Sale Date')),
                'end_of_support': parse_date(row.get('End of Support Date')),
                'announcement': parse_date(row.get('Announcement Date'))
            }
        
        # Process datacenter inventory
        inventory = []
        for _, row in dc_df.iterrows():
            site = row.get('Site', '') if not pd.isna(row.get('Site')) else ''
            hostname = row.get('Hostname', '') if not pd.isna(row.get('Hostname')) else ''
            vendor = row.get('Vendor', '') if not pd.isna(row.get('Vendor')) else ''
            mgmt_ip = row.get('Mgmt IP', '') if not pd.isna(row.get('Mgmt IP')) else ''
            device_type = row.get('Device Type', '') if not pd.isna(row.get('Device Type')) else ''
            model = row.get('Model', '') if not pd.isna(row.get('Model')) else ''
            software = row.get('Software Version', '') if not pd.isna(row.get('Software Version')) else ''
            serial = row.get('Serial Number', '') if not pd.isna(row.get('Serial Number')) else ''
            
            # Skip empty rows
            if not any([hostname, model, serial]):
                continue
            
            # Get EOL dates if available
            eol_info = eol_lookup.get(model, {})
            
            inventory.append({
                'site': site,
                'hostname': hostname,
                'vendor': vendor,
                'mgmt_ip': mgmt_ip,
                'device_type': device_type,
                'model': model,
                'software_version': software,
                'serial_number': serial,
                'end_of_sale': eol_info.get('end_of_sale'),
                'end_of_support': eol_info.get('end_of_support'),
                'announcement_date': eol_info.get('announcement')
            })
        
        # Calculate summary stats
        total_devices = len(inventory)
        unique_models = len(set(item['model'] for item in inventory if item['model']))
        unique_sites = len(set(item['site'] for item in inventory if item['site']))
        
        # Count EOL status
        today = date.today()
        eol_count = sum(1 for item in inventory if item['end_of_support'] and item['end_of_support'] <= today)
        eos_count = sum(1 for item in inventory if item['end_of_sale'] and item['end_of_sale'] <= today 
                       and (not item['end_of_support'] or item['end_of_support'] > today))
        active_count = total_devices - eol_count - eos_count
        
        return {
            'inventory': inventory,
            'summary': {
                'total_devices': total_devices,
                'unique_models': unique_models,
                'unique_sites': unique_sites,
                'eol_devices': eol_count,
                'eos_devices': eos_count,
                'active_devices': active_count
            }
        }
        
    except Exception as e:
        print(f"❌ Error getting datacenter inventory: {e}")
        return {'inventory': [], 'summary': {}}

if __name__ == '__main__':
    print("🏢 Testing Corporate Network Data Functions (Row 62+ only)...")
    
    print("\n📊 Executive Summary Test:")
    summary = get_corp_executive_summary()
    print(f"  Total Models: {summary['overall'].get('total_models', 0)}")
    print(f"  Total Devices: {summary['overall'].get('total_devices', 0)}")
    print(f"  EOL Models: {summary['overall'].get('end_of_life', 0)}")
    print(f"  Device Types: {len(summary['by_device_type'])}")
    for dt in summary['by_device_type']:
        print(f"    {dt['device_type']}: {dt['total_devices']} devices")
    
    print("\n🏢 Data Center Inventory Test:")
    dc_data = get_datacenter_inventory_with_eol()
    print(f"  Total Devices: {dc_data['summary']['total_devices']}")
    print(f"  Unique Models: {dc_data['summary']['unique_models']}")
    print(f"  EOL Devices: {dc_data['summary']['eol_devices']}")
    print(f"  Active Devices: {dc_data['summary']['active_devices']}")