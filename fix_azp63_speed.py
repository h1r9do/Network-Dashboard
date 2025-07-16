#!/usr/bin/env python3
"""Fix AZP 63 circuit speed"""

from models import Circuit, db
from config import Config
from flask import Flask
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    circuit = Circuit.query.filter_by(site_name='AZP 63', circuit_purpose='Primary').first()
    if circuit:
        print(f"Current speed: {circuit.details_ordered_service_speed}")
        circuit.details_ordered_service_speed = 'Satellite'
        circuit.updated_at = datetime.utcnow()
        db.session.commit()
        print(f"Updated AZP 63 Primary circuit speed to: Satellite")
    else:
        print("Circuit not found")