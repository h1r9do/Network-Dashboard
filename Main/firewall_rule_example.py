#!/usr/bin/env python3
"""
Firewall Rule Example with Policy Objects
=========================================

This script shows how to use the extracted policy objects in firewall rules.
"""

import json

def show_firewall_rule_examples():
    """Show examples of how to use policy objects in firewall rules"""
    
    print("Firewall Rule Examples with Policy Objects")
    print("=" * 50)
    
    # Example firewall rule structure
    example_rules = [
        {
            "comment": "Allow Google Android Clients",
            "policy": "allow",
            "protocol": "tcp",
            "srcCidr": "any",
            "srcPort": "any",
            "destCidr": "OBJ(3790904986339115064)",  # Google_AndroidClients
            "destPort": "443",
            "syslogEnabled": False
        },
        {
            "comment": "Allow MS Teams Media",
            "policy": "allow", 
            "protocol": "tcp",
            "srcCidr": "any",
            "srcPort": "any",
            "destCidr": "GRP(3790904986339115076)",  # MS Teams Media IPs
            "destPort": "443",
            "syslogEnabled": False
        },
        {
            "comment": "Allow Outbound EPX",
            "policy": "allow",
            "protocol": "tcp", 
            "srcCidr": "any",
            "srcPort": "any",
            "destCidr": "GRP(3790904986339115043)",  # Outbound EPX
            "destPort": "443",
            "syslogEnabled": False
        }
    ]
    
    print("\nExample Firewall Rules:")
    print("-" * 30)
    for i, rule in enumerate(example_rules, 1):
        print(f"Rule {i}:")
        print(f"  Comment: {rule['comment']}")
        print(f"  Policy: {rule['policy']}")
        print(f"  Protocol: {rule['protocol']}")
        print(f"  Source: {rule['srcCidr']}:{rule['srcPort']}")
        print(f"  Destination: {rule['destCidr']}:{rule['destPort']}")
        print(f"  Syslog: {rule['syslogEnabled']}")
        print()
    
    # Show the complete mapping
    print("Complete Policy Object Reference:")
    print("-" * 40)
    
    policy_objects = {
        "Network Objects": {
            "OBJ(3790904986339115064)": "Google_AndroidClients (android.clients.google.com)",
            "OBJ(3790904986339115065)": "Google_ClientServices (clientservices.googleapis.com)",
            "OBJ(3790904986339115066)": "Google_FireBaseRemoteConfig (firebaseremoteconfig.googleapis.com)",
            "OBJ(3790904986339115067)": "Google_MTalk (mtalk.google.com)",
            "OBJ(3790904986339115074)": "Windows NTP Server IP (40.119.6.228)"
        },
        "Network Object Groups": {
            "GRP(3790904986339115043)": "Outbound EPX (contains 4 objects)",
            "GRP(3790904986339115076)": "MS Teams Media IPs (contains 2 objects)",
            "GRP(3790904986339115077)": "Netrix nVX PBX IPs (contains 2 objects)"
        }
    }
    
    for category, objects in policy_objects.items():
        print(f"\n{category}:")
        for obj_ref, description in objects.items():
            print(f"  {obj_ref}: {description}")
    
    print("\nTo use these in your firewall rules:")
    print("1. Reference them in srcCidr or destCidr fields")
    print("2. Use the exact format: OBJ(id) or GRP(id)")
    print("3. The Meraki API will resolve them to their actual values")

if __name__ == "__main__":
    show_firewall_rule_examples()