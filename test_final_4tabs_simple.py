#!/usr/bin/env python3
"""
Simple test server for final 4-tab inventory
"""
from flask import Flask, render_template, jsonify
import sys
sys.path.insert(0, '/usr/local/bin')
sys.path.insert(0, '/usr/local/bin/Main')

# Import the inventory web format function directly
from get_inventory_web_format_db import get_inventory_web_format_db
from get_inventory_web_format_hierarchical import get_inventory_csv_format_db

app = Flask(__name__, 
            template_folder='/usr/local/bin/templates',
            static_folder='/usr/local/bin/Main/static')

@app.route('/')
def index():
    return """
    <h1>Final 4-Tab Network Inventory Test</h1>
    <p>Simple test server to verify Tab 4 data:</p>
    <ul>
        <li><a href="/test-tab4-data">Test Tab 4 Data</a></li>
        <li><a href="/final/inventory-summary">View Final 4-Tab Inventory</a></li>
    </ul>
    """

@app.route('/test-tab4-data')
def test_tab4_data():
    """Test endpoint to check Tab 4 data"""
    data = get_inventory_web_format_db()
    
    html = "<h1>Tab 4 Data Test</h1>"
    html += f"<p>Total components: {len(data['inventory'])}</p>"
    html += f"<p>Summary: {data['summary']}</p>"
    
    html += "<h2>First 20 Items:</h2>"
    html += "<table border='1'>"
    html += "<tr><th>Hostname</th><th>Position</th><th>Model</th><th>Serial</th><th>EOL</th></tr>"
    
    for item in data['inventory'][:20]:
        html += f"<tr>"
        html += f"<td>{item['hostname']}</td>"
        html += f"<td>{item['position']}</td>"
        html += f"<td>{item['model']}</td>"
        html += f"<td>{item['serial_number']}</td>"
        html += f"<td>{item['end_of_support']}</td>"
        html += f"</tr>"
    
    html += "</table>"
    
    return html

@app.route('/final/inventory-summary')
def inventory_summary():
    """Simplified inventory summary page"""
    # Get Tab 4 data in CSV format
    datacenter_data = get_inventory_csv_format_db()
    
    # Create dummy corporate executive data with all required fields
    corp_executive = {
        'overall': {
            'total_models': 0,
            'total_devices': 0,
            'end_of_life': 0,
            'end_of_sale': 0,
            'active': 0,
            'eol_percentage': 0,
            'eos_percentage': 0,
            'active_percentage': 0
        },
        'by_device_type': [],
        'critical_insights': {
            'immediate_action': [],
            'high_risk_sites': [],
            'budget_planning': [],
            'security_concerns': []
        },
        'datacenter_alerts': []
    }
    
    # For now, return simple test data for other tabs
    # Use the fixed template with all 4 tabs
    return render_template('inventory_final_4tabs_fixed.html',
                         # Meraki data (dummy for now)
                         summary=[],
                         org_names=[],
                         eol_summary={
                             'by_device_type': [],
                             'overall': {
                                 'total_devices': 0,
                                 'end_of_life': 0,
                                 'end_of_sale': 0,
                                 'active': 0,
                                 'eol_percentage': 0,
                                 'eos_percentage': 0,
                                 'active_percentage': 0
                             },
                             'eol_timeline': [],
                             'critical_insights': {
                                 'immediate_action': [],
                                 'critical_years': [],
                                 'major_refreshes': [],
                                 'budget_planning': []
                             }
                         },
                         total_meraki_devices=0,
                         data_source='test',
                         # Corporate data (dummy)
                         corp_executive=corp_executive,
                         # Tab 4 data (real)
                         datacenter_data=datacenter_data,
                         today='2025-07-09')

if __name__ == '__main__':
    print("Starting simple test server on port 5053...")
    print("Visit: http://neamsatcor1ld01.trtc.com:5053/")
    app.run(host='0.0.0.0', port=5053, debug=True)