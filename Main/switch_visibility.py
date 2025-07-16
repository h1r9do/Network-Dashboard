"""
SWITCH PORT VISIBILITY - NETWORK DEVICE TRACKING
===============================================

Purpose:
    - Track and display all devices connected to switch ports
    - Provide real-time visibility into network topology
    - Allow on-demand refresh of switch data
    - Search and filter by various parameters

Pages Served:
    - /switch-visibility (main switch port client listing)

Templates Used:
    - switch_visibility.html (main interface similar to dsrcircuits)

API Endpoints:
    - /api/switch-port-clients (GET) - Retrieve switch port data with filtering
    - /api/switch-port-clients/refresh-switch/<serial> (POST) - Refresh single switch
    - /api/switch-port-clients/refresh-store/<store_name> (POST) - Refresh all switches in store

Key Functions:
    - Real-time switch port client tracking
    - On-demand data refresh per switch or store
    - Search by hostname, IP, MAC, switch name
    - Filter by store, VLAN, port
    - Export to Excel/CSV
    - Manufacturer identification from MAC address

Dependencies:
    - Direct database queries using SQLAlchemy
    - Meraki API for refresh functionality
    - Redis caching for performance
"""

from flask import Blueprint, render_template, jsonify, request, send_file, current_app
import requests
import logging
from datetime import datetime, timedelta
import json
import re
from io import BytesIO
import pandas as pd
from sqlalchemy import text
import redis
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from models import db, SwitchPortClient
from config import Config, get_redis_connection

# Create Blueprint
switch_visibility_bp = Blueprint('switch_visibility', __name__)
logger = logging.getLogger(__name__)

# Meraki API configuration
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY", "5174c907a7d57dea6a0788617287c985cc80b3c1")
MERAKI_BASE_URL = 'https://api.meraki.com/api/v1'
MERAKI_ORG_NAME = 'DTC-Store-Inventory-All'

# Headers for Meraki API
meraki_headers = {
    'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
    'Content-Type': 'application/json'
}

# Request timeout settings
API_TIMEOUT = 15  # seconds
API_RETRY_ATTEMPTS = 2

# Thread lock for logging
log_lock = threading.Lock()

def debug_log(message, level="INFO"):
    """Thread-safe console debugging with timestamps"""
    with log_lock:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] SWITCH_VISIBILITY: {message}")
        if level == "ERROR":
            logger.error(message)
        else:
            logger.info(message)

def make_api_request(url, headers, description="API request", timeout=API_TIMEOUT):
    """Make API request with timeout and retry logic"""
    debug_log(f"Making {description} to {url}")
    
    for attempt in range(API_RETRY_ATTEMPTS):
        try:
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=timeout)
            duration = time.time() - start_time
            
            debug_log(f"{description} completed in {duration:.2f}s (attempt {attempt + 1})")
            
            if response.status_code == 200:
                return response
            else:
                debug_log(f"{description} failed with status {response.status_code}: {response.text}", "ERROR")
                if attempt < API_RETRY_ATTEMPTS - 1:
                    debug_log(f"Retrying {description} in 1 second...", "WARN")
                    time.sleep(1)
                    
        except requests.exceptions.Timeout:
            debug_log(f"{description} timed out after {timeout}s (attempt {attempt + 1})", "ERROR")
            if attempt < API_RETRY_ATTEMPTS - 1:
                debug_log(f"Retrying {description} with longer timeout...", "WARN")
                timeout = timeout * 1.5  # Increase timeout for retry
                time.sleep(1)
        except Exception as e:
            debug_log(f"{description} failed with error: {str(e)} (attempt {attempt + 1})", "ERROR")
            if attempt < API_RETRY_ATTEMPTS - 1:
                time.sleep(1)
    
    return None

def get_mac_manufacturer(mac):
    """Get manufacturer from MAC address using local OUI database"""
    # This is a simplified version - in production you'd have a full OUI database
    mac_prefixes = {
        '00:18:0a': 'Cisco Meraki',
        '00:23:ac': 'Cisco',
        '00:0c:29': 'VMware',
        'f4:ce:46': 'Hewlett Packard',
        '00:50:56': 'VMware',
        '00:1b:21': 'Intel',
        '00:15:5d': 'Microsoft',
        '00:0d:3a': 'Microsoft',
        '00:17:88': 'Philips',
        '00:1a:a0': 'Dell',
        '00:21:9b': 'Dell',
        '00:22:19': 'Dell',
        '00:24:e8': 'Dell',
        '00:25:64': 'Dell',
        '98:90:96': 'Dell',
        'b0:83:fe': 'Dell',
        'd0:94:66': 'Dell',
        'f8:b1:56': 'Dell',
        'f8:bc:12': 'Dell',
        '00:08:74': 'Dell',
        '00:0b:db': 'Dell',
        '00:0f:1f': 'Dell',
        '00:11:43': 'Dell',
        '00:12:3f': 'Dell',
        '00:13:72': 'Dell',
        '00:14:22': 'Dell',
        '00:15:c5': 'Dell',
        '00:16:f0': 'Dell',
        '00:18:8b': 'Dell',
        '00:19:b9': 'Dell',
        '00:1a:a0': 'Dell',
        '00:1c:23': 'Dell',
        '00:1d:09': 'Dell',
        '00:1e:4f': 'Dell',
        '00:1e:c9': 'Dell',
        '00:21:70': 'Dell',
        '00:22:19': 'Dell',
        '00:23:ae': 'Dell',
        '14:b3:1f': 'Dell',
        '18:03:73': 'Dell',
        '18:66:da': 'Dell',
        '1c:40:24': 'Dell',
        '20:04:0f': 'Dell',
        '24:6e:96': 'Dell',
        '28:f1:0e': 'Dell',
        '34:17:eb': 'Dell',
        '44:a8:42': 'Dell',
        '50:9a:4c': 'Dell',
        '54:9f:35': 'Dell',
        '5c:f9:dd': 'Dell',
        '74:86:7a': 'Dell',
        '74:e6:e2': 'Dell',
        '78:2b:cb': 'Dell',
        '84:2b:2b': 'Dell',
        '84:7b:eb': 'Dell',
        '90:b1:1c': 'Dell',
        'a4:1f:72': 'Dell',
        'a4:ba:db': 'Dell',
        'b8:2a:72': 'Dell',
        'b8:ac:6f': 'Dell',
        'bc:30:5b': 'Dell',
        'd0:67:e5': 'Dell',
        'd4:81:d7': 'Dell',
        'd4:ae:52': 'Dell',
        'e0:db:55': 'Dell',
        'ec:f4:bb': 'Dell',
        'f0:1f:af': 'Dell',
        'f4:8e:38': 'Dell',
        'f8:db:88': 'Dell',
        '5c:26:0a': 'HP',
        '3c:d9:2b': 'HP',
        '94:57:a5': 'HP',
        'fc:15:b4': 'HP',
        '70:5a:0f': 'HP',
        '00:21:5a': 'HP',
        '00:23:7d': 'HP',
        '00:25:b3': 'HP',
        '1c:98:ec': 'HP',
        '2c:27:d7': 'HP',
        '40:b0:34': 'HP',
        '64:51:06': 'HP',
        '78:e7:d1': 'HP',
        'a0:b3:cc': 'HP',
        'b4:b5:2f': 'HP',
        'c4:34:6b': 'HP',
        'd8:9d:67': 'HP',
        'ec:8e:b5': 'HP',
        'c8:cb:b8': 'HP',
        '30:e1:71': 'HP',
        '00:30:c1': 'HP',
        '00:1b:78': 'HP',
        '00:1e:0b': 'HP',
        'd4:c9:ef': 'HP',
        '00:9c:02': 'HP',
        '68:b5:99': 'HP',
        '38:63:bb': 'HP',
        '9c:8e:99': 'HP',
        'a0:8c:fd': 'HP',
        'a0:d3:c1': 'HP',
        'ac:16:2d': 'HP',
        '3c:52:82': 'HP',
        '00:0a:57': 'HP',
        'ec:b1:d7': 'HP',
        '10:60:4b': 'HP',
        '00:17:08': 'HP',
        '00:1a:4b': 'HP',
        '00:1f:29': 'HP',
        '00:24:81': 'HP',
        'f0:92:1c': 'HP',
        '00:50:8b': 'Compaq',
        '08:00:09': 'HP',
        '00:01:e6': 'HP',
        '00:02:a5': 'HP',
        '00:04:ea': 'HP',
        '00:08:02': 'HP',
        '00:08:83': 'HP',
        '00:10:83': 'HP',
        '00:10:e3': 'HP',
        '00:11:0a': 'HP',
        '00:11:85': 'HP',
        '00:12:79': 'HP',
        '00:13:21': 'HP',
        '00:14:38': 'HP',
        '00:14:c2': 'HP',
        '00:15:60': 'HP',
        '00:16:35': 'HP',
        '00:18:fe': 'HP',
        '00:19:bb': 'HP',
        '00:1a:4b': 'HP',
        '00:1b:3f': 'HP',
        '00:1c:2e': 'HP',
        '00:1c:c4': 'HP',
        '00:1d:73': 'HP',
        '00:1e:0b': 'HP',
        '00:1f:fe': 'HP',
        '00:21:5a': 'HP',
        '00:22:64': 'HP',
        '00:23:7d': 'HP',
        '00:24:81': 'HP',
        '00:25:61': 'HP',
        '00:25:b3': 'HP',
        '00:26:55': 'HP',
        '00:26:f1': 'HP',
        '00:30:6e': 'HP',
        '00:40:17': 'HP',
        '00:50:8b': 'HP',
        '00:60:b0': 'HP',
        '00:80:a0': 'HP',
        '08:00:09': 'HP',
        '08:2e:5f': 'HP',
        '18:a9:05': 'HP',
        '1c:c1:de': 'HP',
        '28:92:4a': 'HP',
        '2c:23:3a': 'HP',
        '2c:41:38': 'HP',
        '2c:59:e5': 'HP',
        '2c:76:8a': 'HP',
        '30:8d:99': 'HP',
        '3c:4a:92': 'HP',
        '3c:a8:2a': 'HP',
        '3c:d9:2b': 'HP',
        '48:0f:cf': 'HP',
        '48:df:37': 'HP',
        '4c:39:09': 'HP',
        '50:65:f3': 'HP',
        '58:20:b1': 'HP',
        '5c:8a:38': 'HP',
        '5c:b9:01': 'HP',
        '64:31:50': 'HP',
        '68:b5:99': 'HP',
        '6c:3b:e5': 'HP',
        '6c:c2:17': 'HP',
        '70:5a:0f': 'HP',
        '74:46:a0': 'HP',
        '78:0c:b8': 'HP',
        '78:48:59': 'HP',
        '78:ac:c0': 'HP',
        '78:e3:b5': 'HP',
        '80:01:84': 'HP',
        '80:c1:6e': 'HP',
        '80:ce:62': 'HP',
        '80:e8:2c': 'HP',
        '84:34:97': 'HP',
        '88:51:fb': 'HP',
        '88:b1:11': 'HP',
        '8c:dc:d4': 'HP',
        '90:1b:0e': 'HP',
        '90:e7:c4': 'HP',
        '94:18:82': 'HP',
        '94:57:a5': 'HP',
        '98:4b:e1': 'HP',
        '98:e7:f4': 'HP',
        '9c:b6:54': 'HP',
        '9c:dc:71': 'HP',
        'a0:1d:48': 'HP',
        'a0:2b:b8': 'HP',
        'a0:48:1c': 'HP',
        'a0:b3:cc': 'HP',
        'a4:5d:36': 'HP',
        'a8:bd:27': 'HP',
        'ac:b3:13': 'HP',
        'b0:5a:da': 'HP',
        'b4:99:ba': 'HP',
        'b4:b5:2f': 'HP',
        'b8:af:67': 'HP',
        'bc:ea:fa': 'HP',
        'c0:91:34': 'HP',
        'c4:34:6b': 'HP',
        'c8:b5:ad': 'HP',
        'c8:cb:b8': 'HP',
        'c8:d3:ff': 'HP',
        'd0:7e:28': 'HP',
        'd0:bf:9c': 'HP',
        'd4:85:64': 'HP',
        'd8:9d:67': 'HP',
        'd8:b1:2a': 'HP',
        'd8:d3:85': 'HP',
        'dc:4a:3e': 'HP',
        'e0:07:1b': 'HP',
        'e4:11:5b': 'HP',
        'e8:39:35': 'HP',
        'e8:b2:ac': 'HP',
        'e8:f7:24': 'HP',
        'ec:8e:b5': 'HP',
        'ec:b1:d7': 'HP',
        'ec:eb:b8': 'HP',
        'f0:92:1c': 'HP',
        'f4:03:43': 'HP',
        'f4:39:09': 'HP',
        'f4:ce:46': 'HP',
        'f8:b1:56': 'HP',
        'fc:15:b4': 'HP',
        'fc:3f:db': 'HP',
        '00:1f:f3': 'Apple',
        '00:23:32': 'Apple',
        '00:23:df': 'Apple',
        '00:25:4b': 'Apple',
        '00:25:bc': 'Apple',
        '00:26:08': 'Apple',
        '00:26:4a': 'Apple',
        '00:26:b0': 'Apple',
        '00:26:bb': 'Apple',
        '00:3e:e1': 'Apple',
        '00:50:e4': 'Apple',
        '00:61:71': 'Apple',
        '00:88:65': 'Apple',
        '00:a0:40': 'Apple',
        '00:c6:10': 'Apple',
        '00:cd:fe': 'Apple',
        '00:d8:3b': 'Apple',
        '00:db:70': 'Apple',
        '00:f4:b9': 'Apple',
        '00:f7:6f': 'Apple',
        '04:0c:ce': 'Apple',
        '04:15:52': 'Apple',
        '04:1e:64': 'Apple',
        '04:26:65': 'Apple',
        '04:48:9a': 'Apple',
        '04:4b:ed': 'Apple',
        '04:52:f3': 'Apple',
        '04:54:53': 'Apple',
        '04:d3:cf': 'Apple',
        '04:db:56': 'Apple',
        '04:e5:36': 'Apple',
        '04:f1:3e': 'Apple',
        '04:f7:e4': 'Apple',
        '08:00:07': 'Apple',
        '08:66:98': 'Apple',
        '08:6d:41': 'Apple',
        '08:70:45': 'Apple',
        '08:74:02': 'Apple',
        '08:f4:ab': 'Apple',
        '08:f6:9c': 'Apple',
        '0c:15:39': 'Apple',
        '0c:30:21': 'Apple',
        '0c:3e:9f': 'Apple',
        '0c:4d:e9': 'Apple',
        '0c:51:01': 'Apple',
        '0c:74:c2': 'Apple',
        '0c:77:1a': 'Apple',
        '0c:bc:9f': 'Apple',
        '0c:d7:46': 'Apple',
        '0c:f3:46': 'Apple',
        '10:1c:0c': 'Apple',
        '10:40:f3': 'Apple',
        '10:41:7f': 'Apple',
        '10:93:e9': 'Apple',
        '10:94:bb': 'Apple',
        '10:9a:dd': 'Apple',
        '10:dd:b1': 'Apple',
        '14:10:9f': 'Apple',
        '14:5a:05': 'Apple',
        '14:8f:c6': 'Apple',
        '14:99:e2': 'Apple',
        '14:bd:61': 'Apple',
        '14:c2:13': 'Apple',
        '18:20:32': 'Apple',
        '18:34:51': 'Apple',
        '18:65:90': 'Apple',
        '18:9e:fc': 'Apple',
        '18:af:61': 'Apple',
        '18:af:8f': 'Apple',
        '18:e7:f4': 'Apple',
        '18:ee:69': 'Apple',
        '18:f1:d8': 'Apple',
        '18:f6:43': 'Apple',
        '1c:1a:c0': 'Apple',
        '1c:36:bb': 'Apple',
        '1c:5c:f2': 'Apple',
        '1c:91:48': 'Apple',
        '1c:9e:46': 'Apple',
        '1c:ab:a7': 'Apple',
        '1c:e6:2b': 'Apple',
        '20:3c:ae': 'Apple',
        '20:78:f0': 'Apple',
        '20:7d:74': 'Apple',
        '20:9b:cd': 'Apple',
        '20:a2:e4': 'Apple',
        '20:ab:37': 'Apple',
        '20:c9:d0': 'Apple',
        '20:ee:28': 'Apple',
        '24:1e:eb': 'Apple',
        '24:24:0c': 'Apple',
        '24:5b:a7': 'Apple',
        '24:a0:74': 'Apple',
        '24:a2:e1': 'Apple',
        '24:ab:81': 'Apple',
        '24:e3:14': 'Apple',
        '24:f0:94': 'Apple',
        '24:f6:77': 'Apple',
        '28:0b:5c': 'Apple',
        '28:37:37': 'Apple',
        '28:5a:eb': 'Apple',
        '28:6a:b8': 'Apple',
        '28:6a:ba': 'Apple',
        '28:a0:2b': 'Apple',
        '28:cf:da': 'Apple',
        '28:cf:e9': 'Apple',
        '28:e0:2c': 'Apple',
        '28:e1:4c': 'Apple',
        '28:e7:cf': 'Apple',
        '28:ed:6a': 'Apple',
        '28:f0:76': 'Apple',
        '2c:1f:23': 'Apple',
        '2c:20:0b': 'Apple',
        '2c:33:61': 'Apple',
        '2c:b4:3a': 'Apple',
        '2c:be:08': 'Apple',
        '2c:f0:a2': 'Apple',
        '2c:f0:ee': 'Apple',
        '30:10:e4': 'Apple',
        '30:35:ad': 'Apple',
        '30:63:6b': 'Apple',
        '30:90:ab': 'Apple',
        '30:f7:c5': 'Apple',
        '34:08:bc': 'Apple',
        '34:12:98': 'Apple',
        '34:15:9e': 'Apple',
        '34:36:3b': 'Apple',
        '34:51:c9': 'Apple',
        '34:7c:25': 'Apple',
        '34:a3:95': 'Apple',
        '34:ab:37': 'Apple',
        '34:c0:59': 'Apple',
        '34:e2:fd': 'Apple',
        '38:0f:4a': 'Apple',
        '38:48:4c': 'Apple',
        '38:53:9c': 'Apple',
        '38:66:f0': 'Apple',
        '38:71:de': 'Apple',
        '38:b5:4d': 'Apple',
        '38:c9:86': 'Apple',
        '38:ca:da': 'Apple',
        '38:f9:d3': 'Apple',
        '3c:07:54': 'Apple',
        '3c:0e:23': 'Apple',
        '3c:15:c2': 'Apple',
        '3c:2e:f9': 'Apple',
        '3c:2e:ff': 'Apple',
        '3c:ab:8e': 'Apple',
        '3c:d0:f8': 'Apple',
        '3c:e0:72': 'Apple',
        '40:30:04': 'Apple',
        '40:33:1a': 'Apple',
        '40:3c:fc': 'Apple',
        '40:4d:7f': 'Apple',
        '40:6c:8f': 'Apple',
        '40:83:1d': 'Apple',
        '40:98:ad': 'Apple',
        '40:a6:d9': 'Apple',
        '40:b3:95': 'Apple',
        '40:bc:60': 'Apple',
        '40:cb:c0': 'Apple',
        '40:d3:2d': 'Apple',
        '44:00:10': 'Apple',
        '44:2a:60': 'Apple',
        '44:4c:0c': 'Apple',
        '44:d8:84': 'Apple',
        '44:fb:42': 'Apple',
        '48:43:7c': 'Apple',
        '48:4b:aa': 'Apple',
        '48:60:bc': 'Apple',
        '48:74:6e': 'Apple',
        '48:a1:95': 'Apple',
        '48:bf:6b': 'Apple',
        '48:d7:05': 'Apple',
        '48:e9:f1': 'Apple',
        '4c:32:75': 'Apple',
        '4c:57:ca': 'Apple',
        '4c:74:bf': 'Apple',
        '4c:7c:5f': 'Apple',
        '4c:8d:79': 'Apple',
        '4c:b1:99': 'Apple',
        '50:32:37': 'Apple',
        '50:7a:55': 'Apple',
        '50:82:d5': 'Apple',
        '50:ea:d6': 'Apple',
        '50:ed:3c': 'Apple',
        '54:26:96': 'Apple',
        '54:33:cb': 'Apple',
        '54:4e:90': 'Apple',
        '54:72:4f': 'Apple',
        '54:9f:13': 'Apple',
        '54:ae:27': 'Apple',
        '54:e4:3a': 'Apple',
        '54:ea:a8': 'Apple',
        '58:1f:aa': 'Apple',
        '58:40:4e': 'Apple',
        '58:55:ca': 'Apple',
        '58:7f:57': 'Apple',
        '58:b0:35': 'Apple',
        '58:e2:8f': 'Apple',
        '5c:1d:d9': 'Apple',
        '5c:59:48': 'Apple',
        '5c:5f:67': 'Apple',
        '5c:8d:4e': 'Apple',
        '5c:95:ae': 'Apple',
        '5c:96:9d': 'Apple',
        '5c:97:f3': 'Apple',
        '5c:ad:cf': 'Apple',
        '5c:e9:1e': 'Apple',
        '5c:f5:da': 'Apple',
        '5c:f7:e6': 'Apple',
        '5c:f9:38': 'Apple',
        '60:03:08': 'Apple',
        '60:33:4b': 'Apple',
        '60:69:44': 'Apple',
        '60:8c:4a': 'Apple',
        '60:92:17': 'Apple',
        '60:a3:7d': 'Apple',
        '60:c5:47': 'Apple',
        '60:d9:c7': 'Apple',
        '60:f4:45': 'Apple',
        '60:f8:1d': 'Apple',
        '60:fa:cd': 'Apple',
        '60:fb:42': 'Apple',
        '60:fe:c5': 'Apple',
        '64:20:0c': 'Apple',
        '64:4b:f0': 'Apple',
        '64:76:ba': 'Apple',
        '64:9a:be': 'Apple',
        '64:a3:cb': 'Apple',
        '64:a5:c3': 'Apple',
        '64:b0:a6': 'Apple',
        '64:b9:e8': 'Apple',
        '64:e6:82': 'Apple',
        '68:09:27': 'Apple',
        '68:5b:35': 'Apple',
        '68:64:4b': 'Apple',
        '68:96:7b': 'Apple',
        '68:9c:70': 'Apple',
        '68:a8:6d': 'Apple',
        '68:ab:1e': 'Apple',
        '68:ae:20': 'Apple',
        '68:ce:0d': 'Apple',
        '68:d9:3c': 'Apple',
        '68:db:ca': 'Apple',
        '68:ee:96': 'Apple',
        '68:ef:43': 'Apple',
        '68:fb:7e': 'Apple',
        '6c:19:c0': 'Apple',
        '6c:3e:6d': 'Apple',
        '6c:40:08': 'Apple',
        '6c:4d:73': 'Apple',
        '6c:70:9f': 'Apple',
        '6c:72:e7': 'Apple',
        '6c:8d:c1': 'Apple',
        '6c:94:f8': 'Apple',
        '6c:96:cf': 'Apple',
        '6c:ab:31': 'Apple',
        '6c:c2:6b': 'Apple',
        '6c:e8:5c': 'Apple',
        '70:11:24': 'Apple',
        '70:14:a6': 'Apple',
        '70:3e:ac': 'Apple',
        '70:48:0f': 'Apple',
        '70:56:81': 'Apple',
        '70:73:cb': 'Apple',
        '70:81:eb': 'Apple',
        '70:a2:b3': 'Apple',
        '70:cd:60': 'Apple',
        '70:de:e2': 'Apple',
        '70:e7:2c': 'Apple',
        '70:ec:e4': 'Apple',
        '70:ef:00': 'Apple',
        '70:f0:87': 'Apple',
        '74:1b:b2': 'Apple',
        '74:81:14': 'Apple',
        '74:8d:08': 'Apple',
        '74:e1:b6': 'Apple',
        '74:e2:f5': 'Apple',
        '78:28:ca': 'Apple',
        '78:31:c1': 'Apple',
        '78:3a:84': 'Apple',
        '78:4f:43': 'Apple',
        '78:67:d7': 'Apple',
        '78:6c:1c': 'Apple',
        '78:7e:61': 'Apple',
        '78:88:6d': 'Apple',
        '78:9f:70': 'Apple',
        '78:a3:e4': 'Apple',
        '78:bf:db': 'Apple',
        '78:ca:39': 'Apple',
        '78:d7:5f': 'Apple',
        '78:fd:94': 'Apple',
        '7c:01:91': 'Apple',
        '7c:04:d0': 'Apple',
        '7c:11:be': 'Apple',
        '7c:5c:f8': 'Apple',
        '7c:6d:62': 'Apple',
        '7c:6d:f8': 'Apple',
        '7c:c3:a1': 'Apple',
        '7c:c5:37': 'Apple',
        '7c:d1:c3': 'Apple',
        '7c:f0:5f': 'Apple',
        '7c:fa:df': 'Apple',
        '80:00:6e': 'Apple',
        '80:19:34': 'Apple',
        '80:49:71': 'Apple',
        '80:6c:1b': 'Apple',
        '80:92:9f': 'Apple',
        '80:b0:3d': 'Apple',
        '80:be:05': 'Apple',
        '80:d6:05': 'Apple',
        '80:e6:50': 'Apple',
        '80:ea:96': 'Apple',
        '80:ed:2c': 'Apple',
        '84:29:99': 'Apple',
        '84:38:35': 'Apple',
        '84:78:8b': 'Apple',
        '84:85:06': 'Apple',
        '84:89:ad': 'Apple',
        '84:8e:0c': 'Apple',
        '84:a1:34': 'Apple',
        '84:b1:53': 'Apple',
        '84:fc:fe': 'Apple',
        '88:1f:a1': 'Apple',
        '88:53:95': 'Apple',
        '88:63:df': 'Apple',
        '88:69:08': 'Apple',
        '88:c6:63': 'Apple',
        '88:cb:87': 'Apple',
        '88:e8:7f': 'Apple',
        '88:e9:fe': 'Apple',
        '8c:00:6d': 'Apple',
        '8c:29:37': 'Apple',
        '8c:2d:aa': 'Apple',
        '8c:58:77': 'Apple',
        '8c:79:67': 'Apple',
        '8c:7b:9d': 'Apple',
        '8c:7c:92': 'Apple',
        '8c:85:90': 'Apple',
        '8c:8e:f2': 'Apple',
        '8c:8f:e9': 'Apple',
        '8c:fa:ba': 'Apple',
        '90:27:e4': 'Apple',
        '90:3c:92': 'Apple',
        '90:60:f1': 'Apple',
        '90:72:40': 'Apple',
        '90:84:0d': 'Apple',
        '90:8d:6c': 'Apple',
        '90:b0:ed': 'Apple',
        '90:b9:31': 'Apple',
        '90:c1:c6': 'Apple',
        '90:fd:61': 'Apple',
        '94:94:26': 'Apple',
        '94:bf:2d': 'Apple',
        '94:e9:6a': 'Apple',
        '94:f6:65': 'Apple',
        '98:01:a7': 'Apple',
        '98:03:d8': 'Apple',
        '98:10:e8': 'Apple',
        '98:46:0a': 'Apple',
        '98:5a:eb': 'Apple',
        '98:9e:63': 'Apple',
        '98:b8:e3': 'Apple',
        '98:ca:33': 'Apple',
        '98:d6:bb': 'Apple',
        '98:e0:d9': 'Apple',
        '98:f0:ab': 'Apple',
        '98:fa:e3': 'Apple',
        '98:fe:94': 'Apple',
        '9c:04:eb': 'Apple',
        '9c:20:7b': 'Apple',
        '9c:29:3f': 'Apple',
        '9c:35:eb': 'Apple',
        '9c:4f:da': 'Apple',
        '9c:84:bf': 'Apple',
        '9c:f3:87': 'Apple',
        '9c:f4:8e': 'Apple',
        '9c:fc:01': 'Apple',
        'a0:18:28': 'Apple',
        'a0:3b:e3': 'Apple',
        'a0:4e:a7': 'Apple',
        'a0:99:9b': 'Apple',
        'a0:d7:95': 'Apple',
        'a0:ed:cd': 'Apple',
        'a4:5e:60': 'Apple',
        'a4:67:06': 'Apple',
        'a4:83:e7': 'Apple',
        'a4:b1:97': 'Apple',
        'a4:b8:05': 'Apple',
        'a4:c3:61': 'Apple',
        'a4:d1:8c': 'Apple',
        'a4:d1:d2': 'Apple',
        'a4:d9:31': 'Apple',
        'a4:f1:e8': 'Apple',
        'a8:20:66': 'Apple',
        'a8:5b:78': 'Apple',
        'a8:5c:2c': 'Apple',
        'a8:66:7f': 'Apple',
        'a8:6b:ad': 'Apple',
        'a8:88:08': 'Apple',
        'a8:8e:24': 'Apple',
        'a8:96:8a': 'Apple',
        'a8:bb:cf': 'Apple',
        'a8:be:27': 'Apple',
        'a8:fa:d8': 'Apple',
        'ac:1f:74': 'Apple',
        'ac:29:3a': 'Apple',
        'ac:3c:0b': 'Apple',
        'ac:5f:3e': 'Apple',
        'ac:61:ea': 'Apple',
        'ac:7f:3e': 'Apple',
        'ac:87:a3': 'Apple',
        'ac:bc:32': 'Apple',
        'ac:cf:5c': 'Apple',
        'ac:de:48': 'Apple',
        'ac:e4:b5': 'Apple',
        'ac:fd:ec': 'Apple',
        'b0:19:c6': 'Apple',
        'b0:34:95': 'Apple',
        'b0:48:1a': 'Apple',
        'b0:65:bd': 'Apple',
        'b0:70:2d': 'Apple',
        'b0:9f:ba': 'Apple',
        'b0:ca:68': 'Apple',
        'b4:18:d1': 'Apple',
        'b4:8b:19': 'Apple',
        'b4:f0:ab': 'Apple',
        'b4:f6:1c': 'Apple',
        'b8:09:8a': 'Apple',
        'b8:17:c2': 'Apple',
        'b8:41:a4': 'Apple',
        'b8:44:d9': 'Apple',
        'b8:53:ac': 'Apple',
        'b8:5d:0a': 'Apple',
        'b8:63:4d': 'Apple',
        'b8:78:2e': 'Apple',
        'b8:8d:12': 'Apple',
        'b8:c7:5d': 'Apple',
        'b8:e8:56': 'Apple',
        'b8:f6:b1': 'Apple',
        'b8:ff:61': 'Apple',
        'bc:3b:af': 'Apple',
        'bc:4c:c4': 'Apple',
        'bc:52:b7': 'Apple',
        'bc:54:36': 'Apple',
        'bc:67:78': 'Apple',
        'bc:6c:21': 'Apple',
        'bc:92:6b': 'Apple',
        'bc:9f:ef': 'Apple',
        'bc:a9:20': 'Apple',
        'bc:fe:8c': 'Apple',
        'c0:1a:da': 'Apple',
        'c0:63:94': 'Apple',
        'c0:84:7a': 'Apple',
        'c0:9f:42': 'Apple',
        'c0:a5:3e': 'Apple',
        'c0:ce:cd': 'Apple',
        'c0:d0:12': 'Apple',
        'c0:f2:fb': 'Apple',
        'c4:2c:03': 'Apple',
        'c4:b3:01': 'Apple',
        'c8:1e:e7': 'Apple',
        'c8:2a:14': 'Apple',
        'c8:33:4b': 'Apple',
        'c8:3c:85': 'Apple',
        'c8:6f:1d': 'Apple',
        'c8:69:cd': 'Apple',
        'c8:85:50': 'Apple',
        'c8:b5:b7': 'Apple',
        'c8:bc:c8': 'Apple',
        'c8:d0:83': 'Apple',
        'c8:e0:eb': 'Apple',
        'c8:f6:50': 'Apple',
        'cc:08:8d': 'Apple',
        'cc:08:e0': 'Apple',
        'cc:20:e8': 'Apple',
        'cc:25:ef': 'Apple',
        'cc:29:f5': 'Apple',
        'cc:2d:b7': 'Apple',
        'cc:44:63': 'Apple',
        'cc:4b:73': 'Apple',
        'cc:78:5f': 'Apple',
        'cc:c7:60': 'Apple',
        'd0:03:4b': 'Apple',
        'd0:23:db': 'Apple',
        'd0:25:98': 'Apple',
        'd0:33:11': 'Apple',
        'd0:4f:7e': 'Apple',
        'd0:65:ca': 'Apple',
        'd0:a6:37': 'Apple',
        'd0:c5:f3': 'Apple',
        'd0:cd:e1': 'Apple',
        'd0:d2:b0': 'Apple',
        'd0:e1:40': 'Apple',
        'd4:61:9d': 'Apple',
        'd4:9a:20': 'Apple',
        'd4:f4:6f': 'Apple',
        'd8:00:4d': 'Apple',
        'd8:1c:79': 'Apple',
        'd8:1d:72': 'Apple',
        'd8:30:62': 'Apple',
        'd8:8f:76': 'Apple',
        'd8:96:95': 'Apple',
        'd8:9e:3f': 'Apple',
        'd8:a2:5e': 'Apple',
        'd8:bb:2c': 'Apple',
        'd8:cf:9c': 'Apple',
        'd8:d1:cb': 'Apple',
        'dc:0c:5c': 'Apple',
        'dc:2b:2a': 'Apple',
        'dc:2b:61': 'Apple',
        'dc:37:14': 'Apple',
        'dc:3e:f8': 'Apple',
        'dc:41:5f': 'Apple',
        'dc:56:e7': 'Apple',
        'dc:86:d8': 'Apple',
        'dc:9b:9c': 'Apple',
        'dc:a4:ca': 'Apple',
        'dc:a9:04': 'Apple',
        'e0:5f:45': 'Apple',
        'e0:66:78': 'Apple',
        'e0:ac:cb': 'Apple',
        'e0:b5:2d': 'Apple',
        'e0:b9:ba': 'Apple',
        'e0:c7:67': 'Apple',
        'e0:c9:7a': 'Apple',
        'e0:f5:c6': 'Apple',
        'e0:f8:47': 'Apple',
        'e4:25:e7': 'Apple',
        'e4:8b:7f': 'Apple',
        'e4:98:bb': 'Apple',
        'e4:9a:dc': 'Apple',
        'e4:c6:3d': 'Apple',
        'e4:ce:8f': 'Apple',
        'e4:e4:ab': 'Apple',
        'e8:04:0b': 'Apple',
        'e8:06:88': 'Apple',
        'e8:80:2e': 'Apple',
        'e8:8d:28': 'Apple',
        'ec:35:86': 'Apple',
        'ec:85:2f': 'Apple',
        'ec:a8:6b': 'Apple',
        'f0:18:98': 'Apple',
        'f0:24:75': 'Apple',
        'f0:5c:d5': 'Apple',
        'f0:72:8c': 'Apple',
        'f0:79:60': 'Apple',
        'f0:99:bf': 'Apple',
        'f0:b4:79': 'Apple',
        'f0:b5:d1': 'Apple',
        'f0:c1:f1': 'Apple',
        'f0:cb:a1': 'Apple',
        'f0:d1:a9': 'Apple',
        'f0:db:e2': 'Apple',
        'f0:db:f8': 'Apple',
        'f0:dc:e2': 'Apple',
        'f0:f6:1c': 'Apple',
        'f4:0f:24': 'Apple',
        'f4:1b:a1': 'Apple',
        'f4:37:b7': 'Apple',
        'f4:f1:5a': 'Apple',
        'f4:f9:51': 'Apple',
        'f8:03:77': 'Apple',
        'f8:1e:df': 'Apple',
        'f8:27:93': 'Apple',
        'f8:2d:7c': 'Apple',
        'f8:38:80': 'Apple',
        'f8:62:14': 'Apple',
        'f8:95:ea': 'Apple',
        'f8:a9:d0': 'Apple',
        'f8:e9:4e': 'Apple',
        'f8:ff:0b': 'Apple',
        'fc:25:3f': 'Apple',
        'fc:e9:98': 'Apple',
        'fc:fc:48': 'Apple'
    }
    
    if mac:
        mac_lower = mac.lower()
        prefix = mac_lower[:8]
        if prefix in mac_prefixes:
            return mac_prefixes[prefix]
    return 'Unknown'

def get_meraki_organization_id():
    """Get organization ID by name"""
    url = f'{MERAKI_BASE_URL}/organizations'
    response = make_api_request(url, meraki_headers, "Get organizations")
    
    if response:
        for org in response.json():
            if org['name'] == MERAKI_ORG_NAME:
                debug_log(f"Found organization {MERAKI_ORG_NAME} with ID {org['id']}")
                return org['id']
    debug_log(f"Organization {MERAKI_ORG_NAME} not found", "ERROR")
    return None

def refresh_switch_data(serial):
    """Refresh data for a single switch"""
    debug_log(f"Starting refresh for switch {serial}")
    
    try:
        # Get device details
        url = f'{MERAKI_BASE_URL}/devices/{serial}'
        device_response = make_api_request(url, meraki_headers, f"Get device details for {serial}")
        
        if not device_response:
            error_msg = f'Failed to get device details for {serial}'
            debug_log(error_msg, "ERROR")
            return {'error': error_msg}, 400
        
        device = device_response.json()
        debug_log(f"Device {serial} details retrieved: {device.get('name', 'Unknown')}")
        
        # Get clients connected to this switch
        url = f'{MERAKI_BASE_URL}/devices/{serial}/clients'
        clients_response = make_api_request(url, meraki_headers, f"Get clients for switch {serial}")
        
        if not clients_response:
            error_msg = f'Failed to get clients for switch {serial}'
            debug_log(error_msg, "ERROR")
            return {'error': error_msg}, 400
        
        clients = clients_response.json()
        debug_log(f"Retrieved {len(clients)} clients for switch {serial}")
        
        # Get network details
        url = f'{MERAKI_BASE_URL}/networks/{device["networkId"]}'
        network_response = make_api_request(url, meraki_headers, f"Get network details for {serial}")
        
        if network_response:
            network = network_response.json()
            store_name = network['name']
            debug_log(f"Switch {serial} belongs to store: {store_name}")
        else:
            store_name = 'Unknown'
            debug_log(f"Could not determine store name for switch {serial}", "WARN")
        
        # Update database
        updated_count = 0
        for client in clients:
            # Skip if no switchport info (not a wired client)
            if 'switchport' not in client:
                continue
            
            port_id = client.get('switchport', 'Unknown')
            hostname = client.get('description', client.get('dhcpHostname', ''))
            ip_address = client.get('ip', '')
            mac_address = client.get('mac', '')
            vlan = client.get('vlan', None)
            manufacturer = get_mac_manufacturer(mac_address)
            description = client.get('notes', '')
            
            # Check if record exists
            existing = SwitchPortClient.query.filter_by(
                switch_serial=serial,
                port_id=port_id,
                mac_address=mac_address
            ).first()
            
            if existing:
                # Update existing record
                existing.hostname = hostname
                existing.ip_address = ip_address
                existing.vlan = vlan
                existing.manufacturer = manufacturer
                existing.description = description
                existing.last_seen = datetime.utcnow()
                existing.updated_at = datetime.utcnow()
                updated_count += 1
            else:
                # Create new record
                new_client = SwitchPortClient(
                    store_name=store_name,
                    switch_name=device.get('name', ''),
                    switch_serial=serial,
                    port_id=port_id,
                    hostname=hostname,
                    ip_address=ip_address,
                    mac_address=mac_address,
                    vlan=vlan,
                    manufacturer=manufacturer,
                    description=description,
                    last_seen=datetime.utcnow()
                )
                db.session.add(new_client)
                updated_count += 1
        
        db.session.commit()
        debug_log(f"Database updated for switch {serial}: {updated_count} clients")
        
        # Clear cache for this switch
        redis_conn = get_redis_connection()
        if redis_conn:
            pattern = f"switch_visibility:*{serial}*"
            cache_keys = list(redis_conn.scan_iter(match=pattern))
            for key in cache_keys:
                redis_conn.delete(key)
            debug_log(f"Cleared {len(cache_keys)} cache keys for switch {serial}")
        
        success_msg = f'Successfully refreshed {updated_count} clients for switch {device.get("name", serial)}'
        debug_log(success_msg)
        return {
            'success': True,
            'message': success_msg,
            'clients_updated': updated_count
        }, 200
        
    except Exception as e:
        error_msg = f"Error refreshing switch {serial}: {str(e)}"
        debug_log(error_msg, "ERROR")
        db.session.rollback()
        return {'error': f'Failed to refresh switch data: {str(e)}'}, 500

def refresh_store_data(store_name):
    """Refresh data for all switches in a store using database switch information"""
    debug_log(f"Starting store refresh for {store_name}")
    start_time = time.time()
    
    try:
        # Get switches for this store from our database
        debug_log(f"Getting switches for {store_name} from database")
        switches_query = db.session.query(SwitchPortClient.switch_serial, SwitchPortClient.switch_name).filter(
            SwitchPortClient.store_name == store_name
        ).distinct().all()
        
        if not switches_query:
            error_msg = f'No switches found in database for store {store_name}'
            debug_log(error_msg, "ERROR")
            return {'error': error_msg}, 404
        
        # Convert to list of switch serials
        switches = [{'serial': row.switch_serial, 'name': row.switch_name} for row in switches_query]
        debug_log(f"Found {len(switches)} switches in database for {store_name}: {[s['serial'] for s in switches]}")
        
        if not switches:
            warning_msg = f'No switches found in store {store_name}'
            debug_log(warning_msg, "WARN")
            return {'success': True, 'message': warning_msg, 'switches_updated': 0, 'clients_updated': 0}, 200
        
        # Process switches sequentially to avoid Flask context issues
        debug_log(f"Processing {len(switches)} switches sequentially")
        total_switches = 0
        total_clients = 0
        failed_switches = []
        
        for switch in switches:
            serial = switch['serial']
            try:
                debug_log(f"Processing switch {serial} ({switch['name']})")
                result, status_code = refresh_switch_data(serial)
                total_switches += 1
                
                if status_code == 200:
                    total_clients += result.get('clients_updated', 0)
                    debug_log(f"Switch {serial} completed successfully: {result.get('clients_updated', 0)} clients")
                else:
                    failed_switches.append(serial)
                    debug_log(f"Switch {serial} failed: {result.get('error', 'Unknown error')}", "ERROR")
                    
            except Exception as e:
                failed_switches.append(serial)
                debug_log(f"Switch {serial} processing failed: {str(e)}", "ERROR")
        
        # Clear cache for this store
        redis_conn = get_redis_connection()
        if redis_conn:
            pattern = f"switch_visibility:*{store_name}*"
            cache_keys = list(redis_conn.scan_iter(match=pattern))
            for key in cache_keys:
                redis_conn.delete(key)
            debug_log(f"Cleared {len(cache_keys)} cache keys for store {store_name}")
        
        total_duration = time.time() - start_time
        success_msg = f'Successfully refreshed {total_switches} switches with {total_clients} clients in {store_name} (took {total_duration:.2f}s)'
        
        if failed_switches:
            success_msg += f'. Failed switches: {failed_switches}'
            debug_log(f"Store refresh completed with {len(failed_switches)} failures: {failed_switches}", "WARN")
        
        debug_log(success_msg)
        return {
            'success': True,
            'message': success_msg,
            'switches_updated': total_switches,
            'clients_updated': total_clients,
            'failed_switches': failed_switches
        }, 200
        
    except Exception as e:
        total_duration = time.time() - start_time
        error_msg = f"Error refreshing store {store_name} after {total_duration:.2f}s: {str(e)}"
        debug_log(error_msg, "ERROR")
        return {'error': f'Failed to refresh store data: {str(e)}'}, 500

@switch_visibility_bp.route('/switch-visibility')
def switch_visibility():
    """Main switch visibility page"""
    return render_template('switch_visibility.html')

@switch_visibility_bp.route('/api/switch-port-clients')
def get_switch_port_clients():
    """Get switch port client data with filtering"""
    try:
        # Get filter parameters
        store_filter = request.args.get('store')
        switch_filter = request.args.get('switch')
        search_filter = request.args.get('search')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 100)), 500000)  # Cap at 500K for safety
        
        # Try Redis cache first
        redis_conn = get_redis_connection()
        cache_key = f"switch_visibility:{store_filter or 'all'}:{switch_filter or 'all'}:{search_filter or 'none'}:{page}:{per_page}"
        
        if redis_conn:
            cached_data = redis_conn.get(cache_key)
            if cached_data:
                return jsonify(json.loads(cached_data))
        
        # Build query
        query = SwitchPortClient.query
        
        if store_filter:
            # Check if multiple stores are provided (comma-separated)
            if ',' in store_filter:
                stores = store_filter.split(',')
                query = query.filter(SwitchPortClient.store_name.in_(stores))
            else:
                query = query.filter(SwitchPortClient.store_name == store_filter)
        
        if switch_filter:
            query = query.filter(SwitchPortClient.switch_serial == switch_filter)
        
        if search_filter:
            search_pattern = f'%{search_filter}%'
            query = query.filter(
                db.or_(
                    SwitchPortClient.hostname.ilike(search_pattern),
                    SwitchPortClient.ip_address.ilike(search_pattern),
                    SwitchPortClient.mac_address.ilike(search_pattern),
                    SwitchPortClient.switch_name.ilike(search_pattern),
                    SwitchPortClient.manufacturer.ilike(search_pattern)
                )
            )
        
        # Order by store, switch, port
        query = query.order_by(
            SwitchPortClient.store_name,
            SwitchPortClient.switch_name,
            SwitchPortClient.port_id
        )
        
        # Paginate
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Get unique stores and switches for filters
        stores = db.session.query(SwitchPortClient.store_name).distinct().order_by(SwitchPortClient.store_name).all()
        switches = db.session.query(
            SwitchPortClient.switch_serial,
            SwitchPortClient.switch_name
        ).distinct().order_by(SwitchPortClient.switch_name).all()
        
        result = {
            'data': [client.to_dict() for client in paginated.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginated.total,
                'pages': paginated.pages,
                'has_prev': paginated.has_prev,
                'has_next': paginated.has_next
            },
            'filters': {
                'stores': [s[0] for s in stores],
                'switches': [{'serial': s[0], 'name': s[1]} for s in switches]
            }
        }
        
        # Cache for 5 minutes
        if redis_conn:
            redis_conn.setex(cache_key, 300, json.dumps(result))
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting switch port clients: {str(e)}")
        return jsonify({'error': str(e)}), 500

@switch_visibility_bp.route('/api/switch-port-clients/refresh-switch/<serial>', methods=['POST'])
def refresh_switch(serial):
    """Refresh data for a single switch"""
    return refresh_switch_data(serial)

@switch_visibility_bp.route('/api/switch-port-clients/refresh-store/<store_name>', methods=['POST'])
def refresh_store(store_name):
    """Refresh data for all switches in a store"""
    return refresh_store_data(store_name)

@switch_visibility_bp.route('/api/switch-port-clients/export')
def export_switch_port_clients():
    """Export switch port client data to Excel"""
    try:
        # Check if we want all data or filtered
        export_all = request.args.get('all', 'false').lower() == 'true'
        
        # Build query
        query = SwitchPortClient.query
        
        # Apply filters unless exporting all
        if not export_all:
            store_filter = request.args.get('store')
            switch_filter = request.args.get('switch')
            search_filter = request.args.get('search')
            
            if store_filter:
                query = query.filter(SwitchPortClient.store_name == store_filter)
            if switch_filter:
                query = query.filter(SwitchPortClient.switch_serial == switch_filter)
            if search_filter:
                search_pattern = f'%{search_filter}%'
                query = query.filter(
                    db.or_(
                        SwitchPortClient.hostname.ilike(search_pattern),
                        SwitchPortClient.ip_address.ilike(search_pattern),
                        SwitchPortClient.mac_address.ilike(search_pattern)
                    )
                )
        
        # Order results
        query = query.order_by(
            SwitchPortClient.store_name,
            SwitchPortClient.switch_name,
            SwitchPortClient.port_id
        )
        
        clients = query.all()
        
        # Create DataFrame
        data = []
        for client in clients:
            data.append({
                'Store': client.store_name,
                'Switch Name': client.switch_name,
                'Switch Serial': client.switch_serial,
                'Port ID': client.port_id,
                'Hostname': client.hostname,
                'IP Address': client.ip_address,
                'MAC Address': client.mac_address,
                'VLAN': client.vlan,
                'Manufacturer': client.manufacturer,
                'Description': client.description,
                'Last Seen': client.last_seen.strftime('%Y-%m-%d %H:%M:%S') if client.last_seen else ''
            })
        
        df = pd.DataFrame(data)
        
        # Create Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Switch Port Clients', index=False)
            
            # Auto-adjust columns width
            worksheet = writer.sheets['Switch Port Clients']
            for i, col in enumerate(df.columns):
                column_width = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, column_width)
        
        output.seek(0)
        
        # Generate filename
        filename_prefix = 'switch_port_clients_all' if export_all else 'switch_port_clients'
        filename = f'{filename_prefix}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting switch port clients: {str(e)}")
        return jsonify({'error': str(e)}), 500