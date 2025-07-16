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
from sqlalchemy import and_, or_, func
from models import db, Circuit, EnrichedCircuit, MerakiInventory
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
dsrcircuits_bp = Blueprint('dsrcircuits', __name__)

@dsrcircuits_bp.route('/')
def index():
    """
    Default route - redirect to main circuits page
    
    Returns:
        Rendered index.html template (simple redirect page)
    """
    return render_template('index.html')

@dsrcircuits_bp.route('/dsrcircuits')
def dsrcircuits():
    """
    IMPROVED: Main circuits data table page with provider-based cost matching
    
    Uses improved provider matching logic to accurately assign costs
    from Non-DSR circuits and other circuit records.
    
    Returns:
        Rendered dsrcircuits.html template with circuit data
    """
    try:
        # Check if we should show all networks or just Discount-Tire
        show_all_networks = request.args.get('filter') == 'all'
        
        # Build query based on filter
        query = db.session.query(EnrichedCircuit, MerakiInventory).join(
            MerakiInventory,
            EnrichedCircuit.network_name == MerakiInventory.network_name
        )
        
        # Apply Discount-Tire filter unless showing all networks
        if not show_all_networks:
            query = query.filter(
                # Only include networks where MerakiInventory has Discount-Tire tag
                db.text("meraki_inventory.device_tags @> ARRAY['Discount-Tire']")
            ).filter(
                # Exclude sites with lab/hub/voice/test tags even if they have Discount-Tire
                db.text("""
                    NOT EXISTS (
                        SELECT 1 FROM unnest(meraki_inventory.device_tags) AS tag 
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
            )
            logger.info("Filtering for Discount-Tire tag only, excluding lab/hub/voice/test tagged sites")
        else:
            logger.info("Showing all networks (no tag filter)")
        
        # Always exclude hub/lab/voice/test sites and sites without IPs
        enriched_circuits = query.filter(
            # Exclude hub/lab/voice/test sites
            ~(
                EnrichedCircuit.network_name.ilike('%hub%') |
                EnrichedCircuit.network_name.ilike('%lab%') |
                EnrichedCircuit.network_name.ilike('%voice%') |
                EnrichedCircuit.network_name.ilike('%test%')
            )
        ).order_by(EnrichedCircuit.network_name).all()
        
        grouped_data = []
        
        for circuit, meraki_device in enriched_circuits:
            # Get all circuits for this site
            site_circuits = Circuit.query.filter(
                func.lower(Circuit.site_name) == func.lower(circuit.network_name),
                Circuit.status == 'Enabled'
            ).all()
            
            # Use improved cost assignment logic
            wan1_cost, wan2_cost, wan1_info, wan2_info = assign_costs_improved(circuit, site_circuits)
            
            # Check for Non-DSR circuits at this site
            non_dsr_circuits = [c for c in site_circuits if c.data_source == 'Non-DSR']
            has_non_dsr = len(non_dsr_circuits) > 0
            
            # Check if WAN1/WAN2 are Non-DSR (not Cell/Satellite and not DSR-verified)
            wan1_has_non_dsr = False
            wan2_has_non_dsr = False
            
            # WAN1 logic: If has provider and speed, not cell/satellite, and not DSR-verified = Non-DSR
            if circuit.wan1_provider and circuit.wan1_speed:
                wan1_speed_lower = circuit.wan1_speed.lower()
                is_cellular_satellite = 'cell' in wan1_speed_lower or 'satellite' in wan1_speed_lower
                is_dsr_verified = wan1_info and (
                    (hasattr(wan1_info, 'dsr_verified') and wan1_info.dsr_verified) or
                    (isinstance(wan1_info, dict) and wan1_info.get('dsr_verified'))
                )
                if not is_cellular_satellite and not is_dsr_verified:
                    wan1_has_non_dsr = True
            
            # WAN2 logic: If has provider and speed, not cell/satellite, and not DSR-verified = Non-DSR  
            if circuit.wan2_provider and circuit.wan2_speed:
                wan2_speed_lower = circuit.wan2_speed.lower()
                is_cellular_satellite = 'cell' in wan2_speed_lower or 'satellite' in wan2_speed_lower
                is_dsr_verified = wan2_info and (
                    (hasattr(wan2_info, 'dsr_verified') and wan2_info.dsr_verified) or
                    (isinstance(wan2_info, dict) and wan2_info.get('dsr_verified'))
                )
                if not is_cellular_satellite and not is_dsr_verified:
                    wan2_has_non_dsr = True
            
            # Determine wireless badges based on ARIN provider data
            wan1_wireless_badge = None
            wan2_wireless_badge = None
            
            # Check for cellular providers - flexible logic
            wan1_combined = f"{circuit.wan1_provider or ''} {circuit.wan1_speed or ''}".upper()
            if 'CELL' in wan1_combined:
                if 'VZW' in wan1_combined or 'VERIZON' in wan1_combined:
                    wan1_wireless_badge = 'VZW'
                elif 'AT&T' in wan1_combined or 'ATT' in wan1_combined:
                    wan1_wireless_badge = 'ATT'
                elif 'T-MOBILE' in wan1_combined or 'TMOBILE' in wan1_combined:
                    wan1_wireless_badge = 'ATT'  # Show as AT&T for now
                # If it's just "Cell" without provider, check ARIN
                elif not wan1_wireless_badge and meraki_device and meraki_device.wan1_arin_provider:
                    arin_upper = meraki_device.wan1_arin_provider.upper()
                    if 'VERIZON' in arin_upper or 'VZW' in arin_upper:
                        wan1_wireless_badge = 'VZW'
                    elif 'AT&T' in arin_upper or 'ATT' in arin_upper:
                        wan1_wireless_badge = 'ATT'
            
            # Check for Starlink (satellite speed OR provider name OR SpaceX ARIN)
            if (circuit.wan1_speed and 'satellite' in circuit.wan1_speed.lower()) or \
               (circuit.wan1_provider and 'starlink' in circuit.wan1_provider.lower()) or \
               (meraki_device.wan1_arin_provider and 'SPACEX' in meraki_device.wan1_arin_provider.upper()):
                wan1_wireless_badge = 'STARLINK'
            
            # Check WAN2 for cellular providers - flexible logic
            wan2_combined = f"{circuit.wan2_provider or ''} {circuit.wan2_speed or ''}".upper()
            if 'CELL' in wan2_combined:
                if 'VZW' in wan2_combined or 'VERIZON' in wan2_combined:
                    wan2_wireless_badge = 'VZW'
                elif 'AT&T' in wan2_combined or 'ATT' in wan2_combined:
                    wan2_wireless_badge = 'ATT'
                elif 'T-MOBILE' in wan2_combined or 'TMOBILE' in wan2_combined:
                    wan2_wireless_badge = 'ATT'  # Show as AT&T for now
                # If it's just "Cell" without provider, check ARIN
                elif not wan2_wireless_badge and meraki_device and meraki_device.wan2_arin_provider:
                    arin_upper = meraki_device.wan2_arin_provider.upper()
                    if 'VERIZON' in arin_upper or 'VZW' in arin_upper:
                        wan2_wireless_badge = 'VZW'
                    elif 'AT&T' in arin_upper or 'ATT' in arin_upper:
                        wan2_wireless_badge = 'ATT'
            
            # Check for Starlink (satellite speed OR provider name OR SpaceX ARIN)
            if (circuit.wan2_speed and 'satellite' in circuit.wan2_speed.lower()) or \
               (circuit.wan2_provider and 'starlink' in circuit.wan2_provider.lower()) or \
               (meraki_device.wan2_arin_provider and 'SPACEX' in meraki_device.wan2_arin_provider.upper()):
                wan2_wireless_badge = 'STARLINK'
            
            grouped_data.append({
                'network_name': circuit.network_name,
                'device_tags': circuit.device_tags or [],
                'has_non_dsr': has_non_dsr,
                'non_dsr_count': len(non_dsr_circuits),
                'wan1': {
                    'provider': circuit.wan1_provider or '',
                    'speed': circuit.wan1_speed or '',
                    'monthly_cost': wan1_cost,
                    'circuit_role': circuit.wan1_circuit_role or 'Primary',
                    'confirmed': circuit.wan1_confirmed or False,
                    'match_info': wan1_info,
                    'wireless_badge': wan1_wireless_badge,
                    'has_non_dsr': wan1_has_non_dsr
                },
                'wan2': {
                    'provider': circuit.wan2_provider or '',
                    'speed': circuit.wan2_speed or '',
                    'monthly_cost': wan2_cost,
                    'circuit_role': circuit.wan2_circuit_role or 'Secondary',
                    'confirmed': circuit.wan2_confirmed or False,
                    'match_info': wan2_info,
                    'wireless_badge': wan2_wireless_badge,
                    'has_non_dsr': wan2_has_non_dsr
                }
            })
        
        # Calculate badge counts for header display
        dsr_count = vzw_count = att_count = starlink_count = non_dsr_count = 0
        
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
                
            # Count wireless providers (match test page logic)
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
                
            # Count Non-DSR badges
            if entry['wan1'].get('has_non_dsr'):
                non_dsr_count += 1
            if entry['wan2'].get('has_non_dsr'):
                non_dsr_count += 1
        
        badge_counts = {
            'dsr': dsr_count,
            'vzw': vzw_count, 
            'att': att_count,
            'starlink': starlink_count,
            'non_dsr': non_dsr_count
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
        
        # Use the updated template with badge counts and timestamp
        return render_template('dsrcircuits.html', grouped_data=grouped_data, badge_counts=badge_counts, last_updated=last_updated)
        
    except Exception as e:
        logger.error(f"Error in main dsrcircuits: {e}")
        return render_template('dsrcircuits.html', error=f"Error: {e}")


@dsrcircuits_bp.route('/api/circuits/data')
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

@dsrcircuits_bp.route('/dsrcircuits-legacy')
def dsrcircuits_legacy():
    """
    LEGACY: Main circuits data table page - DATABASE VERSION
    
    Original version kept for rollback purposes.
    
    Returns:
        Rendered dsrcircuits.html template with circuit data
    """
    try:
        # Query enriched circuits from database, excluding those with hub, lab, voice, datacenter, test in network name or device tags
        enriched_circuits = EnrichedCircuit.query.filter(
            ~(
                # Exclude by network name patterns
                EnrichedCircuit.network_name.ilike('%hub%') |
                EnrichedCircuit.network_name.ilike('%lab%') |
                EnrichedCircuit.network_name.ilike('%voice%') |
                EnrichedCircuit.network_name.ilike('%datacenter%') |
                EnrichedCircuit.network_name.ilike('%test%') |
                EnrichedCircuit.network_name.ilike('%store in a box%') |
                EnrichedCircuit.network_name.ilike('%sib%')  # Store in a box abbreviation
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
        ).order_by(EnrichedCircuit.network_name).all()
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
        
        return render_template('dsrcircuits.html', grouped_data=grouped_data)
        
    except Exception as e:
        import traceback
        print(f"❌ Error loading circuit data from database: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        current_app.logger.error(f"Error in dsrcircuits: {str(e)}")
        return render_template('dsrcircuits.html', error=f"Error loading data: {e}")

@dsrcircuits_bp.route('/api/sites-without-ips', methods=['GET'])
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
@dsrcircuits_bp.route('/confirm/<site_name>', methods=['POST'])
def confirm_circuit(site_name):
    """Handle circuit confirmation popup data"""
    logger.info(f"Confirm circuit called for site: {site_name}")
    result = confirm_site(site_name)
    logger.info(f"Confirm result for {site_name}: {result}")
    return jsonify(result)

@dsrcircuits_bp.route('/confirm/<site_name>/submit', methods=['POST'])
def submit_confirmation(site_name):
    """Submit confirmed circuit data to database and push to Meraki"""
    logger.info(f"Submit confirmation called for site: {site_name}")
    data = request.get_json()
    logger.info(f"Confirmation data: {data}")
    
    try:
        # Get the existing enriched circuit (case-insensitive)
        circuit = EnrichedCircuit.query.filter(func.lower(EnrichedCircuit.network_name) == func.lower(site_name)).first()
        
        if not circuit:
            # Create new enriched circuit if it doesn't exist
            circuit = EnrichedCircuit(network_name=site_name)
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
            
            # Also update the device notes in meraki_inventory with the formatted notes
            meraki_device = MerakiInventory.query.filter(func.lower(MerakiInventory.network_name) == func.lower(site_name)).first()
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

@dsrcircuits_bp.route('/confirm/<site_name>/reset', methods=['POST'])
def reset_confirmation_status(site_name):
    """Reset confirmation status for a site"""
    result = reset_confirmation(site_name)
    return jsonify(result)

@dsrcircuits_bp.route('/dsrallcircuits')
def dsrallcircuits():
    """
    All circuits data table page - shows all enabled circuits from database
    
    Displays all enabled circuits with site name, site ID, circuit purpose,
    provider, speed, and cost in a sortable/filterable table format.
    
    Returns:
        Rendered dsrallcircuits.html template with all enabled circuit data
    """
    try:
        # Query only "Enabled" circuits (exclude "Enabled/Disconnected" and Non-DSR circuits)
        enabled_circuits = Circuit.query.filter(
            and_(
                Circuit.status == 'Enabled',
                or_(
                    Circuit.data_source != 'Non-DSR',
                    Circuit.data_source.is_(None)
                )
            )
        ).all()
        
        print(f"🔍 Found {len(enabled_circuits)} enabled DSR circuits in database (excluding Non-DSR)")
        
        # Count circuits per site for filtering
        site_circuit_counts = {}
        for circuit in enabled_circuits:
            site_name = circuit.site_name or ''
            if site_name:
                site_circuit_counts[site_name] = site_circuit_counts.get(site_name, 0) + 1
        
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
            
            site_name = circuit.site_name or ''
            circuit_count = site_circuit_counts.get(site_name, 1)
            
            circuit_data = {
                'site_name': site_name,
                'site_id': circuit.site_id or '',
                'circuit_purpose': circuit.circuit_purpose or '',
                'provider_name': circuit.provider_name or '',
                'details_ordered_service_speed': circuit.details_ordered_service_speed or '',
                'billing_monthly_cost': cost_str,
                'status': circuit.status or '',
                'circuit_count': circuit_count  # Add circuit count for filtering
            }
            circuits_data.append(circuit_data)
        
        print(f"✅ Prepared {len(circuits_data)} circuits for display")
        
        # Calculate statistics for the filter button
        sites_with_multiple_circuits_list = [site for site, count in site_circuit_counts.items() if count > 2]
        sites_with_multiple_circuits = len(sites_with_multiple_circuits_list)
        total_circuits_at_multi_sites = sum([count for site, count in site_circuit_counts.items() if count > 2])
        
        filter_stats = {
            'sites_with_multiple_circuits': sites_with_multiple_circuits,
            'total_circuits_at_multi_sites': total_circuits_at_multi_sites
        }
        
        return render_template('dsrallcircuits.html', 
                             circuits_data=circuits_data, 
                             filter_stats=filter_stats,
                             sites_with_multiple_circuits=sites_with_multiple_circuits_list)
        
    except Exception as e:
        import traceback
        print(f"❌ Error loading all circuits data: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        current_app.logger.error(f"Error in dsrallcircuits: {str(e)}")
        return render_template('dsrallcircuits.html', error=f"Error loading data: {e}")

@dsrcircuits_bp.route('/push_to_meraki', methods=['POST'])
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

@dsrcircuits_bp.route('/api/update-circuit/<int:circuit_id>', methods=['POST'])
def update_circuit(circuit_id):
    """Update a Non-DSR circuit field"""
    try:
        data = request.get_json()
        field = data.get('field')
        value = data.get('value')
        
        if not field or value is None:
            return jsonify({'success': False, 'error': 'Missing field or value'}), 400
        
        # Validate field name for security
        allowed_fields = ['provider_name', 'details_ordered_service_speed', 'billing_monthly_cost']
        if field not in allowed_fields:
            return jsonify({'success': False, 'error': 'Invalid field'}), 400
        
        # Get the circuit and verify it's Non-DSR
        circuit = Circuit.query.filter_by(id=circuit_id).first()
        if not circuit:
            return jsonify({'success': False, 'error': 'Circuit not found'}), 404
            
        if circuit.data_source != 'Non-DSR':
            return jsonify({'success': False, 'error': 'Only Non-DSR circuits can be edited'}), 403
        
        # Update the field
        setattr(circuit, field, value)
        db.session.commit()
        
        logger.info(f"Updated circuit {circuit_id}: {field} = {value}")
        
        return jsonify({
            'success': True, 
            'message': f'Circuit {circuit_id} updated successfully',
            'circuit_id': circuit_id,
            'field': field,
            'value': value
        })
        
    except Exception as e:
        logger.error(f"Error updating circuit {circuit_id}: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@dsrcircuits_bp.route('/api/create-non-dsr-circuit', methods=['POST'])
def create_non_dsr_circuit():
    """Create a new Non-DSR circuit"""
    try:
        data = request.get_json()
        
        # Required fields
        required_fields = ['site_name', 'provider_name', 'details_ordered_service_speed']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Generate unique ID by finding max ID and adding 1
        max_id = db.session.query(db.func.max(Circuit.id)).scalar() or 0
        new_id = max_id + 1
        
        # Create new circuit with default values
        new_circuit = Circuit(
            id=new_id,
            site_name=data['site_name'],
            site_id=data.get('site_id', ''),
            provider_name=data['provider_name'],
            details_ordered_service_speed=data['details_ordered_service_speed'],
            billing_monthly_cost=data.get('billing_monthly_cost', 0.0),
            status='Enabled',
            data_source='Non-DSR',
            circuit_purpose='Primary'  # Default for new circuits
        )
        
        # Add to database
        db.session.add(new_circuit)
        db.session.commit()
        
        logger.info(f"Created new Non-DSR circuit {new_id} for {data['site_name']}")
        
        return jsonify({
            'success': True, 
            'message': f'Non-DSR circuit created successfully',
            'circuit_id': new_id,
            'circuit': {
                'id': new_id,
                'site_name': data['site_name'],
                'site_id': data.get('site_id', ''),
                'provider_name': data['provider_name'],
                'details_ordered_service_speed': data['details_ordered_service_speed'],
                'billing_monthly_cost': data.get('billing_monthly_cost', 0.0),
                'status': 'Enabled',
                'data_source': 'Non-DSR',
                'date_created': new_circuit.created_at.strftime('%Y-%m-%d')
            }
        })
        
    except Exception as e:
        logger.error(f"Error creating Non-DSR circuit: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@dsrcircuits_bp.route('/api/non-dsr-circuits/<site_name>', methods=['GET'])
def get_non_dsr_circuits(site_name):
    """Get Non-DSR circuits for a specific site"""
    try:
        # Get all Non-DSR circuits for this site
        non_dsr_circuits = Circuit.query.filter(
            func.lower(Circuit.site_name) == func.lower(site_name),
            Circuit.data_source == 'Non-DSR',
            Circuit.status == 'Enabled'
        ).all()
        
        if not non_dsr_circuits:
            return jsonify({
                'success': True,
                'circuits': [],
                'message': f'No Non-DSR circuits found for {site_name}'
            })
        
        # Convert to JSON format
        circuits_data = []
        for circuit in non_dsr_circuits:
            circuits_data.append({
                'id': circuit.id,
                'site_name': circuit.site_name,
                'site_id': circuit.site_id or '',
                'provider_name': circuit.provider_name,
                'details_ordered_service_speed': circuit.details_ordered_service_speed,
                'details_service_speed': circuit.details_service_speed,
                'billing_monthly_cost': float(circuit.billing_monthly_cost) if circuit.billing_monthly_cost else 0.0,
                'status': circuit.status,
                'circuit_purpose': circuit.circuit_purpose,
                'data_source': circuit.data_source,
                'created_at': circuit.created_at.strftime('%Y-%m-%d') if circuit.created_at else '',
                'ip_address_start': circuit.ip_address_start or ''
            })
        
        return jsonify({
            'success': True,
            'site_name': site_name,
            'circuits': circuits_data,
            'count': len(circuits_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting Non-DSR circuits for {site_name}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@dsrcircuits_bp.route('/api/refresh-arin/<site_name>', methods=['POST'])
def refresh_arin_data(site_name):
    """Refresh ARIN data for a site via DDNS/Meraki API lookup"""
    try:
        # Import ARIN lookup functions (assuming they exist in nightly scripts)
        import requests
        import os
        
        # Get Meraki API key
        meraki_api_key = os.getenv('MERAKI_API_KEY')
        if not meraki_api_key:
            # Try loading from .env file
            from dotenv import load_dotenv
            load_dotenv('/usr/local/bin/meraki.env')
            meraki_api_key = os.getenv('MERAKI_API_KEY')
            if not meraki_api_key:
                return jsonify({'success': False, 'error': 'Meraki API key not configured'}), 500
        
        # Get organization ID
        org_name = "DTC-Store-Inventory-All"
        headers = {
            'X-Cisco-Meraki-API-Key': meraki_api_key,
            'Content-Type': 'application/json'
        }
        
        # Get organization ID
        orgs_response = requests.get("https://api.meraki.com/api/v1/organizations", headers=headers, timeout=30)
        orgs_response.raise_for_status()
        org_id = None
        for org in orgs_response.json():
            if org.get('name') == org_name:
                org_id = org['id']
                break
        
        if not org_id:
            return jsonify({'success': False, 'error': 'Organization not found'}), 404
        
        # Initialize result structure
        result = {
            'wan1_ip': None,
            'wan1_arin_provider': None,
            'wan2_ip': None,
            'wan2_arin_provider': None,
            'source': None,
            'warnings': []
        }
        
        # Strategy 1: Try to get device serial for this site
        meraki_device = MerakiInventory.query.filter(
            func.lower(MerakiInventory.network_name) == func.lower(site_name)
        ).first()
        
        # If we have a Meraki device, try to get fresh data from API
        if meraki_device and meraki_device.device_serial:
            # Query organization-wide uplink statuses
            uplink_url = f"https://api.meraki.com/api/v1/organizations/{org_id}/appliance/uplink/statuses"
            
            try:
                response = requests.get(uplink_url, headers=headers, timeout=30)
                response.raise_for_status()
                all_uplinks = response.json()
                
                # Find uplinks for our device
                device_serial = meraki_device.device_serial
                
                for device_status in all_uplinks:
                    if device_status.get('serial') == device_serial:
                        uplinks = device_status.get('uplinks', [])
                        for uplink in uplinks:
                            if uplink.get('interface') == 'wan1':
                                # Prefer publicIp over ip (interface IP might be private)
                                result['wan1_ip'] = uplink.get('publicIp') or uplink.get('ip')
                            elif uplink.get('interface') == 'wan2':
                                # Prefer publicIp over ip (interface IP might be private)
                                result['wan2_ip'] = uplink.get('publicIp') or uplink.get('ip')
                        result['source'] = 'meraki_api'
                        break
                        
            except requests.exceptions.RequestException as e:
                logger.warning(f"Failed to get Meraki API data: {e}")
                # Fall back to database data
                if meraki_device.wan1_ip or meraki_device.wan2_ip:
                    result['wan1_ip'] = meraki_device.wan1_ip
                    result['wan2_ip'] = meraki_device.wan2_ip
                    result['source'] = 'meraki_db'
                    result['warnings'].append('Using cached Meraki data')
        
        # Strategy 2: If no Meraki device or no IPs found, check enriched_circuits table
        if not result['wan1_ip'] and not result['wan2_ip']:
            enriched = EnrichedCircuit.query.filter(
                func.lower(EnrichedCircuit.network_name) == func.lower(site_name)
            ).first()
            
            if enriched:
                # enriched_circuits doesn't have wan1_public_ip column, just wan1_ip
                result['wan1_ip'] = enriched.wan1_ip
                result['wan2_ip'] = enriched.wan2_ip
                result['source'] = 'enriched_circuits'
                result['warnings'].append('No Meraki device found, using enriched circuits data')
        
        # Strategy 3: Check circuits table (using correct column names)
        if not result['wan1_ip'] and not result['wan2_ip']:
            circuits = Circuit.query.filter(
                func.lower(Circuit.site_name) == func.lower(site_name)
            ).all()
            
            # Use ip_address_start column which actually exists in circuits table
            for circuit in circuits:
                if hasattr(circuit, 'ip_address_start') and circuit.ip_address_start and not result['wan1_ip']:
                    result['wan1_ip'] = circuit.ip_address_start
                    result['source'] = 'circuits_table'
                    result['warnings'].append('Using circuit table IP address')
                    break
        
        # If still no IPs found, provide detailed error information
        if not result['wan1_ip'] and not result['wan2_ip']:
            error_details = []
            
            # Check what data we do have
            if meraki_device:
                error_details.append(f"Meraki device found (serial: {meraki_device.device_serial}) but no IP addresses recorded")
            else:
                error_details.append("No Meraki device found for this site")
            
            # Check circuit records
            circuit_count = Circuit.query.filter(func.lower(Circuit.site_name) == func.lower(site_name)).count()
            if circuit_count > 0:
                error_details.append(f"Found {circuit_count} circuit record(s) but no usable IP addresses")
            
            return jsonify({
                'success': False, 
                'error': f'No IP data found for {site_name}. {" ".join(error_details)}. This site may not have active IP configuration.',
                'warnings': result['warnings']
            }), 404
        
        # Query ARIN for provider information using same logic as nightly script
        def query_arin_rdap(ip):
            if not ip or ip == '0.0.0.0':
                return 'Unknown'
            
            # Check special Verizon range first
            try:
                import ipaddress
                ip_addr = ipaddress.ip_address(ip)
                if ipaddress.IPv4Address("166.80.0.0") <= ip_addr <= ipaddress.IPv4Address("166.80.255.255"):
                    return "Verizon Business"
            except:
                pass
            
            try:
                arin_url = f"https://rdap.arin.net/registry/ip/{ip}"
                arin_response = requests.get(arin_url, timeout=10)
                if arin_response.status_code == 200:
                    arin_data = arin_response.json()
                    return parse_arin_response_enhanced(arin_data)
                return 'Unknown'
            except:
                return 'Unknown'
        
        def parse_arin_response_enhanced(rdap_data):
            """Parse ARIN response with same logic as nightly script"""
            import re
            from datetime import datetime
            
            def collect_org_entities(entities):
                """Recursively collect organization names with their latest event dates"""
                org_candidates = []
                
                for entity in entities:
                    vcard = entity.get("vcardArray", [])
                    if vcard and isinstance(vcard, list) and len(vcard) > 1:
                        vcard_props = vcard[1]
                        name = None
                        kind = None
                        
                        for prop in vcard_props:
                            if len(prop) >= 4:
                                label = prop[0]
                                value = prop[3]
                                if label == "fn":
                                    name = value
                                elif label == "kind":
                                    kind = value
                        
                        # Only use organization entities, not person entities
                        if name and kind == "org":
                            # Get the latest event date
                            latest_date = datetime.min
                            events = entity.get("events", [])
                            for event in events:
                                event_date_str = event.get("eventDate", "")
                                if event_date_str:
                                    try:
                                        event_date = datetime.fromisoformat(event_date_str.replace("Z", "+00:00"))
                                        if event_date > latest_date:
                                            latest_date = event_date
                                    except:
                                        pass
                            
                            org_candidates.append((name, latest_date))
                
                # Check sub-entities
                sub_entities = entity.get("entities", [])
                if sub_entities:
                    org_candidates.extend(collect_org_entities(sub_entities))
                
                return org_candidates
            
            # First try network name directly
            network_name = rdap_data.get('name')
            logger.info(f"ARIN RDAP network name: {network_name}")
            
            # Check if it's an AT&T network (SBC-*) FIRST before checking entities
            if network_name and network_name.startswith('SBC-'):
                logger.info("Network name starts with SBC-, returning AT&T")
                return 'AT&T'
            
            # Get organization entities
            entities = rdap_data.get('entities', [])
            org_names = []
            if entities:
                org_names = collect_org_entities(entities)
                # Sort by date (newest first)
                org_names.sort(key=lambda x: x[1], reverse=True)
            
            # If we have org names, use the first one (newest by date)
            if org_names:
                clean_name = org_names[0][0]  # Extract name from (name, date) tuple
                clean_name = re.sub(r"^Private Customer -\s*", "", clean_name).strip()
                
                # Apply known company normalizations
                company_map = {
                    "AT&T": ["AT&T", "AT&T Internet Services", "AT&T Enterprises, LLC", "AT&T Broadband", 
                             "IPAdmin-ATT Internet Services", "AT&T Communications", "AT&T Business"],
                    "Charter Communications": ["Charter Communications LLC", "Charter Communications Inc", 
                                             "Charter Communications, LLC", "Charter Communications"],
                    "Comcast": ["Comcast Cable Communications, LLC", "Comcast Communications", 
                                "Comcast Cable", "Comcast Corporation"],
                    "Cox Communications": ["Cox Communications Inc.", "Cox Communications", "Cox Communications Group"],
                    "CenturyLink": ["CenturyLink Communications", "CenturyLink", "Lumen Technologies", 
                                    "Level 3 Parent, LLC", "Level 3 Communications", "Level3"],
                    "Frontier Communications": ["Frontier Communications Corporation", "Frontier Communications", 
                                              "Frontier Communications Inc."],
                    "Verizon": ["Verizon Communications", "Verizon Internet", "Verizon Business", "Verizon Wireless"],
                    "Optimum": ["Optimum", "Altice USA", "Suddenlink Communications"],
                    "Crown Castle": ["Crown Castle", "CROWN CASTLE"],
                    "Cable One, Inc.": ["CABLE ONE, INC.", "Cable One, Inc.", "Cable One"],
                }
                
                for company, variations in company_map.items():
                    for variant in variations:
                        if variant.lower() in clean_name.lower():
                            return company
                
                return clean_name
            
            # If no org entities found, try to normalize the network name
            if network_name:
                # Check if it's an AT&T network (SBC-*)
                if network_name.startswith('SBC-'):
                    return 'AT&T'
                # Check for other patterns
                elif 'CHARTER' in network_name.upper():
                    return 'Charter Communications'
                elif 'COMCAST' in network_name.upper():
                    return 'Comcast'
                elif 'COX' in network_name.upper():
                    return 'Cox Communications'
                elif 'VERIZON' in network_name.upper():
                    return 'Verizon'
                elif 'CENTURYLINK' in network_name.upper():
                    return 'CenturyLink'
                elif 'FRONTIER' in network_name.upper():
                    return 'Frontier Communications'
                elif 'CC04' in network_name:  # Charter network code
                    return 'Charter Communications'
                else:
                    return network_name
            
            return 'Unknown'
        
        # Query ARIN for any IPs we found
        result['wan1_arin_provider'] = query_arin_rdap(result['wan1_ip']) if result['wan1_ip'] else 'No IP'
        result['wan2_arin_provider'] = query_arin_rdap(result['wan2_ip']) if result['wan2_ip'] else 'No IP'
        
        # Update database based on source
        if meraki_device and result['source'] in ['meraki_api', 'meraki_db']:
            meraki_device.wan1_ip = result['wan1_ip']
            meraki_device.wan2_ip = result['wan2_ip']
            meraki_device.wan1_arin_provider = result['wan1_arin_provider']
            meraki_device.wan2_arin_provider = result['wan2_arin_provider']
            meraki_device.last_updated = datetime.utcnow()
        
        # Always try to update enriched_circuits if we have data
        if result['wan1_ip'] or result['wan2_ip']:
            enriched = EnrichedCircuit.query.filter(
                func.lower(EnrichedCircuit.network_name) == func.lower(site_name)
            ).first()
            
            if enriched:
                if result['wan1_ip']:
                    enriched.wan1_ip = result['wan1_ip']
                    enriched.wan1_arin_org = result['wan1_arin_provider']  # column is wan1_arin_org not wan1_arin_provider
                if result['wan2_ip']:
                    enriched.wan2_ip = result['wan2_ip']
                    enriched.wan2_arin_org = result['wan2_arin_provider']  # column is wan2_arin_org not wan2_arin_provider
                enriched.last_updated = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Enhanced ARIN refresh for {site_name}: "
                   f"WAN1={result['wan1_ip']}({result['wan1_arin_provider']}), "
                   f"WAN2={result['wan2_ip']}({result['wan2_arin_provider']}), "
                   f"Source={result['source']}")
        
        return jsonify({
            'success': True,
            'message': f'ARIN data refreshed from {result["source"]}',
            'wan1_ip': result['wan1_ip'] or 'N/A',
            'wan1_arin_provider': result['wan1_arin_provider'],
            'wan2_ip': result['wan2_ip'] or 'N/A',
            'wan2_arin_provider': result['wan2_arin_provider'],
            'source': result['source'],
            'warnings': result['warnings']
        })
        
    except Exception as e:
        logger.error(f"Error refreshing ARIN data for {site_name}: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@dsrcircuits_bp.route('/api/update-device-tags/<device_serial>', methods=['POST'])
def update_device_tags(device_serial):
    """Update tags for a Meraki MX device"""
    try:
        import requests
        import os
        from dotenv import load_dotenv
        import time
        
        # Load Meraki API key
        load_dotenv('/usr/local/bin/meraki.env')
        MERAKI_API_KEY = os.getenv('MERAKI_API_KEY')
        
        if not MERAKI_API_KEY:
            return jsonify({'success': False, 'error': 'Meraki API key not configured'}), 500
        
        data = request.get_json()
        action = data.get('action', 'replace')  # 'replace', 'add', or 'remove'
        tags = data.get('tags', [])
        
        # Get current device from database
        meraki_device = MerakiInventory.query.filter_by(device_serial=device_serial).first()
        if not meraki_device:
            return jsonify({'success': False, 'error': 'Device not found in database'}), 404
        
        # Get current tags from database (it's already a list)
        current_tags = meraki_device.device_tags or []
        
        # Calculate new tags based on action
        if action == 'add':
            # Add new tags to existing ones (avoid duplicates)
            new_tags = list(set(current_tags + tags))
        elif action == 'remove':
            # Remove specified tags
            new_tags = [tag for tag in current_tags if tag not in tags]
        else:  # replace
            # Replace all tags
            new_tags = tags
        
        
        # First, get the device from Meraki to ensure it exists
        check_url = f"https://api.meraki.com/api/v1/devices/{device_serial}"
        headers = {
            'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
            'Content-Type': 'application/json'
        }
        
        # Check if device exists in Meraki
        check_response = requests.get(check_url, headers=headers, timeout=30)
        if check_response.status_code == 404:
            # Device not found in Meraki, skip API update but update database
            logger.warning(f"Device {device_serial} not found in Meraki API, updating database only")
        else:
            # Update device tags via Meraki API
            for attempt in range(3):
                try:
                    response = requests.put(check_url, headers=headers, json={'tags': new_tags}, timeout=30)
                    
                    if response.status_code == 429:  # Rate limited
                        time.sleep(2 ** attempt)
                        continue
                        
                    response.raise_for_status()
                    break
                except requests.exceptions.RequestException as e:
                    if attempt == 2:  # Last attempt
                        logger.warning(f"Device {device_serial} not found in Meraki API, updating database only")
                        logger.error(f"Failed to update Meraki API for {device_serial}: {e}")
                        # Continue to update database even if API fails
        
        # Update database
        meraki_device.device_tags = new_tags  # SQLAlchemy handles the array conversion
        meraki_device.last_updated = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"Updated tags for device {device_serial}: {new_tags} (action: {action})")
        
        return jsonify({
            'success': True,
            'message': f'Tags updated for device {device_serial}',
            'tags': new_tags,
            'action': action
        })
        
    except Exception as e:
        logger.error(f"Error updating device tags for {device_serial}: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@dsrcircuits_bp.route('/api/mark-remodeling/<site_name>', methods=['POST'])
def mark_remodeling(site_name):
    """Mark a site as remodeling - adds tag, updates notes, saves to database and pushes to Meraki"""
    try:
        data = request.get_json()
        device_serial = data.get('device_serial')
        tags = data.get('tags', [])
        
        # Ensure "Remodeling" tag is in the list
        if "Remodeling" not in tags:
            tags.append("Remodeling")
        
        # Find the meraki device
        meraki_device = MerakiInventory.query.filter_by(device_serial=device_serial).first()
        if not meraki_device:
            return jsonify({'success': False, 'error': 'Device not found in database'}), 404
        
        # Update device tags
        meraki_device.device_tags = tags
        
        # Update device notes - add "Remodeling" to the bottom if not already there
        current_notes = meraki_device.device_notes or ""
        if "Remodeling" not in current_notes:
            if current_notes.strip():
                updated_notes = current_notes.strip() + "\nRemodeling"
            else:
                updated_notes = "Remodeling"
            meraki_device.device_notes = updated_notes
        
        meraki_device.last_updated = datetime.utcnow()
        
        # Push to Meraki API
        import requests
        import os
        from dotenv import load_dotenv
        
        load_dotenv('/usr/local/bin/meraki.env')
        MERAKI_API_KEY = os.getenv('MERAKI_API_KEY')
        
        if MERAKI_API_KEY:
            headers = {
                'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
                'Content-Type': 'application/json'
            }
            
            # Update tags
            try:
                tag_url = f"https://api.meraki.com/api/v1/devices/{device_serial}"
                tag_response = requests.put(tag_url, headers=headers, json={'tags': tags}, timeout=30)
                tag_response.raise_for_status()
                logger.info(f"Successfully updated Meraki tags for {device_serial}")
            except Exception as e:
                logger.warning(f"Failed to update Meraki tags for {device_serial}: {e}")
            
            # Update notes
            try:
                notes_response = requests.put(tag_url, headers=headers, json={'notes': meraki_device.device_notes}, timeout=30)
                notes_response.raise_for_status()
                logger.info(f"Successfully updated Meraki notes for {device_serial}")
            except Exception as e:
                logger.warning(f"Failed to update Meraki notes for {device_serial}: {e}")
        
        # Save to database
        db.session.commit()
        
        logger.info(f"Successfully marked {site_name} as remodeling")
        return jsonify({
            'success': True, 
            'message': f'Site {site_name} marked as remodeling',
            'tags': tags,
            'notes': meraki_device.device_notes
        })
        
    except Exception as e:
        logger.error(f"Error marking {site_name} as remodeling: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@dsrcircuits_bp.route('/api/mark-remodeling-done/<site_name>', methods=['POST'])
def mark_remodeling_done(site_name):
    """Mark remodeling as complete - removes tag, updates notes, saves to database and pushes to Meraki"""
    try:
        data = request.get_json()
        device_serial = data.get('device_serial')
        tags = data.get('tags', [])
        
        # Ensure "Remodeling" tag is NOT in the list
        if "Remodeling" in tags:
            tags.remove("Remodeling")
        
        # Find the meraki device
        meraki_device = MerakiInventory.query.filter_by(device_serial=device_serial).first()
        if not meraki_device:
            return jsonify({'success': False, 'error': 'Device not found in database'}), 404
        
        # Update device tags
        meraki_device.device_tags = tags
        
        # Update device notes - remove "Remodeling" from notes
        current_notes = meraki_device.device_notes or ""
        if "Remodeling" in current_notes:
            # Remove "Remodeling" and clean up extra newlines
            updated_notes = current_notes.replace("\nRemodeling", "").replace("Remodeling\n", "").replace("Remodeling", "")
            updated_notes = updated_notes.strip()
            meraki_device.device_notes = updated_notes
        
        meraki_device.last_updated = datetime.utcnow()
        
        # Push to Meraki API
        import requests
        import os
        from dotenv import load_dotenv
        
        load_dotenv('/usr/local/bin/meraki.env')
        MERAKI_API_KEY = os.getenv('MERAKI_API_KEY')
        
        if MERAKI_API_KEY:
            headers = {
                'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
                'Content-Type': 'application/json'
            }
            
            # Update tags
            try:
                tag_url = f"https://api.meraki.com/api/v1/devices/{device_serial}"
                tag_response = requests.put(tag_url, headers=headers, json={'tags': tags}, timeout=30)
                tag_response.raise_for_status()
                logger.info(f"Successfully updated Meraki tags for {device_serial}")
            except Exception as e:
                logger.warning(f"Failed to update Meraki tags for {device_serial}: {e}")
            
            # Update notes
            try:
                notes_response = requests.put(tag_url, headers=headers, json={'notes': meraki_device.device_notes}, timeout=30)
                notes_response.raise_for_status()
                logger.info(f"Successfully updated Meraki notes for {device_serial}")
            except Exception as e:
                logger.warning(f"Failed to update Meraki notes for {device_serial}: {e}")
        
        # Save to database
        db.session.commit()
        
        logger.info(f"Successfully marked {site_name} remodeling as complete")
        return jsonify({
            'success': True, 
            'message': f'Remodeling complete for {site_name}',
            'tags': tags,
            'notes': meraki_device.device_notes
        })
        
    except Exception as e:
        logger.error(f"Error marking {site_name} remodeling as complete: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500