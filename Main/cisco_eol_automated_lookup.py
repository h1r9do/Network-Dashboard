#!/usr/bin/env python3
"""
Automated Cisco EoL/EoS Data Lookup Script
==========================================

This script attempts to automatically fetch End of Life and End of Sale dates
for Cisco equipment using various methods.

Methods:
1. Web scraping Cisco Support Tools (requires authentication)
2. Using Cisco Support API (requires API credentials)
3. Web scraping public EOL notices
4. Searching cached EOL PDFs
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
from urllib.parse import quote

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/cisco_eol_lookup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'T3dC$gLp9'
}

class CiscoEoLLookup:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Cisco Support Tools base URL
        self.cisco_base = "https://www.cisco.com/c/en/us/support"
        
        # Alternative sources
        self.alternative_sources = [
            "https://www.cisco.com/c/en/us/products/collateral/switches/",
            "https://www.cisco.com/c/en/us/products/collateral/routers/",
            "https://www.cisco.com/c/en/us/products/eos-eol-listing.html"
        ]
        
    def search_cisco_eol_page(self, model):
        """Search Cisco's EoL page for model information"""
        try:
            # Try searching the EoL listing page
            search_url = f"https://www.cisco.com/c/en/us/products/eos-eol-listing.html"
            
            response = self.session.get(search_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for model in the page
                model_pattern = re.compile(re.escape(model), re.IGNORECASE)
                
                # Search in tables
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        if model_pattern.search(row.get_text()):
                            # Try to extract dates from the row
                            cells = row.find_all('td')
                            if len(cells) >= 3:
                                dates = self.extract_dates_from_text(row.get_text())
                                if dates:
                                    return dates
                                    
        except Exception as e:
            logger.debug(f"Error searching Cisco EoL page for {model}: {e}")
            
        return None
        
    def search_cisco_support_api(self, model):
        """
        Search using Cisco Support API (requires API credentials)
        This is a placeholder - actual implementation requires Cisco API access
        """
        # Cisco Support API endpoints
        api_endpoints = [
            f"https://api.cisco.com/supporttools/eox/rest/5/EOXByProductID/1/{model}",
            f"https://api.cisco.com/product/v1/information/product_ids/{model}"
        ]
        
        # Note: Actual implementation would require:
        # - OAuth2 authentication
        # - API keys from Cisco Developer Portal
        # - Proper rate limiting
        
        logger.info(f"Cisco API lookup for {model} - requires API credentials")
        return None
        
    def search_web_sources(self, model):
        """Search various web sources for EoL information"""
        eol_data = {
            'model': model,
            'announcement_date': None,
            'end_of_sale_date': None,
            'end_of_support_date': None,
            'source': None
        }
        
        # Search patterns for dates
        date_patterns = {
            'announcement': r'announced?.*?(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            'end_of_sale': r'end.of.sale.*?(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            'end_of_support': r'end.of.(support|life).*?(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
        }
        
        # Try different search queries
        search_queries = [
            f'Cisco {model} end of sale',
            f'Cisco {model} end of life',
            f'Cisco {model} EoL EoS dates',
            f'{model} end of support announcement'
        ]
        
        for query in search_queries:
            try:
                # Use a search engine API or web scraping
                # This is a simplified example
                search_url = f"https://www.google.com/search?q={quote(query)}"
                
                # Note: In production, you'd want to:
                # - Use a proper search API (Google Custom Search, Bing API, etc.)
                # - Implement rate limiting
                # - Handle CAPTCHAs
                
                logger.debug(f"Would search: {query}")
                
            except Exception as e:
                logger.error(f"Search error for {model}: {e}")
                
        return eol_data if any([eol_data['end_of_sale_date'], eol_data['end_of_support_date']]) else None
        
    def extract_dates_from_text(self, text):
        """Extract dates from text using regex patterns"""
        dates = {}
        
        # Common date formats
        date_patterns = [
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',  # MM-DD-YYYY or MM/DD/YYYY
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',  # YYYY-MM-DD or YYYY/MM/DD
            r'(\w+ \d{1,2}, \d{4})',           # Month DD, YYYY
            r'(\d{1,2} \w+ \d{4})'             # DD Month YYYY
        ]
        
        # Keywords to look for
        keywords = {
            'announcement': ['announced', 'announcement'],
            'end_of_sale': ['end of sale', 'eos', 'last day to order'],
            'end_of_support': ['end of support', 'eol', 'end of life', 'last day of support']
        }
        
        for date_type, terms in keywords.items():
            for term in terms:
                pattern = f"{term}.*?({'|'.join(date_patterns)})"
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    date_str = match.group(1)
                    parsed_date = self.parse_date_string(date_str)
                    if parsed_date:
                        dates[date_type] = parsed_date
                        break
                        
        return dates
        
    def parse_date_string(self, date_str):
        """Parse various date formats into YYYY-MM-DD"""
        date_formats = [
            '%m-%d-%Y', '%m/%d/%Y',
            '%Y-%m-%d', '%Y/%m/%d',
            '%B %d, %Y', '%b %d, %Y',
            '%d %B %Y', '%d %b %Y'
        ]
        
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
                
        return None
        
    def check_local_cache(self, model):
        """Check local cache of EOL documents"""
        cache_dir = "/var/www/html/meraki-data/cisco_eol_cache"
        
        if os.path.exists(cache_dir):
            for filename in os.listdir(cache_dir):
                if model.lower() in filename.lower():
                    filepath = os.path.join(cache_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read()
                            dates = self.extract_dates_from_text(content)
                            if dates:
                                logger.info(f"Found {model} in local cache: {filename}")
                                return dates
                    except Exception as e:
                        logger.error(f"Error reading cache file {filename}: {e}")
                        
        return None
        
    def lookup_model(self, model):
        """Main lookup function that tries various methods"""
        logger.info(f"Looking up EoL data for: {model}")
        
        # Try methods in order of preference
        methods = [
            ('Local Cache', self.check_local_cache),
            ('Cisco EoL Page', self.search_cisco_eol_page),
            ('Web Sources', self.search_web_sources),
            ('Cisco API', self.search_cisco_support_api)
        ]
        
        for method_name, method_func in methods:
            try:
                logger.debug(f"Trying {method_name} for {model}")
                result = method_func(model)
                if result:
                    logger.info(f"Found data for {model} using {method_name}")
                    return result
            except Exception as e:
                logger.error(f"Error in {method_name} for {model}: {e}")
                
            # Rate limiting
            time.sleep(1)
            
        logger.warning(f"No EoL data found for {model}")
        return None
        
    def update_database(self, model_data):
        """Update the corporate_eol table with found data"""
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        try:
            # Check if model exists
            cursor.execute("SELECT id FROM corporate_eol WHERE model = %s", (model_data['model'],))
            existing = cursor.fetchone()
            
            if existing and any([model_data.get('end_of_sale_date'), model_data.get('end_of_support_date')]):
                # Update existing record
                cursor.execute("""
                    UPDATE corporate_eol 
                    SET announcement_date = COALESCE(%s, announcement_date),
                        end_of_sale_date = COALESCE(%s, end_of_sale_date),
                        end_of_support_date = COALESCE(%s, end_of_support_date),
                        source = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE model = %s
                """, (
                    model_data.get('announcement_date'),
                    model_data.get('end_of_sale_date'),
                    model_data.get('end_of_support_date'),
                    model_data.get('source', 'automated_lookup'),
                    model_data['model']
                ))
                logger.info(f"Updated database for {model_data['model']}")
            elif not existing:
                # Insert new record
                cursor.execute("""
                    INSERT INTO corporate_eol 
                    (model, announcement_date, end_of_sale_date, end_of_support_date, source)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    model_data['model'],
                    model_data.get('announcement_date'),
                    model_data.get('end_of_sale_date'),
                    model_data.get('end_of_support_date'),
                    model_data.get('source', 'automated_lookup')
                ))
                logger.info(f"Inserted new record for {model_data['model']}")
                
            conn.commit()
            
        except Exception as e:
            logger.error(f"Database error for {model_data['model']}: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

def main():
    """Main function to process models from file"""
    lookup = CiscoEoLLookup()
    
    # Read models from file
    models_file = "/usr/local/bin/Main/datacenter_models_list.txt"
    
    if not os.path.exists(models_file):
        logger.error(f"Models file not found: {models_file}")
        return
        
    with open(models_file, 'r') as f:
        models = [line.strip() for line in f if line.strip()]
        
    logger.info(f"Processing {len(models)} models")
    
    results = {
        'found': 0,
        'not_found': 0,
        'errors': 0
    }
    
    for i, model in enumerate(models, 1):
        logger.info(f"Processing {i}/{len(models)}: {model}")
        
        try:
            result = lookup.lookup_model(model)
            if result:
                result['model'] = model
                lookup.update_database(result)
                results['found'] += 1
            else:
                results['not_found'] += 1
                
        except Exception as e:
            logger.error(f"Error processing {model}: {e}")
            results['errors'] += 1
            
        # Rate limiting - be respectful of web sources
        time.sleep(2)
        
    # Summary
    logger.info("=" * 60)
    logger.info(f"Processing complete:")
    logger.info(f"  Found EoL data: {results['found']}")
    logger.info(f"  Not found: {results['not_found']}")
    logger.info(f"  Errors: {results['errors']}")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()