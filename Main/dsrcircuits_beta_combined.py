
# Combined Beta Module for DSR Circuits
# This module includes both provider matching and the beta blueprint

import re
from fuzzywuzzy import fuzz
import logging
from flask import Blueprint, render_template, jsonify, request, current_app
from sqlalchemy import and_, or_, func
from models import db, Circuit, EnrichedCircuit, MerakiInventory
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# === PROVIDER MATCHING SYSTEM ===

class ProviderMatcher:
    """Centralized provider matching with normalization and fuzzy matching"""
    
    # Comprehensive provider mappings including all known variations
    PROVIDER_MAPPINGS = {
        # Charter/Spectrum
        'CHARTER': ['CHARTER', 'SPECTRUM', 'CHARTER COMMUNICATIONS', 'CHARTER BUSINESS'],
        'SPECTRUM': ['SPECTRUM', 'CHARTER', 'CHARTER COMMUNICATIONS', 'CHARTER BUSINESS'],
        
        # AT&T variations
        'AT&T': ['AT&T', 'ATT', 'AT&T BROADBAND', 'AT&T BROADBAND II', 'AT&T ABF', 
                 'AT&T ADI', 'AT&T ENTERPRISES LLC', 'DSR AT&T', 'NOT DSR AT&T'],
        
        # Cox variations
        'COX': ['COX', 'COX BUSINESS', 'COX BUSINESS/BOI', 'COX BUSINESS BOI', 
                'COX COMMUNICATIONS', 'COX BUSINESS BOI EXTENDED CABLE'],
        
        # Comcast variations
        'COMCAST': ['COMCAST', 'COMCAST WORKPLACE', 'COMCAST BUSINESS', 'AGG COMCAST',
                    'COMCASTAGG COMCAST', 'COMCAST CABLE COMMUNICATIONS'],
        
        # Verizon variations
        'VERIZON': ['VERIZON', 'VERIZON BUSINESS', 'VERIZON WIRELESS'],
        'VERIZON CELL': ['VZW CELL', 'VZWCELL', 'VERIZON CELL', 'VZ GATEWAY', 'VZG', 
                         'VERIZON CELLULAR', 'CELL CELL'],
        
        # CenturyLink variations
        'CENTURYLINK': ['CENTURYLINK', 'CENTURY LINK', 'QWEST', 'LUMEN', 
                        'CENTURYLINK COMMUNICATIONS', 'CENTURYLINK FIBER',
                        'CENTURYLINK FIBER PLUS', 'DSR CLINK', 'COMCASTAGG CLINK'],
        
        # Starlink
        'STARLINK': ['STARLINK', 'STAR LINK', 'SPACEX STARLINK'],
        
        # Other cellular providers
        'DIGI': ['DIGI', 'DIGI CELLULAR', 'DIG'],
        'ACCELERATED': ['ACCELERATED', 'ACCELERATED CELLULAR'],
        'INSEEGO': ['INSEEGO', 'INSEEGO CELLULAR'],
        
        # Other providers
        'SPARKLIGHT': ['SPARKLIGHT', 'CABLE ONE', 'CABLEONE'],
        'FRONTIER': ['FRONTIER', 'FRONTIER COMMUNICATIONS'],
        'WINDSTREAM': ['WINDSTREAM', 'WINDSTREAM COMMUNICATIONS'],
        'OPTIMUM': ['OPTIMUM', 'ALTICE', 'ALTICE WEST', 'ALTICE USA'],
        'ALTICE': ['ALTICE', 'OPTIMUM', 'ALTICE WEST', 'ALTICE USA'],
    }
    
    # Build reverse mapping
    REVERSE_MAPPING = {}
    for canonical, variations in PROVIDER_MAPPINGS.items():
        for variation in variations:
            REVERSE_MAPPING[variation.upper()] = canonical
    
    @classmethod
    def normalize_provider(cls, provider, preserve_original=False):
        if not provider or str(provider).lower() in ['', 'null', 'none', 'nan', 'unknown']:
            return ''
        
        cleaned = str(provider).strip()
        cleaned_upper = cleaned.upper()
        
        if cleaned_upper in cls.REVERSE_MAPPING:
            return cls.REVERSE_MAPPING[cleaned_upper]
        
        return cleaned if preserve_original else cleaned_upper
    
    @classmethod
    def providers_match(cls, provider1, provider2, threshold=80):
        if not provider1 or not provider2:
            return False, 0
        
        norm1 = cls.normalize_provider(provider1)
        norm2 = cls.normalize_provider(provider2)
        
        if norm1 == norm2:
            return True, 100
        
        ratio = fuzz.ratio(norm1, norm2)
        return ratio >= threshold, ratio

# === BETA BLUEPRINT ===

dsrcircuits_beta_bp = Blueprint('dsrcircuits_beta', __name__)

def assign_costs_improved(enriched_circuit, site_circuits):
    """Improved cost assignment logic with Cell/Satellite awareness"""
    wan1_cost = '$0.00'
    wan2_cost = '$0.00'
    wan1_match_info = {'matched': False, 'dsr_verified': False}
    wan2_match_info = {'matched': False, 'dsr_verified': False}
    
    assigned_circuits = set()
    
    # Match WAN1
    if enriched_circuit.wan1_provider:
        # Check if WAN1 is Cell/Satellite
        wan1_is_cellular = enriched_circuit.wan1_speed and enriched_circuit.wan1_speed.lower() in ['cell', 'satellite']
        
        for circuit in site_circuits:
            if not circuit.billing_monthly_cost or id(circuit) in assigned_circuits:
                continue
            
            # Check if circuit is Cell/Satellite
            circuit_is_cellular = circuit.details_ordered_service_speed and circuit.details_ordered_service_speed.lower() in ['cell', 'satellite']
            
            # Skip if one is cellular/satellite and the other isn't
            if wan1_is_cellular != circuit_is_cellular:
                continue
            
            # For non-cellular circuits, also check speed matches
            if not wan1_is_cellular and enriched_circuit.wan1_speed != circuit.details_ordered_service_speed:
                continue
            
            matches, confidence = ProviderMatcher.providers_match(
                enriched_circuit.wan1_provider, 
                circuit.provider_name
            )
            
            if matches:
                wan1_cost = f"${float(circuit.billing_monthly_cost):.2f}"
                wan1_match_info = {
                    'matched': True, 
                    'confidence': confidence,
                    'dsr_verified': circuit.data_source == 'csv_import'  # DSR data comes from CSV
                }
                assigned_circuits.add(id(circuit))
                break
    
    # Match WAN2
    if enriched_circuit.wan2_provider:
        # Check if WAN2 is Cell/Satellite
        wan2_is_cellular = enriched_circuit.wan2_speed and enriched_circuit.wan2_speed.lower() in ['cell', 'satellite']
        
        for circuit in site_circuits:
            if not circuit.billing_monthly_cost or id(circuit) in assigned_circuits:
                continue
            
            # Check if circuit is Cell/Satellite
            circuit_is_cellular = circuit.details_ordered_service_speed and circuit.details_ordered_service_speed.lower() in ['cell', 'satellite']
            
            # Skip if one is cellular/satellite and the other isn't
            if wan2_is_cellular != circuit_is_cellular:
                continue
            
            # For non-cellular circuits, also check speed matches
            if not wan2_is_cellular and enriched_circuit.wan2_speed != circuit.details_ordered_service_speed:
                continue
            
            matches, confidence = ProviderMatcher.providers_match(
                enriched_circuit.wan2_provider, 
                circuit.provider_name
            )
            
            if matches:
                wan2_cost = f"${float(circuit.billing_monthly_cost):.2f}"
                wan2_match_info = {
                    'matched': True, 
                    'confidence': confidence,
                    'dsr_verified': circuit.data_source == 'csv_import'  # DSR data comes from CSV
                }
                assigned_circuits.add(id(circuit))
                break
    
    return wan1_cost, wan2_cost, wan1_match_info, wan2_match_info

@dsrcircuits_beta_bp.route('/dsrcircuits-beta')
def dsrcircuits_beta():
    """Beta version with improved matching"""
    try:
        enriched_circuits = EnrichedCircuit.query.filter(
            ~(
                EnrichedCircuit.network_name.ilike('%hub%') |
                EnrichedCircuit.network_name.ilike('%lab%') |
                EnrichedCircuit.network_name.ilike('%voice%') |
                EnrichedCircuit.network_name.ilike('%test%')
            )
        ).order_by(EnrichedCircuit.network_name).all()
        
        grouped_data = []
        stats = {
            'total_sites': len(enriched_circuits),
            'wan1_matched': 0,
            'wan2_matched': 0,
            'improvements': []
        }
        
        for circuit in enriched_circuits:
            site_circuits = Circuit.query.filter(
                func.lower(Circuit.site_name) == func.lower(circuit.network_name),
                Circuit.status == 'Enabled'
            ).all()
            
            wan1_cost, wan2_cost, wan1_info, wan2_info = assign_costs_improved(circuit, site_circuits)
            
            if wan1_info['matched']:
                stats['wan1_matched'] += 1
            if wan2_info['matched']:
                stats['wan2_matched'] += 1
                
            # Track Starlink improvements
            if circuit.wan2_provider and 'starlink' in circuit.wan2_provider.lower():
                if wan2_info['matched'] and wan2_cost != '$0.00':
                    stats['improvements'].append({
                        'site': circuit.network_name,
                        'provider': circuit.wan2_provider,
                        'cost': wan2_cost
                    })
            
            grouped_data.append({
                'network_name': circuit.network_name,
                'device_tags': circuit.device_tags or [],
                'wan1': {
                    'provider': circuit.wan1_provider or '',
                    'speed': circuit.wan1_speed or '',
                    'monthly_cost': wan1_cost,
                    'circuit_role': circuit.wan1_circuit_role or 'Primary',
                    'confirmed': circuit.wan1_confirmed or False,
                    'match_info': wan1_info
                },
                'wan2': {
                    'provider': circuit.wan2_provider or '',
                    'speed': circuit.wan2_speed or '',
                    'monthly_cost': wan2_cost,
                    'circuit_role': circuit.wan2_circuit_role or 'Secondary',
                    'confirmed': circuit.wan2_confirmed or False,
                    'match_info': wan2_info
                }
            })
        
        # Use the existing dsrcircuits.html template with beta indicator
        return render_template('dsrcircuits_beta_no_roles.html', 
                             grouped_data=grouped_data,
                             beta_mode=True,
                             stats=stats)
        
    except Exception as e:
        logger.error(f"Error in beta dsrcircuits: {e}")
        return render_template('dsrcircuits_beta_no_roles.html', error=f"Beta Error: {e}")
