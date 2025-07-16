#!/usr/bin/env python3
"""Quick fix for CAL 17 to demonstrate the correct logic"""

import sys
sys.path.insert(0, '/usr/local/bin/Main')
from nightly_meraki_db import get_db_connection, parse_raw_notes, get_provider_for_ip, compare_providers
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# The raw notes from June 24th
raw_notes = """WAN1 NOT DSR Frontier Fiber 500.0M x 500.0M
First IP 47.176.201.18
Gateway 47.176.201.17
Subnet 255.255.255.248
EVC Circuit:45/CUXP/986199/   /FTNC/
UNI Circuit:45/L1XN/986198/   /FTNC/
WAN2 VZG IMEI: 356405432462415"""

# Parse the notes
wan1_label, wan1_speed_label, wan2_label, wan2_speed_label = parse_raw_notes(raw_notes)
logger.info(f"Parsed notes:")
logger.info(f"  WAN1: Provider='{wan1_label}', Speed='{wan1_speed_label}'")
logger.info(f"  WAN2: Provider='{wan2_label}', Speed='{wan2_speed_label}'")

# Get ARIN providers
ip_cache = {}
missing_ips = set()
wan1_arin = get_provider_for_ip("47.176.201.18", ip_cache, missing_ips)
wan2_arin = get_provider_for_ip("192.168.0.151", ip_cache, missing_ips)
logger.info(f"ARIN lookups:")
logger.info(f"  WAN1: {wan1_arin}")
logger.info(f"  WAN2: {wan2_arin}")

# Compare
wan1_comparison = compare_providers(wan1_arin, wan1_label)
wan2_comparison = compare_providers(wan2_arin, wan2_label)
logger.info(f"Comparisons:")
logger.info(f"  WAN1: {wan1_comparison}")
logger.info(f"  WAN2: {wan2_comparison}")

# Check DSR data
conn = get_db_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT circuit_purpose, provider_name, status
    FROM circuits
    WHERE site_name = 'CAL 17'
    ORDER BY circuit_purpose
""")

logger.info("DSR circuits for CAL 17:")
for row in cursor.fetchall():
    logger.info(f"  {row[0]}: {row[1]} (Status: {row[2]})")

# Determine final providers
# Since DSR circuit is "Order Canceled", we should use the notes/ARIN data
wan1_final = wan1_arin  # "Frontier Communications" - matches notes
wan2_final = wan2_label if wan2_label else "VZW Cell"  # Use parsed label "VZG"

logger.info(f"\nFinal providers:")
logger.info(f"  WAN1: {wan1_final}")
logger.info(f"  WAN2: {wan2_final}")

# Update database
cursor.execute("""
    UPDATE meraki_inventory
    SET device_notes = %s,
        wan1_provider_label = %s,
        wan1_speed_label = %s,
        wan2_provider_label = %s,
        wan2_speed_label = %s,
        wan1_provider_comparison = %s,
        wan2_provider_comparison = %s,
        last_updated = NOW()
    WHERE network_name = 'CAL 17'
""", (
    raw_notes,
    wan1_label,
    wan1_speed_label,
    wan2_label,
    wan2_speed_label,
    wan1_comparison,
    wan2_comparison
))

cursor.execute("""
    UPDATE enriched_circuits
    SET wan1_provider = %s,
        wan1_speed = %s,
        wan2_provider = %s,
        wan2_speed = %s,
        last_updated = NOW()
    WHERE network_name = 'CAL 17'
""", (
    wan1_final,
    wan1_speed_label,
    wan2_final,
    "Cell"  # VZG is a cell provider
))

conn.commit()
cursor.close()
conn.close()

logger.info("CAL 17 updated successfully")