#!/usr/bin/env python3
"""
VLAN Migration Connectivity Monitor
===================================

This script monitors device connectivity before, during, and after VLAN migration
to ensure no devices are lost during the process.

Usage:
    # Before migration - capture baseline
    python3 vlan_migration_connectivity_monitor.py --network-id <network_id> --action baseline
    
    # After migration - verify connectivity
    python3 vlan_migration_connectivity_monitor.py --network-id <network_id> --action verify
    
    # Continuous monitoring during migration
    python3 vlan_migration_connectivity_monitor.py --network-id <network_id> --action monitor

Author: Claude
Date: July 2025
"""

import os
import sys
import json
import requests
import subprocess
import argparse
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"
HEADERS = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json'
}

class ConnectivityMonitor:
    def __init__(self, network_id):
        """Initialize connectivity monitor"""
        self.network_id = network_id
        self.baseline_file = f"connectivity_baseline_{network_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.log_entries = []
        
        # Get network info
        self.network_info = self.get_network_info()
        self.log(f"Monitoring network: {self.network_info['name']}")
    
    def log(self, message, level="INFO"):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.log_entries.append(log_entry)
        print(log_entry)
    
    def get_network_info(self):
        """Get network information"""
        url = f"{BASE_URL}/networks/{self.network_id}"
        response = requests.get(url, headers=HEADERS)
        return response.json()
    
    def get_online_clients(self):
        """Get all currently online clients"""
        self.log("Getting online clients...")
        
        url = f"{BASE_URL}/networks/{self.network_id}/clients"
        params = {
            'timespan': 300,  # Last 5 minutes
            'perPage': 1000,
            'statuses': ['Online']
        }
        
        all_clients = []
        
        # Handle pagination
        while url:
            response = requests.get(url, headers=HEADERS, params=params)
            
            if response.status_code != 200:
                self.log(f"Failed to get clients: {response.status_code}", "ERROR")
                break
            
            clients = response.json()
            all_clients.extend(clients)
            
            # Check for next page
            link_header = response.headers.get('Link', '')
            url = None
            if 'rel="next"' in link_header:
                # Extract next URL from Link header
                parts = link_header.split(',')
                for part in parts:
                    if 'rel="next"' in part:
                        url = part.split(';')[0].strip('<>')
                        params = {}  # URL already has params
        
        # Filter for clients with IP addresses
        clients_with_ip = [c for c in all_clients if c.get('ip')]
        
        self.log(f"Found {len(clients_with_ip)} online clients with IP addresses")
        return clients_with_ip
    
    def get_network_devices(self):
        """Get network devices (switches, APs, etc.)"""
        self.log("Getting network devices...")
        
        url = f"{BASE_URL}/networks/{self.network_id}/devices"
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code != 200:
            self.log(f"Failed to get devices: {response.status_code}", "ERROR")
            return []
        
        devices = response.json()
        
        # Filter for devices with LAN IP
        devices_with_ip = []
        for device in devices:
            if device.get('lanIp'):
                devices_with_ip.append({
                    'name': device['name'],
                    'model': device['model'],
                    'serial': device['serial'],
                    'ip': device['lanIp'],
                    'type': 'network_device'
                })
        
        self.log(f"Found {len(devices_with_ip)} network devices with IP addresses")
        return devices_with_ip
    
    def get_static_ip_assignments(self):
        """Get static IP assignments from DHCP reservations"""
        self.log("Getting DHCP reservations...")
        
        static_ips = []
        
        # Get VLANs
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans"
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code == 200:
            vlans = response.json()
            
            for vlan in vlans:
                if vlan.get('fixedIpAssignments'):
                    vlan_id = vlan['id']
                    for mac, assignment in vlan['fixedIpAssignments'].items():
                        static_ips.append({
                            'mac': mac,
                            'ip': assignment['ip'],
                            'name': assignment.get('name', 'Unknown'),
                            'vlan': vlan_id,
                            'type': 'dhcp_reservation'
                        })
        
        self.log(f"Found {len(static_ips)} DHCP reservations")
        return static_ips
    
    def ping_host(self, ip_address, count=3, timeout=2):
        """Ping a host and return result"""
        try:
            # Use system ping command
            if sys.platform.startswith('win'):
                cmd = ['ping', '-n', str(count), '-w', str(timeout * 1000), ip_address]
            else:
                cmd = ['ping', '-c', str(count), '-W', str(timeout), ip_address]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout * count + 2)
            
            # Parse result
            if result.returncode == 0:
                # Extract average RTT
                output = result.stdout
                if 'avg' in output or 'Average' in output:
                    # Try to extract RTT
                    if sys.platform.startswith('win'):
                        # Windows: "Average = XXms"
                        if 'Average = ' in output:
                            rtt = output.split('Average = ')[1].split('ms')[0]
                            return {'reachable': True, 'rtt': float(rtt)}
                    else:
                        # Linux/Mac: "rtt min/avg/max/mdev = X.X/X.X/X.X/X.X ms"
                        if '/avg/' in output:
                            rtt_line = [l for l in output.split('\n') if '/avg/' in l][0]
                            avg_rtt = rtt_line.split('/')[4]
                            return {'reachable': True, 'rtt': float(avg_rtt)}
                
                return {'reachable': True, 'rtt': None}
            else:
                return {'reachable': False, 'rtt': None}
                
        except Exception as e:
            return {'reachable': False, 'error': str(e)}
    
    def capture_baseline(self):
        """Capture baseline connectivity state"""
        self.log("\n" + "="*60)
        self.log("CAPTURING CONNECTIVITY BASELINE")
        self.log("="*60)
        
        baseline = {
            'network_id': self.network_id,
            'network_name': self.network_info['name'],
            'capture_time': datetime.now().isoformat(),
            'clients': [],
            'devices': [],
            'reservations': []
        }
        
        # Get online clients
        clients = self.get_online_clients()
        for client in clients:
            baseline['clients'].append({
                'mac': client.get('mac'),
                'ip': client['ip'],
                'description': client.get('description', ''),
                'vlan': client.get('vlan'),
                'switchport': client.get('switchport'),
                'manufacturer': client.get('manufacturer', 'Unknown')
            })
        
        # Get network devices
        devices = self.get_network_devices()
        baseline['devices'] = devices
        
        # Get DHCP reservations
        reservations = self.get_static_ip_assignments()
        baseline['reservations'] = reservations
        
        # Test connectivity to all IPs
        self.log("\nTesting connectivity to all devices...")
        all_ips = []
        
        # Collect all IPs
        for client in baseline['clients']:
            all_ips.append((client['ip'], 'client', client.get('description', '')))
        
        for device in baseline['devices']:
            all_ips.append((device['ip'], 'device', device['name']))
        
        for reservation in baseline['reservations']:
            all_ips.append((reservation['ip'], 'reservation', reservation['name']))
        
        # Remove duplicates
        unique_ips = {}
        for ip, typ, name in all_ips:
            if ip not in unique_ips:
                unique_ips[ip] = {'type': typ, 'name': name}
        
        # Ping all IPs in parallel
        self.log(f"Pinging {len(unique_ips)} unique IP addresses...")
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            future_to_ip = {
                executor.submit(self.ping_host, ip): ip 
                for ip in unique_ips.keys()
            }
            
            reachable_count = 0
            unreachable_count = 0
            
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    result = future.result()
                    unique_ips[ip]['ping_result'] = result
                    
                    if result['reachable']:
                        reachable_count += 1
                    else:
                        unreachable_count += 1
                        
                except Exception as e:
                    self.log(f"Error pinging {ip}: {e}", "ERROR")
                    unique_ips[ip]['ping_result'] = {'reachable': False, 'error': str(e)}
                    unreachable_count += 1
        
        baseline['connectivity'] = unique_ips
        
        # Save baseline
        with open(self.baseline_file, 'w') as f:
            json.dump(baseline, f, indent=2)
        
        self.log(f"\n✅ Baseline captured:")
        self.log(f"   - Total unique IPs: {len(unique_ips)}")
        self.log(f"   - Reachable: {reachable_count}")
        self.log(f"   - Unreachable: {unreachable_count}")
        self.log(f"   - Baseline saved to: {self.baseline_file}")
        
        # Show summary by type
        self.log("\nSummary by device type:")
        type_summary = {}
        for ip, data in unique_ips.items():
            typ = data['type']
            if typ not in type_summary:
                type_summary[typ] = {'total': 0, 'reachable': 0}
            type_summary[typ]['total'] += 1
            if data['ping_result']['reachable']:
                type_summary[typ]['reachable'] += 1
        
        for typ, counts in type_summary.items():
            self.log(f"   {typ}: {counts['reachable']}/{counts['total']} reachable")
        
        return baseline
    
    def verify_connectivity(self, baseline_file=None):
        """Verify connectivity against baseline"""
        self.log("\n" + "="*60)
        self.log("VERIFYING CONNECTIVITY POST-MIGRATION")
        self.log("="*60)
        
        # Load baseline
        if not baseline_file:
            # Find most recent baseline
            import glob
            baselines = glob.glob(f"connectivity_baseline_{self.network_id}_*.json")
            if not baselines:
                self.log("No baseline file found!", "ERROR")
                return False
            baseline_file = sorted(baselines)[-1]
        
        self.log(f"Loading baseline from: {baseline_file}")
        
        with open(baseline_file, 'r') as f:
            baseline = json.load(f)
        
        baseline_ips = baseline['connectivity']
        
        # Test connectivity to all baseline IPs
        self.log(f"\nTesting connectivity to {len(baseline_ips)} baseline IPs...")
        
        results = {
            'still_reachable': 0,
            'became_reachable': 0,
            'became_unreachable': 0,
            'still_unreachable': 0,
            'details': []
        }
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            future_to_ip = {
                executor.submit(self.ping_host, ip): ip 
                for ip in baseline_ips.keys()
            }
            
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                baseline_data = baseline_ips[ip]
                
                try:
                    current_result = future.result()
                    baseline_result = baseline_data['ping_result']
                    
                    # Compare results
                    was_reachable = baseline_result['reachable']
                    is_reachable = current_result['reachable']
                    
                    if was_reachable and is_reachable:
                        results['still_reachable'] += 1
                    elif not was_reachable and is_reachable:
                        results['became_reachable'] += 1
                        results['details'].append({
                            'ip': ip,
                            'name': baseline_data['name'],
                            'type': baseline_data['type'],
                            'change': 'became_reachable'
                        })
                    elif was_reachable and not is_reachable:
                        results['became_unreachable'] += 1
                        results['details'].append({
                            'ip': ip,
                            'name': baseline_data['name'],
                            'type': baseline_data['type'],
                            'change': 'lost_connectivity'
                        })
                    else:
                        results['still_unreachable'] += 1
                        
                except Exception as e:
                    self.log(f"Error testing {ip}: {e}", "ERROR")
                    if baseline_data['ping_result']['reachable']:
                        results['became_unreachable'] += 1
                        results['details'].append({
                            'ip': ip,
                            'name': baseline_data['name'],
                            'type': baseline_data['type'],
                            'change': 'error',
                            'error': str(e)
                        })
        
        # Generate report
        self.log("\n" + "="*60)
        self.log("CONNECTIVITY VERIFICATION RESULTS")
        self.log("="*60)
        
        self.log(f"\nSummary:")
        self.log(f"  Still reachable: {results['still_reachable']}")
        self.log(f"  Became reachable: {results['became_reachable']}")
        self.log(f"  Lost connectivity: {results['became_unreachable']} ⚠️")
        self.log(f"  Still unreachable: {results['still_unreachable']}")
        
        if results['became_unreachable'] > 0:
            self.log("\n❌ DEVICES THAT LOST CONNECTIVITY:")
            for detail in results['details']:
                if detail['change'] == 'lost_connectivity':
                    self.log(f"  - {detail['ip']} ({detail['name']}) - {detail['type']}")
        
        if results['became_reachable'] > 0:
            self.log("\n✅ DEVICES THAT BECAME REACHABLE:")
            for detail in results['details']:
                if detail['change'] == 'became_reachable':
                    self.log(f"  - {detail['ip']} ({detail['name']}) - {detail['type']}")
        
        # Save verification report
        report_file = f"connectivity_verification_{self.network_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'baseline_file': baseline_file,
                'verification_time': datetime.now().isoformat(),
                'results': results,
                'log': self.log_entries
            }, f, indent=2)
        
        self.log(f"\nReport saved to: {report_file}")
        
        # Return success if no devices lost connectivity
        return results['became_unreachable'] == 0
    
    def continuous_monitor(self, interval=30, duration=1800):
        """Continuously monitor connectivity during migration"""
        self.log("\n" + "="*60)
        self.log("CONTINUOUS CONNECTIVITY MONITORING")
        self.log("="*60)
        self.log(f"Monitoring every {interval} seconds for {duration} seconds")
        
        # Load baseline
        import glob
        baselines = glob.glob(f"connectivity_baseline_{self.network_id}_*.json")
        if not baselines:
            self.log("No baseline found! Run with --action baseline first", "ERROR")
            return
        
        baseline_file = sorted(baselines)[-1]
        with open(baseline_file, 'r') as f:
            baseline = json.load(f)
        
        baseline_ips = list(baseline['connectivity'].keys())
        self.log(f"Monitoring {len(baseline_ips)} IP addresses")
        
        start_time = time.time()
        check_count = 0
        
        while time.time() - start_time < duration:
            check_count += 1
            self.log(f"\n[Check #{check_count}] {datetime.now().strftime('%H:%M:%S')}")
            
            # Quick ping check (1 packet, 1 second timeout)
            unreachable = []
            
            with ThreadPoolExecutor(max_workers=100) as executor:
                future_to_ip = {
                    executor.submit(self.ping_host, ip, count=1, timeout=1): ip 
                    for ip in baseline_ips
                }
                
                for future in as_completed(future_to_ip):
                    ip = future_to_ip[future]
                    try:
                        result = future.result()
                        if not result['reachable']:
                            unreachable.append(ip)
                    except:
                        unreachable.append(ip)
            
            if unreachable:
                self.log(f"  ⚠️  {len(unreachable)} devices unreachable:")
                for ip in unreachable[:5]:  # Show first 5
                    name = baseline['connectivity'][ip]['name']
                    self.log(f"     - {ip} ({name})")
                if len(unreachable) > 5:
                    self.log(f"     ... and {len(unreachable)-5} more")
            else:
                self.log(f"  ✅ All {len(baseline_ips)} devices reachable")
            
            # Wait for next check
            time.sleep(interval)
        
        self.log("\nMonitoring complete!")

def main():
    parser = argparse.ArgumentParser(description='VLAN Migration Connectivity Monitor')
    parser.add_argument('--network-id', required=True, help='Network ID to monitor')
    parser.add_argument('--action', required=True, 
                       choices=['baseline', 'verify', 'monitor'],
                       help='Action to perform')
    parser.add_argument('--baseline-file', help='Specific baseline file to use for verification')
    parser.add_argument('--interval', type=int, default=30, 
                       help='Monitoring interval in seconds (default: 30)')
    parser.add_argument('--duration', type=int, default=1800,
                       help='Monitoring duration in seconds (default: 1800/30min)')
    
    args = parser.parse_args()
    
    monitor = ConnectivityMonitor(args.network_id)
    
    if args.action == 'baseline':
        monitor.capture_baseline()
    elif args.action == 'verify':
        success = monitor.verify_connectivity(args.baseline_file)
        sys.exit(0 if success else 1)
    elif args.action == 'monitor':
        monitor.continuous_monitor(args.interval, args.duration)

if __name__ == "__main__":
    main()