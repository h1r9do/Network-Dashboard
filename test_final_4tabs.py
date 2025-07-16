#!/usr/bin/env python3
"""
Final 4-tab test with rich executive summaries - Updated for comprehensive inventory
"""
from flask import Flask, render_template_string
import sys
sys.path.insert(0, '/usr/local/bin')

from inventory_final_4tabs import inventory_bp

app = Flask(__name__)
app.register_blueprint(inventory_bp, url_prefix='/final')

# Load the tab 2 content
with open('/usr/local/bin/templates/tab2_corp_executive_content.html', 'r') as f:
    TAB2_CONTENT = f.read()

# Create a custom template that includes the rich tab 2
CUSTOM_TEMPLATE = '''{% extends "inventory_summary.html" %}

{% block additional_content %}
<script>
// Override to add tab functionality
var TAB2_HTML = `{{ tab2_content|safe }}`;
</script>
{% endblock %}
'''

@app.route('/')
def index():
    return """
    <h1>Final 4-Tab Network Inventory</h1>
    <p>Complete implementation with rich executive summaries:</p>
    <ul>
        <li><strong>Tab 1:</strong> Meraki Executive Summary (original, unchanged)</li>
        <li><strong>Tab 2:</strong> Corp Network Executive Summary (rich format like Tab 1)</li>
        <li><strong>Tab 3:</strong> Meraki Inventory Details (original table)</li>
        <li><strong>Tab 4:</strong> All Data Centers with EOL dates</li>
    </ul>
    <p><a href="/final/inventory-summary">View Final 4-Tab Inventory</a></p>
    """

@app.context_processor
def inject_tab2():
    return dict(tab2_content=TAB2_CONTENT)

if __name__ == '__main__':
    print("Starting final 4-tab server on port 5053...")
    print("Visit: http://neamsatcor1ld01.trtc.com:5053/final/inventory-summary")
    app.run(host='0.0.0.0', port=5053, debug=True)