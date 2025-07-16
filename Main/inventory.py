"""
INVENTORY MANAGEMENT AND DEVICE TRACKING - DATABASE ONLY VERSION
=================================================================

Purpose:
    - Meraki device inventory management and tracking from database
    - Device model analysis and lifecycle monitoring
    - Organization-based inventory reporting
    - End-of-life and end-of-sale tracking

Pages Served:
    - /inventory-summary (device model summary with EOL/EOS status)
    - /inventory-details (detailed device inventory by organization)

Templates Used:
    - inventory_summary.html (summary table with device model counts and lifecycle status)
    - inventory_details.html (detailed inventory with filtering and search)

API Endpoints:
    - /api/inventory-summary (GET) - Device model summary data
    - /api/inventory-details (GET) - Detailed device inventory with filtering

Key Functions:
    - Device model aggregation and counting
    - End-of-life (EOL) and end-of-sale (EOS) status tracking
    - Organization-based inventory breakdown
    - Device filtering and search capabilities
    - Lifecycle status highlighting and warnings

Dependencies:
    - Direct database queries using psycopg2
    - config.py for database connection

Data Sources:
    - Database tables only (inventory_summary, inventory_devices)

Features:
    - Interactive model filtering and search
    - Organization-based views and tabs
    - End-of-life status highlighting
    - Export capabilities (Excel, PDF)
    - Device detail viewing and management
    - Lifecycle status color coding
"""

from flask import Blueprint, render_template, jsonify, request
import json
import psycopg2
import re
from config import Config
# Import tab functions
from inventory_tabs_functions import get_corp_network_summary, get_datacenter_inventory

# Create Blueprint
inventory_bp = Blueprint('inventory', __name__)

def get_db_connection():
    """Get database connection"""
    # Use the correct credentials that work with our production setup
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='T3dC$gLp9'
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
    current_year_data = next((year for year in timeline_data if year['year'] == current_year), None)
    if current_year_data and current_year_data['total_devices'] > 0:
        insights['immediate_action'].append({
            'year': current_year,
            'devices': current_year_data['total_devices'],
            'message': f"{current_year_data['total_devices']} devices reaching EOL this year - immediate replacement needed"
        })
    
    # Find critical years (>= 5% of total devices or >500 devices)
    for year_data in timeline_data:
        if year_data['year'] > current_year and year_data['total_devices'] > 0:
            percentage = (year_data['total_devices'] / total_devices) * 100
            if percentage >= 5 or year_data['total_devices'] >= 500:
                insights['critical_years'].append({
                    'year': year_data['year'],
                    'devices': year_data['total_devices'],
                    'percentage': round(percentage, 1),
                    'message': f"{year_data['year']}: {year_data['total_devices']} devices ({percentage:.1f}% of network) reaching EOL"
                })
    
    # Find major device type refreshes (>1000 devices of same type in one year)
    for year_data in timeline_data:
        if year_data['year'] >= current_year:
            for device_type, count in year_data['by_device_type'].items():
                if count >= 1000:
                    insights['major_refreshes'].append({
                        'year': year_data['year'],
                        'device_type': device_type,
                        'devices': count,
                        'message': f"{year_data['year']}: {count} {device_type} devices - major refresh required"
                    })
    
    # Budget planning insights - find years with highest costs
    future_years = [year for year in timeline_data if year['year'] >= current_year and year['total_devices'] > 0]
    future_years.sort(key=lambda x: x['total_devices'], reverse=True)
    
    for i, year_data in enumerate(future_years[:3]):  # Top 3 years
        percentage = (year_data['total_devices'] / total_devices) * 100
        priority = ['Highest', 'High', 'Moderate'][i] if i < 3 else 'Low'
        insights['budget_planning'].append({
            'year': year_data['year'],
            'devices': year_data['total_devices'],
            'percentage': round(percentage, 1),
            'priority': priority,
            'message': f"{year_data['year']}: {priority} priority - {year_data['total_devices']} devices ({percentage:.1f}%)"
        })
    
    # Sort lists by year
    for key in insights:
        if isinstance(insights[key], list):
            insights[key].sort(key=lambda x: x['year'])
    
    return insights

def calculate_eol_summary(summary_data):
    """Calculate EOL summary statistics by device type with year-by-year timeline"""
    from datetime import datetime
    today = datetime.now().date()
    
    # Initialize stats by device type
    device_stats = {}
    # Track year-by-year EOL timeline
    eol_timeline = {}
    
    for item in summary_data:
        device_type = get_device_type_from_model(item['model'])
        total_devices = item['total']
        
        if device_type not in device_stats:
            device_stats[device_type] = {
                'total_devices': 0,
                'end_of_life': 0,
                'end_of_sale': 0,
                'active': 0
            }
        
        device_stats[device_type]['total_devices'] += total_devices
        
        # Parse dates to determine status
        try:
            end_of_sale_str = item['end_of_sale']
            end_of_support_str = item['end_of_support']
            
            end_of_sale = None
            end_of_support = None
            
            if end_of_sale_str:
                try:
                    end_of_sale = datetime.strptime(end_of_sale_str, '%b %d, %Y').date()
                except:
                    pass
                    
            if end_of_support_str:
                try:
                    end_of_support = datetime.strptime(end_of_support_str, '%b %d, %Y').date()
                except:
                    pass
            
            # Add to year-by-year timeline for End of Support
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

def get_inventory_summary_data():
    """Get inventory summary data from database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT model, total_count, org_counts, announcement_date, 
                   end_of_sale, end_of_support, highlight
            FROM inventory_summary
            ORDER BY model
        """)
        
        results = cursor.fetchall()
        summary_data = []
        org_names = set()
        
        for row in results:
            model, total_count, org_counts_json, announcement_date, end_of_sale, end_of_support, highlight = row
            
            # Handle org_counts - it might be a string like "SNMP: 22" or JSON
            if org_counts_json:
                try:
                    # Try to parse as JSON first
                    org_counts = json.loads(org_counts_json)
                except (json.JSONDecodeError, TypeError):
                    # If not JSON, parse the string format "SNMP: 22"
                    org_counts = {}
                    if ':' in str(org_counts_json):
                        parts = str(org_counts_json).split(':')
                        if len(parts) == 2:
                            org_name = parts[0].strip()
                            try:
                                count = int(parts[1].strip())
                                org_counts[org_name] = count
                            except ValueError:
                                pass
            else:
                org_counts = {}
            org_names.update(org_counts.keys())
            
            # Format dates in Meraki style (Mar 28, 2025)
            def format_date_meraki(date_str):
                if not date_str:
                    return ''
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(str(date_str), '%Y-%m-%d')
                    return date_obj.strftime('%b %d, %Y')
                except:
                    return date_str or ''
            
            summary_data.append({
                'model': model,
                'total': total_count,
                'org_counts': org_counts,
                'announcement_date': format_date_meraki(announcement_date),
                'end_of_sale': format_date_meraki(end_of_sale),
                'end_of_support': format_date_meraki(end_of_support),
                'highlight': highlight or ''
            })
        
        cursor.close()
        conn.close()
        
        # Calculate EOL summary
        eol_summary = calculate_eol_summary(summary_data)
        
        return {
            'summary': summary_data,
            'org_names': sorted(list(org_names)),
            'eol_summary': eol_summary,
            'data_source': 'database'
        }
        
    except Exception as e:
        print(f"❌ Error getting inventory summary from database: {e}")
        import traceback
        traceback.print_exc()
        return {'summary': [], 'org_names': [], 'eol_summary': {}, 'data_source': 'error'}

def get_inventory_details_data(org_filter=None, model_filter=None):
    """Get detailed inventory data from database - optimized for performance"""
    try:
        import time
        start_time = time.time()
        
        # Try Redis cache first for full dataset
        cache_key = f"inventory_full:{org_filter or 'all'}:{model_filter or 'all'}"
        try:
            from config import get_redis_connection
            redis_conn = get_redis_connection()
            if redis_conn:
                cached_result = redis_conn.get(cache_key)
                if cached_result:
                    print(f"📊 Inventory: Cache hit for full dataset")
                    return json.loads(cached_result), 'database-cached'
        except Exception as e:
            print(f"Redis cache error: {e}")
            redis_conn = None
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Ultra-optimized query - let database handle JSON validation and defaults
        query = """
            SELECT serial, model, organization, 
                   COALESCE(network_id, '') as network_id, 
                   COALESCE(network_name, '') as network_name,
                   COALESCE(name, '') as name, 
                   COALESCE(mac, '') as mac, 
                   COALESCE(lan_ip, '') as lan_ip, 
                   COALESCE(firmware, '') as firmware, 
                   COALESCE(product_type, '') as product_type,
                   CASE 
                     WHEN tags IS NULL OR tags = '' OR tags = 'null' THEN '[]'
                     ELSE tags 
                   END as tags,
                   COALESCE(notes, '') as notes,
                   CASE 
                     WHEN details IS NULL OR details = '' OR details = 'null' THEN '{}'
                     ELSE details 
                   END as details
            FROM inventory_devices
            WHERE 1=1
            AND NOT EXISTS (
                SELECT 1 FROM jsonb_array_elements_text(
                    CASE 
                        WHEN tags IS NULL OR tags = '' OR tags = 'null' THEN '[]'::jsonb
                        ELSE tags::jsonb 
                    END
                ) tag
                WHERE LOWER(tag) LIKE '%hub%' 
                   OR LOWER(tag) LIKE '%lab%' 
                   OR LOWER(tag) LIKE '%voice%'
            )
        """
        params = []
        
        if org_filter:
            query += " AND organization = %s"
            params.append(org_filter)
        
        if model_filter:
            query += " AND model ILIKE %s"
            params.append(f'%{model_filter}%')
        
        query += " ORDER BY organization, model"
        
        print(f"📊 Loading inventory from database with filters: org={org_filter}, model={model_filter}")
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        results = cursor.fetchall()
        
        load_time = time.time() - start_time
        print(f"📊 Database query completed in {load_time:.3f}s for {len(results)} devices")
        
        # Optimized processing - batch JSON parsing and use list comprehension where possible
        inventory_data = {}
        processing_start = time.time()
        
        # Ultra-fast processing with pre-allocated structures and minimal function calls
        json_loads = json.loads  # Cache function reference
        
        for row in results:
            serial, model, organization, network_id, network_name, name, mac, lan_ip, firmware, product_type, tags, notes, details = row
            
            # Fast organization grouping
            if organization not in inventory_data:
                inventory_data[organization] = []
            
            # Fast JSON parsing - database already provided defaults
            try:
                parsed_tags = json_loads(tags) if tags != '[]' else []
            except (json.JSONDecodeError, TypeError):
                parsed_tags = []
            
            try:
                parsed_details = json_loads(details) if details != '{}' else {}
            except (json.JSONDecodeError, TypeError):
                parsed_details = {}
            
            # Direct dictionary creation - no unnecessary string coercion since DB handles it
            inventory_data[organization].append({
                'serial': serial,
                'model': model,
                'device_model': model,
                'organization': organization,
                'networkId': network_id,
                'networkName': network_name,
                'name': name,
                'mac': mac,
                'lanIp': lan_ip,
                'firmware': firmware,
                'productType': product_type,
                'tags': parsed_tags,
                'notes': notes,
                'details': parsed_details
            })
        
        processing_time = time.time() - processing_start
        total_time = time.time() - start_time
        
        print(f"📊 Processing completed in {processing_time:.3f}s. Total time: {total_time:.3f}s")
        print(f"📊 Loaded {len(inventory_data)} organizations with {len(results)} devices")
        
        cursor.close()
        conn.close()
        
        # Cache the result for 10 minutes (longer cache for full dataset)
        if redis_conn and len(results) > 0:
            try:
                redis_conn.setex(cache_key, 600, json.dumps(inventory_data))
                print(f"📊 Cached full inventory dataset for 10 minutes")
            except Exception as e:
                print(f"Redis cache set error: {e}")
        
        return inventory_data, 'database-optimized'
        
    except Exception as e:
        print(f"❌ Error getting inventory details from database: {e}")
        import traceback
        traceback.print_exc()
        return {}, 'error'

@inventory_bp.route('/inventory-summary')
def inventory_summary():
    """
    Device model summary page with lifecycle status
    
    Displays aggregated device model counts across all organizations
    with end-of-life and end-of-sale status highlighting.
    
    Returns:
        Rendered inventory_summary.html template with summary data
        OR error message if data cannot be loaded
    """
    try:
        data = get_inventory_summary_data()
        
        summary_data = data.get('summary', [])
        org_names = data.get('org_names', [])
        eol_summary = data.get('eol_summary', {})
        data_source = data.get('data_source', 'unknown')
        
        print(f"📊 Loaded inventory summary from {data_source}: {len(summary_data)} models across {len(org_names)} orgs")
        
        if data_source == 'error':
            return "Error loading inventory summary from database", 500
        
        # Calculate total devices for display
        total_devices = sum(entry.get('total', 0) for entry in summary_data)
        
        return render_template('inventory_summary_tabs.html', 
                             summary=summary_data, 
                             org_names=org_names,
                             eol_summary=eol_summary,
                             total_devices=total_devices,
                             data_source=data_source)

    except Exception as e:
        print(f"❌ Error loading inventory summary: {e}")
        import traceback
        traceback.print_exc()
        return f"Error loading inventory summary: {e}", 500

@inventory_bp.route('/inventory-details')
def inventory_details():
    """
    Detailed device inventory page
    
    Displays detailed device information organized by organization
    with filtering, search, and export capabilities.
    
    Returns:
        Rendered inventory_details.html template with detailed inventory data
        OR error message if data cannot be loaded
    """
    try:
        full_data, data_source = get_inventory_details_data()
        
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

@inventory_bp.route('/inventory-details-legacy')
def inventory_details_legacy():
    """
    LEGACY: Detailed device inventory page
    
    Original version kept for rollback purposes.
    
    Returns:
        Rendered inventory_details.html template with detailed inventory data
        OR error message if data cannot be loaded
    """
    try:
        full_data, data_source = get_inventory_details_data()
        
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

@inventory_bp.route('/api/inventory-org-data/<org_name>')
def api_inventory_org_data(org_name):
    """
    Fast API endpoint for loading specific organization device data
    
    Loads device data for a single organization for progressive loading.
    
    Parameters:
        org_name (str): Organization name to load data for
        
    Query Parameters:
        limit (int, optional): Limit results (default: 1000)
        offset (int, optional): Offset for pagination (default: 0)
    
    Returns:
        JSON response with organization device data
    """
    import time
    start_time = time.time()
    
    try:
        limit = min(int(request.args.get('limit', 1000)), 5000)  # Max 5000 devices
        offset = int(request.args.get('offset', 0))
        
        # Use optimized query for single organization
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT serial, model, 
                   COALESCE(network_id, '') as network_id, 
                   COALESCE(network_name, '') as network_name,
                   COALESCE(name, '') as name, 
                   COALESCE(mac, '') as mac, 
                   COALESCE(lan_ip, '') as lan_ip, 
                   COALESCE(firmware, '') as firmware, 
                   COALESCE(product_type, '') as product_type,
                   CASE 
                     WHEN tags IS NULL OR tags = '' OR tags = 'null' THEN '[]'
                     ELSE tags 
                   END as tags,
                   COALESCE(notes, '') as notes
            FROM inventory_devices
            WHERE organization = %s
            AND NOT EXISTS (
                SELECT 1 FROM jsonb_array_elements_text(
                    CASE 
                        WHEN tags IS NULL OR tags = '' OR tags = 'null' THEN '[]'::jsonb
                        ELSE tags::jsonb 
                    END
                ) tag
                WHERE LOWER(tag) LIKE '%hub%' 
                   OR LOWER(tag) LIKE '%lab%' 
                   OR LOWER(tag) LIKE '%voice%'
            )
            ORDER BY model, name
            LIMIT %s OFFSET %s
        """
        
        cursor.execute(query, (org_name, limit, offset))
        results = cursor.fetchall()
        
        # Get total count for this organization
        count_query = """
            SELECT COUNT(*) FROM inventory_devices
            WHERE organization = %s
            AND NOT EXISTS (
                SELECT 1 FROM jsonb_array_elements_text(
                    CASE 
                        WHEN tags IS NULL OR tags = '' OR tags = 'null' THEN '[]'::jsonb
                        ELSE tags::jsonb 
                    END
                ) tag
                WHERE LOWER(tag) LIKE '%hub%' 
                   OR LOWER(tag) LIKE '%lab%' 
                   OR LOWER(tag) LIKE '%voice%'
            )
        """
        cursor.execute(count_query, (org_name,))
        total_count = cursor.fetchone()[0]
        
        query_time = time.time() - start_time
        
        # Fast processing
        devices = []
        json_loads = json.loads
        
        for row in results:
            serial, model, network_id, network_name, name, mac, lan_ip, firmware, product_type, tags, notes = row
            
            # Fast JSON parsing
            try:
                parsed_tags = json_loads(tags) if tags != '[]' else []
            except (json.JSONDecodeError, TypeError):
                parsed_tags = []
            
            devices.append({
                'serial': serial,
                'model': model,
                'device_model': model,
                'organization': org_name,
                'networkId': network_id,
                'networkName': network_name,
                'name': name,
                'mac': mac,
                'lanIp': lan_ip,
                'firmware': firmware,
                'productType': product_type,
                'tags': parsed_tags,
                'notes': notes
            })
        
        cursor.close()
        conn.close()
        
        processing_time = time.time() - start_time
        
        has_more = (offset + len(results)) < total_count
        
        result = {
            'organization': org_name,
            'devices': devices,
            'pagination': {
                'offset': offset,
                'limit': limit,
                'returned': len(devices),
                'total': total_count,
                'has_more': has_more
            },
            'query_time_ms': int(processing_time * 1000)
        }
        
        print(f"⚡ API: Loaded {len(devices)} devices for {org_name} in {processing_time*1000:.1f}ms")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error loading organization data for {org_name}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@inventory_bp.route('/api/inventory-summary')
def api_inventory_summary():
    """
    API endpoint for inventory summary data
    
    Returns raw JSON data for the inventory summary, useful for
    programmatic access or AJAX updates.
    
    Returns:
        JSON response with inventory summary data:
        - summary: List of device models with counts and lifecycle info
        - org_names: List of organization names
        OR error message if data cannot be loaded
    """
    try:
        data = get_inventory_summary_data()
        
        if data.get('data_source') == 'error':
            return jsonify({"error": "Failed to load summary data from database"}), 500
        
        print(f"📊 API: Returning summary data from {data.get('data_source')} for {len(data.get('summary', []))} models")
        return jsonify(data)
        
    except Exception as e:
        print(f"❌ Error in inventory summary API: {e}")
        return jsonify({"error": str(e)}), 500

@inventory_bp.route('/api/inventory-details')
def api_inventory_details():
    """
    Optimized API endpoint for detailed inventory data with filtering and pagination
    
    Query Parameters:
        org (str, optional): Filter by specific organization
        model (str, optional): Filter by device model (partial match)
        limit (int, optional): Limit results (default: 100 for performance)
        offset (int, optional): Offset for pagination (default: 0)
        summary_only (bool, optional): Return only organization counts (default: false)
    
    Returns:
        JSON response with filtered device inventory data or summary
    """
    try:
        import time
        start_time = time.time()
        
        org_filter = request.args.get('org')
        model_filter = request.args.get('model')
        limit = int(request.args.get('limit', 50))  # Reduced default for better performance
        offset = int(request.args.get('offset', 0))
        summary_only = request.args.get('summary_only', 'false').lower() == 'true'
        
        # If no filters and summary_only is true, return just organization counts
        if summary_only and not org_filter and not model_filter:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT organization, COUNT(*) as device_count
                FROM inventory_devices
                WHERE NOT EXISTS (
                    SELECT 1 FROM jsonb_array_elements_text(
                        CASE 
                            WHEN tags IS NULL OR tags = '' OR tags = 'null' THEN '[]'::jsonb
                            ELSE tags::jsonb 
                        END
                    ) tag
                    WHERE LOWER(tag) LIKE '%hub%' 
                       OR LOWER(tag) LIKE '%lab%' 
                       OR LOWER(tag) LIKE '%voice%'
                )
                GROUP BY organization
                ORDER BY organization
            """)
            
            results = cursor.fetchall()
            summary_data = {org: count for org, count in results}
            
            cursor.close()
            conn.close()
            
            query_time = time.time() - start_time
            print(f"📊 API: Returned org summary in {query_time:.3f}s - {len(summary_data)} orgs")
            
            return jsonify({
                "summary": summary_data,
                "data_source": "database-summary",
                "total_orgs": len(summary_data),
                "query_time_ms": int(query_time * 1000)
            })
        
        # Use Redis cache for repeated queries
        cache_key = f"inventory_details:{org_filter or 'all'}:{model_filter or 'all'}:{limit}:{offset}"
        
        try:
            from config import get_redis_connection
            redis_conn = get_redis_connection()
            if redis_conn:
                cached_result = redis_conn.get(cache_key)
                if cached_result:
                    print(f"📊 API: Cache hit for {cache_key}")
                    return jsonify(json.loads(cached_result))
        except Exception as e:
            print(f"Redis cache error: {e}")
            redis_conn = None
        
        # Build optimized query with pagination
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Count total matching records first
        count_query = """SELECT COUNT(*) FROM inventory_devices 
                         WHERE 1=1
                         AND NOT EXISTS (
                             SELECT 1 FROM jsonb_array_elements_text(
                                 CASE 
                                     WHEN tags IS NULL OR tags = '' OR tags = 'null' THEN '[]'::jsonb
                                     ELSE tags::jsonb 
                                 END
                             ) tag
                             WHERE LOWER(tag) LIKE '%hub%' 
                                OR LOWER(tag) LIKE '%lab%' 
                                OR LOWER(tag) LIKE '%voice%'
                         )"""
        params = []
        
        if org_filter:
            count_query += " AND organization = %s"
            params.append(org_filter)
        
        if model_filter:
            count_query += " AND model ILIKE %s"
            params.append(f'%{model_filter}%')
        
        if params:
            cursor.execute(count_query, params)
        else:
            cursor.execute(count_query)
        total_count = cursor.fetchone()[0]
        
        # Get paginated data - exclude heavy JSON fields if not needed
        if limit <= 50 or request.args.get('minimal') == 'true':
            # Minimal data for fast loading
            query = """
                SELECT serial, model, organization, network_id, network_name,
                       name, mac, lan_ip, firmware, product_type
                FROM inventory_devices
                WHERE 1=1
                AND NOT EXISTS (
                    SELECT 1 FROM jsonb_array_elements_text(
                        CASE 
                            WHEN tags IS NULL OR tags = '' OR tags = 'null' THEN '[]'::jsonb
                            ELSE tags::jsonb 
                        END
                    ) tag
                    WHERE LOWER(tag) LIKE '%hub%' 
                       OR LOWER(tag) LIKE '%lab%' 
                       OR LOWER(tag) LIKE '%voice%'
                )
            """
            include_json = False
        else:
            # Full data including JSON fields
            query = """
                SELECT serial, model, organization, network_id, network_name,
                       name, mac, lan_ip, firmware, product_type, tags, notes, details
                FROM inventory_devices
                WHERE 1=1
                AND NOT EXISTS (
                    SELECT 1 FROM jsonb_array_elements_text(
                        CASE 
                            WHEN tags IS NULL OR tags = '' OR tags = 'null' THEN '[]'::jsonb
                            ELSE tags::jsonb 
                        END
                    ) tag
                    WHERE LOWER(tag) LIKE '%hub%' 
                       OR LOWER(tag) LIKE '%lab%' 
                       OR LOWER(tag) LIKE '%voice%'
                )
            """
            include_json = True
        
        if org_filter:
            query += " AND organization = %s"
        
        if model_filter:
            query += " AND model ILIKE %s"
        
        query += " ORDER BY organization, model LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        results = cursor.fetchall()
        
        # Group by organization (optimized processing)
        inventory_data = {}
        for row in results:
            if include_json:
                serial, model, organization, network_id, network_name, name, mac, lan_ip, firmware, product_type, tags, notes, details = row
                
                # Optimized JSON parsing - only parse if not empty/null
                parsed_tags = []
                parsed_details = {}
                
                if tags and tags.strip() and tags != 'null':
                    try:
                        parsed_tags = json.loads(tags)
                    except (json.JSONDecodeError, TypeError):
                        parsed_tags = []
                
                if details and details.strip() and details != 'null':
                    try:
                        parsed_details = json.loads(details)
                    except (json.JSONDecodeError, TypeError):
                        parsed_details = {}
                
                device_data = {
                    'serial': serial,
                    'model': model,
                    'device_model': model,
                    'organization': organization,
                    'networkId': network_id or '',
                    'networkName': network_name or '',
                    'name': name or '',
                    'mac': mac or '',
                    'lanIp': lan_ip or '',
                    'firmware': firmware or '',
                    'productType': product_type or '',
                    'tags': parsed_tags,
                    'notes': notes or '',
                    'details': parsed_details
                }
            else:
                # Minimal data mode - no JSON parsing
                serial, model, organization, network_id, network_name, name, mac, lan_ip, firmware, product_type = row
                
                device_data = {
                    'serial': serial,
                    'model': model,
                    'device_model': model,
                    'organization': organization,
                    'networkId': network_id or '',
                    'networkName': network_name or '',
                    'name': name or '',
                    'mac': mac or '',
                    'lanIp': lan_ip or '',
                    'firmware': firmware or '',
                    'productType': product_type or '',
                    'tags': [],
                    'notes': '',
                    'details': {}
                }
            
            if organization not in inventory_data:
                inventory_data[organization] = []
            inventory_data[organization].append(device_data)
        
        cursor.close()
        conn.close()
        
        query_time = time.time() - start_time
        
        result = {
            "data": inventory_data,
            "data_source": "database-paginated" + ("-minimal" if not include_json else ""),
            "filters": {
                "org": org_filter,
                "model": model_filter
            },
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total_count": total_count,
                "returned_count": len(results),
                "has_more": offset + limit < total_count,
                "page": (offset // limit) + 1,
                "total_pages": (total_count + limit - 1) // limit
            },
            "query_time_ms": int(query_time * 1000),
            "total_organizations": len(inventory_data),
            "performance_mode": "minimal" if not include_json else "full"
        }
        
        # Cache successful results for 5 minutes
        if redis_conn and len(results) > 0:
            try:
                redis_conn.setex(cache_key, 300, json.dumps(result))
            except Exception as e:
                print(f"Redis cache set error: {e}")
        
        print(f"📊 API: Returning paginated data in {query_time:.3f}s - {len(results)}/{total_count} devices, {len(inventory_data)} orgs")
        if org_filter:
            print(f"   🏢 Org filter: {org_filter}")
        if model_filter:
            print(f"   📱 Model filter: {model_filter}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in inventory details API: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@inventory_bp.route('/api/ssh-inventory')
def api_ssh_inventory():
    """
    API endpoint for SSH-collected network device inventory with hierarchical components
    
    Returns hierarchical view where each master device shows its modules/blades/SFPs as child rows
    
    Query Parameters:
        device_filter (str, optional): Filter by hostname or IP address
        component_type (str, optional): Filter by component type (chassis_blade, hardware_component, sfp_module)
        
    Returns:
        JSON response with hierarchical device inventory data
    """
    try:
        device_filter = request.args.get('device_filter', '').strip()
        component_type = request.args.get('component_type', '').strip()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query for devices with their component counts
        device_query = """
            SELECT nd.id, nd.ip_address, nd.hostname, nd.collection_timestamp, 
                   nd.device_type, nd.interfaces_count,
                   COUNT(DISTINCT cb.id) as chassis_blades_count,
                   COUNT(DISTINCT hc.id) as hardware_components_count,
                   COUNT(DISTINCT sm.id) as sfp_modules_count
            FROM network_devices nd
            LEFT JOIN chassis_blades cb ON nd.id = cb.device_id
            LEFT JOIN hardware_components hc ON nd.id = hc.device_id
            LEFT JOIN sfp_modules sm ON nd.id = sm.device_id
            WHERE 1=1
        """
        params = []
        
        if device_filter:
            device_query += " AND (nd.hostname ILIKE %s OR nd.ip_address ILIKE %s)"
            params.extend([f'%{device_filter}%', f'%{device_filter}%'])
        
        device_query += " GROUP BY nd.id ORDER BY nd.hostname"
        
        cursor.execute(device_query, params)
        devices = cursor.fetchall()
        
        result = {
            'devices': [],
            'total_devices': len(devices),
            'total_components': 0
        }
        
        for device in devices:
            device_id, ip_address, hostname, collection_timestamp, device_type, interfaces_count, chassis_count, hw_count, sfp_count = device
            
            device_data = {
                'id': device_id,
                'ip_address': ip_address,
                'hostname': hostname,
                'collection_timestamp': collection_timestamp.isoformat() if collection_timestamp else None,
                'device_type': device_type,
                'interfaces_count': interfaces_count,
                'components_summary': {
                    'chassis_blades': chassis_count,
                    'hardware_components': hw_count,
                    'sfp_modules': sfp_count
                },
                'components': []
            }
            
            # Get detailed components if requested or if any exist
            if chassis_count > 0 or hw_count > 0 or sfp_count > 0:
                
                # Get chassis blades
                if not component_type or component_type == 'chassis_blade':
                    cursor.execute("""
                        SELECT 'chassis_blade' as type, module_number, ports, card_type, model, serial_number, NULL as name, NULL as description
                        FROM chassis_blades 
                        WHERE device_id = %s 
                        ORDER BY 
                        CASE 
                            WHEN module_number ~ '^[0-9]+$' THEN CAST(module_number AS INTEGER)
                            ELSE 999
                        END, module_number
                    """, [device_id])
                    
                    for row in cursor.fetchall():
                        component = {
                            'type': row[0],
                            'module_number': row[1],
                            'ports': row[2],
                            'description': row[3],
                            'model': row[4],
                            'serial_number': row[5]
                        }
                        device_data['components'].append(component)
                
                # Get hardware components (SFPs on interfaces)
                if not component_type or component_type == 'hardware_component':
                    cursor.execute("""
                        SELECT 'hardware_component' as type, name, description, pid, vid, serial_number, component_type
                        FROM hardware_components 
                        WHERE device_id = %s 
                        ORDER BY name
                    """, [device_id])
                    
                    for row in cursor.fetchall():
                        component = {
                            'type': row[0],
                            'interface': row[1],
                            'description': row[2],
                            'pid': row[3],
                            'vid': row[4],
                            'serial_number': row[5],
                            'component_type': row[6]
                        }
                        device_data['components'].append(component)
                
                # Get SFP modules
                if not component_type or component_type == 'sfp_module':
                    cursor.execute("""
                        SELECT 'sfp_module' as type, interface, module_type, status, product_id
                        FROM sfp_modules 
                        WHERE device_id = %s 
                        ORDER BY interface
                    """, [device_id])
                    
                    for row in cursor.fetchall():
                        component = {
                            'type': row[0],
                            'interface': row[1],
                            'module_type': row[2],
                            'status': row[3],
                            'product_id': row[4]
                        }
                        device_data['components'].append(component)
            
            result['total_components'] += len(device_data['components'])
            result['devices'].append(device_data)
        
        cursor.close()
        conn.close()
        
        print(f"📡 SSH Inventory API: Returning {len(result['devices'])} devices with {result['total_components']} total components")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in SSH inventory API: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@inventory_bp.route('/ssh-inventory')
def ssh_inventory():
    """
    SSH Network Device Inventory page with hierarchical component display
    """
    return render_template('ssh_inventory.html')
# ========================================
# COLLECTED INVENTORY ROUTES (July 4, 2025)
# ========================================

@inventory_bp.route('/collected-inventory')
def collected_inventory():
    """
    Collected Network Device Inventory page showing SSH-collected components
    """
    return render_template('collected_inventory.html')

@inventory_bp.route('/api/collected-inventory')
def api_collected_inventory():
    """
    API endpoint for collected inventory from SSH collections
    
    Returns hierarchical view of collected components from database
    
    Query Parameters:
        device_filter (str, optional): Filter by hostname or IP address
        component_type (str, optional): Filter by component type
        
    Returns:
        JSON response with collected inventory data
    """
    try:
        device_filter = request.args.get('device_filter', '').strip()
        component_type = request.args.get('component_type', '').strip()
        
        # Import the function from corp_network_data_db.py
        import sys
        sys.path.insert(0, '/usr/local/bin')
        from corp_network_data_db import get_collected_inventory_db
        
        # Get the collected inventory data
        result = get_collected_inventory_db()
        
        # Filter data if requested
        inventory_data = result.get('inventory', [])
        
        # Apply filters
        if device_filter:
            inventory_data = [
                item for item in inventory_data 
                if device_filter.lower() in item['hostname'].lower() or 
                   device_filter.lower() in item.get('ip', '').lower()
            ]
        
        if component_type and component_type != 'all':
            inventory_data = [
                item for item in inventory_data 
                if item['component_type'].lower() == component_type.lower()
            ]
        
        # Group by device for hierarchical display
        devices_dict = {}
        for item in inventory_data:
            hostname = item['hostname']
            if hostname not in devices_dict:
                devices_dict[hostname] = {
                    'hostname': hostname,
                    'ip': item.get('ip', 'N/A'),
                    'components': [],
                    'component_counts': {}
                }
            
            devices_dict[hostname]['components'].append(item)
            comp_type = item['component_type']
            devices_dict[hostname]['component_counts'][comp_type] = devices_dict[hostname]['component_counts'].get(comp_type, 0) + 1
        
        # Convert to list and sort
        devices_list = list(devices_dict.values())
        devices_list.sort(key=lambda x: x['hostname'])
        
        # Create response
        response = {
            'devices': devices_list,
            'summary': result.get('summary', {}),
            'total_devices': len(devices_list),
            'total_components': len(inventory_data),
            'component_types': list(set(item['component_type'] for item in inventory_data))
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Error in collected inventory API: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/api/inventory-corp-summary')
def api_inventory_corp_summary():
    """
    API endpoint for corporate network summary data (Tab 2)
    
    Returns:
        JSON response with corporate network summary data
    """
    try:
        data = get_corp_network_summary()
        return jsonify(data)
    except Exception as e:
        print(f"❌ Error in corp network summary API: {e}")
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/api/inventory-datacenter')
def api_inventory_datacenter():
    """
    API endpoint for datacenter inventory data (Tab 4)
    
    Returns:
        JSON response with datacenter inventory data
    """
    try:
        data = get_datacenter_inventory()
        return jsonify(data)
    except Exception as e:
        print(f"❌ Error in datacenter inventory API: {e}")
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/inventory-4tabs')
def inventory_4tabs():
    """
    4-Tab Inventory Page with Tab 4 using our processed data
    
    Returns:
        Rendered inventory page with 4 tabs including datacenter inventory
    """
    try:
        # Get data for all tabs
        # Tab 1: Meraki Executive Summary (placeholder for now)
        meraki_summary = {}
        
        # Tab 3: Get Meraki inventory summary data
        summary_data = get_inventory_summary_data()
        summary = summary_data.get('summary', [])
        org_names = summary_data.get('org_names', [])
        
        # Tab 2: Corp Network Summary
        corp_summary_response = get_corp_network_summary()
        corp_executive = corp_summary_response.get('data', {}) if corp_summary_response.get('status') == 'success' else {}
        
        # Tab 4: Datacenter Inventory
        datacenter_data = get_datacenter_inventory()
        
        # Pass all required data to template
        return render_template('inventory_final_4tabs.html', 
                             meraki_summary=meraki_summary,
                             summary=summary,
                             org_names=org_names,
                             corp_executive=corp_executive,
                             datacenter_data=datacenter_data)
    except Exception as e:
        print(f"❌ Error loading 4-tab inventory page: {e}")
        import traceback
        traceback.print_exc()
        return f"Error loading 4-tab inventory page: {e}", 500

