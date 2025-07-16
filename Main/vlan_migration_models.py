"""
Database models for VLAN Migration tracking
Add these to your existing models.py file
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from models import db

class VlanMigrationHistory(db.Model):
    """Track VLAN migration jobs"""
    __tablename__ = 'vlan_migration_history'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String(50), unique=True, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    networks_total = Column(Integer, nullable=False)
    networks_completed = Column(Integer, default=0)
    networks_failed = Column(Integer, default=0)
    status = Column(String(20), nullable=False)  # initializing, running, completed, failed
    initiated_by = Column(String(100))
    notes = Column(Text)
    
    # Relationships
    logs = relationship('VlanMigrationLog', backref='job', lazy='dynamic')
    network_details = relationship('VlanMigrationNetworkDetail', backref='job', lazy='dynamic')
    
    def __repr__(self):
        return f'<VlanMigrationHistory {self.job_id}>'

class VlanMigrationLog(db.Model):
    """Store migration console logs"""
    __tablename__ = 'vlan_migration_logs'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String(50), ForeignKey('vlan_migration_history.job_id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    phase = Column(String(20))  # backup, clear, migrate, restore, complete, error
    network = Column(String(100))
    message = Column(Text)
    
    def __repr__(self):
        return f'<VlanMigrationLog {self.job_id} - {self.phase}>'

class VlanMigrationNetworkDetail(db.Model):
    """Track individual network migration details"""
    __tablename__ = 'vlan_migration_network_details'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String(50), ForeignKey('vlan_migration_history.job_id'), nullable=False)
    network_id = Column(String(50), nullable=False)
    network_name = Column(String(100))
    migration_status = Column(String(20))  # pending, running, success, failed
    backup_file = Column(String(200))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    firewall_rules_before = Column(Integer)
    firewall_rules_after = Column(Integer)
    validation_status = Column(String(20))  # passed, failed, warning
    validation_details = Column(Text)
    error_message = Column(Text)
    
    def __repr__(self):
        return f'<VlanMigrationNetworkDetail {self.network_name}>'

class VlanMigrationTemplate(db.Model):
    """Store VLAN migration templates"""
    __tablename__ = 'vlan_migration_templates'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    firewall_template_file = Column(String(200))
    vlan_mappings = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f'<VlanMigrationTemplate {self.name}>'

# SQL to create tables
CREATE_TABLES_SQL = """
-- VLAN Migration History
CREATE TABLE IF NOT EXISTS vlan_migration_history (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(50) UNIQUE NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    networks_total INTEGER NOT NULL,
    networks_completed INTEGER DEFAULT 0,
    networks_failed INTEGER DEFAULT 0,
    status VARCHAR(20) NOT NULL,
    initiated_by VARCHAR(100),
    notes TEXT
);

-- VLAN Migration Logs
CREATE TABLE IF NOT EXISTS vlan_migration_logs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(50) NOT NULL REFERENCES vlan_migration_history(job_id),
    timestamp TIMESTAMP NOT NULL,
    phase VARCHAR(20),
    network VARCHAR(100),
    message TEXT
);

-- VLAN Migration Network Details
CREATE TABLE IF NOT EXISTS vlan_migration_network_details (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(50) NOT NULL REFERENCES vlan_migration_history(job_id),
    network_id VARCHAR(50) NOT NULL,
    network_name VARCHAR(100),
    migration_status VARCHAR(20),
    backup_file VARCHAR(200),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    firewall_rules_before INTEGER,
    firewall_rules_after INTEGER,
    validation_status VARCHAR(20),
    validation_details TEXT,
    error_message TEXT
);

-- VLAN Migration Templates
CREATE TABLE IF NOT EXISTS vlan_migration_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    firewall_template_file VARCHAR(200),
    vlan_mappings TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE
);

-- Indexes for performance
CREATE INDEX idx_vlan_migration_history_status ON vlan_migration_history(status);
CREATE INDEX idx_vlan_migration_history_start_time ON vlan_migration_history(start_time DESC);
CREATE INDEX idx_vlan_migration_logs_job_id ON vlan_migration_logs(job_id);
CREATE INDEX idx_vlan_migration_network_details_job_id ON vlan_migration_network_details(job_id);
CREATE INDEX idx_vlan_migration_network_details_network_id ON vlan_migration_network_details(network_id);
"""