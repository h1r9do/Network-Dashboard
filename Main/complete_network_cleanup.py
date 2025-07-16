#!/usr/bin/env python3
"""
Complete Network Cleanup Script
===============================

This script performs a complete cleanup of a Meraki MX network in the proper order
to handle all dependencies. It reverses the migration process:

1. Clear firewall rules (removes dependencies on VLANs and objects)
2. Clear syslog configuration
3. Delete all VLANs except one (removes group policy dependencies)
4. Delete group policies
5. Delete policy objects and groups from organization

Usage:
    python3 complete_network_cleanup.py --network-id <network_id> [--include-policy-objects]

Example:
    python3 complete_network_cleanup.py --network-id L_3790904986339115852
    python3 complete_network_cleanup.py --network-id L_3790904986339115852 --include-policy-objects

Author: Claude
Date: July 2025
"""

import os
import sys
import json
import requests
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"
HEADERS = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

class NetworkCleaner:
    def __init__(self, network_id):
        """Initialize the network cleaner"""
        self.network_id = network_id
        self.org_id = self.get_network_org_id()
        self.log_entries = []
        
        self.log(f"Network Cleaner initialized for {network_id}")
        self.log(f"Organization: {self.org_id}")
        
    def log(self, message, level='INFO'):
        """Add log entry"""
        entry = f"[{datetime.now().strftime('%H:%M:%S')}] {level}: {message}"
        self.log_entries.append(entry)
        print(entry)
        
    def make_api_request(self, url, method='GET', data=None):
        """Make API request with error handling"""
        time.sleep(0.5)  # Rate limiting
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=HEADERS, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, headers=HEADERS, json=data, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=HEADERS, json=data, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=HEADERS, timeout=30)
                
            if response.status_code == 429:
                self.log("Rate limited, waiting 60 seconds...", "WARNING")
                time.sleep(60)
                return self.make_api_request(url, method, data)
                
            response.raise_for_status()
            
            if response.text:
                return response.json()
            return {}
            
        except Exception as e:
            self.log(f"Error {method} {url}: {e}", "ERROR")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                self.log(f"Response: {e.response.text}", "ERROR")
            return None
    
    def get_network_org_id(self):
        """Get organization ID for the network"""
        url = f"{BASE_URL}/networks/{self.network_id}"
        response = self.make_api_request(url)
        if response:
            return response['organizationId']
        else:
            raise Exception("Could not determine organization ID")
    
    def clear_firewall_rules(self):
        """Step 1: Clear all firewall rules"""
        self.log("\nStep 1: Clearing firewall rules...")
        
        # Get current rules
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/firewall/l3FirewallRules"
        current_rules = self.make_api_request(url)
        
        if current_rules:
            rule_count = len(current_rules.get('rules', []))
            self.log(f"  Found {rule_count} existing firewall rules")
            
            # Apply minimal default rule set
            default_rules = [{
                'comment': 'Default allow all',
                'srcCidr': 'Any',
                'srcPort': 'Any', 
                'destCidr': 'Any',
                'destPort': 'Any',
                'protocol': 'any',
                'policy': 'allow',
                'syslogEnabled': False
            }]
            
            data = {'rules': default_rules}
            result = self.make_api_request(url, method='PUT', data=data)
            
            if result:
                self.log("  ✓ Firewall rules cleared (set to default allow)")
            else:
                self.log("  ✗ Failed to clear firewall rules", "ERROR")
                return False
        else:
            self.log("  No firewall rules found")
        
        return True
    
    def clear_syslog(self):
        """Step 2: Clear syslog configuration"""
        self.log("\nStep 2: Clearing syslog configuration...")
        
        # Get current syslog config
        url = f"{BASE_URL}/networks/{self.network_id}/syslogServers"
        current_syslog = self.make_api_request(url)
        
        if current_syslog and current_syslog.get('servers'):
            server_count = len(current_syslog['servers'])
            self.log(f"  Found {server_count} syslog server(s)")
            
            # Clear syslog servers
            data = {'servers': []}
            result = self.make_api_request(url, method='PUT', data=data)
            
            if result:
                self.log("  ✓ Syslog configuration cleared")
            else:
                self.log("  ✗ Failed to clear syslog configuration", "ERROR")
                return False
        else:
            self.log("  No syslog servers configured")
        
        return True
    
    def delete_vlans(self):
        """Step 3: Delete all VLANs except one"""
        self.log("\nStep 3: Deleting VLANs...")
        
        # Get current VLANs
        url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans"
        vlans = self.make_api_request(url)
        
        if not vlans:
            self.log("  No VLANs found")
            return True
        
        self.log(f"  Found {len(vlans)} VLANs")
        
        # Sort VLANs by ID (delete higher IDs first to avoid dependency issues)
        vlans_sorted = sorted(vlans, key=lambda x: x['id'], reverse=True)
        
        # Keep track of how many we've deleted
        deleted_count = 0
        
        # Delete all but the last VLAN (Meraki requires at least one)
        for i, vlan in enumerate(vlans_sorted):
            vlan_id = vlan['id']
            vlan_name = vlan['name']
            
            # Keep the last VLAN (lowest ID)
            if i == len(vlans_sorted) - 1:
                self.log(f"  Keeping VLAN {vlan_id} ({vlan_name}) - required minimum")
                
                # Reset the remaining VLAN to a default state
                default_data = {
                    'name': 'Default',
                    'subnet': '192.168.128.0/24',
                    'applianceIp': '192.168.128.1'
                }
                
                update_url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans/{vlan_id}"
                result = self.make_api_request(update_url, method='PUT', data=default_data)
                
                if result:
                    self.log(f"    ✓ Reset VLAN {vlan_id} to default configuration")
                else:
                    self.log(f"    ⚠️  Could not reset VLAN {vlan_id} to default", "WARNING")
                break
            
            # Delete this VLAN
            self.log(f"  Deleting VLAN {vlan_id} ({vlan_name})...")
            delete_url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans/{vlan_id}"
            result = self.make_api_request(delete_url, method='DELETE')
            
            if result is not None:  # DELETE returns empty response on success
                deleted_count += 1
                self.log(f"    ✓ Deleted VLAN {vlan_id}")
            else:
                self.log(f"    ✗ Failed to delete VLAN {vlan_id}", "ERROR")
            
            time.sleep(1)  # Rate limiting
        
        self.log(f"  Deleted {deleted_count} VLANs, kept 1 minimum required")
        return True
    
    def delete_group_policies(self):
        """Step 4: Delete all group policies"""
        self.log("\nStep 4: Deleting group policies...")
        
        # Get current group policies
        url = f"{BASE_URL}/networks/{self.network_id}/groupPolicies"
        policies = self.make_api_request(url)
        
        if not policies:
            self.log("  No group policies found")
            return True
        
        self.log(f"  Found {len(policies)} group policies")
        
        deleted_count = 0
        for policy in policies:
            policy_id = policy['groupPolicyId']
            policy_name = policy['name']
            
            self.log(f"  Deleting group policy: {policy_name} (ID: {policy_id})")
            delete_url = f"{BASE_URL}/networks/{self.network_id}/groupPolicies/{policy_id}"
            result = self.make_api_request(delete_url, method='DELETE')
            
            if result is not None:  # DELETE returns empty response on success
                deleted_count += 1
                self.log(f"    ✓ Deleted group policy {policy_id}")
            else:
                self.log(f"    ✗ Failed to delete group policy {policy_id}", "ERROR")
            
            time.sleep(1)  # Rate limiting
        
        self.log(f"  Deleted {deleted_count} group policies")
        return True
    
    def delete_policy_objects(self, include_policy_objects=False):
        """Step 5: Delete policy objects and groups (optional)"""
        if not include_policy_objects:
            self.log("\nStep 5: Skipping policy objects deletion (use --include-policy-objects to delete)")
            return True
            
        self.log("\nStep 5: Deleting policy objects and groups...")
        
        # Get current policy groups first (they depend on objects)
        groups_url = f"{BASE_URL}/organizations/{self.org_id}/policyObjects/groups"
        groups = self.make_api_request(groups_url) or []
        
        self.log(f"  Found {len(groups)} policy groups")
        
        # Delete groups first
        deleted_groups = 0
        for group in groups:
            group_id = group['id']
            group_name = group['name']
            
            # Only delete groups that look like they were created by our migration
            # (to avoid deleting pre-existing organizational groups)
            if any(keyword in group_name.lower() for keyword in ['epx', 'teams', 'pbx', 'netrix']):
                self.log(f"  Deleting policy group: {group_name} (ID: {group_id})")
                delete_url = f"{BASE_URL}/organizations/{self.org_id}/policyObjects/groups/{group_id}"
                result = self.make_api_request(delete_url, method='DELETE')
                
                if result is not None:
                    deleted_groups += 1
                    self.log(f"    ✓ Deleted group {group_id}")
                else:
                    self.log(f"    ✗ Failed to delete group {group_id}", "ERROR")
                    
                time.sleep(1)
            else:
                self.log(f"  Skipping group: {group_name} (pre-existing)")
        
        # Get current policy objects
        objects_url = f"{BASE_URL}/organizations/{self.org_id}/policyObjects"
        objects = self.make_api_request(objects_url) or []
        
        self.log(f"  Found {len(objects)} policy objects")
        
        # Delete objects
        deleted_objects = 0
        for obj in objects:
            obj_id = obj['id']
            obj_name = obj['name']
            
            # Only delete objects that look like they were created by our migration
            migration_keywords = ['google', 'epx', 'windows', 'ntp', 'teams', 'pbx', 'netrix']
            if any(keyword in obj_name.lower() for keyword in migration_keywords):
                self.log(f"  Deleting policy object: {obj_name} (ID: {obj_id})")
                delete_url = f"{BASE_URL}/organizations/{self.org_id}/policyObjects/{obj_id}"
                result = self.make_api_request(delete_url, method='DELETE')
                
                if result is not None:
                    deleted_objects += 1
                    self.log(f"    ✓ Deleted object {obj_id}")
                else:
                    self.log(f"    ✗ Failed to delete object {obj_id}", "ERROR")
                    
                time.sleep(1)
            else:
                self.log(f"  Skipping object: {obj_name} (pre-existing)")
        
        self.log(f"  Deleted {deleted_groups} policy groups and {deleted_objects} policy objects")
        return True
    
    def verify_cleanup(self):
        """Verify the cleanup was successful"""
        self.log("\nStep 6: Verifying cleanup...")
        
        # Check VLANs
        vlans_url = f"{BASE_URL}/networks/{self.network_id}/appliance/vlans"
        vlans = self.make_api_request(vlans_url) or []
        self.log(f"  Remaining VLANs: {len(vlans)}")
        
        # Check group policies
        policies_url = f"{BASE_URL}/networks/{self.network_id}/groupPolicies"
        policies = self.make_api_request(policies_url) or []
        self.log(f"  Remaining group policies: {len(policies)}")
        
        # Check firewall rules
        fw_url = f"{BASE_URL}/networks/{self.network_id}/appliance/firewall/l3FirewallRules"
        fw_result = self.make_api_request(fw_url)
        fw_count = len(fw_result.get('rules', [])) if fw_result else 0
        self.log(f"  Firewall rules: {fw_count} (should be 1 default)")
        
        # Check syslog
        syslog_url = f"{BASE_URL}/networks/{self.network_id}/syslogServers"
        syslog_result = self.make_api_request(syslog_url)
        syslog_count = len(syslog_result.get('servers', [])) if syslog_result else 0
        self.log(f"  Syslog servers: {syslog_count} (should be 0)")
        
        # Summary
        if len(vlans) <= 1 and len(policies) == 0 and fw_count <= 1 and syslog_count == 0:
            self.log("  ✅ Cleanup successful - network reset to minimal state")
            return True
        else:
            self.log("  ⚠️  Some items may not have been cleaned up", "WARNING")
            return False
    
    def generate_report(self):
        """Generate cleanup report"""
        report = f"""
Network Cleanup Report
======================
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Network ID: {self.network_id}
Organization: {self.org_id}

Cleanup Log:
"""
        for entry in self.log_entries:
            report += entry + "\n"
            
        return report

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Complete Network Cleanup Tool')
    parser.add_argument('--network-id', required=True, help='Target network ID to clean')
    parser.add_argument('--include-policy-objects', action='store_true', 
                       help='Also delete policy objects and groups from organization')
    parser.add_argument('--auto-confirm', action='store_true', help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    print("🧹 Complete Network Cleanup Tool")
    print("=" * 50)
    print(f"Target Network: {args.network_id}")
    
    if args.include_policy_objects:
        print("⚠️  Will also delete policy objects and groups from organization")
    
    # Confirm before proceeding
    if not args.auto_confirm:
        print(f"\n⚠️  WARNING: This will completely clean network {args.network_id}")
        print("This will remove:")
        print("  • All firewall rules (set to default allow)")
        print("  • Syslog configuration")
        print("  • All VLANs except one (reset to default)")
        print("  • All group policies")
        if args.include_policy_objects:
            print("  • Policy objects and groups from organization")
            
        response = input("\n❓ Proceed with cleanup? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Cleanup cancelled")
            return
    
    # Perform cleanup
    try:
        cleaner = NetworkCleaner(args.network_id)
        
        # Execute cleanup steps in proper order
        success = True
        success &= cleaner.clear_firewall_rules()
        success &= cleaner.clear_syslog()
        success &= cleaner.delete_vlans()
        success &= cleaner.delete_group_policies()
        success &= cleaner.delete_policy_objects(args.include_policy_objects)
        success &= cleaner.verify_cleanup()
        
        # Generate report
        report = cleaner.generate_report()
        report_file = f"cleanup_report_{args.network_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\n📄 Cleanup report saved to: {report_file}")
        
        if success:
            print("\n✅ 🎉 CLEANUP COMPLETED SUCCESSFULLY!")
            print("Network is ready for fresh deployment.")
        else:
            print("\n⚠️ 🔶 CLEANUP COMPLETED WITH WARNINGS")
            print("Some items may not have been fully cleaned. Check the report for details.")
        
    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(__doc__)
        print("\nExample usage:")
        print("  python3 complete_network_cleanup.py --network-id L_3790904986339115852")
        print("  python3 complete_network_cleanup.py --network-id L_3790904986339115852 --include-policy-objects --auto-confirm")
    else:
        main()