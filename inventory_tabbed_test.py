"""
INVENTORY MANAGEMENT - TABBED LAYOUT VERSION
=============================================
Executive Summary (Meraki) | Executive Summary (Corp) | Inventory (Meraki) | Inventory (Corp)
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

def get_meraki_inventory_data():
    """Get Meraki inventory data"""
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
        
        return {
            'summary': summary_data,
            'org_names': sorted(list(org_names)),
            'data_source': 'database'
        }
        
    except Exception as e:
        print(f"Error getting Meraki inventory: {e}")
        return {'summary': [], 'org_names': [], 'data_source': 'error'}
    finally:
        cursor.close()
        conn.close()

def get_corporate_inventory_data():
    """Get Corporate Network inventory data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get detailed device data
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
        
        # Get summary by device type
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
        
        summary_data = []
        total_models = 0
        total_logical = 0
        total_physical = 0
        total_eol = 0
        total_eos = 0
        
        for row in cursor.fetchall():
            device_type, model_count, logical_count, physical_count, eol_count, eos_count = row
            
            summary_data.append({
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
        
        return {
            'summary': summary_data,
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
        print(f"Error getting corporate inventory: {e}")
        return {'summary': [], 'details': [], 'totals': {}}
    finally:
        cursor.close()
        conn.close()

def calculate_meraki_eol_summary(inventory_data):
    """Calculate EOL summary for Meraki devices"""
    from datetime import datetime
    today = datetime.now().date()
    
    device_stats = {}
    
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
        
        # Parse dates and categorize
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
            
            if end_of_support and end_of_support <= today:
                device_stats[device_type]['end_of_life'] += total_devices
            elif end_of_sale and end_of_sale <= today:
                device_stats[device_type]['end_of_sale'] += total_devices
            else:
                device_stats[device_type]['active'] += total_devices
                
        except Exception:
            device_stats[device_type]['active'] += total_devices
    
    # Calculate totals and percentages
    overall_totals = {'total': 0, 'eol': 0, 'eos': 0, 'active': 0}
    eol_summary = []
    
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
            
            overall_totals['total'] += total
            overall_totals['eol'] += stats['end_of_life']
            overall_totals['eos'] += stats['end_of_sale']
            overall_totals['active'] += stats['active']
    
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
    
    return {
        'by_device_type': eol_summary,
        'overall': overall_summary
    }

@inventory_bp.route('/inventory-summary')
def inventory_summary():
    """
    Tabbed inventory summary page
    """
    try:
        # Get both data sets
        meraki_data = get_meraki_inventory_data()
        corporate_data = get_corporate_inventory_data()
        
        if meraki_data.get('data_source') == 'error':
            return "Error loading Meraki inventory from database", 500
        
        # Calculate EOL summaries
        meraki_eol = calculate_meraki_eol_summary(meraki_data['summary'])
        
        print(f"📊 Meraki: {len(meraki_data['summary'])} models")
        print(f"🏢 Corporate: {len(corporate_data['details'])} models, {corporate_data.get('totals', {}).get('physical', 0)} physical devices")
        
        return render_template('inventory_summary_tabbed.html', 
                             meraki_data=meraki_data,
                             corporate_data=corporate_data,
                             meraki_eol=meraki_eol)

    except Exception as e:
        print(f"❌ Error loading inventory summary: {e}")
        return f"Error loading inventory summary: {e}", 500

@inventory_bp.route('/api/inventory-summary')
def api_inventory_summary():
    """API endpoint for tabbed inventory data"""
    try:
        meraki_data = get_meraki_inventory_data()
        corporate_data = get_corporate_inventory_data()
        
        if meraki_data.get('data_source') == 'error':
            return jsonify({"error": "Failed to load data from database"}), 500
        
        meraki_eol = calculate_meraki_eol_summary(meraki_data['summary'])
        
        return jsonify({
            'meraki': meraki_data,
            'corporate': corporate_data,
            'meraki_eol': meraki_eol
        })
        
    except Exception as e:
        print(f"❌ Error in inventory API: {e}")
        return jsonify({"error": str(e)}), 500