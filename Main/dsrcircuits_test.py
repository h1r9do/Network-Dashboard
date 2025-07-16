"""
MAIN CIRCUITS PAGE AND MERAKI INTEGRATION - DATABASE VERSION
===========================================================

Purpose:
    - Main circuits browsing and management interface
    - Meraki device integration and confirmation workflows  
    - Circuit data confirmation and push-to-Meraki functionality
    - Database-driven version using PostgreSQL

Pages Served:
    - / (root redirect to main page)
    - /dsrcircuits (main circuits data table and management)

Templates Used:
    - index.html (simple redirect page)
    - dsrcircuits.html (main circuits table with filtering, confirmation, Meraki integration)

API Endpoints:
    - /confirm/<site_name> (POST) - Get confirmation popup data for a site
    - /confirm/<site_name>/submit (POST) - Submit confirmed circuit data
    - /confirm/<site_name>/reset (POST) - Reset confirmation status
    - /push_to_meraki (POST) - Push confirmed circuits to Meraki devices
    - /api/sites-without-ips (GET) - Get sites without IP addresses on WAN interfaces

Key Functions:
    - Circuit data display with advanced filtering and search
    - Interactive confirmation workflow with data validation
    - Meraki device configuration pushing
    - Export functionality (Excel, PDF)
    - Real-time data updates and status tracking

Dependencies:
    - models.py (database models)
    - utils.py (shared utilities, Meraki functions)
    - confirm_meraki_notes.py (optional, for Meraki integration)

Data Sources:
    - circuits table (main circuit data)
    - enriched_circuits table (enriched circuit data with Meraki info)
    - meraki_inventory table (device inventory)

Features:
    - Advanced filtering by provider, speed, cost, role
    - Site confirmation workflow with multiple data sources
    - Meraki configuration validation and pushing
    - Data export and reporting
    - Real-time status updates
"""

from flask import Blueprint, render_template, jsonify, request, current_app
from sqlalchemy import and_, or_, func, text
from models import db, Circuit, EnrichedCircuit, MerakiInventory, EnrichedCircuitBeta, MerakiInventoryBeta
from sqlalchemy import func
from dsrcircuits_beta_combined import ProviderMatcher, assign_costs_improved
from datetime import datetime
import json
import logging
from utils import (
    MERAKI_FUNCTIONS_AVAILABLE,
    confirm_site, reset_confirmation, push_to_meraki
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
dsrcircuits_test_bp = Blueprint('dsrcircuits_test', __name__)

# Root route handled by main dsrcircuits_blueprint

@dsrcircuits_test_bp.route('/dsrcircuits-test')
def dsrcircuits_test_page():
    """
    IMPROVED: Main circuits data table page with provider-based cost matching
    
    Uses improved provider matching logic to accurately assign costs
    from Non-DSR circuits and other circuit records.
    
    Returns:
        Rendered dsrcircuits.html template with circuit data
    """
    try:
        # Get enriched circuits data from BETA TABLES
        enriched_circuits = db.session.query(EnrichedCircuitBeta).join(
            MerakiInventoryBeta,
            EnrichedCircuitBeta.network_name == MerakiInventoryBeta.network_name
        ).filter(
            # Exclude hub/lab/voice/test sites
            ~(
                EnrichedCircuitBeta.network_name.ilike('%hub%') |
                EnrichedCircuitBeta.network_name.ilike('%lab%') |
                EnrichedCircuitBeta.network_name.ilike('%voice%') |
                EnrichedCircuitBeta.network_name.ilike('%test%')
            )
        ).filter(
            # Exclude sites without any IP addresses in Meraki (not live)
            ~(
                ((MerakiInventoryBeta.wan1_ip.is_(None)) | (MerakiInventoryBeta.wan1_ip == '') | (MerakiInventoryBeta.wan1_ip == 'None')) &
                ((MerakiInventoryBeta.wan2_ip.is_(None)) | (MerakiInventoryBeta.wan2_ip == '') | (MerakiInventoryBeta.wan2_ip == 'None'))
            )
        ).order_by(EnrichedCircuitBeta.network_name).all()
        
        grouped_data = []
        
        for circuit in enriched_circuits:
            # Get all circuits for this site
            site_circuits = Circuit.query.filter(
                func.lower(Circuit.site_name) == func.lower(circuit.network_name),
                Circuit.status == 'Enabled'
            ).all()
            
            # Use improved cost assignment logic
            wan1_cost, wan2_cost, wan1_info, wan2_info = assign_costs_improved(circuit, site_circuits)
            
            # Initialize wireless badges
            wan1_wireless_badge = None
            wan2_wireless_badge = None
            
            grouped_data.append({
                'network_name': circuit.network_name,
                'device_tags': circuit.device_tags or [],
                'wan1': {
                    'provider': circuit.wan1_provider or '',
                    'speed': circuit.wan1_speed or '',
                    'monthly_cost': wan1_cost,
                    'circuit_role': circuit.wan1_circuit_role or 'Primary',
                    'confirmed': circuit.wan1_confirmed or False,
                    'match_info': wan1_info,
                    'wireless_badge': wan1_wireless_badge
                },
                'wan2': {
                    'provider': circuit.wan2_provider or '',
                    'speed': circuit.wan2_speed or '',
                    'monthly_cost': wan2_cost,
                    'circuit_role': circuit.wan2_circuit_role or 'Secondary',
                    'confirmed': circuit.wan2_confirmed or False,
                    'match_info': wan2_info,
                    'wireless_badge': wan2_wireless_badge
                }
            })
        
        # Use the updated template (now without role columns)
        return render_template('dsrcircuits_test.html', grouped_data=grouped_data)
        
    except Exception as e:
        logger.error(f"Error in main dsrcircuits: {e}")
        return render_template('dsrcircuits_test.html', error=f"Error: {e}")



@dsrcircuits_test_bp.route('/dsrcircuits-test')
def dsrcircuits_test():
    """
    TEST VERSION: Copy of production dsrcircuits for development
    
    Identical to production but serves on /dsrcircuits-test route
    for safe development and testing.
    
    Returns:
        Rendered dsrcircuits.html template with circuit data
    """
    try:
        # Check if we should show all networks or just Discount-Tire
        show_all_networks = request.args.get('filter') == 'all'
        # Debug: Check how many devices have Discount-Tire tag
        discount_tire_count = db.session.query(MerakiInventoryBeta).filter(
            db.text("device_tags @> ARRAY['Discount-Tire']")
        ).count()
        logger.info(f"DEBUG: Found {discount_tire_count} devices with Discount-Tire tag")
        
        # Build query based on filter
        query = db.session.query(EnrichedCircuitBeta).join(
            MerakiInventoryBeta,
            EnrichedCircuitBeta.network_name == MerakiInventoryBeta.network_name
        )
        
        # Apply Discount-Tire filter unless showing all networks
        if not show_all_networks:
            query = query.filter(
                # Only include networks where MerakiInventoryBeta has Discount-Tire tag
                db.text("meraki_inventory_beta.device_tags @> ARRAY['Discount-Tire']")
            )
            logger.info("Filtering for Discount-Tire tag only")
        else:
            logger.info("Showing all networks (no tag filter)")
        
        # Always exclude hub/lab/voice/test sites
        query = query.filter(
            ~(
                EnrichedCircuitBeta.network_name.ilike('%hub%') |
                EnrichedCircuitBeta.network_name.ilike('%lab%') |
                EnrichedCircuitBeta.network_name.ilike('%voice%') |
                EnrichedCircuitBeta.network_name.ilike('%test%')
            )
        ).filter(
            # Exclude sites without any IP addresses in Meraki (not live)
            ~(
                ((MerakiInventoryBeta.wan1_ip.is_(None)) | (MerakiInventoryBeta.wan1_ip == '') | (MerakiInventoryBeta.wan1_ip == 'None')) &
                ((MerakiInventoryBeta.wan2_ip.is_(None)) | (MerakiInventoryBeta.wan2_ip == '') | (MerakiInventoryBeta.wan2_ip == 'None'))
            )
        )
        
        # Execute query
        enriched_circuits = query.order_by(EnrichedCircuitBeta.network_name).all()
        
        logger.info(f"DEBUG: Query returned {len(enriched_circuits)} enriched circuits with Discount-Tire tag")
        
        grouped_data = []
        
        for circuit in enriched_circuits:
            # Get all circuits for this site
            site_circuits = Circuit.query.filter(
                func.lower(Circuit.site_name) == func.lower(circuit.network_name),
                Circuit.status == 'Enabled'
            ).all()
            
            # Use improved cost assignment logic
            wan1_cost, wan2_cost, wan1_info, wan2_info = assign_costs_improved(circuit, site_circuits)
            
            # Check for wireless badges
            wan1_wireless_badge = None
            wan2_wireless_badge = None
            
            # Check WAN1 for wireless (cell=VZW/AT&T, satellite=Starlink)
            meraki_device = MerakiInventoryBeta.query.filter_by(network_name=circuit.network_name).first()
            
            # Check for cellular providers
            if circuit.wan1_speed and 'cell' in circuit.wan1_speed.lower():
                if meraki_device and meraki_device.wan1_arin_provider:
                    arin_provider = meraki_device.wan1_arin_provider.upper()
                    if 'VERIZON' in arin_provider or 'VZW' in arin_provider:
                        wan1_wireless_badge = 'VZW'
                    elif 'AT&T' in arin_provider or 'ATT' in arin_provider:
                        wan1_wireless_badge = 'ATT'
            
            # Check for Starlink (satellite speed OR provider name OR SpaceX ARIN)
            if (circuit.wan1_speed and 'satellite' in circuit.wan1_speed.lower()) or \
               (circuit.wan1_provider and 'starlink' in circuit.wan1_provider.lower()) or \
               (meraki_device and meraki_device.wan1_arin_provider and 'SPACEX' in meraki_device.wan1_arin_provider.upper()):
                wan1_wireless_badge = 'STARLINK'
            
            # Check WAN2 for wireless (cell=VZW/AT&T, satellite=Starlink)
            if not meraki_device:
                meraki_device = MerakiInventoryBeta.query.filter_by(network_name=circuit.network_name).first()
            
            # Check for cellular providers
            if circuit.wan2_speed and 'cell' in circuit.wan2_speed.lower():
                if meraki_device and meraki_device.wan2_arin_provider:
                    arin_provider = meraki_device.wan2_arin_provider.upper()
                    if 'VERIZON' in arin_provider or 'VZW' in arin_provider:
                        wan2_wireless_badge = 'VZW'
                    elif 'AT&T' in arin_provider or 'ATT' in arin_provider:
                        wan2_wireless_badge = 'ATT'
            
            # Check for Starlink (satellite speed OR provider name OR SpaceX ARIN)
            if (circuit.wan2_speed and 'satellite' in circuit.wan2_speed.lower()) or \
               (circuit.wan2_provider and 'starlink' in circuit.wan2_provider.lower()) or \
               (meraki_device and meraki_device.wan2_arin_provider and 'SPACEX' in meraki_device.wan2_arin_provider.upper()):
                wan2_wireless_badge = 'STARLINK'
            
            grouped_data.append({
                'network_name': circuit.network_name,
                'device_tags': circuit.device_tags or [],
                'wan1': {
                    'provider': circuit.wan1_provider or '',
                    'speed': circuit.wan1_speed or '',
                    'monthly_cost': wan1_cost,
                    'circuit_role': circuit.wan1_circuit_role or 'Primary',
                    'confirmed': circuit.wan1_confirmed or False,
                    'match_info': wan1_info,
                    'wireless_badge': wan1_wireless_badge
                },
                'wan2': {
                    'provider': circuit.wan2_provider or '',
                    'speed': circuit.wan2_speed or '',
                    'monthly_cost': wan2_cost,
                    'circuit_role': circuit.wan2_circuit_role or 'Secondary',
                    'confirmed': circuit.wan2_confirmed or False,
                    'match_info': wan2_info,
                    'wireless_badge': wan2_wireless_badge
                }
            })
        
        # Calculate badge counts for header display
        dsr_count = vzw_count = att_count = starlink_count = 0
        
        for entry in grouped_data:
            # Count DSR badges - check if match_info is dict or object
            wan1_info = entry['wan1']['match_info']
            if wan1_info:
                if hasattr(wan1_info, 'dsr_verified'):
                    if wan1_info.dsr_verified:
                        dsr_count += 1
                elif isinstance(wan1_info, dict) and wan1_info.get('dsr_verified'):
                    dsr_count += 1
                    
            wan2_info = entry['wan2']['match_info']
            if wan2_info:
                if hasattr(wan2_info, 'dsr_verified'):
                    if wan2_info.dsr_verified:
                        dsr_count += 1
                elif isinstance(wan2_info, dict) and wan2_info.get('dsr_verified'):
                    dsr_count += 1
                
            # Count wireless providers (not badges, actual providers)
            # Check WAN1
            if entry['wan1'].get('wireless_badge'):
                if entry['wan1']['wireless_badge'] == 'VZW':
                    vzw_count += 1
                elif entry['wan1']['wireless_badge'] == 'ATT':
                    att_count += 1
            
            # Count Starlink based on provider name
            if entry['wan1']['provider'] and 'starlink' in entry['wan1']['provider'].lower():
                starlink_count += 1
                    
            # Check WAN2
            if entry['wan2'].get('wireless_badge'):
                if entry['wan2']['wireless_badge'] == 'VZW':
                    vzw_count += 1
                elif entry['wan2']['wireless_badge'] == 'ATT':
                    att_count += 1
                    
            # Count Starlink based on provider name
            if entry['wan2']['provider'] and 'starlink' in entry['wan2']['provider'].lower():
                starlink_count += 1
        
        badge_counts = {
            'dsr': dsr_count,
            'vzw': vzw_count, 
            'att': att_count,
            'starlink': starlink_count
        }
        
        # Get DSR data last updated timestamp from circuits table
        from datetime import datetime
        try:
            # Get the most recent updated_at from circuits table (when DSR data was last pulled)
            latest_dsr_update = db.session.execute(
                db.text("SELECT MAX(updated_at) FROM circuits WHERE updated_at IS NOT NULL")
            ).scalar()
            
            if latest_dsr_update:
                last_updated = latest_dsr_update.strftime("%B %d, %Y at %I:%M %p")
            else:
                # Fallback - check if we have any timestamp data
                last_updated = "DSR data timestamp unavailable"
        except Exception as e:
            print(f"Error getting DSR timestamp: {e}")
            last_updated = "Unable to determine DSR update time"
        
        # Use the test template with badge counts and timestamp
        return render_template('dsrcircuits_test.html', grouped_data=grouped_data, badge_counts=badge_counts, last_updated=last_updated)
        
    except Exception as e:
        logger.error(f"Error in test dsrcircuits: {e}")
        return render_template('dsrcircuits_test.html', error=f"Error: {e}")


@dsrcircuits_test_bp.route('/export/non-dsr-circuits')
def export_non_dsr_circuits():
    """Export all non-DSR circuits with site, interface, provider, speed, and cost"""
    try:
        from flask import make_response
        import csv
        from io import StringIO
        
        # Get sites that have DSR circuits (Primary circuits)
        dsr_sites = db.session.query(Circuit.site_name).filter(
            Circuit.circuit_purpose == 'Primary',
            Circuit.status == 'Enabled'
        ).subquery()
        
        # Query for non-DSR circuits (exclude all circuits from DSR sites)
        results = db.session.query(
            Circuit.site_name,
            Circuit.circuit_purpose,
            Circuit.provider_name,
            Circuit.details_service_speed,
            Circuit.billing_monthly_cost,
            Circuit.status,
            Circuit.ip_address_start,
            Circuit.sctask,
            Circuit.assigned_to
        ).filter(
            Circuit.status == 'Enabled',
            ~Circuit.site_name.in_(db.session.query(dsr_sites.c.site_name)),
            ~(
                Circuit.site_name.ilike('%hub%') |
                Circuit.site_name.ilike('%lab%') |
                Circuit.site_name.ilike('%voice%') |
                Circuit.site_name.ilike('%test%')
            )
        ).order_by(Circuit.site_name, Circuit.circuit_purpose).all()
        
        # Create CSV in memory
        si = StringIO()
        writer = csv.writer(si)
        
        # Write header
        writer.writerow([
            'Site Name',
            'Interface/Purpose',
            'Provider',
            'Speed',
            'Monthly Cost',
            'Status',
            'IP Address',
            'SCTASK',
            'Assigned To'
        ])
        
        # Write data
        for row in results:
            writer.writerow([
                row.site_name,
                row.circuit_purpose or 'Unknown',
                row.provider_name or 'N/A',
                row.details_service_speed or 'N/A',
                f"${row.billing_monthly_cost}" if row.billing_monthly_cost else 'N/A',
                row.status,
                row.ip_address_start or 'N/A',
                row.sctask or 'N/A',
                row.assigned_to or 'N/A'
            ])
        
        # Create response
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = f"attachment; filename=non_dsr_circuits_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output.headers["Content-type"] = "text/csv"
        
        return output
        
    except Exception as e:
        logger.error(f"Error exporting non-DSR circuits: {e}")
        return jsonify({'error': str(e)}), 500


@dsrcircuits_test_bp.route('/export/wan2-unknown-speeds')
def export_wan2_unknown_speeds():
    """Export WAN2 interfaces with unknown/N/A speed showing DSR vs ARIN provider data"""
    # Check if we want all providers or just AT&T/Verizon
    all_providers = request.args.get('all') == 'true'
    try:
        from flask import make_response
        import csv
        from io import StringIO
        
        # Query for WAN2 with unknown speed and AT&T or Verizon provider
        results = db.session.query(
            EnrichedCircuitBeta.network_name,
            EnrichedCircuitBeta.wan2_provider,
            EnrichedCircuitBeta.wan2_speed,
            MerakiInventoryBeta.wan2_ip,
            MerakiInventoryBeta.wan2_arin_provider,
            MerakiInventoryBeta.device_tags
        ).join(
            MerakiInventoryBeta,
            EnrichedCircuitBeta.network_name == MerakiInventoryBeta.network_name
        ).filter(
            # WAN2 speed is unknown or N/A
            db.or_(
                EnrichedCircuitBeta.wan2_speed.ilike('%unknown%'),
                EnrichedCircuitBeta.wan2_speed.ilike('%n/a%'),
                EnrichedCircuitBeta.wan2_speed.is_(None),
                EnrichedCircuitBeta.wan2_speed == '',
                EnrichedCircuitBeta.wan2_speed == 'N/A'
            )
        ).filter(
            # Exclude hub/lab/voice/test sites
            ~(
                EnrichedCircuitBeta.network_name.ilike('%hub%') |
                EnrichedCircuitBeta.network_name.ilike('%lab%') |
                EnrichedCircuitBeta.network_name.ilike('%voice%') |
                EnrichedCircuitBeta.network_name.ilike('%test%')
            )
        ).order_by(EnrichedCircuitBeta.network_name).all()
        
        # Create CSV in memory
        si = StringIO()
        writer = csv.writer(si)
        
        # Write header
        writer.writerow([
            'Network Name',
            'WAN2 DSR Provider', 
            'WAN2 Speed',
            'WAN2 IP',
            'WAN2 ARIN Provider',
            'Provider Match',
            'Device Tags'
        ])
        
        # Write data
        for row in results:
            # Convert tags list to string
            tags = row.device_tags if row.device_tags else []
            tags_str = ', '.join(tags) if isinstance(tags, list) else str(tags)
            
            # Check if providers match
            provider_match = 'No'
            if row.wan2_provider and row.wan2_arin_provider:
                if row.wan2_provider.lower() != 'unknown' and row.wan2_provider.lower() != 'n/a':
                    provider_match = 'Yes'
                elif 'at&t' in row.wan2_arin_provider.lower() or 'verizon' in row.wan2_arin_provider.lower():
                    provider_match = 'ARIN has data!'
            
            writer.writerow([
                row.network_name,
                row.wan2_provider or 'N/A',
                row.wan2_speed or 'Unknown',
                row.wan2_ip or 'N/A',
                row.wan2_arin_provider or 'N/A',
                provider_match,
                tags_str
            ])
        
        # Create response
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = f"attachment; filename=wan2_unknown_speeds_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output.headers["Content-type"] = "text/csv"
        
        return output
        
    except Exception as e:
        logger.error(f"Error exporting WAN2 unknown speeds: {e}")
        return jsonify({'error': str(e)}), 500


@dsrcircuits_test_bp.route('/api/circuits/data')
def circuits_data_api():
    """
    Progressive loading API for circuit data
    
    Supports pagination for faster initial page loads.
    
    Query Parameters:
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 50, max: 200)
        search (str): Search term for filtering
    
    Returns:
        JSON response with paginated circuit data
    """
    import time
    start_time = time.time()
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 200)  # Max 200 per page
        search = request.args.get('search', '', type=str)
        
        # Build cache key including parameters
        cache_key = f"circuits_api_page_{page}_{per_page}_{search}"
        redis_conn = None
        
        try:
            from config import get_redis_connection
            redis_conn = get_redis_connection()
            if redis_conn:
                cached_result = redis_conn.get(cache_key)
                if cached_result:
                    import json
                    result = json.loads(cached_result)
                    cache_time = time.time() - start_time
                    print(f"⚡ /api/circuits/data cache hit - page {page} in {cache_time*1000:.1f}ms")
                    return jsonify(result)
        except Exception as e:
            print(f"Redis cache error: {e}")
            redis_conn = None
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Build query with optional search
        base_query = """
            SELECT 
                network_name,
                device_tags,
                wan1_provider, wan1_speed, wan1_circuit_role, wan1_confirmed,
                wan2_provider, wan2_speed, wan2_circuit_role, wan2_confirmed,
                wan1_cost, wan2_cost
            FROM v_circuit_summary
        """
        
        count_query = "SELECT COUNT(*) FROM v_circuit_summary"
        
        params = {}
        if search:
            search_filter = """
                WHERE (
                    network_name ILIKE :search
                    OR wan1_provider ILIKE :search
                    OR wan2_provider ILIKE :search
                    OR wan1_speed ILIKE :search
                    OR wan2_speed ILIKE :search
                )
            """
            base_query += search_filter
            count_query += search_filter
            params['search'] = f'%{search}%'
        
        # Get total count
        total_count = db.session.execute(db.text(count_query), params).scalar()
        
        # Get paginated data
        data_query = base_query + " ORDER BY network_name LIMIT :limit OFFSET :offset"
        params.update({'limit': per_page, 'offset': offset})
        
        result_rows = db.session.execute(db.text(data_query), params).fetchall()
        
        query_time = time.time() - start_time
        print(f"⏱️ API query took {query_time*1000:.1f}ms for {len(result_rows)} circuits (page {page})")
        
        # Convert to expected format
        circuits_data = []
        for row in result_rows:
            # Parse device tags
            device_tags = []
            if row.device_tags:
                try:
                    if isinstance(row.device_tags, str):
                        device_tags = json.loads(row.device_tags)
                    elif isinstance(row.device_tags, list):
                        device_tags = row.device_tags
                except:
                    device_tags = []
            
            # Format costs
            wan1_cost = f"${float(row.wan1_cost):.2f}" if row.wan1_cost else '$0.00'
            wan2_cost = f"${float(row.wan2_cost):.2f}" if row.wan2_cost else '$0.00'
            
            circuit_data = {
                'network_name': row.network_name,
                'device_tags': device_tags,
                'wan1': {
                    'provider': row.wan1_provider or '',
                    'speed': row.wan1_speed or '',
                    'monthly_cost': wan1_cost,
                    'circuit_role': row.wan1_circuit_role or 'Primary',
                    'confirmed': row.wan1_confirmed or False
                },
                'wan2': {
                    'provider': row.wan2_provider or '',
                    'speed': row.wan2_speed or '',
                    'monthly_cost': wan2_cost,
                    'circuit_role': row.wan2_circuit_role or 'Secondary',
                    'confirmed': row.wan2_confirmed or False
                }
            }
            circuits_data.append(circuit_data)
        
        # Calculate pagination info
        total_pages = (total_count + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
        result = {
            'data': circuits_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'total_pages': total_pages,
                'has_next': has_next,
                'has_prev': has_prev
            },
            'search': search,
            'query_time_ms': int((time.time() - start_time) * 1000)
        }
        
        # Cache for 2 minutes (shorter than main cache)
        if redis_conn:
            try:
                import json
                redis_conn.setex(cache_key, 120, json.dumps(result))
                print(f"📊 Cached API page {page} for 2 minutes")
            except Exception as e:
                print(f"Redis cache set error: {e}")
        
        processing_time = time.time() - start_time
        print(f"✅ API returned {len(circuits_data)} circuits in {processing_time*1000:.1f}ms")
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        print(f"❌ Error in circuits API: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        current_app.logger.error(f"Error in circuits API: {str(e)}")
        return jsonify({"error": str(e)}), 500

@dsrcircuits_test_bp.route('/dsrcircuits-legacy')
def dsrcircuits_legacy():
    """
    LEGACY: Main circuits data table page - DATABASE VERSION
    
    Original version kept for rollback purposes.
    
    Returns:
        Rendered dsrcircuits.html template with circuit data
    """
    try:
        # Query enriched circuits from database, excluding those with hub, lab, voice, datacenter, test in network name or device tags
        enriched_circuits = EnrichedCircuitBeta.query.filter(
            ~(
                # Exclude by network name patterns
                EnrichedCircuitBeta.network_name.ilike('%hub%') |
                EnrichedCircuitBeta.network_name.ilike('%lab%') |
                EnrichedCircuitBeta.network_name.ilike('%voice%') |
                EnrichedCircuitBeta.network_name.ilike('%datacenter%') |
                EnrichedCircuitBeta.network_name.ilike('%test%') |
                EnrichedCircuitBeta.network_name.ilike('%store in a box%') |
                EnrichedCircuitBeta.network_name.ilike('%sib%')  # Store in a box abbreviation
            )
        ).filter(
            db.text("""
                NOT EXISTS (
                    SELECT 1 FROM unnest(device_tags) AS tag 
                    WHERE LOWER(tag) LIKE '%hub%' 
                       OR LOWER(tag) LIKE '%lab%' 
                       OR LOWER(tag) LIKE '%voice%'
                       OR LOWER(tag) LIKE '%test%'
                       OR LOWER(tag) = 'hub'
                       OR LOWER(tag) = 'lab'
                       OR LOWER(tag) = 'voice'
                       OR LOWER(tag) = 'test'
                )
            """)
        ).order_by(EnrichedCircuitBeta.network_name).all()
        print(f"🔍 Found {len(enriched_circuits)} enriched circuits in database")
        
        # If no enriched circuits, try to build from main circuits table
        if not enriched_circuits:
            print("⚠️ No enriched circuits found, building from circuits table")
            
            # Get all unique site names from circuits, excluding hub/lab/voice/datacenter/test sites
            sites = db.session.query(Circuit.site_name).filter(
                ~(
                    Circuit.site_name.ilike('%hub%') |
                    Circuit.site_name.ilike('%lab%') |
                    Circuit.site_name.ilike('%voice%') |
                    Circuit.site_name.ilike('%datacenter%') |
                    Circuit.site_name.ilike('%test%') |
                    Circuit.site_name.ilike('%store in a box%') |
                    Circuit.site_name.ilike('%sib%')  # Store in a box abbreviation
                )
            ).distinct().all()
            
            grouped_data = []
            for (site_name,) in sites:
                if not site_name:
                    continue
                    
                # Get all circuits for this site
                site_circuits = Circuit.query.filter_by(site_name=site_name).all()
                
                # Find primary and secondary circuits
                primary_circuit = None
                secondary_circuit = None
                
                for circuit in site_circuits:
                    if circuit.circuit_purpose:
                        purpose_lower = circuit.circuit_purpose.lower()
                        if purpose_lower == 'primary' and not primary_circuit:
                            primary_circuit = circuit
                        elif purpose_lower == 'secondary' and not secondary_circuit:
                            secondary_circuit = circuit
                        elif 'backup' in purpose_lower and not secondary_circuit:
                            secondary_circuit = circuit
                
                # Build enriched data structure
                enriched_data = {
                    'network_name': site_name,
                    'device_tags': [],
                    'wan1': {},
                    'wan2': {}
                }
                
                # Always initialize both WAN structures
                enriched_data['wan1'] = {
                    'provider': '',
                    'speed': '',
                    'monthly_cost': '$0.00',
                    'circuit_role': 'Primary',
                    'ip_address': '',
                    'confirmed': False
                }
                enriched_data['wan2'] = {
                    'provider': '',
                    'speed': '',
                    'monthly_cost': '$0.00',
                    'circuit_role': 'Secondary',
                    'ip_address': '',
                    'confirmed': False
                }
                
                # Add primary circuit data
                if primary_circuit:
                    cost = primary_circuit.billing_monthly_cost
                    if cost is not None:
                        try:
                            cost_str = f"${float(cost):.2f}"
                        except:
                            cost_str = '$0.00'
                    else:
                        cost_str = '$0.00'
                        
                    enriched_data['wan1']['provider'] = primary_circuit.provider_name or ''
                    enriched_data['wan1']['speed'] = primary_circuit.details_ordered_service_speed or ''
                    enriched_data['wan1']['monthly_cost'] = cost_str
                    enriched_data['wan1']['ip_address'] = primary_circuit.ip_address_start or ''
                
                # Add secondary circuit data
                if secondary_circuit:
                    cost = secondary_circuit.billing_monthly_cost
                    if cost is not None:
                        try:
                            cost_str = f"${float(cost):.2f}"
                        except:
                            cost_str = '$0.00'
                    else:
                        cost_str = '$0.00'
                        
                    enriched_data['wan2']['provider'] = secondary_circuit.provider_name or ''
                    enriched_data['wan2']['speed'] = secondary_circuit.details_ordered_service_speed or ''
                    enriched_data['wan2']['monthly_cost'] = cost_str
                    enriched_data['wan2']['ip_address'] = secondary_circuit.ip_address_start or ''
                
                grouped_data.append(enriched_data)
            
            print(f"✅ Built {len(grouped_data)} circuit groups from database")
            
        else:
            # Convert enriched circuits to expected format
            grouped_data = []
            for circuit in enriched_circuits:
                # Parse device tags if stored as JSON string
                device_tags = []
                if circuit.device_tags:
                    try:
                        device_tags = json.loads(circuit.device_tags)
                    except:
                        device_tags = []
                
                # Get cost data from circuits table (DSR source of truth)
                # Important: DSR Primary/Secondary is just informational - match by provider!
                wan1_cost = '$0.00'
                wan2_cost = '$0.00'
                
                # Get ALL enabled circuits for this site
                site_circuits = Circuit.query.filter(
                    func.lower(Circuit.site_name) == func.lower(circuit.network_name),
                    Circuit.status == 'Enabled'
                ).all()
                
                # Match circuits to WAN1/WAN2 based on provider matching
                for dsr_circuit in site_circuits:
                    if not dsr_circuit.billing_monthly_cost:
                        continue
                        
                    # Normalize provider names for comparison
                    dsr_provider = (dsr_circuit.provider_name or '').upper().strip()
                    
                    # Try to match with WAN1 provider
                    wan1_provider = (circuit.wan1_provider or '').upper().strip()
                    if wan1_provider and dsr_provider:
                        # Check for common provider name variations
                        if (dsr_provider in wan1_provider or wan1_provider in dsr_provider or
                            # Spectrum/Charter variations
                            ('SPECTRUM' in dsr_provider and ('CHARTER' in wan1_provider or 'SPECTRUM' in wan1_provider)) or
                            ('CHARTER' in dsr_provider and ('SPECTRUM' in wan1_provider or 'CHARTER' in wan1_provider)) or
                            # AT&T variations
                            ('AT&T' in dsr_provider and 'AT&T' in wan1_provider) or
                            ('ATT' in dsr_provider and 'AT&T' in wan1_provider) or
                            # Cox variations
                            ('COX' in dsr_provider and 'COX' in wan1_provider) or
                            # Comcast variations
                            ('COMCAST' in dsr_provider and 'COMCAST' in wan1_provider) or
                            # Verizon variations
                            ('VERIZON' in dsr_provider and 'VERIZON' in wan1_provider) or
                            # CenturyLink variations
                            ('CENTURYLINK' in dsr_provider and ('CENTURYLINK' in wan1_provider or 'CENTURY LINK' in wan1_provider)) or
                            ('CENTURY LINK' in dsr_provider and ('CENTURYLINK' in wan1_provider or 'CENTURY LINK' in wan1_provider)) or
                            ('QWEST' in dsr_provider and 'CENTURYLINK' in wan1_provider) or
                            ('LUMEN' in dsr_provider and 'CENTURYLINK' in wan1_provider) or
                            # Other providers
                            ('SPARKLIGHT' in dsr_provider and 'SPARKLIGHT' in wan1_provider) or
                            ('FRONTIER' in dsr_provider and 'FRONTIER' in wan1_provider) or
                            ('WINDSTREAM' in dsr_provider and 'WINDSTREAM' in wan1_provider) or
                            ('OPTIMUM' in dsr_provider and ('OPTIMUM' in wan1_provider or 'ALTICE' in wan1_provider)) or
                            ('ALTICE' in dsr_provider and ('OPTIMUM' in wan1_provider or 'ALTICE' in wan1_provider))):
                            try:
                                wan1_cost = f"${float(dsr_circuit.billing_monthly_cost):.2f}"
                            except:
                                wan1_cost = '$0.00'
                            continue
                    
                    # Try to match with WAN2 provider
                    wan2_provider = (circuit.wan2_provider or '').upper().strip()
                    if wan2_provider and dsr_provider:
                        if (dsr_provider in wan2_provider or wan2_provider in dsr_provider or
                            # Spectrum/Charter variations
                            ('SPECTRUM' in dsr_provider and ('CHARTER' in wan2_provider or 'SPECTRUM' in wan2_provider)) or
                            ('CHARTER' in dsr_provider and ('SPECTRUM' in wan2_provider or 'CHARTER' in wan2_provider)) or
                            # AT&T variations
                            ('AT&T' in dsr_provider and 'AT&T' in wan2_provider) or
                            ('ATT' in dsr_provider and 'AT&T' in wan2_provider) or
                            # Cox variations
                            ('COX' in dsr_provider and 'COX' in wan2_provider) or
                            # Comcast variations
                            ('COMCAST' in dsr_provider and 'COMCAST' in wan2_provider) or
                            # Verizon variations
                            ('VERIZON' in dsr_provider and 'VERIZON' in wan2_provider) or
                            # CenturyLink variations
                            ('CENTURYLINK' in dsr_provider and ('CENTURYLINK' in wan2_provider or 'CENTURY LINK' in wan2_provider)) or
                            ('CENTURY LINK' in dsr_provider and ('CENTURYLINK' in wan2_provider or 'CENTURY LINK' in wan2_provider)) or
                            ('QWEST' in dsr_provider and 'CENTURYLINK' in wan2_provider) or
                            ('LUMEN' in dsr_provider and 'CENTURYLINK' in wan2_provider) or
                            # Other providers
                            ('SPARKLIGHT' in dsr_provider and 'SPARKLIGHT' in wan2_provider) or
                            ('FRONTIER' in dsr_provider and 'FRONTIER' in wan2_provider) or
                            ('WINDSTREAM' in dsr_provider and 'WINDSTREAM' in wan2_provider) or
                            ('OPTIMUM' in dsr_provider and ('OPTIMUM' in wan2_provider or 'ALTICE' in wan2_provider)) or
                            ('ALTICE' in dsr_provider and ('OPTIMUM' in wan2_provider or 'ALTICE' in wan2_provider))):
                            try:
                                wan2_cost = f"${float(dsr_circuit.billing_monthly_cost):.2f}"
                            except:
                                wan2_cost = '$0.00'
                
                enriched_data = {
                    'network_name': circuit.network_name,
                    'device_tags': device_tags,
                    'wan1': {
                        'provider': circuit.wan1_provider or '',
                        'speed': circuit.wan1_speed or '',
                        'monthly_cost': wan1_cost,  # Cost from DSR matched by provider
                        'circuit_role': circuit.wan1_circuit_role or 'Primary',
                        'confirmed': circuit.wan1_confirmed or False
                    },
                    'wan2': {
                        'provider': circuit.wan2_provider or '',
                        'speed': circuit.wan2_speed or '',
                        'monthly_cost': wan2_cost,  # Cost from DSR matched by provider
                        'circuit_role': circuit.wan2_circuit_role or 'Secondary',
                        'confirmed': circuit.wan2_confirmed or False
                    },
                    # Push tracking removed - no longer needed
                }
                grouped_data.append(enriched_data)
            
            print(f"✅ Loaded {len(grouped_data)} circuit groups from enriched_circuits table")
        
        return render_template('dsrcircuits_test.html', grouped_data=grouped_data)
        
    except Exception as e:
        import traceback
        print(f"❌ Error loading circuit data from database: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        current_app.logger.error(f"Error in dsrcircuits: {str(e)}")
        return render_template('dsrcircuits_test.html', error=f"Error loading data: {e}")

@dsrcircuits_test_bp.route('/api/sites-without-ips', methods=['GET'])
def sites_without_ips():
    """
    Get sites that have missing IP addresses on circuits - DATABASE VERSION
    
    This endpoint queries the database to identify sites where circuits
    are missing IP addresses, indicating incomplete configurations.
    
    Returns:
        JSON response with sites missing IP addresses
    """
    try:
        # Query circuits without IP addresses
        circuits_without_ip = Circuit.query.filter(
            or_(
                Circuit.ip_address_start == None,
                Circuit.ip_address_start == '',
                Circuit.ip_address_start == 'None'
            )
        ).all()
        
        # Group by site
        sites_without_ips = {}
        for circuit in circuits_without_ip:
            if circuit.site_name:
                if circuit.site_name not in sites_without_ips:
                    sites_without_ips[circuit.site_name] = {
                        'site_name': circuit.site_name,
                        'missing_ips': []
                    }
                
                sites_without_ips[circuit.site_name]['missing_ips'].append({
                    'circuit_purpose': circuit.circuit_purpose or 'Unknown',
                    'provider': circuit.provider_name or 'Unknown',
                    'status': circuit.status or 'Unknown'
                })
        
        # Get total site count
        total_sites = db.session.query(func.count(func.distinct(Circuit.site_name))).scalar()
        
        result = {
            'sites': list(sites_without_ips.keys()),
            'total_sites': total_sites,
            'sites_without_ips': len(sites_without_ips),
            'details': list(sites_without_ips.values())
        }
        
        print(f"🔍 Found {len(sites_without_ips)} sites without IP addresses")
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error finding sites without IPs: {e}")
        current_app.logger.error(f"Error in sites_without_ips: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Keep the existing Meraki integration endpoints as they are
@dsrcircuits_test_bp.route('/confirm/<site_name>', methods=['POST'])
def confirm_circuit(site_name):
    """Handle circuit confirmation popup data"""
    logger.info(f"Confirm circuit called for site: {site_name}")
    result = confirm_site(site_name)
    logger.info(f"Confirm result for {site_name}: {result}")
    return jsonify(result)

@dsrcircuits_test_bp.route('/confirm/<site_name>/submit', methods=['POST'])
def submit_confirmation(site_name):
    """Submit confirmed circuit data to database and push to Meraki"""
    logger.info(f"Submit confirmation called for site: {site_name}")
    data = request.get_json()
    logger.info(f"Confirmation data: {data}")
    
    try:
        # Get the existing enriched circuit (case-insensitive)
        circuit = EnrichedCircuitBeta.query.filter(func.lower(EnrichedCircuitBeta.network_name) == func.lower(site_name)).first()
        
        if not circuit:
            # Create new enriched circuit if it doesn't exist
            circuit = EnrichedCircuitBeta(network_name=site_name)
            db.session.add(circuit)
        
        # Update with confirmed data - ONLY provider and speed, NOT cost!
        # Cost data comes exclusively from DSR nightly pull
        if 'wan1' in data:
            circuit.wan1_provider = data['wan1'].get('provider', '')
            circuit.wan1_speed = data['wan1'].get('speed', '')
            # DO NOT update wan1_monthly_cost - this comes from DSR only
            circuit.wan1_circuit_role = data['wan1'].get('circuit_role', 'Primary')
            circuit.wan1_confirmed = True
        
        if 'wan2' in data:
            circuit.wan2_provider = data['wan2'].get('provider', '')
            circuit.wan2_speed = data['wan2'].get('speed', '')
            # DO NOT update wan2_monthly_cost - this comes from DSR only
            circuit.wan2_circuit_role = data['wan2'].get('circuit_role', 'Secondary')
            circuit.wan2_confirmed = True
        
        circuit.last_updated = datetime.utcnow()
        
        # Save to database first
        db.session.commit()
        
        # Now push to Meraki
        logger.info(f"Pushing to Meraki for site: {site_name}")
        push_result = push_to_meraki([site_name])
        
        # Check if push was successful
        if push_result.get('success'):
            # Push successful - no need to track status
            
            # Also update the device notes in meraki_inventory_beta with the formatted notes
            meraki_device = MerakiInventoryBeta.query.filter(func.lower(MerakiInventoryBeta.network_name) == func.lower(site_name)).first()
            if meraki_device:
                # Build formatted notes for Meraki
                notes_lines = []
                if 'wan1' in data and data['wan1'].get('provider'):
                    notes_lines.append("WAN 1")
                    notes_lines.append(data['wan1']['provider'])
                    if data['wan1'].get('speed'):
                        notes_lines.append(data['wan1']['speed'])
                
                if 'wan2' in data and data['wan2'].get('provider'):
                    notes_lines.append("WAN 2")
                    notes_lines.append(data['wan2']['provider'])
                    if data['wan2'].get('speed'):
                        notes_lines.append(data['wan2']['speed'])
                
                formatted_notes = "\n".join(notes_lines)
                meraki_device.device_notes = formatted_notes
                
                # Update parsed labels
                if 'wan1' in data:
                    meraki_device.wan1_provider_label = data['wan1'].get('provider', '')
                    meraki_device.wan1_speed_label = data['wan1'].get('speed', '')
                if 'wan2' in data:
                    meraki_device.wan2_provider_label = data['wan2'].get('provider', '')
                    meraki_device.wan2_speed_label = data['wan2'].get('speed', '')
                
                meraki_device.last_updated = datetime.utcnow()
                db.session.commit()
            
            return jsonify({
                "success": True, 
                "message": f"Data saved and pushed to Meraki for {site_name}",
                "pushed": True,
                "notes": formatted_notes
            })
        else:
            # Save succeeded but push failed
            error_msg = push_result.get('error', 'Unknown error pushing to Meraki')
            return jsonify({
                "success": True,
                "message": f"Data saved but failed to push to Meraki: {error_msg}",
                "pushed": False,
                "error": error_msg
            })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error saving confirmation: {e}")
        return jsonify({"error": str(e)}), 500

@dsrcircuits_test_bp.route('/confirm/<site_name>/reset', methods=['POST'])
def reset_confirmation_status(site_name):
    """Reset confirmation status for a site"""
    result = reset_confirmation(site_name)
    return jsonify(result)

@dsrcircuits_test_bp.route('/dsrallcircuits')
def dsrallcircuits():
    """
    All circuits data table page - shows all enabled circuits from database
    
    Displays all enabled circuits with site name, site ID, circuit purpose,
    provider, speed, and cost in a sortable/filterable table format.
    
    Returns:
        Rendered dsrallcircuits.html template with all enabled circuit data
    """
    try:
        # Query only "Enabled" circuits (exclude "Enabled/Disconnected")
        enabled_circuits = Circuit.query.filter(
            Circuit.status == 'Enabled'
        ).all()
        
        print(f"🔍 Found {len(enabled_circuits)} enabled circuits in database")
        
        # Convert to display format
        circuits_data = []
        for circuit in enabled_circuits:
            # Format cost
            cost = circuit.billing_monthly_cost
            if cost is not None:
                try:
                    cost_str = f"${float(cost):.2f}"
                except:
                    cost_str = '$0.00'
            else:
                cost_str = '$0.00'
            
            circuit_data = {
                'site_name': circuit.site_name or '',
                'site_id': circuit.site_id or '',
                'circuit_purpose': circuit.circuit_purpose or '',
                'provider_name': circuit.provider_name or '',
                'details_ordered_service_speed': circuit.details_ordered_service_speed or '',
                'billing_monthly_cost': cost_str,
                'status': circuit.status or ''
            }
            circuits_data.append(circuit_data)
        
        print(f"✅ Prepared {len(circuits_data)} circuits for display")
        
        return render_template('dsrallcircuits.html', circuits_data=circuits_data)
        
    except Exception as e:
        import traceback
        print(f"❌ Error loading all circuits data: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        current_app.logger.error(f"Error in dsrallcircuits: {str(e)}")
        return render_template('dsrallcircuits.html', error=f"Error loading data: {e}")

@dsrcircuits_test_bp.route('/push_to_meraki', methods=['POST'])
def push_to_meraki_endpoint():
    """Push confirmed circuits to Meraki devices"""
    logger.info("Push to Meraki endpoint called")
    
    data = request.get_json()
    logger.info(f"Request data: {data}")
    
    if not data or 'sites' not in data:
        logger.error("No sites provided in request")
        return jsonify({"error": "No sites provided"}), 400
    
    sites = data['sites']
    logger.info(f"Pushing {len(sites)} sites to Meraki: {sites}")
    
    # Process in smaller batches to avoid timeout
    if len(sites) > 50:
        logger.info(f"Large batch detected ({len(sites)} sites), processing first 50 only")
        # Return information about the batch limitation
        return jsonify({
            "error": f"Too many sites to process at once ({len(sites)}). Please refresh the page to see already pushed sites.",
            "info": "The system has marked sites as pushed in the database. Refresh to see current status.",
            "sites_count": len(sites)
        }), 400
    
    result = push_to_meraki(sites)
    
    logger.info(f"Push result: {result}")
    
    # Check if we have partial success - don't return 400 if some sites succeeded
    if result.get('success') and result.get('successful', 0) > 0:
        # Some sites succeeded - return 200 with detailed results
        return jsonify(result), 200
    elif result.get('error'):
        # Complete failure - return 400
        return jsonify(result), 400
    else:
        # Default to success response
        return jsonify(result), 200

# ========================================
# PROVIDER MATCHING TEST ROUTES
# ========================================

@dsrcircuits_test_bp.route('/provider-test')
def provider_matching_test():
    """Provider matching test interface using provider_match_test table"""
    
    try:
        # Get statistics from test table
        stats_query = db.session.execute(text("SELECT * FROM provider_test_statistics"))
        stats_row = stats_query.fetchone()
        stats = dict(stats_row._mapping) if stats_row else {}
        
        # Get sample data
        sample_query = db.session.execute(text("""
            SELECT * FROM provider_match_test_display
            ORDER BY provider_match_confidence DESC, site_name
            LIMIT 20
        """))
        sample_circuits = [dict(row._mapping) for row in sample_query.fetchall()]
        
        return render_template('provider_matching_test.html', 
                             stats=stats, 
                             sample_circuits=sample_circuits)
    except Exception as e:
        logger.error(f"Error in provider-matching-test: {e}")
        return f"Error: {e}", 500

@dsrcircuits_test_bp.route('/api/circuit-matches-test/<site_name>')
def get_circuit_matches_test(site_name):
    """Get circuit matches for a specific site from test table"""
    
    try:
        circuits_query = db.session.execute(text("""
            SELECT 
                circuit_purpose,
                dsr_provider,
                arin_provider,
                provider_match_status as match_status,
                provider_match_confidence as match_confidence,
                match_reason,
                CASE 
                    WHEN provider_match_status = 'matched' AND provider_match_confidence >= 90 THEN '✓'
                    WHEN provider_match_status = 'matched' AND provider_match_confidence >= 70 THEN '⚠'
                    WHEN provider_match_status = 'no_match' THEN '✗'
                    ELSE '?'
                END as match_icon,
                CASE 
                    WHEN provider_match_confidence >= 95 THEN 'Excellent'
                    WHEN provider_match_confidence >= 80 THEN 'Good'
                    WHEN provider_match_confidence >= 70 THEN 'Fair'
                    WHEN provider_match_confidence > 0 THEN 'Poor'
                    ELSE 'No Match'
                END as match_quality,
                CASE 
                    WHEN provider_match_confidence >= 90 THEN 'success'
                    WHEN provider_match_confidence >= 70 THEN 'warning'
                    WHEN provider_match_status = 'no_match' THEN 'danger'
                    ELSE 'secondary'
                END as match_color,
                speed,
                cost
            FROM provider_match_test
            WHERE site_name = :site_name
            ORDER BY circuit_purpose
        """), {"site_name": site_name})
        
        circuits = [dict(row._mapping) for row in circuits_query.fetchall()]
        
        # Calculate summary
        total_count = len(circuits)
        matched_count = sum(1 for c in circuits if c['match_status'] == 'matched')
        avg_confidence = sum(c['match_confidence'] for c in circuits if c['match_confidence']) / total_count if total_count > 0 else 0
        
        return jsonify({
            'site_name': site_name,
            'circuits': circuits,
            'total_count': total_count,
            'matched_count': matched_count,
            'avg_confidence': round(avg_confidence, 1),
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Error getting test circuit matches for {site_name}: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@dsrcircuits_test_bp.route('/api/test-statistics')
def get_test_statistics_api():
    """Get provider matching test statistics"""
    
    try:
        stats_query = db.session.execute(text("SELECT * FROM provider_test_statistics"))
        stats_row = stats_query.fetchone()
        stats = dict(stats_row._mapping) if stats_row else {}
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting test statistics: {e}")
        return jsonify({'error': str(e)}), 500

@dsrcircuits_test_bp.route('/api/test-no-matches')
def get_test_no_matches():
    """Get circuits that didn't match for analysis"""
    
    try:
        no_matches_query = db.session.execute(text("""
            SELECT site_name, circuit_purpose, dsr_provider, arin_provider, 
                   match_reason, provider_match_confidence
            FROM provider_match_test
            WHERE provider_match_status IN ('no_match', 'no_data')
            ORDER BY site_name, circuit_purpose
            LIMIT 50
        """))
        
        no_matches = [dict(row._mapping) for row in no_matches_query.fetchall()]
        
        return jsonify({
            'no_matches': no_matches,
            'count': len(no_matches),
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Error getting no matches: {e}")
        return jsonify({'error': str(e)}), 500

@dsrcircuits_test_bp.route('/test-site/<site_name>')
def test_site_circuits(site_name):
    """Test page to show circuits for a specific site"""
    
    try:
        # Get test results for this site
        test_query = db.session.execute(text("""
            SELECT * FROM provider_match_test_display
            WHERE site_name = :site_name
            ORDER BY circuit_purpose
        """), {"site_name": site_name})
        
        test_circuits = [dict(row._mapping) for row in test_query.fetchall()]
        
        # Get original DSR data for comparison
        dsr_circuits = Circuit.query.filter_by(site_name=site_name, status='Enabled').all()
        dsr_circuits_data = [{
            'site_name': c.site_name,
            'circuit_purpose': c.circuit_purpose,
            'provider_name': c.provider_name,
            'ip_address_start': c.ip_address_start,
            'details_ordered_service_speed': c.details_ordered_service_speed,
            'billing_monthly_cost': c.billing_monthly_cost
        } for c in dsr_circuits]
        
        return render_template('test_site_circuits.html',
                             site_name=site_name,
                             test_circuits=test_circuits,
                             dsr_circuits=dsr_circuits_data)
        
    except Exception as e:
        logger.error(f"Error testing site {site_name}: {e}")
        return f"Error: {e}", 500