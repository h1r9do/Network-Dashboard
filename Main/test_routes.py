#!/usr/bin/env python3
"""
Test routes to add to dsrcircuits.py for provider matching testing
"""

# Add these routes to your dsrcircuits.py file

@app.route('/dsrcircuits-test')
def dsrcircuits_test():
    """Test version of DSR Circuits using provider_match_test table"""
    
    try:
        # Get statistics from test table
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Get statistics
                cursor.execute("SELECT * FROM provider_test_statistics")
                stats = cursor.fetchone()
                stats = dict(stats) if stats else {}
                
                # Get sample data
                cursor.execute("""
                    SELECT * FROM provider_match_test_display
                    ORDER BY provider_match_confidence DESC, site_name
                    LIMIT 20
                """)
                sample_circuits = [dict(row) for row in cursor.fetchall()]
                
                return render_template('dsrcircuits_test.html', 
                                     stats=stats, 
                                     sample_circuits=sample_circuits)
    except Exception as e:
        logger.error(f"Error in dsrcircuits-test: {e}")
        return f"Error: {e}", 500

@app.route('/api/circuit-matches-test/<site_name>')
def get_circuit_matches_test(site_name):
    """Get circuit matches for a specific site from test table"""
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("""
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
                    WHERE site_name = %s
                    ORDER BY circuit_purpose
                """, (site_name,))
                
                circuits = [dict(row) for row in cursor.fetchall()]
                
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

@app.route('/api/test-statistics')
def get_test_statistics_api():
    """Get provider matching test statistics"""
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM provider_test_statistics")
                stats = cursor.fetchone()
                return jsonify(dict(stats) if stats else {})
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
                    FROM provider_match_test
                    WHERE provider_match_status IN ('no_match', 'no_data')
                    ORDER BY site_name, circuit_purpose
                    LIMIT 50
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

@app.route('/test-site/<site_name>')
def test_site_circuits(site_name):
    """Test page to show circuits for a specific site"""
    
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Get test results for this site
                cursor.execute("""
                    SELECT * FROM provider_match_test_display
                    WHERE site_name = %s
                    ORDER BY circuit_purpose
                """, (site_name,))
                
                test_circuits = [dict(row) for row in cursor.fetchall()]
                
                # Get original DSR data for comparison
                cursor.execute("""
                    SELECT site_name, circuit_purpose, provider_name, 
                           ip_address_start, details_ordered_service_speed, billing_monthly_cost
                    FROM circuits
                    WHERE site_name = %s AND status = 'Enabled'
                    ORDER BY circuit_purpose
                """, (site_name,))
                
                dsr_circuits = [dict(row) for row in cursor.fetchall()]
                
                return render_template('test_site_circuits.html',
                                     site_name=site_name,
                                     test_circuits=test_circuits,
                                     dsr_circuits=dsr_circuits)
                
    except Exception as e:
        logger.error(f"Error testing site {site_name}: {e}")
        return f"Error: {e}", 500