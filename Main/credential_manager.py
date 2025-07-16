#!/usr/bin/env python3
"""
Encrypted SNMP Credential Manager
Handles encrypted storage and retrieval of SNMP credentials from PostgreSQL
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import getpass

class SNMPCredentialManager:
    def __init__(self, encryption_key=None):
        """Initialize credential manager with optional encryption key"""
        self.encryption_key = encryption_key or os.environ.get('SNMP_ENCRYPTION_KEY', 'default_snmp_key_2025')
        self.connection = None
        
    def connect_db(self):
        """Connect to PostgreSQL database"""
        try:
            # Try to get database connection info from environment or use defaults
            db_config = {
                'host': os.environ.get('DB_HOST', 'localhost'),
                'database': os.environ.get('DB_NAME', 'dsrcircuits'),
                'user': os.environ.get('DB_USER', 'dsruser'),
                'password': os.environ.get('DB_PASSWORD', 'dsruser'),
                'port': os.environ.get('DB_PORT', '5432')
            }
            
            self.connection = psycopg2.connect(**db_config)
            return True
            
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    def close_db(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            
    def get_credential(self, credential_name):
        """Get decrypted credential by name"""
        if not self.connection:
            if not self.connect_db():
                return None
                
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM get_snmp_credential(%s, %s)",
                    (credential_name, self.encryption_key)
                )
                result = cursor.fetchone()
                
                if result:
                    return dict(result)
                return None
                
        except Exception as e:
            print(f"Error retrieving credential '{credential_name}': {e}")
            return None
    
    def get_all_credentials(self):
        """Get all decrypted credentials as a dictionary"""
        if not self.connection:
            if not self.connect_db():
                return {}
                
        credentials = {}
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get list of credential names
                cursor.execute("SELECT credential_name FROM snmp_credentials WHERE is_active = TRUE")
                names = [row['credential_name'] for row in cursor.fetchall()]
                
                # Get each credential
                for name in names:
                    cred = self.get_credential(name)
                    if cred:
                        credentials[name] = {
                            'type': cred['credential_type'],
                            'community': cred['community'],
                            'user': cred['username'],
                            'auth_protocol': cred['auth_protocol'],
                            'auth_password': cred['auth_password'],
                            'priv_protocol': cred['priv_protocol'],
                            'priv_password': cred['priv_password']
                        }
                        
        except Exception as e:
            print(f"Error retrieving all credentials: {e}")
            
        return credentials
    
    def list_credentials(self):
        """List available credentials (without sensitive data)"""
        if not self.connection:
            if not self.connect_db():
                return []
                
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM snmp_credentials_list")
                return cursor.fetchall()
                
        except Exception as e:
            print(f"Error listing credentials: {e}")
            return []
    
    def add_snmpv2c_credential(self, name, community, description=None):
        """Add new SNMPv2c credential"""
        if not self.connection:
            if not self.connect_db():
                return False
                
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT insert_snmpv2c_credential(%s, %s, %s, %s)",
                    (name, community, description, self.encryption_key)
                )
                self.connection.commit()
                print(f"Added SNMPv2c credential: {name}")
                return True
                
        except Exception as e:
            print(f"Error adding SNMPv2c credential: {e}")
            self.connection.rollback()
            return False
    
    def add_snmpv3_credential(self, name, username, auth_protocol, auth_password, 
                             priv_protocol, priv_password, description=None):
        """Add new SNMPv3 credential"""
        if not self.connection:
            if not self.connect_db():
                return False
                
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT insert_snmpv3_credential(%s, %s, %s, %s, %s, %s, %s, %s)",
                    (name, username, auth_protocol, auth_password, 
                     priv_protocol, priv_password, description, self.encryption_key)
                )
                self.connection.commit()
                print(f"Added SNMPv3 credential: {name}")
                return True
                
        except Exception as e:
            print(f"Error adding SNMPv3 credential: {e}")
            self.connection.rollback()
            return False

def main():
    """Command line interface for credential management"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SNMP Credential Manager')
    parser.add_argument('--list', action='store_true', help='List all credentials')
    parser.add_argument('--get', help='Get specific credential by name')
    parser.add_argument('--get-all', action='store_true', help='Get all credentials as JSON')
    parser.add_argument('--add-v2c', nargs=2, metavar=('NAME', 'COMMUNITY'), 
                       help='Add SNMPv2c credential')
    parser.add_argument('--add-v3', nargs=6, 
                       metavar=('NAME', 'USER', 'AUTH_PROTO', 'AUTH_PASS', 'PRIV_PROTO', 'PRIV_PASS'),
                       help='Add SNMPv3 credential')
    parser.add_argument('--description', help='Description for new credential')
    parser.add_argument('--encryption-key', help='Custom encryption key')
    
    args = parser.parse_args()
    
    # Initialize credential manager
    manager = SNMPCredentialManager(args.encryption_key)
    
    try:
        if args.list:
            credentials = manager.list_credentials()
            print(f"Available SNMP Credentials ({len(credentials)}):")
            print("-" * 60)
            for cred in credentials:
                print(f"Name: {cred['credential_name']}")
                print(f"Type: {cred['credential_type']}")
                print(f"Description: {cred['description'] or 'N/A'}")
                print(f"Created: {cred['created_at']}")
                print("-" * 40)
                
        elif args.get:
            cred = manager.get_credential(args.get)
            if cred:
                print(f"Credential: {args.get}")
                print(f"Type: {cred['credential_type']}")
                if cred['credential_type'] == 'SNMPv2c':
                    print(f"Community: {cred['community']}")
                else:
                    print(f"Username: {cred['username']}")
                    print(f"Auth Protocol: {cred['auth_protocol']}")
                    print(f"Auth Password: {cred['auth_password']}")
                    print(f"Priv Protocol: {cred['priv_protocol']}")
                    print(f"Priv Password: {cred['priv_password']}")
            else:
                print(f"Credential '{args.get}' not found")
                
        elif args.get_all:
            credentials = manager.get_all_credentials()
            print(json.dumps(credentials, indent=2))
            
        elif args.add_v2c:
            name, community = args.add_v2c
            manager.add_snmpv2c_credential(name, community, args.description)
            
        elif args.add_v3:
            name, user, auth_proto, auth_pass, priv_proto, priv_pass = args.add_v3
            manager.add_snmpv3_credential(name, user, auth_proto, auth_pass, 
                                        priv_proto, priv_pass, args.description)
        else:
            parser.print_help()
            
    finally:
        manager.close_db()

if __name__ == "__main__":
    main()