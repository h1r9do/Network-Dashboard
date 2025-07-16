#!/usr/bin/env python3
"""Test ARIN lookup performance and optimization opportunities"""

import time
import sys
import json
import concurrent.futures
import threading
from datetime import datetime
sys.path.insert(0, '/usr/local/bin/Main')
from nightly_meraki_db import get_provider_for_ip, parse_arin_response, fetch_json
import psycopg2
from psycopg2.extras import execute_values
from config import Config
import re

# Thread-safe cache
cache_lock = threading.Lock()
thread_safe_cache = {}

def get_db_connection():
    """Get database connection using config"""
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
    if not match:
        raise ValueError("Invalid database URI")
    
    user, password, host, port, database = match.groups()
    
    return psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password
    )

def test_sequential_lookups(ips):
    """Test sequential ARIN lookups"""
    print("\n=== Testing Sequential Lookups ===")
    start_time = time.time()
    results = {}
    cache = {}
    missing_set = set()
    
    for i, ip in enumerate(ips):
        print(f"  Looking up {i+1}/{len(ips)}: {ip}...", end='', flush=True)
        ip_start = time.time()
        provider = get_provider_for_ip(ip, cache, missing_set)
        ip_time = time.time() - ip_start
        results[ip] = provider
        print(f" {provider} ({ip_time:.2f}s)")
    
    total_time = time.time() - start_time
    return results, total_time

def thread_safe_get_provider(ip):
    """Thread-safe provider lookup"""
    # Check cache first
    with cache_lock:
        if ip in thread_safe_cache:
            return thread_safe_cache[ip]
    
    # Do the lookup
    missing_set = set()
    local_cache = {}
    provider = get_provider_for_ip(ip, local_cache, missing_set)
    
    # Update shared cache
    with cache_lock:
        thread_safe_cache[ip] = provider
    
    return provider

def test_parallel_lookups(ips, max_workers=10):
    """Test parallel ARIN lookups"""
    print(f"\n=== Testing Parallel Lookups (max_workers={max_workers}) ===")
    start_time = time.time()
    results = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all lookups
        future_to_ip = {executor.submit(thread_safe_get_provider, ip): ip for ip in ips}
        
        # Collect results as they complete
        for i, future in enumerate(concurrent.futures.as_completed(future_to_ip)):
            ip = future_to_ip[future]
            try:
                provider = future.result()
                results[ip] = provider
                print(f"  Completed {i+1}/{len(ips)}: {ip} → {provider}")
            except Exception as e:
                print(f"  Error for {ip}: {e}")
                results[ip] = "Error"
    
    total_time = time.time() - start_time
    return results, total_time

def test_batch_database_updates(devices):
    """Test batch database updates vs individual updates"""
    print("\n=== Testing Database Update Performance ===")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Test 1: Individual updates
    print("Testing individual updates...")
    start_time = time.time()
    
    for device in devices[:10]:  # Test with first 10
        cursor.execute("""
            UPDATE meraki_inventory 
            SET wan1_arin_provider = %s, last_updated = %s
            WHERE device_serial = %s
        """, (device['provider'], datetime.now(), device['serial']))
    
    conn.commit()
    individual_time = time.time() - start_time
    print(f"  Individual updates (10 devices): {individual_time:.2f}s")
    
    # Test 2: Batch update
    print("Testing batch update...")
    start_time = time.time()
    
    # Prepare data for batch update
    update_data = [(device['provider'], datetime.now(), device['serial']) for device in devices[10:20]]
    
    # Use execute_values for batch update
    execute_values(cursor, """
        UPDATE meraki_inventory AS m
        SET wan1_arin_provider = data.provider,
            last_updated = data.updated
        FROM (VALUES %s) AS data(provider, updated, serial)
        WHERE m.device_serial = data.serial
    """, update_data)
    
    conn.commit()
    batch_time = time.time() - start_time
    print(f"  Batch update (10 devices): {batch_time:.2f}s")
    print(f"  Speed improvement: {individual_time/batch_time:.1f}x faster")
    
    cursor.close()
    conn.close()

def main():
    print("ARIN Lookup Performance Testing")
    print("=" * 60)
    
    # Get some test IPs from the database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get IPs that need ARIN lookups
    cursor.execute("""
        SELECT DISTINCT wan1_ip 
        FROM meraki_inventory 
        WHERE wan1_ip IS NOT NULL 
        AND wan1_ip != ''
        AND wan1_arin_provider = 'Unknown'
        AND wan1_ip NOT LIKE '192.168%'
        AND wan1_ip NOT LIKE '10.%'
        AND wan1_ip NOT LIKE '172.%'
        LIMIT 20
    """)
    
    test_ips = [row[0] for row in cursor.fetchall()]
    
    if not test_ips:
        print("No IPs found that need ARIN lookups. Getting any public IPs...")
        cursor.execute("""
            SELECT DISTINCT wan1_ip 
            FROM meraki_inventory 
            WHERE wan1_ip IS NOT NULL 
            AND wan1_ip != ''
            AND wan1_ip NOT LIKE '192.168%'
            AND wan1_ip NOT LIKE '10.%'
            AND wan1_ip NOT LIKE '172.%'
            LIMIT 20
        """)
        test_ips = [row[0] for row in cursor.fetchall()]
    
    print(f"Found {len(test_ips)} test IPs")
    
    if test_ips:
        # Test sequential lookups
        seq_results, seq_time = test_sequential_lookups(test_ips[:5])
        print(f"\nSequential time for 5 IPs: {seq_time:.2f}s ({seq_time/5:.2f}s per IP)")
        
        # Test parallel lookups with different worker counts
        for workers in [5, 10, 20]:
            par_results, par_time = test_parallel_lookups(test_ips, max_workers=workers)
            print(f"\nParallel time for {len(test_ips)} IPs with {workers} workers: {par_time:.2f}s")
            print(f"  Average: {par_time/len(test_ips):.2f}s per IP")
            print(f"  Speed improvement: {(seq_time/5*len(test_ips))/par_time:.1f}x faster than sequential")
    
    # Test database update performance
    print("\n" + "=" * 60)
    test_devices = [
        {'serial': f'TEST-{i}', 'provider': f'Provider-{i}'} 
        for i in range(20)
    ]
    test_batch_database_updates(test_devices)
    
    # Estimate time savings
    print("\n" + "=" * 60)
    print("OPTIMIZATION OPPORTUNITIES:")
    print("=" * 60)
    
    # Get total device count
    cursor.execute("SELECT COUNT(*) FROM meraki_inventory WHERE device_model LIKE 'MX%'")
    total_devices = cursor.fetchone()[0]
    
    print(f"\nTotal MX devices: {total_devices}")
    print(f"Estimated current time (sequential): {total_devices * 0.5:.0f} seconds ({total_devices * 0.5 / 60:.1f} minutes)")
    print(f"Estimated optimized time (parallel, 20 workers): {total_devices * 0.05:.0f} seconds ({total_devices * 0.05 / 60:.1f} minutes)")
    print(f"Potential time savings: {((total_devices * 0.5) - (total_devices * 0.05)) / 60:.1f} minutes")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()