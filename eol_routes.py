#!/usr/bin/env python3
"""
EOL Dashboard Routes - Flask blueprint for EOL tracking interface
"""

from flask import Blueprint, render_template, jsonify, request
from datetime import datetime, date, timedelta
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Create blueprint
eol_bp = Blueprint('eol', __name__)

@eol_bp.route('/eol')
def eol_dashboard():
    """Render EOL dashboard page"""
    return render_template('eol_dashboard.html')

@eol_bp.route('/api/eol/summary')
def api_eol_summary():
    """Get EOL summary data with inventory counts"""
    from models import db
    
    try:
        # Get EOL data with inventory counts
        query = text("""
            WITH eol_latest AS (
                SELECT DISTINCT ON (model) 
                    model,
                    model_variants,
                    announcement_date,
                    end_of_sale_date,
                    end_of_support_date,
                    pdf_url,
                    pdf_filename,
                    CASE 
                        WHEN pdf_source AND csv_source THEN 'both'
                        WHEN pdf_source THEN 'pdf'
                        WHEN csv_source THEN 'csv'
                        ELSE 'none'
                    END as eol_source,
                    updated_at
                FROM meraki_eol
                ORDER BY model, updated_at DESC
            ),
            inventory_counts AS (
                SELECT 
                    model,
                    total_count as inventory_count
                FROM inventory_summary
            )
            SELECT 
                e.*,
                COALESCE(i.inventory_count, 0) as inventory_count
            FROM eol_latest e
            LEFT JOIN inventory_counts i ON e.model = i.model
            ORDER BY 
                CASE 
                    WHEN e.end_of_support_date <= CURRENT_DATE THEN 1
                    WHEN e.end_of_sale_date <= CURRENT_DATE THEN 2
                    WHEN e.end_of_sale_date <= CURRENT_DATE + INTERVAL '90 days' THEN 3
                    ELSE 4
                END,
                e.end_of_sale_date,
                e.model
        """)
        
        result = db.session.execute(query)
        models = []
        
        today = date.today()
        summary = {
            'total_models': 0,
            'eos_count': 0,
            'eol_count': 0,
            'upcoming_count': 0
        }
        
        for row in result:
            model_data = {
                'model': row.model,
                'model_variants': row.model_variants or [row.model],
                'announcement_date': row.announcement_date.isoformat() if row.announcement_date else None,
                'end_of_sale_date': row.end_of_sale_date.isoformat() if row.end_of_sale_date else None,
                'end_of_support_date': row.end_of_support_date.isoformat() if row.end_of_support_date else None,
                'pdf_url': row.pdf_url,
                'pdf_filename': row.pdf_filename,
                'eol_source': row.eol_source,
                'inventory_count': row.inventory_count,
                'updated_at': row.updated_at.isoformat() if row.updated_at else None
            }
            models.append(model_data)
            
            # Update summary counts
            summary['total_models'] += 1
            
            if row.end_of_support_date and row.end_of_support_date <= today:
                summary['eol_count'] += 1
            elif row.end_of_sale_date and row.end_of_sale_date <= today:
                summary['eos_count'] += 1
            elif row.end_of_sale_date and row.end_of_sale_date <= today + timedelta(days=90):
                summary['upcoming_count'] += 1
        
        # Get last update time
        last_update_query = text("""
            SELECT MAX(updated_at) as last_update 
            FROM meraki_eol
        """)
        last_update_result = db.session.execute(last_update_query).fetchone()
        last_update = last_update_result.last_update if last_update_result else None
        
        return jsonify({
            'success': True,
            'models': models,
            'summary': summary,
            'last_update': last_update.isoformat() if last_update else None
        })
        
    except Exception as e:
        logger.error(f"Error getting EOL summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@eol_bp.route('/api/eol/model/<model>')
def api_eol_model_detail(model):
    """Get detailed EOL information for a specific model"""
    from models import db
    
    try:
        # Get all EOL records for this model
        query = text("""
            SELECT 
                *,
                CASE 
                    WHEN pdf_source AND csv_source THEN 'both'
                    WHEN pdf_source THEN 'pdf'
                    WHEN csv_source THEN 'csv'
                    ELSE 'none'
                END as source_type
            FROM meraki_eol
            WHERE model = :model 
                OR :model = ANY(model_variants)
            ORDER BY updated_at DESC
        """)
        
        result = db.session.execute(query, {'model': model.upper()})
        records = []
        
        for row in result:
            record = {
                'id': row.id,
                'model': row.model,
                'model_variants': row.model_variants or [],
                'announcement_date': row.announcement_date.isoformat() if row.announcement_date else None,
                'end_of_sale_date': row.end_of_sale_date.isoformat() if row.end_of_sale_date else None,
                'end_of_support_date': row.end_of_support_date.isoformat() if row.end_of_support_date else None,
                'pdf_url': row.pdf_url,
                'pdf_filename': row.pdf_filename,
                'source_type': row.source_type,
                'parsed_data': row.parsed_data,
                'created_at': row.created_at.isoformat() if row.created_at else None,
                'updated_at': row.updated_at.isoformat() if row.updated_at else None
            }
            records.append(record)
        
        # Get inventory information
        inv_query = text("""
            SELECT 
                COUNT(*) as device_count,
                array_agg(DISTINCT organization) as organizations,
                array_agg(DISTINCT network_name) as networks
            FROM inventory_devices
            WHERE model = :model
        """)
        
        inv_result = db.session.execute(inv_query, {'model': model.upper()}).fetchone()
        
        inventory_info = {
            'device_count': inv_result.device_count if inv_result else 0,
            'organizations': list(filter(None, inv_result.organizations)) if inv_result and inv_result.organizations else [],
            'networks': list(filter(None, inv_result.networks))[:10] if inv_result and inv_result.networks else []  # Limit to 10
        }
        
        return jsonify({
            'success': True,
            'model': model.upper(),
            'eol_records': records,
            'inventory': inventory_info
        })
        
    except Exception as e:
        logger.error(f"Error getting EOL detail for {model}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@eol_bp.route('/api/eol/affected-devices')
def api_affected_devices():
    """Get devices affected by EOL/EOS"""
    from models import db
    
    try:
        # Get devices with EOL/EOS models
        query = text("""
            WITH eol_models AS (
                SELECT DISTINCT 
                    model,
                    end_of_sale_date,
                    end_of_support_date
                FROM meraki_eol
                WHERE end_of_sale_date <= CURRENT_DATE
            )
            SELECT 
                id.serial,
                id.name as device_name,
                id.model,
                id.network_name,
                id.organization,
                id.lan_ip,
                em.end_of_sale_date,
                em.end_of_support_date,
                CASE 
                    WHEN em.end_of_support_date <= CURRENT_DATE THEN 'eol'
                    ELSE 'eos'
                END as status
            FROM inventory_devices id
            INNER JOIN eol_models em ON id.model = em.model
            ORDER BY em.end_of_support_date, id.organization, id.network_name
        """)
        
        result = db.session.execute(query)
        devices = []
        
        for row in result:
            device = {
                'serial': row.serial,
                'device_name': row.device_name,
                'model': row.model,
                'network_name': row.network_name,
                'organization': row.organization,
                'lan_ip': row.lan_ip,
                'end_of_sale_date': row.end_of_sale_date.isoformat() if row.end_of_sale_date else None,
                'end_of_support_date': row.end_of_support_date.isoformat() if row.end_of_support_date else None,
                'status': row.status
            }
            devices.append(device)
        
        return jsonify({
            'success': True,
            'affected_devices': devices,
            'total_count': len(devices)
        })
        
    except Exception as e:
        logger.error(f"Error getting affected devices: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@eol_bp.route('/api/eol/refresh', methods=['POST'])
def api_eol_refresh():
    """Trigger EOL data refresh (admin only)"""
    import subprocess
    
    try:
        # Check for admin authentication (implement as needed)
        # For now, just run the EOL tracker
        
        result = subprocess.run(
            ['/usr/bin/python3', '/usr/local/bin/Main/meraki_eol_tracker.py'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True,
                'message': 'EOL data refresh completed successfully',
                'output': result.stdout[-1000:] if result.stdout else ''  # Last 1000 chars
            })
        else:
            return jsonify({
                'success': False,
                'message': 'EOL data refresh failed',
                'error': result.stderr[-1000:] if result.stderr else 'Unknown error'
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'EOL refresh timed out after 5 minutes'
        }), 500
    except Exception as e:
        logger.error(f"Error refreshing EOL data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500