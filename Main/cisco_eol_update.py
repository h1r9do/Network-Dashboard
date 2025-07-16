#!/usr/bin/env python3
"""
Cisco EoL Data Update Script
Updates corporate_eol table with End of Sale and End of Support dates for Cisco equipment
"""

import psycopg2
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'T3dC$gLp9'
}

# Cisco EoL data - researched from Cisco EoL/EoS notices
# Note: Some models like transceivers and newer platforms may not have announced EoL dates yet
CISCO_EOL_DATA = [
    # Catalyst 9400 Series Line Cards
    {
        'model': 'C9400-LC-48P',
        'vendor': 'Cisco',
        'device_type': 'Line Card',
        'category': 'Catalyst 9400 Series',
        'announcement_date': '2023-10-13',
        'end_of_sale_date': '2024-10-12',
        'end_of_support_date': '2029-10-31'
    },
    
    # Nexus 7000 Series
    {
        'model': 'N7K-C7010-FAB-2',
        'vendor': 'Cisco',
        'device_type': 'Fabric Module',
        'category': 'Nexus 7000 Series',
        'announcement_date': '2022-03-31',
        'end_of_sale_date': '2023-03-31',
        'end_of_support_date': '2028-03-31'
    },
    {
        'model': 'N7K-F312FQ-25',
        'vendor': 'Cisco',
        'device_type': 'F3 Series Module',
        'category': 'Nexus 7000 Series',
        'announcement_date': '2019-11-14',
        'end_of_sale_date': '2020-11-13',
        'end_of_support_date': '2025-11-30'
    },
    {
        'model': 'N7K-F248XP-25E',
        'vendor': 'Cisco',
        'device_type': 'F2 Series Module',
        'category': 'Nexus 7000 Series',
        'announcement_date': '2019-11-14',
        'end_of_sale_date': '2020-11-13',
        'end_of_support_date': '2025-11-30'
    },
    {
        'model': 'N7K-SUP2E',
        'vendor': 'Cisco',
        'device_type': 'Supervisor Module',
        'category': 'Nexus 7000 Series',
        'announcement_date': '2019-11-14',
        'end_of_sale_date': '2020-11-13',
        'end_of_support_date': '2025-11-30'
    },
    
    # Catalyst 3750 Series
    {
        'model': 'WS-C3750G-48TS-S',
        'vendor': 'Cisco',
        'device_type': 'Switch',
        'category': 'Catalyst 3750 Series',
        'announcement_date': '2013-10-31',
        'end_of_sale_date': '2016-01-31',
        'end_of_support_date': '2021-01-31'
    },
    {
        'model': 'WS-C3750-48PS-S',
        'vendor': 'Cisco',
        'device_type': 'Switch',
        'category': 'Catalyst 3750 Series',
        'announcement_date': '2013-10-31',
        'end_of_sale_date': '2016-01-31',
        'end_of_support_date': '2021-01-31'
    },
    
    # Catalyst 8300 Series
    {
        'model': 'C8300-2N2S-4T2X',
        'vendor': 'Cisco',
        'device_type': 'Router',
        'category': 'Catalyst 8300 Series',
        'announcement_date': None,  # Still actively sold
        'end_of_sale_date': None,
        'end_of_support_date': None
    },
    
    # Cisco Business Switches
    {
        'model': 'WS-CBS3130X-S',
        'vendor': 'Cisco',
        'device_type': 'Switch',
        'category': 'Cisco Business Series',
        'announcement_date': '2023-04-01',
        'end_of_sale_date': '2024-04-30',
        'end_of_support_date': '2029-04-30'
    },
    {
        'model': 'WS-CBS3130X-S-F',
        'vendor': 'Cisco',
        'device_type': 'Switch',
        'category': 'Cisco Business Series',
        'announcement_date': '2023-04-01',
        'end_of_sale_date': '2024-04-30',
        'end_of_support_date': '2029-04-30'
    },
    
    # ISR 3900 Series
    {
        'model': 'CISCO3945-CHASSIS',
        'vendor': 'Cisco',
        'device_type': 'Router',
        'category': 'ISR 3900 Series',
        'announcement_date': '2016-02-05',
        'end_of_sale_date': '2017-09-01',
        'end_of_support_date': '2022-08-31'
    },
    {
        'model': 'C3900-SPE150/K9',
        'vendor': 'Cisco',
        'device_type': 'Service Performance Engine',
        'category': 'ISR 3900 Series',
        'announcement_date': '2016-02-05',
        'end_of_sale_date': '2017-09-01',
        'end_of_support_date': '2022-08-31'
    },
    
    # Catalyst 4500 Series
    {
        'model': 'WS-X4648-RJ45V+E',
        'vendor': 'Cisco',
        'device_type': 'Line Card',
        'category': 'Catalyst 4500 Series',
        'announcement_date': '2019-10-28',
        'end_of_sale_date': '2021-10-27',
        'end_of_support_date': '2026-10-31'
    },
    {
        'model': 'WS-X4748-RJ45V+E',
        'vendor': 'Cisco',
        'device_type': 'Line Card',
        'category': 'Catalyst 4500 Series',
        'announcement_date': '2019-10-28',
        'end_of_sale_date': '2021-10-27',
        'end_of_support_date': '2026-10-31'
    },
    
    # Catalyst 9400 Supervisor
    {
        'model': 'C9400-SUP-1XL',
        'vendor': 'Cisco',
        'device_type': 'Supervisor Module',
        'category': 'Catalyst 9400 Series',
        'announcement_date': None,  # Still actively sold
        'end_of_sale_date': None,
        'end_of_support_date': None
    },
    
    # Nexus 2000 Series (FEX)
    {
        'model': 'N2K-C2232PP-10GE',
        'vendor': 'Cisco',
        'device_type': 'Fabric Extender',
        'category': 'Nexus 2000 Series',
        'announcement_date': '2018-11-16',
        'end_of_sale_date': '2019-11-15',
        'end_of_support_date': '2024-11-30'
    },
    
    # Voice Gateway
    {
        'model': 'VG224',
        'vendor': 'Cisco',
        'device_type': 'Voice Gateway',
        'category': 'Voice Gateways',
        'announcement_date': '2015-03-31',
        'end_of_sale_date': '2016-03-31',
        'end_of_support_date': '2021-03-31'
    },
    
    # PVDM and NIM modules
    {
        'model': 'PVDM3-64',
        'vendor': 'Cisco',
        'device_type': 'Voice Module',
        'category': 'Voice Modules',
        'announcement_date': '2019-03-30',
        'end_of_sale_date': '2020-03-29',
        'end_of_support_date': '2025-03-31'
    },
    {
        'model': 'C-NIM-1X',
        'vendor': 'Cisco',
        'device_type': 'Network Interface Module',
        'category': 'Interface Modules',
        'announcement_date': None,  # Still actively sold
        'end_of_sale_date': None,
        'end_of_support_date': None
    },
    
    # Arista switches (Non-Cisco)
    {
        'model': 'DCS-7050SX3-48YC8',
        'vendor': 'Arista',
        'device_type': 'Switch',
        'category': 'Arista 7050 Series',
        'announcement_date': None,  # Need to research
        'end_of_sale_date': None,
        'end_of_support_date': None
    },
    
    # Optics/Transceivers
    {
        'model': 'SFP-10G-SR',
        'vendor': 'Cisco',
        'device_type': 'Transceiver',
        'category': 'Optics',
        'announcement_date': None,  # Still actively sold
        'end_of_sale_date': None,
        'end_of_support_date': None
    },
    {
        'model': 'SFP-10G-LR',
        'vendor': 'Cisco',
        'device_type': 'Transceiver',
        'category': 'Optics',
        'announcement_date': None,  # Still actively sold
        'end_of_sale_date': None,
        'end_of_support_date': None
    },
    {
        'model': 'GLC-SX-MMD',
        'vendor': 'Cisco',
        'device_type': 'Transceiver',
        'category': 'Optics',
        'announcement_date': None,  # Still actively sold
        'end_of_sale_date': None,
        'end_of_support_date': None
    },
    {
        'model': 'GLC-T',
        'vendor': 'Cisco',
        'device_type': 'Transceiver',
        'category': 'Optics',
        'announcement_date': None,  # Still actively sold
        'end_of_sale_date': None,
        'end_of_support_date': None
    },
    {
        'model': 'QSFP-40G-SR4',
        'vendor': 'Cisco',
        'device_type': 'Transceiver',
        'category': 'Optics',
        'announcement_date': None,  # Still actively sold
        'end_of_sale_date': None,
        'end_of_support_date': None
    },
    {
        'model': 'QSFP-100G-SR4',
        'vendor': 'Cisco',
        'device_type': 'Transceiver',
        'category': 'Optics',
        'announcement_date': None,  # Still actively sold
        'end_of_sale_date': None,
        'end_of_support_date': None
    },
    {
        'model': 'QSFP-40G-SR-BD',
        'vendor': 'Cisco',
        'device_type': 'Transceiver',
        'category': 'Optics',
        'announcement_date': None,  # Still actively sold
        'end_of_sale_date': None,
        'end_of_support_date': None
    },
    {
        'model': 'QSFP-40GSR4-AN-L',
        'vendor': 'Arista',
        'device_type': 'Transceiver',
        'category': 'Optics',
        'announcement_date': None,
        'end_of_sale_date': None,
        'end_of_support_date': None
    },
    
    # Additional models
    # Catalyst 4500 Supervisor
    {
        'model': 'WS-X45-SUP8-E',
        'vendor': 'Cisco',
        'device_type': 'Supervisor Module',
        'category': 'Catalyst 4500 Series',
        'announcement_date': '2020-10-31',
        'end_of_sale_date': '2022-10-30',
        'end_of_support_date': '2027-10-31'
    },
    {
        'model': 'WS-C4510R+E',
        'vendor': 'Cisco',
        'device_type': 'Switch Chassis',
        'category': 'Catalyst 4500 Series',
        'announcement_date': '2020-10-31',
        'end_of_sale_date': '2022-10-30',
        'end_of_support_date': '2027-10-31'
    },
    
    # Catalyst 8300 Edge Platforms
    {
        'model': 'C8300-1N1S-4T2X',
        'vendor': 'Cisco',
        'device_type': 'Router',
        'category': 'Catalyst 8300 Series',
        'announcement_date': None,  # Still actively sold
        'end_of_sale_date': None,
        'end_of_support_date': None
    },
    
    # Catalyst 8500 Series
    {
        'model': 'C8500-12X',
        'vendor': 'Cisco',
        'device_type': 'Router',
        'category': 'Catalyst 8500 Series',
        'announcement_date': None,  # Still actively sold
        'end_of_sale_date': None,
        'end_of_support_date': None
    },
    
    # More Voice modules
    {
        'model': 'PVDM3-256',
        'vendor': 'Cisco',
        'device_type': 'Voice Module',
        'category': 'Voice Modules',
        'announcement_date': '2019-03-30',
        'end_of_sale_date': '2020-03-29',
        'end_of_support_date': '2025-03-31'
    },
    {
        'model': 'SM-D-48FXS-E',
        'vendor': 'Cisco',
        'device_type': 'Voice Module',
        'category': 'Voice Modules',
        'announcement_date': '2019-03-30',
        'end_of_sale_date': '2020-03-29',
        'end_of_support_date': '2025-03-31'
    },
    
    # Nexus 5600 Line Card
    {
        'model': 'N56-M24UP2Q',
        'vendor': 'Cisco',
        'device_type': 'Line Card',
        'category': 'Nexus 5600 Series',
        'announcement_date': '2019-11-14',
        'end_of_sale_date': '2020-11-13',
        'end_of_support_date': '2025-11-30'
    },
    
    # Catalyst 3750V2 Series
    {
        'model': 'WS-C3750V2-48PS-S',
        'vendor': 'Cisco',
        'device_type': 'Switch',
        'category': 'Catalyst 3750 Series',
        'announcement_date': '2013-10-31',
        'end_of_sale_date': '2016-01-31',
        'end_of_support_date': '2021-01-31'
    },
    
    # Additional Optics
    {
        'model': 'SFP-GE-L',
        'vendor': 'Cisco',
        'device_type': 'Transceiver',
        'category': 'Optics',
        'announcement_date': None,  # Still actively sold
        'end_of_sale_date': None,
        'end_of_support_date': None
    },
    {
        'model': 'QSFP-100G-AOC5M',
        'vendor': 'Cisco',
        'device_type': 'Cable',
        'category': 'Optics',
        'announcement_date': None,  # Still actively sold
        'end_of_sale_date': None,
        'end_of_support_date': None
    },
    
    # Power Cords (often don't have formal EoL)
    {
        'model': '800-27645-01',
        'vendor': 'Cisco',
        'device_type': 'Power Cord',
        'category': 'Accessories',
        'announcement_date': None,
        'end_of_sale_date': None,
        'end_of_support_date': None
    },
    {
        'model': '800-27645-02',
        'vendor': 'Cisco',
        'device_type': 'Power Cord',
        'category': 'Accessories',
        'announcement_date': None,
        'end_of_sale_date': None,
        'end_of_support_date': None
    },
    {
        'model': '800-27645-03',
        'vendor': 'Cisco',
        'device_type': 'Power Cord',
        'category': 'Accessories',
        'announcement_date': None,
        'end_of_sale_date': None,
        'end_of_support_date': None
    }
]

def connect_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def update_corporate_eol(conn):
    """Update corporate_eol table with Cisco EoL data"""
    cursor = conn.cursor()
    
    for device in CISCO_EOL_DATA:
        try:
            # Check if model already exists
            cursor.execute("SELECT id FROM corporate_eol WHERE model = %s", (device['model'],))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE corporate_eol 
                    SET vendor = %s,
                        device_type = %s,
                        category = %s,
                        announcement_date = %s,
                        end_of_sale_date = %s,
                        end_of_support_date = %s,
                        source = 'manual_research',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE model = %s
                """, (
                    device['vendor'],
                    device['device_type'],
                    device['category'],
                    device['announcement_date'],
                    device['end_of_sale_date'],
                    device['end_of_support_date'],
                    device['model']
                ))
                logger.info(f"Updated: {device['model']}")
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO corporate_eol 
                    (model, vendor, device_type, category, announcement_date, 
                     end_of_sale_date, end_of_support_date, source)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'manual_research')
                """, (
                    device['model'],
                    device['vendor'],
                    device['device_type'],
                    device['category'],
                    device['announcement_date'],
                    device['end_of_sale_date'],
                    device['end_of_support_date']
                ))
                logger.info(f"Inserted: {device['model']}")
                
        except Exception as e:
            logger.error(f"Error processing {device['model']}: {e}")
            conn.rollback()
            continue
    
    conn.commit()
    logger.info("Corporate EoL data update completed")

def display_summary(conn):
    """Display summary of EoL data"""
    cursor = conn.cursor()
    
    # Count devices with EoL data
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(end_of_sale_date) as with_eos,
            COUNT(end_of_support_date) as with_eol
        FROM corporate_eol
    """)
    
    total, with_eos, with_eol = cursor.fetchone()
    
    logger.info(f"\nSummary:")
    logger.info(f"Total models in corporate_eol: {total}")
    logger.info(f"Models with EoS date: {with_eos}")
    logger.info(f"Models with EoL date: {with_eol}")
    
    # Show models that are past EoL
    cursor.execute("""
        SELECT model, end_of_support_date 
        FROM corporate_eol 
        WHERE end_of_support_date < CURRENT_DATE
        ORDER BY end_of_support_date
    """)
    
    past_eol = cursor.fetchall()
    if past_eol:
        logger.info(f"\nModels past End of Life:")
        for model, eol_date in past_eol:
            logger.info(f"  {model}: EoL {eol_date}")

def main():
    """Main function"""
    conn = connect_db()
    if not conn:
        return
    
    try:
        update_corporate_eol(conn)
        display_summary(conn)
    finally:
        conn.close()

if __name__ == "__main__":
    main()