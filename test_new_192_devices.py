#!/usr/bin/env python3
"""
Test SNMP collection for the new 192.168.x.x devices only
"""
import json
import subprocess
import multiprocessing
import time
from datetime import datetime
import os
import sys
import logging

# Add the directory containing our modules to the path
sys.path.append('/usr/local/bin/Main')

try:
    from credential_manager import SNMPCredentialManager
except ImportError:
    print("Could not import credential_manager - continuing without encrypted credentials")
    SNMPCredentialManager = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test devices - final missing devices from sessions.txt analysis
TEST_DEVICES = [
    # Final missing devices that were just added to nightly script
    {"hostname": "MDF-3130-O3-ENC1-A", "ip": "10.0.255.94", "credential": "DTC4nmgt", "device_type": "Network Device"},
    {"hostname": "FW-9300-01", "ip": "192.168.255.12", "credential": "DT_Network_SNMPv3", "device_type": "HQ Firewall"},
    {"hostname": "FW-9300-02", "ip": "192.168.255.13", "credential": "DT_Network_SNMPv3", "device_type": "HQ Firewall"},
    # Previously missing 192.168.x.x devices
    {"hostname": "AL-DMZ-7010-01", "ip": "192.168.200.10", "credential": "DT_Network_SNMPv3", "device_type": "Alameda DMZ Firewall"},
    {"hostname": "AL-DMZ-7010-02", "ip": "192.168.200.11", "credential": "DT_Network_SNMPv3", "device_type": "Alameda DMZ Firewall"}
]

def run_snmp_command(cmd, timeout=15):
    """Run SNMP command with timeout"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None

def test_device_snmp(device):
    """Test SNMP connectivity to a single device"""
    hostname = device['hostname']
    ip = device['ip']
    
    print(f"\n{'='*60}")
    print(f"Testing {hostname} ({ip})")
    print(f"{'='*60}")
    
    result = {
        'hostname': hostname,
        'ip': ip,
        'ping_success': False,
        'snmp_v2_success': False,
        'snmp_v3_success': False,
        'system_description': None,
        'error': None
    }
    
    # Test ping first
    ping_cmd = f"ping -c 3 -W 2 {ip}"
    print(f"🔍 Testing ping to {ip}...")
    ping_result = subprocess.run(ping_cmd, shell=True, capture_output=True, text=True)
    if ping_result.returncode == 0:
        result['ping_success'] = True
        print(f"✅ Ping successful")
        # Extract ping statistics
        if "packet loss" in ping_result.stdout:
            loss_line = [line for line in ping_result.stdout.split('\n') if 'packet loss' in line]
            if loss_line:
                print(f"   📊 {loss_line[0].strip()}")
    else:
        print(f"❌ Ping failed")
        result['error'] = "Ping failed"
        return result
    
    # For 192.168.x.x devices, test SNMPv3 first (they use DT_Network_SNMPv3)
    if ip.startswith('192.168.') and device['credential'] == 'DT_Network_SNMPv3':
        print(f"\n🔍 Testing SNMPv3 (primary for 192.168.x.x devices)...")
        print(f"   🔐 Using DT_Network_SNMPv3 credentials for {ip}")
        # Load credentials from credential manager or use fallback
        try:
            # Set environment variables for database connection
            os.environ['DB_HOST'] = 'localhost'
            os.environ['DB_NAME'] = 'dsrcircuits'
            os.environ['DB_USER'] = 'dsruser'
            os.environ['DB_PASSWORD'] = 'dsruser'
            os.environ['DB_PORT'] = '5432'
            
            sys.path.append('/usr/local/bin/Main')
            from credential_manager import SNMPCredentialManager
            cred_manager = SNMPCredentialManager()
            cred_info = cred_manager.get_credential('DT_Network_SNMPv3')
            
            if cred_info:
                snmp_v3_cmd = (f"snmpget -v3 -u {cred_info['user']} -l authPriv "
                              f"-a {cred_info['auth_protocol']} -A '{cred_info['auth_password']}' "
                              f"-x {cred_info['priv_protocol']} -X '{cred_info['priv_password']}' "
                              f"-t 5 -r 1 {ip} 1.3.6.1.2.1.1.1.0")
                snmp_v3_result = run_snmp_command(snmp_v3_cmd, timeout=10)
                if snmp_v3_result:
                    result['snmp_v3_success'] = True
                    result['system_description'] = snmp_v3_result
                    print(f"   ✅ SNMPv3 successful with DT_Network_SNMPv3")
                    print(f"   📝 System: {snmp_v3_result[:100]}...")
                else:
                    print(f"   ❌ SNMPv3 failed with DT_Network_SNMPv3 credentials")
            else:
                print(f"   ❌ Could not load DT_Network_SNMPv3 credentials")
        except Exception as e:
            print(f"   ❌ Error loading SNMPv3 credentials: {e}")
            # Fallback - try with the nightly script directly
            print(f"   🔄 Attempting fallback - running nightly script to test connection...")
            fallback_cmd = f"cd /usr/local/bin/Main && python3 -c \"from credential_manager import SNMPCredentialManager; cm = SNMPCredentialManager(); print('Credential test:', cm.get_credential('DT_Network_SNMPv3') is not None)\""
            fallback_result = run_snmp_command(fallback_cmd, timeout=10)
            if fallback_result:
                print(f"   📝 Fallback result: {fallback_result}")
            else:
                print(f"   ❌ Fallback also failed - database connection issue")
    else:
        # For other devices, test SNMPv2c first
        print(f"\n🔍 Testing SNMPv2c...")
        communities = ['DTC4nmgt', 'public', 'private']
        for community in communities:
            snmp_cmd = f"snmpget -v2c -c {community} -t 5 -r 1 {ip} 1.3.6.1.2.1.1.1.0"
            print(f"   Trying community: {community}")
            snmp_result = run_snmp_command(snmp_cmd, timeout=10)
            if snmp_result:
                result['snmp_v2_success'] = True
                result['system_description'] = snmp_result
                print(f"   ✅ SNMPv2c successful with community: {community}")
                print(f"   📝 System: {snmp_result[:100]}...")
                break
            else:
                print(f"   ❌ Failed with community: {community}")
    
    # Test SNMPv3 using proper credentials for 192.168.x.x devices
    print(f"\n🔍 Testing SNMPv3...")
    
    # For 192.168.x.x devices, use DT_Network_SNMPv3 with proper auth
    if ip.startswith('192.168.') and device['credential'] == 'DT_Network_SNMPv3' and not result['snmp_v3_success']:
        print(f"   🔐 Using DT_Network_SNMPv3 credentials for {ip}")
        # Load credentials from credential manager
        try:
            sys.path.append('/usr/local/bin/Main')
            from credential_manager import SNMPCredentialManager
            cred_manager = SNMPCredentialManager()
            cred_info = cred_manager.get_credential('DT_Network_SNMPv3')
            
            if cred_info:
                snmp_v3_cmd = (f"snmpget -v3 -u {cred_info['user']} -l authPriv "
                              f"-a {cred_info['auth_protocol']} -A '{cred_info['auth_password']}' "
                              f"-x {cred_info['priv_protocol']} -X '{cred_info['priv_password']}' "
                              f"-t 5 -r 1 {ip} 1.3.6.1.2.1.1.1.0")
                snmp_v3_result = run_snmp_command(snmp_v3_cmd, timeout=10)
                if snmp_v3_result:
                    result['snmp_v3_success'] = True
                    if not result['system_description']:
                        result['system_description'] = snmp_v3_result
                    print(f"   ✅ SNMPv3 successful with DT_Network_SNMPv3")
                else:
                    print(f"   ❌ SNMPv3 failed with DT_Network_SNMPv3 credentials")
            else:
                print(f"   ❌ Could not load DT_Network_SNMPv3 credentials")
        except Exception as e:
            print(f"   ❌ Error loading SNMPv3 credentials: {e}")
    else:
        # For other devices, try basic SNMPv3
        print(f"   ⚠️  Note: Testing basic SNMPv3 (may fail without proper credentials)")
        snmp_v3_cmd = f"snmpget -v3 -u DT_Network_SNMPv3 -l noAuthNoPriv -t 5 -r 1 {ip} 1.3.6.1.2.1.1.1.0"
        snmp_v3_result = run_snmp_command(snmp_v3_cmd, timeout=10)
        if snmp_v3_result:
            result['snmp_v3_success'] = True
            if not result['system_description']:
                result['system_description'] = snmp_v3_result
            print(f"   ✅ SNMPv3 successful (noAuth)")
        else:
            print(f"   ❌ SNMPv3 failed (expected without proper credentials)")
    
    # Test port scan
    print(f"\n🔍 Testing SNMP port (161)...")
    port_cmd = f"timeout 5 bash -c '</dev/tcp/{ip}/161' 2>/dev/null && echo 'Port 161 open' || echo 'Port 161 closed/filtered'"
    port_result = subprocess.run(port_cmd, shell=True, capture_output=True, text=True)
    print(f"   📡 {port_result.stdout.strip()}")
    
    return result

def main():
    """Main test function"""
    print("🧪 Testing SNMP connectivity for new 192.168.x.x devices")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Testing {len(TEST_DEVICES)} devices")
    
    results = []
    success_count = 0
    ping_success_count = 0
    snmp_v2_success_count = 0
    snmp_v3_success_count = 0
    
    start_time = time.time()
    
    for device in TEST_DEVICES:
        result = test_device_snmp(device)
        results.append(result)
        
        if result['ping_success']:
            ping_success_count += 1
        if result['snmp_v2_success'] or result['snmp_v3_success']:
            success_count += 1
        if result['snmp_v2_success']:
            snmp_v2_success_count += 1
        if result['snmp_v3_success']:
            snmp_v3_success_count += 1
    
    elapsed_time = time.time() - start_time
    
    # Print summary
    print(f"\n\n{'='*80}")
    print(f"🏁 TEST SUMMARY")
    print(f"{'='*80}")
    print(f"📊 Total devices tested: {len(TEST_DEVICES)}")
    print(f"🏓 Ping successful: {ping_success_count}/{len(TEST_DEVICES)} ({ping_success_count/len(TEST_DEVICES)*100:.1f}%)")
    print(f"📡 SNMP successful: {success_count}/{len(TEST_DEVICES)} ({success_count/len(TEST_DEVICES)*100:.1f}%)")
    print(f"   📋 SNMPv2c: {snmp_v2_success_count}")
    print(f"   🔐 SNMPv3: {snmp_v3_success_count}")
    print(f"⏱️  Total time: {elapsed_time:.2f} seconds")
    
    # Detailed results
    print(f"\n📋 DETAILED RESULTS:")
    print(f"{'Hostname':<15} {'IP':<16} {'Ping':<6} {'SNMPv2':<8} {'SNMPv3':<8} {'Status'}")
    print(f"{'-'*70}")
    
    for result in results:
        ping_status = "✅" if result['ping_success'] else "❌"
        snmp_v2_status = "✅" if result['snmp_v2_success'] else "❌"
        snmp_v3_status = "✅" if result['snmp_v3_success'] else "❌"
        
        if result['snmp_v2_success'] or result['snmp_v3_success']:
            status = "SNMP OK"
        elif result['ping_success']:
            status = "Ping only"
        else:
            status = "Failed"
        
        print(f"{result['hostname']:<15} {result['ip']:<16} {ping_status:<6} {snmp_v2_status:<8} {snmp_v3_status:<8} {status}")
    
    # Failed devices
    failed_devices = [r for r in results if not (r['snmp_v2_success'] or r['snmp_v3_success'])]
    if failed_devices:
        print(f"\n❌ FAILED DEVICES ({len(failed_devices)}):")
        for result in failed_devices:
            reason = result.get('error', 'SNMP not responding')
            print(f"   • {result['hostname']} ({result['ip']}) - {reason}")
    
    # Successful devices
    successful_devices = [r for r in results if (r['snmp_v2_success'] or r['snmp_v3_success'])]
    if successful_devices:
        print(f"\n✅ SUCCESSFUL DEVICES ({len(successful_devices)}):")
        for result in successful_devices:
            protocol = "SNMPv3" if result['snmp_v3_success'] else "SNMPv2c"
            print(f"   • {result['hostname']} ({result['ip']}) - {protocol}")
            if result['system_description']:
                print(f"     📝 {result['system_description'][:80]}...")
    
    # Save results to file
    output_file = f"/tmp/test_192_devices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tested': len(TEST_DEVICES),
                'ping_successful': ping_success_count,
                'snmp_successful': success_count,
                'snmp_v2_successful': snmp_v2_success_count,
                'snmp_v3_successful': snmp_v3_success_count,
                'elapsed_time': elapsed_time
            },
            'results': results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if ping_success_count == 0:
        print("   🔍 No devices responding to ping - check if these IPs are actually in use")
    elif success_count == 0 and ping_success_count > 0:
        print("   🔧 Devices pingable but no SNMP response - check SNMP configuration")
        print("   🔑 Verify SNMP community strings and SNMPv3 credentials")
    elif success_count > 0:
        print("   ✅ Some devices responding - ready for nightly collection!")
        print("   🔄 Run the nightly script to add these to inventory")

if __name__ == "__main__":
    main()