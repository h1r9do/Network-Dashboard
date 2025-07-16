"""
INVENTORY MANAGEMENT - ORIGINAL WITH CORPORATE NETWORK ADDITION
===============================================================
Keeps original Meraki inventory functionality and adds Corporate Network section
"""

from flask import Blueprint, render_template, jsonify, request
import json
import psycopg2
import re
from config import Config
from datetime import datetime, date

# Create Blueprint
inventory_bp = Blueprint('inventory', __name__)

def get_db_connection():
    """Get database connection"""
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
    if not match:
        raise ValueError("Invalid database URI")
    
    user, password, host, port, database = match.groups()
    
    return psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password
    )

def get_device_type_from_model(model):
    """Categorize device model into device type"""
    if model.startswith('MR'):
        return 'Access Points (MR)'
    elif model.startswith('MS'):
        return 'Switches (MS)'
    elif model.startswith('MX'):
        return 'Security Appliances (MX)'
    elif model.startswith('MV'):
        return 'Cameras (MV)'
    elif model.startswith('MT'):
        return 'Sensors (MT)'
    elif model.startswith('Z'):
        return 'Teleworker Gateway (Z)'
    else:
        return 'Other'

def generate_critical_insights(timeline_data, total_devices):
    """Generate critical planning insights from EOL timeline data"""
    from datetime import datetime
    current_year = datetime.now().year
    
    insights = {
        'immediate_action': [],
        'critical_years': [],
        'major_refreshes': [],
        'budget_planning': []
    }
    
    # Find immediate action items (current year)
    for year_data in timeline_data:
        if year_data['year'] == current_year and year_data['total_devices'] > 0:
            insights['immediate_action'].append({
                'message': f"{year_data['total_devices']:,} devices reaching end-of-support this year",
                'severity': 'critical' if year_data['total_devices'] > 100 else 'warning'
            })
    
    # Find critical years (high device counts)
    critical_threshold = total_devices * 0.1  # 10% of total inventory
    for year_data in timeline_data:
        if year_data['total_devices'] > critical_threshold and year_data['year'] > current_year:
            insights['critical_years'].append({
                'year': year_data['year'],
                'device_count': year_data['total_devices'],
                'percentage': round((year_data['total_devices'] / total_devices) * 100, 1)
            })
    
    # Major refresh recommendations
    total_eol_next_3_years = sum(
        y['total_devices'] for y in timeline_data 
        if current_year <= y['year'] <= current_year + 3
    )
    if total_eol_next_3_years > 0:
        insights['major_refreshes'].append({
            'timeframe': 'Next 3 years',
            'device_count': total_eol_next_3_years,
            'recommendation': 'Plan phased refresh cycles to avoid network disruption'
        })
    
    # Budget planning insights
    if len(insights['critical_years']) > 0:
        peak_year = max(insights['critical_years'], key=lambda x: x['device_count'])
        insights['budget_planning'].append({
            'peak_year': peak_year['year'],
            'peak_devices': peak_year['device_count'],
            'message': f"Peak replacement year: {peak_year['year']} with {peak_year['device_count']:,} devices"
        })
    
    return insights

def get_inventory_summary_data():
    """Get ORIGINAL Meraki inventory summary data - unchanged"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                model,
                total_count,
                org_counts,
                announcement_date,
                end_of_sale,
                end_of_support,
                highlight
            FROM inventory_summary
            WHERE total_count > 0
            ORDER BY total_count DESC
        """)
        
        summary_data = []
        org_names = set()
        
        for row in cursor.fetchall():
            model, total_count, org_counts_json, announcement_date, end_of_sale, end_of_support, highlight = row
            
            # Parse org_counts
            try:
                org_counts = json.loads(org_counts_json) if org_counts_json else {}
            except:
                org_counts = {}
            
            # Add organization names to set
            org_names.update(org_counts.keys())
            
            # Add to summary
            summary_data.append({
                'model': model,
                'total': total_count,
                'org_counts': org_counts,
                'announcement_date': announcement_date,
                'end_of_sale': end_of_sale,
                'end_of_support': end_of_support,
                'highlight': highlight,
                'device_type': get_device_type_from_model(model)
            })
        
        # Calculate EOL summary for Meraki devices
        eol_summary = calculate_eol_summary(summary_data)
        
        return {
            'summary': summary_data,
            'org_names': sorted(list(org_names)),
            'eol_summary': eol_summary,
            'data_source': 'database'
        }
        
    except Exception as e:
        print(f"Error getting inventory summary: {e}")
        return {
            'summary': [],
            'org_names': [],
            'eol_summary': {},
            'data_source': 'error'
        }
    finally:
        cursor.close()
        conn.close()

def get_corporate_network_summary():
    """Get Corporate Network (Netdisco) inventory summary by device type"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get aggregated data by device type
        cursor.execute("""
            SELECT 
                device_type,
                COUNT(DISTINCT model) as model_count,
                SUM(logical_devices) as logical_count,
                SUM(physical_devices) as physical_count,
                COUNT(*) FILTER (WHERE end_of_support IS NOT NULL AND end_of_support <= CURRENT_DATE) as eol_count,
                COUNT(*) FILTER (WHERE end_of_sale IS NOT NULL AND end_of_sale <= CURRENT_DATE AND (end_of_support IS NULL OR end_of_support > CURRENT_DATE)) as eos_count
            FROM netdisco_inventory_summary
            GROUP BY device_type
            ORDER BY physical_count DESC
        """)
        
        corporate_summary = []
        total_models = 0
        total_logical = 0
        total_physical = 0
        total_eol = 0
        total_eos = 0
        
        for row in cursor.fetchall():
            device_type, model_count, logical_count, physical_count, eol_count, eos_count = row
            
            corporate_summary.append({
                'device_type': device_type,
                'model_count': model_count,
                'logical_count': logical_count,
                'physical_count': physical_count,
                'eol_count': eol_count,
                'eos_count': eos_count,
                'active_count': model_count - eol_count - eos_count
            })
            
            total_models += model_count
            total_logical += logical_count
            total_physical += physical_count
            total_eol += eol_count
            total_eos += eos_count
        
        # Get detailed device list for reference
        cursor.execute("""
            SELECT vendor, model, device_type, logical_devices, physical_devices, 
                   end_of_sale, end_of_support
            FROM netdisco_inventory_summary
            ORDER BY device_type, physical_devices DESC
        """)
        
        device_details = []
        for row in cursor.fetchall():
            vendor, model, device_type, logical, physical, eos, eol = row
            device_details.append({
                'vendor': vendor,
                'model': model,
                'device_type': device_type,
                'logical_devices': logical,
                'physical_devices': physical,
                'end_of_sale': eos.isoformat() if eos else None,
                'end_of_support': eol.isoformat() if eol else None
            })
        
        return {
            'summary': corporate_summary,
            'details': device_details,
            'totals': {
                'models': total_models,
                'logical': total_logical,
                'physical': total_physical,
                'eol': total_eol,
                'eos': total_eos,
                'active': total_models - total_eol - total_eos
            }
        }
        
    except Exception as e:
        print(f"Error getting corporate network summary: {e}")
        return {'summary': [], 'details': [], 'totals': {}}
    finally:
        cursor.close()
        conn.close()

def calculate_eol_summary(inventory_data):
    """Calculate EOL summary statistics - ORIGINAL CODE"""
    from datetime import datetime
    today = datetime.now().date()
    
    # Initialize device type stats
    device_stats = {}
    eol_timeline = {}
    
    # Process each device
    for device in inventory_data:
        device_type = device['device_type']
        if device_type not in device_stats:
            device_stats[device_type] = {
                'total_devices': 0,
                'end_of_life': 0,
                'end_of_sale': 0,
                'active': 0
            }
        
        total_devices = device['total']
        device_stats[device_type]['total_devices'] += total_devices
        
        # Parse dates
        try:
            end_of_sale = None
            end_of_support = None
            
            if device.get('end_of_sale'):
                if isinstance(device['end_of_sale'], date):
                    end_of_sale = device['end_of_sale']
                else:
                    end_of_sale = datetime.fromisoformat(device['end_of_sale']).date()
            
            if device.get('end_of_support'):
                if isinstance(device['end_of_support'], date):
                    end_of_support = device['end_of_support']
                else:
                    end_of_support = datetime.fromisoformat(device['end_of_support']).date()
            
            # Track timeline
            if end_of_support:
                eol_year = end_of_support.year
                if eol_year not in eol_timeline:
                    eol_timeline[eol_year] = {}
                if device_type not in eol_timeline[eol_year]:
                    eol_timeline[eol_year][device_type] = 0
                eol_timeline[eol_year][device_type] += total_devices
            
            # Categorize based on EOL status
            if end_of_support and end_of_support <= today:
                device_stats[device_type]['end_of_life'] += total_devices
            elif end_of_sale and end_of_sale <= today:
                device_stats[device_type]['end_of_sale'] += total_devices
            else:
                device_stats[device_type]['active'] += total_devices
                
        except Exception as e:
            # If we can't parse dates, consider as active
            device_stats[device_type]['active'] += total_devices
    
    # Calculate percentages and create summary
    eol_summary = []
    overall_totals = {'total': 0, 'eol': 0, 'eos': 0, 'active': 0}
    
    for device_type, stats in sorted(device_stats.items()):
        total = stats['total_devices']
        if total > 0:
            eol_summary.append({
                'device_type': device_type,
                'total_devices': total,
                'end_of_life': stats['end_of_life'],
                'end_of_sale': stats['end_of_sale'],
                'active': stats['active'],
                'eol_percentage': round((stats['end_of_life'] / total) * 100, 1),
                'eos_percentage': round((stats['end_of_sale'] / total) * 100, 1),
                'active_percentage': round((stats['active'] / total) * 100, 1)
            })
            
            # Add to overall totals
            overall_totals['total'] += total
            overall_totals['eol'] += stats['end_of_life']
            overall_totals['eos'] += stats['end_of_sale']
            overall_totals['active'] += stats['active']
    
    # Calculate overall percentages
    if overall_totals['total'] > 0:
        overall_summary = {
            'total_devices': overall_totals['total'],
            'end_of_life': overall_totals['eol'],
            'end_of_sale': overall_totals['eos'], 
            'active': overall_totals['active'],
            'eol_percentage': round((overall_totals['eol'] / overall_totals['total']) * 100, 1),
            'eos_percentage': round((overall_totals['eos'] / overall_totals['total']) * 100, 1),
            'active_percentage': round((overall_totals['active'] / overall_totals['total']) * 100, 1)
        }
    else:
        overall_summary = {'total_devices': 0, 'eol_percentage': 0, 'eos_percentage': 0, 'active_percentage': 0}
    
    # Process year-by-year timeline
    timeline_data = []
    current_year = today.year
    
    # Include years from current year to 10 years in the future, plus any historical years with data
    all_years = set(range(current_year, current_year + 11))
    all_years.update(eol_timeline.keys())
    
    # Get all device types
    all_device_types = sorted(device_stats.keys())
    
    for year in sorted(all_years):
        year_data = {
            'year': year,
            'total_devices': 0,
            'by_device_type': {},
            'is_past': year < current_year,
            'is_current': year == current_year
        }
        
        # Initialize all device types for this year
        for device_type in all_device_types:
            year_data['by_device_type'][device_type] = 0
        
        # Add actual data if it exists
        if year in eol_timeline:
            for device_type, count in eol_timeline[year].items():
                year_data['by_device_type'][device_type] = count
                year_data['total_devices'] += count
        
        # Only include years with data or future years up to 2035
        if year_data['total_devices'] > 0 or (year >= current_year and year <= current_year + 10):
            timeline_data.append(year_data)
    
    # Generate critical planning insights
    critical_insights = generate_critical_insights(timeline_data, overall_totals['total'])
    
    return {
        'by_device_type': eol_summary,
        'overall': overall_summary,
        'eol_timeline': timeline_data,
        'critical_insights': critical_insights
    }

# ORIGINAL ROUTES - UNCHANGED
@inventory_bp.route('/inventory-summary')
def inventory_summary():
    """
    Device model summary page with lifecycle status - ORIGINAL with Corporate Network addition
    """
    try:
        # Get original Meraki data
        meraki_data = get_inventory_summary_data()
        
        # Get Corporate Network data
        corporate_data = get_corporate_network_summary()
        
        summary_data = meraki_data.get('summary', [])
        org_names = meraki_data.get('org_names', [])
        eol_summary = meraki_data.get('eol_summary', {})
        data_source = meraki_data.get('data_source', 'unknown')
        
        print(f"📊 Loaded inventory summary from {data_source}: {len(summary_data)} models across {len(org_names)} orgs")
        print(f"🏢 Corporate Network: {len(corporate_data.get('details', []))} models, {corporate_data.get('totals', {}).get('physical', 0)} physical devices")
        
        if data_source == 'error':
            return "Error loading inventory summary from database", 500
        
        # Calculate total devices for display
        total_devices = sum(entry.get('total', 0) for entry in summary_data)
        
        return render_template('inventory_summary_with_corp.html', 
                             summary=summary_data, 
                             org_names=org_names,
                             eol_summary=eol_summary,
                             total_devices=total_devices,
                             data_source=data_source,
                             corporate_data=corporate_data)

    except Exception as e:
        print(f"❌ Error loading inventory summary: {e}")
        return f"Error loading inventory summary: {e}", 500

# Copy all other original routes unchanged...
@inventory_bp.route('/inventory-details')
def inventory_details():
    """Original inventory details - unchanged"""
    try:
        # For now, return empty data for inventory details
        full_data = {}
        data_source = 'database'
        
        if data_source == 'error':
            return "Error loading inventory details from database", 500
        
        all_orgs = sorted(set(full_data.keys()))
        
        print(f"📱 Loaded detailed inventory from {data_source} for {len(all_orgs)} organizations")
        
        # Calculate device counts for logging
        total_devices = 0
        for org in all_orgs:
            device_count = len(full_data[org])
            total_devices += device_count
            print(f"   📊 {org}: {device_count} devices")
        
        return render_template('inventory_details.html', 
                             inventory=full_data,
                             all_orgs=all_orgs,
                             total_devices=total_devices,
                             data_source=data_source)
                             
    except Exception as e:
        print(f"❌ Error loading inventory details: {e}")
        return f"Error loading inventory details: {e}", 500

@inventory_bp.route('/api/inventory-summary')
def api_inventory_summary():
    """API endpoint for inventory summary data - ORIGINAL with corporate addition"""
    try:
        meraki_data = get_inventory_summary_data()
        corporate_data = get_corporate_network_summary()
        
        if meraki_data.get('data_source') == 'error':
            return jsonify({"error": "Failed to load summary data from database"}), 500
        
        # Add corporate data to response
        meraki_data['corporate_network'] = corporate_data
        
        print(f"📊 API: Returning summary data from {meraki_data.get('data_source')} for {len(meraki_data.get('summary', []))} models")
        return jsonify(meraki_data)
        
    except Exception as e:
        print(f"❌ Error in inventory summary API: {e}")
        return jsonify({"error": str(e)}), 500