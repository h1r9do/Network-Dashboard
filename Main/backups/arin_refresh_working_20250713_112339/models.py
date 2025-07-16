#!/usr/bin/env python3
"""
Database models for DSR Circuits Application
SQLAlchemy models for optimized database operations
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Index, text
import json

db = SQLAlchemy()

class Circuit(db.Model):
    """Circuit data model optimized for fast queries"""
    
    __tablename__ = 'circuits'
    
    id = db.Column(db.Integer, primary_key=True)
    record_number = db.Column(db.String(50))
    site_name = db.Column(db.String(100), nullable=False, index=True)
    site_id = db.Column(db.String(50))
    circuit_purpose = db.Column(db.String(50), index=True)
    status = db.Column(db.String(100), index=True)
    substatus = db.Column(db.String(100))
    provider_name = db.Column(db.String(100), index=True)
    details_service_speed = db.Column(db.String(100))
    details_ordered_service_speed = db.Column(db.String(100))
    billing_monthly_cost = db.Column(db.Numeric(10, 2))
    ip_address_start = db.Column(db.String(45))  # Support IPv6
    date_record_updated = db.Column(db.DateTime, index=True)
    milestone_service_activated = db.Column(db.DateTime)
    assigned_to = db.Column(db.String(100))
    sctask = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_source = db.Column(db.String(50), default='csv_import')
    
    # Additional fields
    address_1 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(10))
    zipcode = db.Column(db.String(20))
    primary_contact_name = db.Column(db.String(100))
    primary_contact_email = db.Column(db.String(100))
    billing_install_cost = db.Column(db.Numeric(10, 2))
    milestone_enabled = db.Column(db.DateTime)
    target_enablement_date = db.Column(db.Date)
    details_provider = db.Column(db.String(100))
    details_provider_phone = db.Column(db.String(50))
    billing_account = db.Column(db.String(100))
    fingerprint = db.Column(db.String(255), index=True)
    last_csv_file = db.Column(db.String(100))
    manual_override = db.Column(db.Boolean, default=False, index=True)  # Prevents DSR pull from overwriting
    manual_override_date = db.Column(db.DateTime)  # When the manual override was set
    manual_override_by = db.Column(db.String(100))  # Who set the manual override
    notes = db.Column(db.Text)  # Free-form notes field
    
    # Relationships
    history = db.relationship('CircuitHistory', backref='circuit', lazy='dynamic')
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'site_name': self.site_name,
            'site_id': self.site_id,
            'circuit_purpose': self.circuit_purpose,
            'status': self.status,
            'substatus': self.substatus,
            'provider_name': self.provider_name,
            'details_service_speed': self.details_service_speed,
            'billing_monthly_cost': float(self.billing_monthly_cost) if self.billing_monthly_cost else None,
            'ip_address_start': self.ip_address_start,
            'date_record_updated': self.date_record_updated.isoformat() if self.date_record_updated else None,
            'assigned_to': self.assigned_to,
            'sctask': self.sctask,
            'city': self.city,
            'state': self.state,
            'notes': self.notes
        }
    
    @staticmethod
    def get_status_counts():
        """Get count of circuits by status - optimized query"""
        from sqlalchemy import func
        return db.session.query(
            Circuit.status,
            func.count(Circuit.id).label('count')
        ).group_by(Circuit.status).all()
    
    @staticmethod
    def get_recent_enablements(days=30):
        """Get recently enabled circuits"""
        from sqlalchemy import and_, or_
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        enabled_statuses = ['enabled', 'service activated', 'circuit enabled']
        
        return db.session.query(Circuit).filter(
            and_(
                Circuit.milestone_enabled >= cutoff_date,
                or_(*[Circuit.status.ilike(f'%{status}%') for status in enabled_statuses])
            )
        ).order_by(Circuit.milestone_enabled.desc()).all()

class CircuitHistory(db.Model):
    """Circuit change history for tracking modifications"""
    
    __tablename__ = 'circuit_history'
    
    id = db.Column(db.Integer, primary_key=True)
    circuit_id = db.Column(db.Integer, db.ForeignKey('circuits.id'), nullable=False, index=True)
    change_date = db.Column(db.Date, nullable=False, index=True)
    change_type = db.Column(db.String(50))  # 'enabled', 'status_change', 'provider_change'
    field_changed = db.Column(db.String(100))
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    csv_file_source = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'circuit_id': self.circuit_id,
            'change_date': self.change_date.isoformat() if self.change_date else None,
            'change_type': self.change_type,
            'field_changed': self.field_changed,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'csv_file_source': self.csv_file_source
        }

class DailySummary(db.Model):
    """Daily summary statistics for performance"""
    
    __tablename__ = 'daily_summaries'
    
    id = db.Column(db.Integer, primary_key=True)
    summary_date = db.Column(db.Date, nullable=False, unique=True, index=True)
    total_circuits = db.Column(db.Integer)
    enabled_count = db.Column(db.Integer)
    ready_count = db.Column(db.Integer)
    customer_action_count = db.Column(db.Integer)
    construction_count = db.Column(db.Integer)
    planning_count = db.Column(db.Integer)
    csv_file_processed = db.Column(db.String(100))
    processing_time_seconds = db.Column(db.Numeric(10, 3))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'summary_date': self.summary_date.isoformat() if self.summary_date else None,
            'total_circuits': self.total_circuits,
            'enabled_count': self.enabled_count,
            'ready_count': self.ready_count,
            'customer_action_count': self.customer_action_count,
            'construction_count': self.construction_count,
            'planning_count': self.planning_count,
            'processing_time_seconds': float(self.processing_time_seconds) if self.processing_time_seconds else None
        }

class ProviderMapping(db.Model):
    """Provider name mappings for normalization"""
    
    __tablename__ = 'provider_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    original_name = db.Column(db.String(200), nullable=False)
    canonical_name = db.Column(db.String(100), nullable=False)
    mapping_type = db.Column(db.String(50))  # 'manual', 'ip_lookup', 'fuzzy_match'
    confidence_score = db.Column(db.Numeric(3, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_provider_mapping_unique', 'original_name', 'canonical_name', unique=True),
    )
    
    @staticmethod
    def get_canonical_name(original_name):
        """Get canonical provider name with caching"""
        if not original_name:
            return None
            
        mapping = ProviderMapping.query.filter_by(
            original_name=original_name.lower().strip()
        ).first()
        
        return mapping.canonical_name if mapping else original_name

class CircuitAssignment(db.Model):
    """Circuit assignments for team tracking"""
    
    __tablename__ = 'circuit_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(100), nullable=False, index=True)
    sctask = db.Column(db.String(50), index=True)
    assigned_to = db.Column(db.String(100))
    assignment_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='active')
    notes = db.Column(db.Text)
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_assignment_unique', 'site_name', 'sctask', unique=True),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'site_name': self.site_name,
            'sctask': self.sctask,
            'assigned_to': self.assigned_to,
            'assignment_date': self.assignment_date.isoformat() if self.assignment_date else None,
            'status': self.status,
            'notes': self.notes
        }


class NewStore(db.Model):
    """Track new stores being built"""
    __tablename__ = 'new_stores'
    
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    target_opening_date = db.Column(db.Date)  # Target Opening Date (TOD)
    target_opening_date_text = db.Column(db.String(50))  # For storing "TBD" or other text
    added_date = db.Column(db.DateTime, default=datetime.utcnow)
    added_by = db.Column(db.String(100), default='dashboard_user')
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, index=True)
    meraki_network_found = db.Column(db.Boolean, default=False)
    meraki_found_date = db.Column(db.DateTime)
    # Additional fields from Excel
    region = db.Column(db.String(100))
    city = db.Column(db.String(100))
    state = db.Column(db.String(10))
    project_status = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'site_name': self.site_name,
            'target_opening_date': self.target_opening_date.isoformat() if self.target_opening_date else None,
            'target_opening_date_text': self.target_opening_date_text,
            'added_date': self.added_date.isoformat() if self.added_date else None,
            'added_by': self.added_by,
            'notes': self.notes,
            'region': self.region,
            'city': self.city,
            'state': self.state,
            'project_status': self.project_status,
            'is_active': self.is_active,
            'meraki_network_found': self.meraki_network_found,
            'meraki_found_date': self.meraki_found_date.isoformat() if self.meraki_found_date else None
        }


class SwitchPortClient(db.Model):
    """Switch port client information for network visibility"""
    
    __tablename__ = 'switch_port_clients'
    
    id = db.Column(db.Integer, primary_key=True)
    store_name = db.Column(db.String(100), index=True)
    switch_name = db.Column(db.String(100))
    switch_serial = db.Column(db.String(50), index=True)
    port_id = db.Column(db.String(20))
    hostname = db.Column(db.String(200))
    ip_address = db.Column(db.String(45))
    mac_address = db.Column(db.String(17), index=True)
    vlan = db.Column(db.Integer)
    manufacturer = db.Column(db.String(100))
    description = db.Column(db.Text)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('switch_serial', 'port_id', 'mac_address', name='_switch_port_mac_uc'),
    )
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'store_name': self.store_name,
            'switch_name': self.switch_name,
            'switch_serial': self.switch_serial,
            'port_id': self.port_id,
            'hostname': self.hostname,
            'ip_address': self.ip_address,
            'mac_address': self.mac_address,
            'vlan': self.vlan,
            'manufacturer': self.manufacturer,
            'description': self.description,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class InventoryDevice(db.Model):
    """Meraki device inventory for tracking equipment"""
    
    __tablename__ = 'inventory_devices'
    
    id = db.Column(db.Integer, primary_key=True)
    serial = db.Column(db.String(50), nullable=False, unique=True, index=True)
    model = db.Column(db.String(50), nullable=False, index=True)
    organization = db.Column(db.String(100), nullable=False, index=True)
    network_id = db.Column(db.String(50))
    network_name = db.Column(db.String(100))
    name = db.Column(db.String(100))
    mac = db.Column(db.String(20))
    lan_ip = db.Column(db.String(45))
    firmware = db.Column(db.String(50))
    product_type = db.Column(db.String(50))
    tags = db.Column(db.Text)  # JSON string
    notes = db.Column(db.Text)
    details = db.Column(db.Text)  # JSON string for additional data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'serial': self.serial,
            'model': self.model,
            'device_model': self.model,  # For compatibility
            'organization': self.organization,
            'networkId': self.network_id,
            'networkName': self.network_name,
            'name': self.name,
            'mac': self.mac,
            'lanIp': self.lan_ip,
            'firmware': self.firmware,
            'productType': self.product_type,
            'tags': json.loads(self.tags) if self.tags else [],
            'notes': self.notes,
            'details': json.loads(self.details) if self.details else {}
        }

class InventorySummary(db.Model):
    """Device model summary with lifecycle information"""
    
    __tablename__ = 'inventory_summary'
    
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(50), nullable=False, unique=True, index=True)
    total_count = db.Column(db.Integer, default=0)
    org_counts = db.Column(db.Text)  # JSON string
    announcement_date = db.Column(db.String(20))
    end_of_sale = db.Column(db.String(20))
    end_of_support = db.Column(db.String(20))
    highlight = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'model': self.model,
            'total': self.total_count,
            'org_counts': json.loads(self.org_counts) if self.org_counts else {},
            'announcement_date': self.announcement_date or '',
            'end_of_sale': self.end_of_sale or '',
            'end_of_support': self.end_of_support or '',
            'highlight': self.highlight or ''
        }

class EnrichedCircuit(db.Model):
    """Enriched circuit data with Meraki device information"""
    
    __tablename__ = 'enriched_circuits'
    
    id = db.Column(db.Integer, primary_key=True)
    network_name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    device_tags = db.Column(db.ARRAY(db.String))
    wan1_provider = db.Column(db.String(255))
    wan1_speed = db.Column(db.String(100))
    wan1_circuit_role = db.Column(db.String(50), default='Primary')
    wan1_confirmed = db.Column(db.Boolean, default=False)
    wan2_provider = db.Column(db.String(255))
    wan2_speed = db.Column(db.String(100))
    wan2_circuit_role = db.Column(db.String(50), default='Secondary')
    wan2_confirmed = db.Column(db.Boolean, default=False)
    wan1_ip = db.Column(db.String(45))
    wan2_ip = db.Column(db.String(45))
    pushed_to_meraki = db.Column(db.Boolean, default=False)
    pushed_date = db.Column(db.DateTime)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'network_name': self.network_name,
            'device_tags': self.device_tags or [],
            'wan1': {
                'provider': self.wan1_provider,
                'speed': self.wan1_speed,
                'circuit_role': self.wan1_circuit_role,
                'confirmed': self.wan1_confirmed
            },
            'wan2': {
                'provider': self.wan2_provider,
                'speed': self.wan2_speed,
                'circuit_role': self.wan2_circuit_role,
                'confirmed': self.wan2_confirmed
            },
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

class MerakiInventory(db.Model):
    """Meraki device inventory from API"""
    
    __tablename__ = 'meraki_inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    network_id = db.Column(db.String(50), index=True)
    network_name = db.Column(db.String(100), index=True)
    device_serial = db.Column(db.String(50), unique=True, index=True)
    device_model = db.Column(db.String(50))
    device_name = db.Column(db.String(100))
    device_tags = db.Column(db.ARRAY(db.String))  # PostgreSQL array
    wan1_ip = db.Column(db.String(45))
    wan2_ip = db.Column(db.String(45))
    wan1_assignment = db.Column(db.String(255))
    wan2_assignment = db.Column(db.String(255))
    wan1_arin_provider = db.Column(db.String(255))
    wan2_arin_provider = db.Column(db.String(255))
    wan1_provider_comparison = db.Column(db.String(50))
    wan2_provider_comparison = db.Column(db.String(50))
    wan1_provider_label = db.Column(db.String(255))
    wan1_speed_label = db.Column(db.String(100))
    wan2_provider_label = db.Column(db.String(255))
    wan2_speed_label = db.Column(db.String(100))
    device_notes = db.Column(db.Text)
    organization_name = db.Column(db.String(100))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'network_id': self.network_id,
            'network_name': self.network_name,
            'device_serial': self.device_serial,
            'device_model': self.device_model,
            'device_name': self.device_name,
            'device_tags': json.loads(self.device_tags) if self.device_tags else [],
            'wan1_ip': self.wan1_ip,
            'wan2_ip': self.wan2_ip,
            'organization': self.organization_name,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

class PerformanceMetric(db.Model):
    """Performance monitoring metrics for API endpoints"""
    
    __tablename__ = 'performance_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    endpoint_name = db.Column(db.String(255), nullable=False, index=True)
    endpoint_method = db.Column(db.String(10), default='GET')
    endpoint_params = db.Column(db.Text)  # JSON string of parameters
    query_execution_time_ms = db.Column(db.Integer, nullable=False)
    data_size_bytes = db.Column(db.Integer)
    data_rows_returned = db.Column(db.Integer)
    response_status = db.Column(db.Integer, nullable=False)
    error_message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    module_category = db.Column(db.String(100))
    db_query_count = db.Column(db.Integer)
    cache_hit = db.Column(db.Boolean, default=False)
    user_agent = db.Column(db.String(255))
    is_monitoring = db.Column(db.Boolean, default=True)
    
    __table_args__ = (
        Index('idx_performance_timestamp_endpoint', 'timestamp', 'endpoint_name'),
        Index('idx_performance_endpoint_status', 'endpoint_name', 'response_status'),
        Index('idx_performance_module_timestamp', 'module_category', 'timestamp'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'endpoint_name': self.endpoint_name,
            'endpoint_method': self.endpoint_method,
            'endpoint_params': json.loads(self.endpoint_params) if self.endpoint_params else {},
            'query_execution_time_ms': self.query_execution_time_ms,
            'data_size_bytes': self.data_size_bytes,
            'data_rows_returned': self.data_rows_returned,
            'response_status': self.response_status,
            'error_message': self.error_message,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'module_category': self.module_category,
            'cache_hit': self.cache_hit,
            'is_monitoring': self.is_monitoring
        }

class NetworkDevice(db.Model):
    """Network devices from SSH inventory collection"""
    
    __tablename__ = 'network_devices'
    
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False, unique=True, index=True)
    hostname = db.Column(db.String(100), index=True)
    collection_timestamp = db.Column(db.DateTime)
    data_source = db.Column(db.String(50), default='ssh_inventory')
    device_type = db.Column(db.String(50))  # 'master' for standalone or primary chassis device
    interfaces_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    hardware_components = db.relationship('HardwareComponent', backref='parent_device', lazy='dynamic', cascade='all, delete-orphan')
    chassis_blades = db.relationship('ChassisBlade', backref='parent_device', lazy='dynamic', cascade='all, delete-orphan')
    sfp_modules = db.relationship('SfpModule', backref='parent_device', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'hostname': self.hostname,
            'collection_timestamp': self.collection_timestamp.isoformat() if self.collection_timestamp else None,
            'data_source': self.data_source,
            'device_type': self.device_type,
            'interfaces_count': self.interfaces_count,
            'hardware_components_count': self.hardware_components.count(),
            'chassis_blades_count': self.chassis_blades.count(),
            'sfp_modules_count': self.sfp_modules.count()
        }

class HardwareComponent(db.Model):
    """Hardware inventory components (typically SFPs on interfaces)"""
    
    __tablename__ = 'hardware_components'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('network_devices.id'), nullable=False, index=True)
    name = db.Column(db.String(100))  # Interface name like "GigabitEthernet1/0/21"
    description = db.Column(db.String(255))  # "1000BaseSX SFP"
    pid = db.Column(db.String(50))  # Product ID
    vid = db.Column(db.String(50))  # Version ID
    serial_number = db.Column(db.String(50))
    component_type = db.Column(db.String(50), default='SFP')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'name': self.name,
            'description': self.description,
            'pid': self.pid,
            'vid': self.vid,
            'serial_number': self.serial_number,
            'component_type': self.component_type
        }

class ChassisBlade(db.Model):
    """Chassis blade/line card information"""
    
    __tablename__ = 'chassis_blades'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('network_devices.id'), nullable=False, index=True)
    module_number = db.Column(db.String(10))  # "1", "2", "3", etc.
    ports = db.Column(db.String(10))  # "48"
    card_type = db.Column(db.String(255))  # "10/100/1000BaseT Premium POE E Series"
    model = db.Column(db.String(100))  # "WS-X4748-RJ45V+E"
    serial_number = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'module_number': self.module_number,
            'ports': self.ports,
            'card_type': self.card_type,
            'model': self.model,
            'serial_number': self.serial_number
        }

class SfpModule(db.Model):
    """SFP module information from detailed optics inventory"""
    
    __tablename__ = 'sfp_modules'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('network_devices.id'), nullable=False, index=True)
    interface = db.Column(db.String(100))  # Interface designation
    module_type = db.Column(db.String(255))  # SFP type/description
    status = db.Column(db.String(50))  # "present", "not present"
    product_id = db.Column(db.String(100))  # Product identifier
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'interface': self.interface,
            'module_type': self.module_type,
            'status': self.status,
            'product_id': self.product_id
        }
class NetworkVlan(db.Model):
    """Network VLAN configurations"""
    __tablename__ = 'network_vlans'
    
    id = db.Column(db.Integer, primary_key=True)
    network_id = db.Column(db.String(100), nullable=False)
    network_name = db.Column(db.String(100), nullable=False, index=True)
    vlan_id = db.Column(db.Integer, nullable=False)
    vlan_name = db.Column(db.String(100))
    name = db.Column(db.String(100))  # Alias for vlan_name
    appliance_ip = db.Column(db.String(45))
    subnet = db.Column(db.String(50))
    subnet_mask = db.Column(db.String(50))
    dhcp_handling = db.Column(db.String(50))
    dhcp_mode = db.Column(db.String(50))  # Alias for dhcp_handling
    dhcp_lease_time = db.Column(db.String(50))
    dhcp_boot_options_enabled = db.Column(db.Boolean)
    dns_nameservers = db.Column(db.Text)
    reserved_ip_ranges = db.Column(db.Text)
    fixed_ip_assignments = db.Column(db.Text)
    parent_network = db.Column(db.String(50), index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('network_id', 'vlan_id', name='uq_network_vlan'),
        Index('idx_parent_network', 'parent_network'),
        Index('idx_subnet', 'subnet'),
    )

# BETA TESTING MODELS - Identical to production but with _beta suffix

class EnrichedCircuitBeta(db.Model):
    """Beta testing version of enriched circuit data"""
    
    __tablename__ = 'enriched_circuits_beta'
    
    id = db.Column(db.Integer, primary_key=True)
    network_name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    device_tags = db.Column(db.ARRAY(db.String))
    wan1_provider = db.Column(db.String(255))
    wan1_speed = db.Column(db.String(100))
    wan1_circuit_role = db.Column(db.String(50), default='Primary')
    wan1_confirmed = db.Column(db.Boolean, default=False)
    wan2_provider = db.Column(db.String(255))
    wan2_speed = db.Column(db.String(100))
    wan2_circuit_role = db.Column(db.String(50), default='Secondary')
    wan2_confirmed = db.Column(db.Boolean, default=False)
    pushed_to_meraki = db.Column(db.Boolean, default=False)
    pushed_date = db.Column(db.DateTime)
    wan1_ip = db.Column(db.String(45))
    wan2_ip = db.Column(db.String(45))
    wan1_arin_org = db.Column(db.String(200))
    wan2_arin_org = db.Column(db.String(200))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MerakiInventoryBeta(db.Model):
    """Beta testing version of Meraki device inventory"""
    
    __tablename__ = 'meraki_inventory_beta'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_name = db.Column(db.String(255))
    network_id = db.Column(db.String(100), index=True)
    network_name = db.Column(db.String(255), index=True)
    device_serial = db.Column(db.String(100), unique=True, index=True)
    device_model = db.Column(db.String(100))
    device_name = db.Column(db.String(255))
    device_tags = db.Column(db.ARRAY(db.String))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    wan1_ip = db.Column(db.String(45))
    wan2_ip = db.Column(db.String(45))
    wan1_assignment = db.Column(db.String(20))
    wan2_assignment = db.Column(db.String(20))
    wan1_arin_provider = db.Column(db.String(100))
    wan2_arin_provider = db.Column(db.String(100))
    wan1_provider_comparison = db.Column(db.String(20))
    wan2_provider_comparison = db.Column(db.String(20))
    wan1_provider_label = db.Column(db.String(255))
    wan1_speed_label = db.Column(db.String(100))
    wan2_provider_label = db.Column(db.String(255))
    wan2_speed_label = db.Column(db.String(100))
    device_notes = db.Column(db.Text)
    ddns_enabled = db.Column(db.Boolean, default=False)
    ddns_url = db.Column(db.String(255))
    wan1_public_ip = db.Column(db.String(45))
    wan2_public_ip = db.Column(db.String(45))
