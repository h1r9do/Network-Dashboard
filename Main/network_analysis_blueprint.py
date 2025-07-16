#!/usr/bin/env python3
"""
Network Analysis Blueprint for DSR Circuits
Displays network groupings by /16 and /24 networks
"""

from flask import Blueprint, render_template, jsonify, request
from sqlalchemy import text
from models import db
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Create the blueprint
network_analysis_bp = Blueprint('network_analysis', __name__)

@network_analysis_bp.route('/network-analysis')
def network_analysis_page():
    """Serve the network analysis page"""
    return render_template('network_analysis.html')

@network_analysis_bp.route('/api/network-analysis/summary')
def get_network_summary():
    """Get summary statistics for network analysis"""
    try:
        # Get counts
        stats_query = text("""
            SELECT 
                (SELECT COUNT(DISTINCT network_name) FROM network_vlans WHERE network_name NOT ILIKE '%hub%' AND network_name NOT ILIKE '%voice%' AND network_name NOT ILIKE '%lab%') as total_networks,
                (SELECT COUNT(DISTINCT parent_network) FROM network_vlans WHERE parent_network IS NOT NULL) as unique_24_networks,
                (SELECT COUNT(*) FROM sites_by_16_network) as shared_16_count,
                (SELECT COUNT(*) FROM network_vlans) as total_vlans
        """)
        
        result = db.session.execute(stats_query).fetchone()
        
        return jsonify({
            'total_networks': result.total_networks or 0,
            'unique_24_networks': result.unique_24_networks or 0,
            'shared_16_count': result.shared_16_count or 0,
            'total_vlans': result.total_vlans or 0
        })
    except Exception as e:
        logger.error(f"Error getting network summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

@network_analysis_bp.route('/api/network-analysis/by-16')
def get_networks_by_16():
    """Get networks grouped by /16"""
    try:
        # Get filter parameters
        network_filter = request.args.get('network', '').strip()
        min_sites = int(request.args.get('min_sites', 2))
        
        query = text("""
            SELECT 
                parent_16_network::text as network_16,
                site_count,
                sites,
                unique_24_networks,
                all_24_networks
            FROM sites_by_16_network
            WHERE site_count >= :min_sites
            AND (:network_filter = '' OR sites ILIKE :network_pattern OR parent_16_network::text ILIKE :network_pattern)
            ORDER BY site_count DESC, parent_16_network
        """)
        
        results = db.session.execute(query, {
            'min_sites': min_sites,
            'network_filter': network_filter,
            'network_pattern': f'%{network_filter}%'
        }).fetchall()
        
        data = []
        for row in results:
            data.append({
                'network_16': row.network_16,
                'site_count': row.site_count,
                'sites': row.sites,
                'unique_24_networks': row.unique_24_networks,
                'all_24_networks': row.all_24_networks
            })
        
        return jsonify({'data': data, 'total': len(data)})
    except Exception as e:
        logger.error(f"Error getting networks by /16: {str(e)}")
        return jsonify({'error': str(e)}), 500

@network_analysis_bp.route('/api/network-analysis/by-24')
def get_networks_by_24():
    """Get networks grouped by /24"""
    try:
        # Get filter parameters
        network_filter = request.args.get('network', '').strip()
        min_sites = int(request.args.get('min_sites', 2))
        
        query = text("""
            SELECT 
                parent_network::text as network_24,
                network_count,
                networks,
                total_vlans
            FROM network_grouping_by_subnet
            WHERE (:network_filter = '' OR networks ILIKE :network_pattern OR parent_network::text ILIKE :network_pattern)
            AND network_count >= :min_sites
            ORDER BY network_count DESC, parent_network
        """)
        
        results = db.session.execute(query, {
            'network_filter': network_filter,
            'network_pattern': f'%{network_filter}%',
            'min_sites': min_sites
        }).fetchall()
        
        data = []
        for row in results:
            data.append({
                'network_24': row.network_24,
                'network_count': row.network_count,
                'networks': row.networks,
                'total_vlans': row.total_vlans
            })
        
        return jsonify({'data': data, 'total': len(data)})
    except Exception as e:
        logger.error(f"Error getting networks by /24: {str(e)}")
        return jsonify({'error': str(e)}), 500

@network_analysis_bp.route('/api/network-analysis/site-details/<site_name>')
def get_site_network_details(site_name):
    """Get detailed network information for a specific site"""
    try:
        query = text("""
            SELECT 
                network_name,
                vlan_id,
                subnet::text as subnet,
                parent_network::text as parent_24,
                dhcp_mode,
                COUNT(DISTINCT parent_network) OVER (PARTITION BY network_name) as unique_24_count
            FROM network_vlans
            WHERE network_name = :site_name
            AND subnet IS NOT NULL
            ORDER BY vlan_id
        """)
        
        results = db.session.execute(query, {'site_name': site_name}).fetchall()
        
        data = []
        for row in results:
            data.append({
                'vlan_id': row.vlan_id,
                'subnet': row.subnet,
                'parent_24': row.parent_24,
                'dhcp_mode': row.dhcp_mode
            })
        
        return jsonify({
            'site_name': site_name,
            'vlans': data,
            'unique_24_count': results[0].unique_24_count if results else 0
        })
    except Exception as e:
        logger.error(f"Error getting site details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@network_analysis_bp.route('/api/network-analysis/patterns')
def get_network_patterns():
    """Get network pattern analysis"""
    try:
        query = text("""
            SELECT 
                parent_network::text as network,
                sites_using_network,
                site_list,
                network_type
            FROM network_pattern_analysis
            WHERE sites_using_network > 1
            ORDER BY sites_using_network DESC
            LIMIT 100
        """)
        
        results = db.session.execute(query).fetchall()
        
        data = []
        for row in results:
            data.append({
                'network': row.network,
                'sites_using_network': row.sites_using_network,
                'site_list': row.site_list,
                'network_type': row.network_type
            })
        
        return jsonify({'data': data})
    except Exception as e:
        logger.error(f"Error getting network patterns: {str(e)}")
        return jsonify({'error': str(e)}), 500