#!/usr/bin/env python3
"""
Provider matching integration module for nightly scripts
This module provides enhanced provider matching using the provider_mappings table
"""

import re
from thefuzz import fuzz
import logging

logger = logging.getLogger(__name__)

class ProviderMatcher:
    """Enhanced provider matcher with database mapping support"""
    
    def __init__(self, db_conn):
        self.conn = db_conn
        self.mappings = self._load_mappings()
        logger.info(f"Loaded {len(self.mappings)} provider mappings")
    
    def _load_mappings(self):
        """Load provider mappings from database"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT LOWER(dsr_provider) as dsr_lower, 
                       arin_provider, 
                       mapping_type, 
                       confidence_score
                FROM provider_mappings
                WHERE mapping_type != 'ignore'
                ORDER BY confidence_score DESC
            """)
            
            mappings = {}
            for row in cursor.fetchall():
                dsr_lower = row[0]
                if dsr_lower not in mappings:
                    mappings[dsr_lower] = []
                mappings[dsr_lower].append({
                    'arin_provider': row[1],
                    'mapping_type': row[2],
                    'confidence': row[3]
                })
            
            return mappings
        except Exception as e:
            logger.warning(f"Could not load provider mappings: {e}")
            return {}
        finally:
            cursor.close()
    
    def normalize_provider(self, provider):
        """Enhanced provider normalization"""
        if not provider:
            return ""
        
        # Convert to lowercase and strip
        provider = str(provider).lower().strip()
        
        # Handle EB2- prefix
        if provider.startswith('eb2-'):
            provider = provider[4:]
            provider = re.sub(r'\s*(dsl|fiber|cable|kinetic)$', '', provider)
        
        # Remove other prefixes
        provider = re.sub(r'^(dsr|agg|comcastagg|not\s+dsr|--|-)\s+', '', provider)
        
        # Remove service suffixes
        provider = re.sub(r'\s*(extended\s+cable|workplace|broadband\s+ii|fiber\s+plus|/boi|/embarq|/qwest|cable|dsl|fiber)$', '', provider)
        
        # Clean special characters
        provider = re.sub(r'[^\w\s&/-]', ' ', provider)
        provider = re.sub(r'\s+', ' ', provider).strip()
        
        return provider
    
    def match_providers(self, dsr_provider, arin_provider, circuit_purpose='Primary', use_fuzzy=True):
        """
        Enhanced provider matching with mapping table support
        Returns: (is_match, confidence_score, match_reason)
        """
        if not dsr_provider:
            return False, 0, "No DSR provider"
        
        if not arin_provider:
            return False, 0, "No ARIN provider"
        
        # Direct match
        if dsr_provider.lower().strip() == arin_provider.lower().strip():
            return True, 100, "Direct match"
        
        # Check mapping table
        dsr_lower = dsr_provider.lower().strip()
        if dsr_lower in self.mappings:
            for mapping in self.mappings[dsr_lower]:
                if mapping['arin_provider'].lower() == arin_provider.lower():
                    return True, mapping['confidence'], f"Mapped ({mapping['mapping_type']})"
        
        # Normalize and try again
        dsr_norm = self.normalize_provider(dsr_provider)
        arin_norm = self.normalize_provider(arin_provider)
        
        if dsr_norm == arin_norm:
            return True, 95, "Normalized match"
        
        # Check mapping with normalized names
        if dsr_norm in self.mappings:
            for mapping in self.mappings[dsr_norm]:
                if self.normalize_provider(mapping['arin_provider']) == arin_norm:
                    return True, mapping['confidence'], f"Normalized mapped ({mapping['mapping_type']})"
        
        # Handle conflict resolution for secondary circuits
        if circuit_purpose == 'Secondary':
            # Common conflict patterns
            if 'comcast' in dsr_norm and arin_provider == 'AT&T':
                return True, 70, "Secondary circuit conflict (trust DSR)"
            if 'cox' in dsr_norm and arin_provider in ['AT&T', 'Verizon']:
                return True, 70, "Secondary circuit conflict (trust DSR)"
            if 'spectrum' in dsr_norm and arin_provider == 'AT&T':
                return True, 70, "Secondary circuit conflict (trust DSR)"
        
        # Fuzzy matching
        if use_fuzzy:
            score = max(
                fuzz.ratio(dsr_norm, arin_norm),
                fuzz.partial_ratio(dsr_norm, arin_norm),
                fuzz.token_sort_ratio(dsr_norm, arin_norm)
            )
            
            if score >= 80:
                return True, score, f"Fuzzy match ({score}%)"
            elif score >= 60:
                return False, score, f"Possible match ({score}%)"
        
        return False, 0, "No match found"
    
    def get_canonical_provider(self, provider):
        """Get the canonical provider name from mappings"""
        if not provider:
            return provider
        
        provider_lower = provider.lower().strip()
        
        # Check if it's a known DSR provider
        if provider_lower in self.mappings:
            # Return the first high-confidence mapping
            for mapping in self.mappings[provider_lower]:
                if mapping['confidence'] >= 90:
                    return mapping['arin_provider']
        
        # Check normalized
        provider_norm = self.normalize_provider(provider)
        if provider_norm in self.mappings:
            for mapping in self.mappings[provider_norm]:
                if mapping['confidence'] >= 90:
                    return mapping['arin_provider']
        
        # Return original if no mapping found
        return provider