#!/usr/bin/env python3
"""
Cisco EoL Web Scraper
====================

This script attempts to fetch EoL data from Cisco's public EoL/EoS search tool.
It uses the Cisco EoL Product Search which doesn't require authentication.
"""

import os
import sys
import re
import json
import time
import requests
import psycopg2
from datetime import datetime
from bs4 import BeautifulSoup
import logging
from urllib.parse import quote, urlencode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'T3dC$gLp9'
}

class CiscoEoLScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Cisco EoL search URL
        self.search_base = "https://www.cisco.com/c/en/us/support/web/tools/end-of-life-support/search-products.html"
        
    def search_cisco_eol(self, model):
        """Search Cisco's EoL database for a specific model"""
        try:
            # First, try direct product lookup
            logger.info(f"Searching Cisco EoL database for: {model}")
            
            # Cisco's EoL search API endpoint (found by inspecting network traffic)
            api_url = "https://api.cisco.com/supporttools/eox/rest/5/EOXByProductID/1"
            
            # Try searching with the model
            search_params = {
                'responseencoding': 'json',
                'input': model
            }
            
            # Note: This might require authentication headers
            # For now, let's try the public web interface
            
            # Alternative: Use the public search page
            search_url = f"https://www.cisco.com/c/en/us/support/web/tools-catalog/eol/search.html?search={quote(model)}"
            
            response = self.session.get(search_url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for EoL data in the response
                eol_data = self.parse_cisco_response(soup, model)
                if eol_data:
                    return eol_data
                    
        except Exception as e:
            logger.error(f"Error searching Cisco EoL for {model}: {e}")
            
        return None
        
    def parse_cisco_response(self, soup, model):
        """Parse Cisco's EoL page response"""
        eol_data = {
            'model': model,
            'announcement_date': None,
            'end_of_sale_date': None,
            'end_of_support_date': None,
            'end_of_sw_maintenance': None,
            'end_of_routine_failure': None,
            'end_of_service_contract': None,
            'last_support_date': None,
            'source': 'cisco_eol_search'
        }
        
        # Common patterns in Cisco EoL pages
        date_mappings = {
            'End-of-Sale Date': 'end_of_sale_date',
            'End-of-Support Date': 'end_of_support_date',
            'EoL Announcement Date': 'announcement_date',
            'End of SW Maintenance': 'end_of_sw_maintenance',
            'End of Routine Failure Analysis': 'end_of_routine_failure',
            'End of Service Contract Renewal': 'end_of_service_contract',
            'Last Date of Support': 'last_support_date'
        }
        
        # Look for tables containing EoL data
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    
                    for key, field in date_mappings.items():
                        if key.lower() in label.lower():
                            date_parsed = self.parse_date(value)
                            if date_parsed:
                                eol_data[field] = date_parsed
                                
        # Check if we found any dates
        if any([eol_data['end_of_sale_date'], eol_data['end_of_support_date']]):
            return eol_data
            
        return None
        
    def parse_date(self, date_str):
        """Parse various Cisco date formats"""
        if not date_str or date_str.strip() == '':
            return None
            
        # Remove extra whitespace
        date_str = ' '.join(date_str.split())
        
        # Common Cisco date formats
        formats = [
            '%Y-%m-%d',
            '%d-%b-%Y',
            '%d-%B-%Y',
            '%B %d, %Y',
            '%b %d, %Y',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y/%m/%d'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
                
        logger.warning(f"Could not parse date: {date_str}")
        return None
        
    def search_alternative_sources(self, model):
        """Search alternative sources for EoL data"""
        # List of alternative sources
        sources = [
            {
                'name': 'Cisco Lifecycle',
                'url': f'https://www.cisco.com/c/en/us/products/switches/{model.lower()}-series/index.html',
                'patterns': {
                    'end_of_sale': r'end.{0,5}of.{0,5}sale[:\s]+([A-Za-z]+ \d+, \d{4})',
                    'end_of_support': r'end.{0,5}of.{0,5}(support|life)[:\s]+([A-Za-z]+ \d+, \d{4})'
                }
            },
            {
                'name': 'Cisco Datasheet',
                'url': f'https://www.cisco.com/c/en/us/products/collateral/switches/datasheet-{model.lower()}.html',
                'patterns': {
                    'end_of_sale': r'EoS[:\s]+([A-Za-z]+ \d+, \d{4})',
                    'end_of_support': r'EoL[:\s]+([A-Za-z]+ \d+, \d{4})'
                }
            }
        ]
        
        for source in sources:
            try:
                response = self.session.get(source['url'], timeout=10)
                if response.status_code == 200:
                    content = response.text
                    
                    eol_data = {'model': model, 'source': source['name']}
                    
                    for field, pattern in source['patterns'].items():
                        match = re.search(pattern, content, re.IGNORECASE)
                        if match:
                            date_str = match.group(1) if match.lastindex else match.group(0)
                            parsed_date = self.parse_date(date_str)
                            if parsed_date:
                                eol_data[field] = parsed_date
                                
                    if len(eol_data) > 2:  # More than just model and source
                        return eol_data
                        
            except Exception as e:
                logger.debug(f"Alternative source {source['name']} failed for {model}: {e}")
                
        return None
        
    def update_database(self, eol_data):
        """Update the corporate_eol table"""
        if not eol_data or not any([eol_data.get('end_of_sale_date'), eol_data.get('end_of_support_date')]):
            return False
            
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        try:
            # Check if model exists
            cursor.execute("SELECT id FROM corporate_eol WHERE model = %s", (eol_data['model'],))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                update_fields = []
                update_values = []
                
                for field in ['announcement_date', 'end_of_sale_date', 'end_of_support_date']:
                    if eol_data.get(field):
                        update_fields.append(f"{field} = %s")
                        update_values.append(eol_data[field])
                        
                if update_fields:
                    update_values.extend(['web_scraper', eol_data['model']])
                    query = f"""
                        UPDATE corporate_eol 
                        SET {', '.join(update_fields)}, 
                            source = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE model = %s
                    """
                    cursor.execute(query, update_values)
                    logger.info(f"Updated {eol_data['model']} in database")
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO corporate_eol 
                    (model, announcement_date, end_of_sale_date, end_of_support_date, source)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    eol_data['model'],
                    eol_data.get('announcement_date'),
                    eol_data.get('end_of_sale_date'),
                    eol_data.get('end_of_support_date'),
                    'web_scraper'
                ))
                logger.info(f"Inserted {eol_data['model']} into database")
                
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Database error for {eol_data['model']}: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

def main():
    """Main function"""
    scraper = CiscoEoLScraper()
    
    # Read models from file
    models_file = "/usr/local/bin/Main/datacenter_models_list.txt"
    
    if not os.path.exists(models_file):
        logger.error(f"Models file not found: {models_file}")
        return
        
    with open(models_file, 'r') as f:
        models = [line.strip() for line in f if line.strip()]
        
    logger.info(f"Starting EoL lookup for {len(models)} models")
    
    results = {
        'found': 0,
        'not_found': 0,
        'updated': 0,
        'errors': 0
    }
    
    # Process models
    for i, model in enumerate(models, 1):
        logger.info(f"\n[{i}/{len(models)}] Processing: {model}")
        
        try:
            # Skip power cords and accessories
            if model.startswith('800-'):
                logger.info(f"Skipping accessory: {model}")
                continue
                
            # Try Cisco EoL search first
            eol_data = scraper.search_cisco_eol(model)
            
            # If not found, try alternative sources
            if not eol_data:
                eol_data = scraper.search_alternative_sources(model)
                
            if eol_data:
                logger.info(f"Found EoL data for {model}")
                logger.info(f"  EoS: {eol_data.get('end_of_sale_date', 'N/A')}")
                logger.info(f"  EoL: {eol_data.get('end_of_support_date', 'N/A')}")
                
                if scraper.update_database(eol_data):
                    results['updated'] += 1
                results['found'] += 1
            else:
                logger.warning(f"No EoL data found for {model}")
                results['not_found'] += 1
                
        except Exception as e:
            logger.error(f"Error processing {model}: {e}")
            results['errors'] += 1
            
        # Be respectful - rate limit requests
        time.sleep(3)
        
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("EoL Lookup Summary:")
    logger.info(f"  Total models: {len(models)}")
    logger.info(f"  Found EoL data: {results['found']}")
    logger.info(f"  Not found: {results['not_found']}")
    logger.info(f"  Database updated: {results['updated']}")
    logger.info(f"  Errors: {results['errors']}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()