#!/usr/bin/env python3
"""
Working Inventory Page Route
This adds a working inventory page that properly displays Tab 4 data
"""

from flask import Blueprint, render_template_string, jsonify
from inventory_tabs_functions import get_datacenter_inventory

# Create a simple blueprint
inventory_working_bp = Blueprint('inventory_working', __name__)

@inventory_working_bp.route('/inventory-working')
def inventory_working():
    """Working inventory page that displays Tab 4 data"""
    # Get the datacenter inventory data
    data = get_datacenter_inventory()
    inventory = data.get('inventory', [])
    
    # Create a simple HTML template that displays the data
    template = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Inventory Summary - Tab 4 Datacenter</title>
    <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.min.css">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #2c3e50; }
        .summary { background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .parent { background-color: #e8f4f8; font-weight: bold; }
        .fex { background-color: #fff3cd; }
        table { width: 100%; }
        th { background-color: #34495e; color: white; }
    </style>
</head>
<body>
    <h1>Inventory Summary - Tab 4 Datacenter ({{ inventory|length }} items)</h1>
    
    <div class="summary">
        <h3>Summary Statistics</h3>
        <p>Total Inventory Items: {{ inventory|length }}</p>
        {% set site_counts = {} %}
        {% for item in inventory %}
            {% if item.hostname %}
                {% if item.site in site_counts %}
                    {% set _ = site_counts.update({item.site: site_counts[item.site] + 1}) %}
                {% else %}
                    {% set _ = site_counts.update({item.site: 1}) %}
                {% endif %}
            {% endif %}
        {% endfor %}
        <p>Sites: {% for site, count in site_counts.items() %}{{ site }} ({{ count }}){% if not loop.last %}, {% endif %}{% endfor %}</p>
        <p>Parent/Standalone Devices: {{ inventory|selectattr('position', 'in', ['Parent Switch', 'Standalone', 'Master'])|list|length }}</p>
        <p>FEX Devices: {% set fex_count = namespace(value=0) %}{% for item in inventory %}{% if item.position and 'FEX' in item.position %}{% set fex_count.value = fex_count.value + 1 %}{% endif %}{% endfor %}{{ fex_count.value }}</p>
        <p>Modules: {{ inventory|selectattr('position', 'equalto', 'Module')|list|length }}</p>
        <p>SFPs: {{ inventory|selectattr('position', 'equalto', 'SFP')|list|length }}</p>
    </div>
    
    <table id="inventoryTable" class="display">
        <thead>
            <tr>
                <th>Site</th>
                <th>Hostname</th>
                <th>IP Address</th>
                <th>Position</th>
                <th>Model</th>
                <th>Serial Number</th>
                <th>Port Location</th>
                <th>Vendor</th>
                <th>End of Sale</th>
                <th>End of Support</th>
            </tr>
        </thead>
        <tbody>
            {% for item in inventory %}
            <tr class="{% if item.position == 'Parent Switch' %}parent{% elif 'FEX' in item.position %}fex{% endif %}">
                <td>{{ item.site or '' }}</td>
                <td>{{ item.hostname or '' }}</td>
                <td>{{ item.ip_address or '' }}</td>
                <td>{{ item.position or '' }}</td>
                <td>{{ item.model or '' }}</td>
                <td>{{ item.serial_number or '' }}</td>
                <td>{{ item.port_location or '' }}</td>
                <td>{{ item.vendor or '' }}</td>
                <td>{{ item.end_of_sale or '' }}</td>
                <td>{{ item.end_of_support or '' }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js"></script>
    <script>
    $(document).ready(function() {
        $('#inventoryTable').DataTable({
            pageLength: 25,
            order: [[0, 'asc']],
            scrollX: true
        });
    });
    </script>
</body>
</html>
    '''
    
    return render_template_string(template, inventory=inventory)

@inventory_working_bp.route('/api/inventory-working-test')
def inventory_working_test():
    """Test API endpoint to verify data"""
    data = get_datacenter_inventory()
    return jsonify({
        'status': 'success',
        'total_items': len(data.get('inventory', [])),
        'sample': data.get('inventory', [])[:5]
    })