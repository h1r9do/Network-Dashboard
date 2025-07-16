#!/usr/bin/env python3
"""
Quick test endpoint for Excel-only inventory
"""
from flask import Flask, render_template
import sys
sys.path.insert(0, '/usr/local/bin')

from inventory_excel_only import inventory_bp

app = Flask(__name__)
app.register_blueprint(inventory_bp, url_prefix='/excel')

if __name__ == '__main__':
    print("Test server running on port 5053")
    print("Visit: http://neamsatcor1ld01.trtc.com:5053/excel/inventory-summary")
    app.run(host='0.0.0.0', port=5053, debug=True)