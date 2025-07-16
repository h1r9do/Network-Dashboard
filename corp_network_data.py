#!/usr/bin/env python3
"""
Corporate Network Data Functions - Excel Based
"""
import pandas as pd
from datetime import datetime, date
from collections import defaultdict, Counter

def parse_date(date_str):
    """Parse various date formats from Excel"""
    if pd.isna(date_str) or date_str == '' or str(date_str).strip() == '':
        return None
    
    date_str = str(date_str).strip()
    
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
    
    return None

def get_device_type_from_model(model):
    """Determine device type from model name"""
    if not model:
        return 'Unknown'
    
    model = str(model).upper()
    
    # Router patterns
    if any(pattern in model for pattern in ['ASR', 'ISR', 'C1000', 'C2900', 'C3900']):
        return 'Router'
    
    # Switch patterns  
    if any(pattern in model for pattern in ['WS-', 'C3750', 'C3560', 'C2960', 'MS2', 'MS4', 'N7K', 'N9K', '6509', '6513']):
        return 'Switch'
    
    # Security appliance patterns
    if any(pattern in model for pattern in ['MX', 'ASA', 'PIX']):
        return 'Security Appliance'
    
    # Wireless patterns
    if any(pattern in model for pattern in ['MR', 'AP', 'AIR-']):
        return 'Wireless Access Point'
    
    # Firewall patterns
    if any(pattern in model for pattern in ['FIREWALL', 'FW']):
        return 'Firewall'
    
    return 'Other'

def get_corp_executive_summary():
    """Generate executive summary for corporate network from Excel"""
    try:
        # Read EOL data
        eol_df = pd.read_excel('/var/www/html/meraki-data/Discount Tire Network Inventory.xlsx', 
                              sheet_name='End of LIfe Summary Counts')
        
        # Clean and process data
        today = date.today()
        processed_data = []
        
        for _, row in eol_df.iterrows():
            model = row.get('Model')
            if pd.isna(model) or str(model).strip() == '':
                continue
                
            total = row.get('Total', 0) if not pd.isna(row.get('Total')) else 0
            if total <= 0:
                continue
                
            announcement = parse_date(row.get('Announcement Date'))
            end_of_sale = parse_date(row.get('End of Sale Date'))
            end_of_support = parse_date(row.get('End of Support Date'))
            device_type = get_device_type_from_model(model)
            
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
                'announcement_date': announcement,
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
            'models_data': processed_data
        }
        
    except Exception as e:
        print(f"❌ Error generating corp executive summary: {e}")
        return {'overall': {}, 'by_device_type': [], 'eol_timeline': [], 'models_data': []}

def get_corp_inventory_by_location():
    """Get inventory details by location type from Excel"""
    try:
        location_sheets = {
            'All Data Centers': 'Data Center',
            'DT Stores': 'Store',
            'DistibutionCenter': 'Distribution Center', 
            'Warehouses': 'Warehouse',
            'Regional Offices': 'Regional Office'
        }
        
        all_inventory = []
        location_summaries = []
        
        for sheet_name, location_type in location_sheets.items():
            try:
                df = pd.read_excel('/var/www/html/meraki-data/Discount Tire Network Inventory.xlsx', 
                                 sheet_name=sheet_name)
                
                # Process each row
                location_devices = []
                for _, row in df.iterrows():
                    # Skip empty rows
                    if pd.isna(row.get('Hostname')) and pd.isna(row.get('Model')):
                        continue
                    
                    site = row.get('Site', '') if not pd.isna(row.get('Site')) else ''
                    hostname = row.get('Hostname', '') if not pd.isna(row.get('Hostname')) else ''
                    device_type = row.get('Device Type', '') if not pd.isna(row.get('Device Type')) else ''
                    model = row.get('Model', '') if not pd.isna(row.get('Model')) else ''
                    vendor = row.get('Vendor', '') if not pd.isna(row.get('Vendor')) else ''
                    serial = row.get('Serial Number', '') if not pd.isna(row.get('Serial Number')) else ''
                    
                    # Skip if no meaningful data
                    if not any([hostname, model, serial]):
                        continue
                    
                    if not device_type and model:
                        device_type = get_device_type_from_model(model)
                    
                    location_devices.append({
                        'location_type': location_type,
                        'site': site,
                        'hostname': hostname,
                        'device_type': device_type,
                        'model': model,
                        'vendor': vendor,
                        'serial_number': serial
                    })
                
                # Add to overall inventory
                all_inventory.extend(location_devices)
                
                # Create summary for this location
                unique_models = len(set(item['model'] for item in location_devices if item['model']))
                unique_sites = len(set(item['site'] for item in location_devices if item['site']))
                total_devices = len(location_devices)
                
                location_summaries.append({
                    'location_type': location_type,
                    'sheet_name': sheet_name,
                    'unique_models': unique_models,
                    'unique_sites': unique_sites,
                    'total_devices': total_devices,
                    'devices': location_devices
                })
                
            except Exception as e:
                print(f"Error processing {sheet_name}: {e}")
                location_summaries.append({
                    'location_type': location_type,
                    'sheet_name': sheet_name,
                    'unique_models': 0,
                    'unique_sites': 0,
                    'total_devices': 0,
                    'devices': [],
                    'error': str(e)
                })
        
        return {
            'by_location': location_summaries,
            'all_devices': all_inventory
        }
        
    except Exception as e:
        print(f"❌ Error getting inventory by location: {e}")
        return {'by_location': [], 'all_devices': []}

if __name__ == '__main__':
    print("🏢 Testing Corporate Network Data Functions...")
    
    print("\n📊 Executive Summary Test:")
    summary = get_corp_executive_summary()
    print(f"  Total Models: {summary['overall'].get('total_models', 0)}")
    print(f"  Total Devices: {summary['overall'].get('total_devices', 0)}")
    print(f"  EOL Models: {summary['overall'].get('end_of_life', 0)}")
    print(f"  Device Types: {len(summary['by_device_type'])}")
    
    print("\n📋 Inventory by Location Test:")
    inventory = get_corp_inventory_by_location()
    print(f"  Location Types: {len(inventory['by_location'])}")
    print(f"  Total Devices: {len(inventory['all_devices'])}")
    
    for loc in inventory['by_location']:
        print(f"    {loc['location_type']}: {loc['total_devices']} devices, {loc['unique_models']} models")