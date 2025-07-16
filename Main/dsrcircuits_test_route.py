#!/usr/bin/env python3
"""
Flask route additions for dsrcircuits-test endpoint
Add these routes to dsrcircuits.py to test the provider matching
"""

# Add these imports to the top of dsrcircuits.py
import psycopg2.extras

# Add these routes to dsrcircuits.py

@app.route('/dsrcircuits-test')
def dsrcircuits_test():
    """Test version of DSR Circuits using enriched_circuits_test table"""
    
    # Get statistics
    stats = get_test_statistics()
    
    # Get sample data for display
    sample_circuits = get_sample_test_circuits()
    
    return render_template('dsrcircuits_test.html', 
                         stats=stats, 
                         sample_circuits=sample_circuits)

@app.route('/api/circuit-matches-test/<site_name>')
def get_circuit_matches_test(site_name):
    """Get pre-calculated circuit match data for a site from test table"""
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Get circuit matches for this site
                cursor.execute("""
                    SELECT * FROM get_site_circuit_test_matches(%s)
                """, (site_name,))
                
                circuits = cursor.fetchall()
                
                # Calculate summary stats
                total_count = len(circuits)
                matched_count = sum(1 for c in circuits if c['match_status'] == 'matched')
                avg_confidence = sum(c['match_confidence'] for c in circuits if c['match_confidence']) / total_count if total_count > 0 else 0
                
                return jsonify({
                    'site_name': site_name,
                    'circuits': [dict(c) for c in circuits],
                    'total_count': total_count,
                    'matched_count': matched_count,
                    'avg_confidence': round(avg_confidence, 1),
                    'success': True
                })
                
    except Exception as e:
        logger.error(f"Error getting circuit matches for {site_name}: {e}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/api/test-statistics')
def get_test_statistics_api():
    """Get provider matching test statistics"""
    
    try:
        stats = get_test_statistics()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting test statistics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-no-matches')
def get_test_no_matches():
    """Get circuits that didn't match for analysis"""
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT site_name, circuit_purpose, dsr_provider, arin_provider, 
                           match_reason, provider_match_confidence
                    FROM enriched_circuits_test
                    WHERE provider_match_status IN ('no_match', 'no_data')
                    ORDER BY site_name, circuit_purpose
                    LIMIT 100
                """)
                
                no_matches = [dict(row) for row in cursor.fetchall()]
                
                return jsonify({
                    'no_matches': no_matches,
                    'count': len(no_matches),
                    'success': True
                })
                
    except Exception as e:
        logger.error(f"Error getting no matches: {e}")
        return jsonify({'error': str(e)}), 500

# Helper functions

def get_test_statistics():
    """Get statistics from test enrichment"""
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM provider_match_test_statistics")
                stats = cursor.fetchone()
                return dict(stats) if stats else {}
    except Exception as e:
        logger.error(f"Error getting test statistics: {e}")
        return {}

def get_sample_test_circuits(limit=20):
    """Get sample circuits from test table for display"""
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM circuit_match_test_display
                    ORDER BY provider_match_confidence DESC, site_name
                    LIMIT %s
                """, (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error getting sample circuits: {e}")
        return []

# Add this route for testing specific sites
@app.route('/test-site/<site_name>')
def test_site_circuits(site_name):
    """Test page to show circuits for a specific site"""
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Get circuits for this site
                cursor.execute("""
                    SELECT * FROM circuit_match_test_display
                    WHERE site_name = %s
                    ORDER BY circuit_purpose
                """, (site_name,))
                
                circuits = [dict(row) for row in cursor.fetchall()]
                
                # Get DSR data for comparison
                cursor.execute("""
                    SELECT site_name, circuit_purpose, provider_name, 
                           ip_address_start, details_ordered_service_speed, billing_monthly_cost
                    FROM circuits
                    WHERE site_name = %s AND status = 'Enabled'
                    ORDER BY circuit_purpose
                """, (site_name,))
                
                dsr_circuits = [dict(row) for row in cursor.fetchall()]
                
                # Get Meraki data
                cursor.execute("""
                    SELECT DISTINCT ON (network_name)
                        network_name, wan1_ip, wan1_arin_provider, wan2_ip, wan2_arin_provider
                    FROM meraki_inventory
                    WHERE network_name = %s AND device_model LIKE 'MX%'
                    ORDER BY network_name, last_updated DESC
                """, (site_name,))
                
                meraki_data = cursor.fetchone()
                meraki_data = dict(meraki_data) if meraki_data else {}
                
                return render_template('test_site_circuits.html',
                                     site_name=site_name,
                                     enriched_circuits=circuits,
                                     dsr_circuits=dsr_circuits,
                                     meraki_data=meraki_data)
                
    except Exception as e:
        logger.error(f"Error testing site {site_name}: {e}")
        return f"Error: {e}", 500