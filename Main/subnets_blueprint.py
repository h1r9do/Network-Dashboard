"""
Subnets Blueprint - Network VLAN Analysis Module
Shows subnet groupings by /16 and /24 networks with filtering
"""

from flask import Blueprint, render_template, jsonify, request
import logging
import os
from models import db, NetworkVlan
from sqlalchemy import func, distinct, and_, or_
from sqlalchemy.sql import text

logger = logging.getLogger(__name__)

# Create Blueprint with proper template folder
subnets_bp = Blueprint('subnets', __name__, 
                      url_prefix='/subnets',
                      template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

@subnets_bp.route('/')
def subnets_page():
    """Main subnets page"""
    try:
        # Get summary statistics
        total_networks = db.session.query(func.count(distinct(NetworkVlan.network_name)))\
            .filter(~NetworkVlan.subnet.like('172.%'))\
            .filter(~NetworkVlan.network_name.ilike('%hub%'))\
            .filter(~NetworkVlan.network_name.ilike('%voice%'))\
            .filter(~NetworkVlan.network_name.ilike('%lab%'))\
            .scalar() or 0
            
        total_vlans = db.session.query(func.count(NetworkVlan.id))\
            .filter(~NetworkVlan.subnet.like('172.%'))\
            .scalar() or 0
            
        unique_24_networks = db.session.query(func.count(distinct(NetworkVlan.parent_network)))\
            .filter(NetworkVlan.parent_network.isnot(None))\
            .filter(~NetworkVlan.subnet.like('172.%'))\
            .scalar() or 0
        
        # Count shared /16 networks
        shared_16_query = text("""
            SELECT COUNT(*) FROM sites_by_16_network
        """)
        shared_16_count = db.session.execute(shared_16_query).scalar() or 0
        
        return render_template('subnets.html',
                            total_networks=total_networks,
                            total_vlans=total_vlans,
                            unique_24_networks=unique_24_networks,
                            shared_16_count=shared_16_count)
    except Exception as e:
        logger.error(f"Error loading subnets page: {str(e)}")
        return render_template('subnets.html', error=str(e))

@subnets_bp.route('/api/by-16')
def api_networks_by_16():
    """API endpoint for /16 network groupings"""
    try:
        # Get filter parameters
        network_filter = request.args.get('network', '').strip()
        min_sites = int(request.args.get('min_sites', 1))
        
        # Query the sites_by_16_network view
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
        logger.error(f"Error in networks by /16 API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@subnets_bp.route('/api/by-24')
def api_networks_by_24():
    """API endpoint for /24 network groupings"""
    try:
        # Get filter parameters
        network_filter = request.args.get('network', '').strip()
        min_sites = int(request.args.get('min_sites', 1))
        
        # Query the network_grouping_by_subnet view
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
        logger.error(f"Error in networks by /24 API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@subnets_bp.route('/api/site-details/<site_name>')
def api_site_network_details(site_name):
    """Get detailed network information for a specific site"""
    try:
        # Get VLANs for the site
        vlans_query = text("""
            SELECT 
                network_name,
                vlan_id,
                name,
                subnet::text as subnet,
                parent_network::text as parent_24,
                dhcp_handling,
                appliance_ip
            FROM network_vlans
            WHERE network_name = :site_name
            AND subnet IS NOT NULL
            ORDER BY vlan_id
        """)
        
        # Get unique /24 count separately
        count_query = text("""
            SELECT COUNT(DISTINCT parent_network) as unique_24_count
            FROM network_vlans
            WHERE network_name = :site_name
            AND parent_network IS NOT NULL
        """)
        
        results = db.session.execute(vlans_query, {'site_name': site_name}).fetchall()
        count_result = db.session.execute(count_query, {'site_name': site_name}).fetchone()
        
        data = []
        for row in results:
            data.append({
                'vlan_id': row.vlan_id,
                'name': row.name,
                'subnet': row.subnet,
                'parent_24': row.parent_24,
                'dhcp_handling': row.dhcp_handling,
                'appliance_ip': row.appliance_ip
            })
        
        return jsonify({
            'site_name': site_name,
            'vlans': data,
            'unique_24_count': count_result.unique_24_count if count_result else 0
        })
    except Exception as e:
        logger.error(f"Error getting site details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@subnets_bp.route('/api/patterns')
def api_network_patterns():
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

@subnets_bp.route('/api/export/<export_type>')
def export_subnet_data(export_type):
    """Export subnet data in various formats"""
    try:
        # Get current filter parameters
        view_type = request.args.get('view', 'by16')
        network_filter = request.args.get('network', '')
        min_sites = int(request.args.get('min_sites', 1))
        
        if view_type == 'by16':
            query = text("""
                SELECT * FROM sites_by_16_network
                WHERE site_count >= :min_sites
                AND (:network_filter = '' OR sites ILIKE :network_pattern OR parent_16_network::text ILIKE :network_pattern)
                ORDER BY site_count DESC
            """)
        else:  # by24
            query = text("""
                SELECT * FROM network_grouping_by_subnet
                WHERE network_count >= :min_sites
                AND (:network_filter = '' OR networks ILIKE :network_pattern OR parent_network::text ILIKE :network_pattern)
                ORDER BY network_count DESC
            """)
        
        results = db.session.execute(query, {
            'min_sites': min_sites,
            'network_filter': network_filter,
            'network_pattern': f'%{network_filter}%'
        }).fetchall()
        
        if export_type == 'excel':
            # Return Excel format - tabular with individual site columns
            import pandas as pd
            from io import BytesIO
            from flask import send_file
            
            # Prepare tabular data
            data = []
            max_sites = 0
            
            # First pass: determine maximum number of sites for column creation
            for row in results:
                if view_type == 'by16':
                    sites_str = str(row[2])  # sites column
                else:  # by24
                    sites_str = str(row[2])  # networks column
                    
                site_list = [site.strip() for site in sites_str.split(',')]
                max_sites = max(max_sites, len(site_list))
            
            # Second pass: create data rows
            for row in results:
                if view_type == 'by16':
                    row_data = {
                        'Network_16': str(row[0]),
                        'Site_Count': int(row[1]),
                        'Unique_24_Networks': int(row[3])
                    }
                    sites_str = str(row[2])
                else:  # by24
                    row_data = {
                        'Network_24': str(row[0]),
                        'Network_Count': int(row[1]),
                        'Total_VLANs': int(row[3])
                    }
                    sites_str = str(row[2])
                
                # Split sites and add to individual columns
                site_list = [site.strip() for site in sites_str.split(',')]
                for i in range(max_sites):
                    col_name = f'Site_{i+1:02d}'
                    row_data[col_name] = site_list[i] if i < len(site_list) else ''
                
                data.append(row_data)
            
            df = pd.DataFrame(data)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Subnet Data', index=False)
                
                # Auto-adjust column widths
                worksheet = writer.sheets['Subnet Data']
                for i, col in enumerate(df.columns):
                    max_len = max(
                        df[col].astype(str).map(len).max(),
                        len(str(col))
                    ) + 2
                    worksheet.set_column(i, i, min(max_len, 50))
            
            output.seek(0)
            
            return send_file(output, 
                           mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                           download_name=f'subnet_analysis_{view_type}.xlsx',
                           as_attachment=True)
                           
        elif export_type == 'csv':
            # Return CSV format - simple approach
            import csv
            from io import StringIO
            from flask import Response
            
            output = StringIO()
            writer = csv.writer(output)
            
            # Write headers and data
            if results:
                if view_type == 'by16':
                    # Headers for /16 view
                    writer.writerow(['Network_16', 'Site_Count', 'Sites', 'Unique_24_Networks'])
                    
                    # Data rows
                    for row in results:
                        writer.writerow([
                            str(row[0]),  # parent_16_network
                            str(row[1]),  # site_count
                            str(row[2]),  # sites
                            str(row[3])   # unique_24_networks
                        ])
                else:  # by24
                    # Headers for /24 view
                    writer.writerow(['Network_24', 'Network_Count', 'Networks', 'Total_VLANs'])
                    
                    # Data rows
                    for row in results:
                        writer.writerow([
                            str(row[0]),  # parent_network
                            str(row[1]),  # network_count
                            str(row[2]),  # networks
                            str(row[3])   # total_vlans
                        ])
            
            return Response(output.getvalue(),
                          mimetype='text/csv',
                          headers={'Content-Disposition': f'attachment; filename=subnet_analysis_{view_type}.csv'})
        
        return jsonify({'error': 'Invalid export type'}), 400
        
    except Exception as e:
        logger.error(f"Error exporting subnet data: {str(e)}")
        return jsonify({'error': str(e)}), 500