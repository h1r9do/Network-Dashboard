#!/usr/bin/env python3
"""
Integrated DSR Circuits Application with Database and Firewall Management
Database-driven circuit management with Meraki firewall rule management
"""

import os
import sys
from datetime import datetime
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
import redis
import logging
from sqlalchemy import create_engine, text

# Add current directory to path for imports (prioritize Main directory)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Note: Removed test directory path to ensure Main directory modules are used

from config import config, get_redis_connection
from models import db, Circuit, CircuitHistory, DailySummary, ProviderMapping, CircuitAssignment

# Import existing modules
from dsrcircuits_blueprint import dsrcircuits_bp
from status import status_bp
from historical import historical_bp
from inventory import inventory_bp
from reports import reports_bp
from new_stores import new_stores_bp
from performance import performance_bp
from tags import tags_bp
from system_health import system_health_bp
from eol_routes import eol_bp
from switch_visibility import switch_visibility_bp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app(config_name='production'):
    """Application factory function with database integration"""
    app = Flask(__name__, 
                template_folder='/usr/local/bin/templates',
                static_folder='/usr/local/bin/static')
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize cache
    cache = Cache()
    cache.init_app(app)
    
    # Store cache in app context for blueprints
    app.cache = cache
    
    # Test Redis connection
    redis_conn = get_redis_connection()
    if redis_conn:
        logger.info("✅ Redis connection successful")
        app.redis = redis_conn
    else:
        logger.warning("⚠️ Redis connection failed - caching disabled")
        app.redis = None
    
    # Register blueprints (removing URL prefixes for production)
    app.register_blueprint(dsrcircuits_bp)
    app.register_blueprint(status_bp)
    app.register_blueprint(historical_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(new_stores_bp)
    app.register_blueprint(performance_bp)
    app.register_blueprint(tags_bp)
    app.register_blueprint(system_health_bp)
    app.register_blueprint(eol_bp)
    app.register_blueprint(switch_visibility_bp)
    
    # Enhanced API endpoints for database-driven functionality
    @app.route('/api/health')
    def health_check():
        """Health check endpoint"""
        try:
            # Test database connection
            db.session.execute(text('SELECT 1'))
            db_status = "healthy"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        # Test Redis connection
        try:
            if app.redis and app.redis.ping():
                redis_status = "healthy"
            else:
                redis_status = "unavailable"
        except:
            redis_status = "unavailable"
        
        return jsonify({
            'status': 'healthy' if db_status == 'healthy' else 'degraded',
            'database': db_status,
            'cache': redis_status,
            'version': '2.0.0-production-database',
            'timestamp': datetime.now().isoformat()
        })
    
    @app.route('/api/stats/quick')
    def quick_stats():
        """Fast statistics using database queries"""
        try:
            stats = {
                'total_circuits': Circuit.query.count(),
                'status_breakdown': {},
                'database': {}
            }
            
            # Get status counts efficiently
            status_counts = Circuit.get_status_counts()
            for status, count in status_counts:
                stats['status_breakdown'][status or 'Unknown'] = count
            
            # Recent enablements
            recent_enabled = Circuit.get_recent_enablements(days=7)
            stats['recent_enablements_7d'] = len(recent_enabled)
            
            # Additional useful stats
            stats['database']['total_history_records'] = CircuitHistory.query.count()
            stats['database']['total_assignments'] = CircuitAssignment.query.count()
            
            # Get latest daily summary
            latest_summary = DailySummary.query.order_by(DailySummary.summary_date.desc()).first()
            if latest_summary:
                stats['latest_summary'] = {
                    'date': latest_summary.summary_date.isoformat(),
                    'total_circuits': latest_summary.total_circuits,
                    'enabled_count': latest_summary.enabled_count,
                    'ready_count': latest_summary.ready_count
                }
            
            return jsonify(stats)
            
        except Exception as e:
            logger.error(f"Error getting quick stats: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/circuits/search')
    def search_circuits():
        """Advanced circuit search with caching"""
        
        # Get query parameters
        site_name = request.args.get('site_name', '')
        status = request.args.get('status', '')
        provider = request.args.get('provider', '')
        limit = min(int(request.args.get('limit', 100)), 1000)  # Max 1000 results
        
        # Build cache key
        cache_key = f"search:{site_name}:{status}:{provider}:{limit}"
        
        # Try cache first
        if app.redis:
            try:
                cached_result = app.redis.get(cache_key)
                if cached_result:
                    import json
                    return jsonify(json.loads(cached_result))
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
        
        try:
            with app.app_context():
                # Build query
                query = Circuit.query
                
                if site_name:
                    query = query.filter(Circuit.site_name.ilike(f'%{site_name}%'))
                if status:
                    query = query.filter(Circuit.status.ilike(f'%{status}%'))
                if provider:
                    query = query.filter(Circuit.provider_name.ilike(f'%{provider}%'))
                
                # Execute query with limit
                circuits = query.limit(limit).all()
                
                # Convert to dict
                result = {
                    'circuits': [circuit.to_dict() for circuit in circuits],
                    'total_found': len(circuits),
                    'limited': len(circuits) == limit
                }
                
                # Cache result
                if app.redis:
                    try:
                        import json
                        app.redis.setex(cache_key, 600, json.dumps(result))  # Cache 10 minutes
                    except Exception as e:
                        logger.warning(f"Cache write error: {e}")
                
                return jsonify(result)
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Add firewall management routes
    @app.route('/firewall')
    def firewall_dashboard():
        """Firewall management dashboard"""
        return render_template('meraki_firewall.html')
    
    @app.route('/api/networks')
    def get_networks():
        """Get list of networks for dropdown"""
        try:
            engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
            with engine.connect() as conn:
                # Get networks that have devices (from meraki_inventory) 
                result = conn.execute(text("""
                    SELECT DISTINCT network_name, network_id, 
                           COUNT(*) as device_count
                    FROM meraki_inventory 
                    WHERE network_name IS NOT NULL 
                    GROUP BY network_name, network_id
                    ORDER BY network_name
                """))
                
                networks = []
                for row in result:
                    networks.append({
                        'id': row.network_id,
                        'name': row.network_name,
                        'device_count': row.device_count
                    })
                
                # Also add networks that have firewall rules but no devices in inventory
                result = conn.execute(text("""
                    SELECT DISTINCT network_name, network_id,
                           COUNT(*) as rule_count
                    FROM firewall_rules 
                    WHERE network_name NOT IN (
                        SELECT DISTINCT network_name 
                        FROM meraki_inventory 
                        WHERE network_name IS NOT NULL
                    )
                    GROUP BY network_name, network_id
                    ORDER BY network_name
                """))
                
                for row in result:
                    networks.append({
                        'id': row.network_id,
                        'name': row.network_name,
                        'device_count': f"{row.rule_count} rules"
                    })
                
                # Sort all networks by name
                networks.sort(key=lambda x: x['name'])
                
                return jsonify({
                    'success': True,
                    'networks': networks
                })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/firewall/rules/<network_name>')
    def get_firewall_rules(network_name):
        """Get firewall rules for a specific network"""
        try:
            engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
            with engine.connect() as conn:
                # Get L3 firewall rules
                result = conn.execute(text("""
                    SELECT id, rule_order, comment, policy, protocol,
                           src_port, src_cidr, dest_port, dest_cidr,
                           syslog_enabled, rule_type, is_template,
                           created_at, updated_at
                    FROM firewall_rules 
                    WHERE network_name = :network_name
                    ORDER BY rule_order
                """), {'network_name': network_name})
                
                rules = []
                for row in result:
                    rules.append({
                        'id': row.id,
                        'order': row.rule_order,
                        'comment': row.comment,
                        'policy': row.policy,
                        'protocol': row.protocol,
                        'srcPort': row.src_port,
                        'srcCidr': row.src_cidr,
                        'destPort': row.dest_port,
                        'destCidr': row.dest_cidr,
                        'syslogEnabled': row.syslog_enabled,
                        'ruleType': row.rule_type,
                        'isTemplate': row.is_template,
                        'createdAt': row.created_at.isoformat() if row.created_at else None,
                        'updatedAt': row.updated_at.isoformat() if row.updated_at else None
                    })
                
                return jsonify({
                    'success': True,
                    'rules': rules,
                    'networkName': network_name,
                    'ruleCount': len(rules)
                })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/firewall/rules', methods=['POST'])
    def save_firewall_rule():
        """Save a new or updated firewall rule"""
        try:
            data = request.get_json()
            engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
            
            with engine.connect() as conn:
                if data.get('id'):
                    # Update existing rule
                    update_sql = text("""
                        UPDATE firewall_rules SET
                            comment = :comment,
                            policy = :policy,
                            protocol = :protocol,
                            src_port = :src_port,
                            src_cidr = :src_cidr,
                            dest_port = :dest_port,
                            dest_cidr = :dest_cidr,
                            syslog_enabled = :syslog_enabled,
                            updated_at = NOW()
                        WHERE id = :id
                    """)
                    
                    conn.execute(update_sql, {
                        'id': data['id'],
                        'comment': data.get('comment', ''),
                        'policy': data.get('policy', 'allow'),
                        'protocol': data.get('protocol', 'any'),
                        'src_port': data.get('srcPort', 'Any'),
                        'src_cidr': data.get('srcCidr', 'Any'),
                        'dest_port': data.get('destPort', 'Any'),
                        'dest_cidr': data.get('destCidr', 'Any'),
                        'syslog_enabled': data.get('syslogEnabled', False)
                    })
                    
                    conn.commit()
                    return jsonify({'success': True, 'message': 'Rule updated successfully'})
                else:
                    # Insert new rule - get next rule order
                    result = conn.execute(text("""
                        SELECT COALESCE(MAX(rule_order), 0) + 1 as next_order 
                        FROM firewall_rules 
                        WHERE network_name = :network_name
                    """), {'network_name': data['networkName']})
                    
                    next_order = result.scalar()
                    
                    insert_sql = text("""
                        INSERT INTO firewall_rules (
                            network_id, network_name, rule_order, comment, policy,
                            protocol, src_port, src_cidr, dest_port, dest_cidr,
                            syslog_enabled, rule_type, is_template, template_source,
                            created_at, updated_at
                        ) VALUES (
                            :network_id, :network_name, :rule_order, :comment, :policy,
                            :protocol, :src_port, :src_cidr, :dest_port, :dest_cidr,
                            :syslog_enabled, 'l3', false, null,
                            NOW(), NOW()
                        )
                    """)
                    
                    conn.execute(insert_sql, {
                        'network_id': data.get('networkId', ''),
                        'network_name': data.get('networkName', ''),
                        'rule_order': next_order,
                        'comment': data.get('comment', ''),
                        'policy': data.get('policy', 'allow'),
                        'protocol': data.get('protocol', 'any'),
                        'src_port': data.get('srcPort', 'Any'),
                        'src_cidr': data.get('srcCidr', 'Any'),
                        'dest_port': data.get('destPort', 'Any'),
                        'dest_cidr': data.get('destCidr', 'Any'),
                        'syslog_enabled': data.get('syslogEnabled', False)
                    })
                    
                    conn.commit()
                    return jsonify({'success': True, 'message': 'Rule created successfully'})
                    
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/firewall/rules/<int:rule_id>', methods=['DELETE'])
    def delete_firewall_rule(rule_id):
        """Delete a firewall rule"""
        try:
            engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
            with engine.connect() as conn:
                conn.execute(text("DELETE FROM firewall_rules WHERE id = :id"), {'id': rule_id})
                conn.commit()
                
                return jsonify({'success': True, 'message': 'Rule deleted successfully'})
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/firewall/template/<template_name>')
    def get_template_rules(template_name):
        """Get template rules"""
        try:
            engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT id, rule_order, comment, policy, protocol,
                           src_port, src_cidr, dest_port, dest_cidr,
                           syslog_enabled, revision_number
                    FROM firewall_rules 
                    WHERE template_source = :template_name AND is_template = true
                    ORDER BY rule_order
                """), {'template_name': template_name})
                
                rules = []
                for row in result:
                    rules.append({
                        'id': row.id,
                        'order': row.rule_order,
                        'comment': row.comment,
                        'policy': row.policy,
                        'protocol': row.protocol,
                        'srcPort': row.src_port,
                        'srcCidr': row.src_cidr,
                        'destPort': row.dest_port,
                        'destCidr': row.dest_cidr,
                        'syslogEnabled': row.syslog_enabled,
                        'revision': row.revision_number
                    })
                
                return jsonify({
                    'success': True,
                    'rules': rules,
                    'templateName': template_name
                })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/firewall/template/<template_name>/update', methods=['POST'])
    def update_template_rule(template_name):
        """Update a template rule with revision tracking"""
        try:
            data = request.get_json()
            rule_id = data.get('id')
            
            if not rule_id:
                return jsonify({
                    'success': False,
                    'error': 'Rule ID is required'
                }), 400
            
            engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
            
            with engine.connect() as conn:
                # Start transaction
                trans = conn.begin()
                
                try:
                    # Get current rule data for revision
                    current_rule = conn.execute(text("""
                        SELECT rule_order, comment, policy, protocol, src_port, src_cidr,
                               dest_port, dest_cidr, syslog_enabled, revision_number
                        FROM firewall_rules 
                        WHERE id = :id AND template_source = :template_name AND is_template = true
                    """), {'id': rule_id, 'template_name': template_name}).first()
                    
                    if not current_rule:
                        return jsonify({
                            'success': False,
                            'error': 'Rule not found'
                        }), 404
                    
                    # Create revision entry
                    conn.execute(text("""
                        INSERT INTO firewall_rule_revisions (
                            template_source, rule_id, revision_number, action,
                            rule_order, comment, policy, protocol, src_port, src_cidr,
                            dest_port, dest_cidr, syslog_enabled, changed_by, changed_at
                        ) VALUES (
                            :template_source, :rule_id, :revision_number, 'update',
                            :rule_order, :comment, :policy, :protocol, :src_port, :src_cidr,
                            :dest_port, :dest_cidr, :syslog_enabled, 'web_interface', NOW()
                        )
                    """), {
                        'template_source': template_name,
                        'rule_id': rule_id,
                        'revision_number': current_rule.revision_number,
                        'rule_order': current_rule.rule_order,
                        'comment': current_rule.comment,
                        'policy': current_rule.policy,
                        'protocol': current_rule.protocol,
                        'src_port': current_rule.src_port,
                        'src_cidr': current_rule.src_cidr,
                        'dest_port': current_rule.dest_port,
                        'dest_cidr': current_rule.dest_cidr,
                        'syslog_enabled': current_rule.syslog_enabled
                    })
                    
                    # Update the rule
                    new_revision = current_rule.revision_number + 1
                    conn.execute(text("""
                        UPDATE firewall_rules SET
                            comment = :comment,
                            policy = :policy,
                            protocol = :protocol,
                            src_port = :src_port,
                            src_cidr = :src_cidr,
                            dest_port = :dest_port,
                            dest_cidr = :dest_cidr,
                            syslog_enabled = :syslog_enabled,
                            revision_number = :revision_number,
                            last_modified_at = NOW(),
                            last_modified_by = 'web_interface'
                        WHERE id = :id
                    """), {
                        'id': rule_id,
                        'comment': data.get('comment', ''),
                        'policy': data.get('policy', 'allow'),
                        'protocol': data.get('protocol', 'any'),
                        'src_port': data.get('srcPort', 'Any'),
                        'src_cidr': data.get('srcCidr', 'Any'),
                        'dest_port': data.get('destPort', 'Any'),
                        'dest_cidr': data.get('destCidr', 'Any'),
                        'syslog_enabled': data.get('syslogEnabled', False),
                        'revision_number': new_revision
                    })
                    
                    trans.commit()
                    
                    return jsonify({
                        'success': True,
                        'message': f'Rule updated successfully (revision {new_revision})',
                        'revision': new_revision
                    })
                    
                except Exception as e:
                    trans.rollback()
                    raise e
                    
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/firewall/template/<template_name>/add', methods=['POST'])
    def add_template_rule(template_name):
        """Add a new template rule"""
        try:
            data = request.get_json()
            engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
            
            with engine.connect() as conn:
                # Get next rule order
                result = conn.execute(text("""
                    SELECT COALESCE(MAX(rule_order), 0) + 1 as next_order 
                    FROM firewall_rules 
                    WHERE template_source = :template_name AND is_template = true
                """), {'template_name': template_name})
                
                next_order = result.scalar()
                
                # Insert new rule
                result = conn.execute(text("""
                    INSERT INTO firewall_rules (
                        network_id, network_name, rule_order, comment, policy,
                        protocol, src_port, src_cidr, dest_port, dest_cidr,
                        syslog_enabled, rule_type, is_template, template_source,
                        revision_number, created_at, updated_at, last_modified_at,
                        last_modified_by
                    ) VALUES (
                        'template', :template_name, :rule_order, :comment, :policy,
                        :protocol, :src_port, :src_cidr, :dest_port, :dest_cidr,
                        :syslog_enabled, 'l3', true, :template_source,
                        1, NOW(), NOW(), NOW(), 'web_interface'
                    ) RETURNING id
                """), {
                    'template_name': template_name,
                    'rule_order': next_order,
                    'comment': data.get('comment', ''),
                    'policy': data.get('policy', 'allow'),
                    'protocol': data.get('protocol', 'any'),
                    'src_port': data.get('srcPort', 'Any'),
                    'src_cidr': data.get('srcCidr', 'Any'),
                    'dest_port': data.get('destPort', 'Any'),
                    'dest_cidr': data.get('destCidr', 'Any'),
                    'syslog_enabled': data.get('syslogEnabled', False),
                    'template_source': template_name
                })
                
                new_rule_id = result.scalar()
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Rule added successfully',
                    'ruleId': new_rule_id,
                    'order': next_order
                })
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/firewall/template/<template_name>/delete/<int:rule_id>', methods=['DELETE'])
    def delete_template_rule(template_name, rule_id):
        """Delete a template rule with revision tracking"""
        try:
            engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
            
            with engine.connect() as conn:
                trans = conn.begin()
                
                try:
                    # Get rule data for revision
                    rule_data = conn.execute(text("""
                        SELECT rule_order, comment, policy, protocol, src_port, src_cidr,
                               dest_port, dest_cidr, syslog_enabled, revision_number
                        FROM firewall_rules 
                        WHERE id = :id AND template_source = :template_name AND is_template = true
                    """), {'id': rule_id, 'template_name': template_name}).first()
                    
                    if not rule_data:
                        return jsonify({
                            'success': False,
                            'error': 'Rule not found'
                        }), 404
                    
                    # Create revision entry for deletion
                    conn.execute(text("""
                        INSERT INTO firewall_rule_revisions (
                            template_source, rule_id, revision_number, action,
                            rule_order, comment, policy, protocol, src_port, src_cidr,
                            dest_port, dest_cidr, syslog_enabled, changed_by, changed_at
                        ) VALUES (
                            :template_source, :rule_id, :revision_number, 'delete',
                            :rule_order, :comment, :policy, :protocol, :src_port, :src_cidr,
                            :dest_port, :dest_cidr, :syslog_enabled, 'web_interface', NOW()
                        )
                    """), {
                        'template_source': template_name,
                        'rule_id': rule_id,
                        'revision_number': rule_data.revision_number,
                        'rule_order': rule_data.rule_order,
                        'comment': rule_data.comment,
                        'policy': rule_data.policy,
                        'protocol': rule_data.protocol,
                        'src_port': rule_data.src_port,
                        'src_cidr': rule_data.src_cidr,
                        'dest_port': rule_data.dest_port,
                        'dest_cidr': rule_data.dest_cidr,
                        'syslog_enabled': rule_data.syslog_enabled
                    })
                    
                    # Delete the rule
                    conn.execute(text("""
                        DELETE FROM firewall_rules 
                        WHERE id = :id AND template_source = :template_name AND is_template = true
                    """), {'id': rule_id, 'template_name': template_name})
                    
                    trans.commit()
                    
                    return jsonify({
                        'success': True,
                        'message': 'Rule deleted successfully'
                    })
                    
                except Exception as e:
                    trans.rollback()
                    raise e
                    
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/firewall/template/<template_name>/revisions')
    def get_template_revisions(template_name):
        """Get revision history for a template"""
        try:
            engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT rule_id, revision_number, action, comment, policy, protocol,
                           src_port, src_cidr, dest_port, dest_cidr, syslog_enabled,
                           changed_by, changed_at
                    FROM firewall_rule_revisions 
                    WHERE template_source = :template_name
                    ORDER BY changed_at DESC
                    LIMIT 100
                """), {'template_name': template_name})
                
                revisions = []
                for row in result:
                    revisions.append({
                        'ruleId': row.rule_id,
                        'revision': row.revision_number,
                        'action': row.action,
                        'comment': row.comment,
                        'policy': row.policy,
                        'protocol': row.protocol,
                        'srcPort': row.src_port,
                        'srcCidr': row.src_cidr,
                        'destPort': row.dest_port,
                        'destCidr': row.dest_cidr,
                        'syslogEnabled': row.syslog_enabled,
                        'changedBy': row.changed_by,
                        'changedAt': row.changed_at.isoformat() if row.changed_at else None
                    })
                
                return jsonify({
                    'success': True,
                    'revisions': revisions,
                    'templateName': template_name
                })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/firewall/live-rules/<network_id>')
    def get_live_firewall_rules(network_id):
        """Fetch live firewall rules from Meraki API for comparison"""
        try:
            import requests
            import os
            
            # Get Meraki API key from environment
            api_key = os.environ.get('MERAKI_API_KEY')
            if not api_key:
                return jsonify({
                    'success': False,
                    'error': 'Meraki API key not configured'
                }), 500
            
            # Fetch live rules from Meraki API
            headers = {
                'X-Cisco-Meraki-API-Key': api_key,
                'Content-Type': 'application/json'
            }
            
            url = f'https://api.meraki.com/api/v1/networks/{network_id}/appliance/firewall/l3FirewallRules'
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                rules = data.get('rules', [])
                
                # Convert Meraki format to our internal format
                formatted_rules = []
                for i, rule in enumerate(rules):
                    formatted_rules.append({
                        'id': f'live_{i}',
                        'order': i + 1,
                        'comment': rule.get('comment', ''),
                        'policy': rule.get('policy', 'allow'),
                        'protocol': rule.get('protocol', 'any'),
                        'srcPort': rule.get('srcPort', 'Any'),
                        'srcCidr': rule.get('srcCidr', 'Any'),
                        'destPort': rule.get('destPort', 'Any'),
                        'destCidr': rule.get('destCidr', 'Any'),
                        'syslogEnabled': rule.get('syslogEnabled', False),
                        'ruleType': 'l3',
                        'isTemplate': False,
                        'source': 'live_api'
                    })
                
                return jsonify({
                    'success': True,
                    'rules': formatted_rules,
                    'networkId': network_id,
                    'ruleCount': len(formatted_rules),
                    'source': 'meraki_api'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'Meraki API error: {response.status_code} - {response.text}'
                }), response.status_code
                
        except requests.exceptions.Timeout:
            return jsonify({
                'success': False,
                'error': 'Timeout fetching rules from Meraki API'
            }), 504
        except requests.exceptions.RequestException as e:
            return jsonify({
                'success': False,
                'error': f'Network error: {str(e)}'
            }), 500
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }), 500

    @app.route('/api/firewall/deploy', methods=['POST'])
    def deploy_rules():
        """Deploy template rules to target networks"""
        try:
            data = request.get_json()
            template_name = data.get('templateName')
            target_networks = data.get('targetNetworks', [])
            
            if not template_name or not target_networks:
                return jsonify({
                    'success': False,
                    'error': 'Template name and target networks required'
                }), 400
            
            deployed_count = 0
            engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
            
            with engine.connect() as conn:
                # Get template rules
                template_result = conn.execute(text("""
                    SELECT rule_order, comment, policy, protocol,
                           src_port, src_cidr, dest_port, dest_cidr,
                           syslog_enabled
                    FROM firewall_rules 
                    WHERE template_source = :template_name AND is_template = true
                    ORDER BY rule_order
                """), {'template_name': template_name})
                
                template_rules = list(template_result)
                
                for network in target_networks:
                    network_name = network.get('name')
                    network_id = network.get('id')
                    
                    # Insert template rules
                    for rule in template_rules:
                        insert_sql = text("""
                            INSERT INTO firewall_rules (
                                network_id, network_name, rule_order, comment, policy,
                                protocol, src_port, src_cidr, dest_port, dest_cidr,
                                syslog_enabled, rule_type, is_template, template_source,
                                created_at, updated_at
                            ) VALUES (
                                :network_id, :network_name, :rule_order, :comment, :policy,
                                :protocol, :src_port, :src_cidr, :dest_port, :dest_cidr,
                                :syslog_enabled, 'l3', false, :template_source,
                                NOW(), NOW()
                            )
                        """)
                        
                        conn.execute(insert_sql, {
                            'network_id': network_id,
                            'network_name': network_name,
                            'rule_order': rule.rule_order,
                            'comment': rule.comment,
                            'policy': rule.policy,
                            'protocol': rule.protocol,
                            'src_port': rule.src_port,
                            'src_cidr': rule.src_cidr,
                            'dest_port': rule.dest_port,
                            'dest_cidr': rule.dest_cidr,
                            'syslog_enabled': rule.syslog_enabled,
                            'template_source': template_name
                        })
                        
                        deployed_count += 1
                    
                    # Log deployment
                    log_sql = text("""
                        INSERT INTO firewall_deployment_log (
                            template_network_id, template_network_name,
                            target_network_id, target_network_name,
                            deployment_type, rules_deployed, deployment_status,
                            deployed_by, deployment_time
                        ) VALUES (
                            'L_3790904986339115847', :template_name,
                            :target_network_id, :target_network_name,
                            'l3_rules', :rules_deployed, 'success',
                            'web_interface', NOW()
                        )
                    """)
                    
                    conn.execute(log_sql, {
                        'template_name': template_name,
                        'target_network_id': network_id,
                        'target_network_name': network_name,
                        'rules_deployed': len(template_rules)
                    })
                
                conn.commit()
            
            return jsonify({
                'success': True,
                'message': f'Successfully deployed {len(template_rules)} rules to {len(target_networks)} networks',
                'deployedRules': deployed_count
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # Home page route
    @app.route('/home')
    def home():
        """Home page with links to all sections"""
        return render_template('home.html')
    
    @app.route('/readme')
    def readme():
        """Serve documentation page with dsrcircuits styling"""
        return render_template('documentation.html')
    
    @app.route('/api/documentation/content')
    def documentation_content():
        """Serve README.md content as HTML"""
        try:
            import markdown
            with open('/usr/local/bin/README.md', 'r') as f:
                content = f.read()
            # Convert markdown to HTML with extensions
            html_content = markdown.markdown(
                content, 
                extensions=[
                    'tables', 
                    'fenced_code', 
                    'toc',
                    'codehilite',
                    'attr_list'
                ]
            )
            return html_content
        except Exception as e:
            return f'<div style="color: #e74c3c; padding: 20px; background: #f8f9fa; border-radius: 5px; border-left: 4px solid #e74c3c;"><h3>Error Loading Documentation</h3><p>Unable to load README.md: {str(e)}</p><p>Please check that the README.md file exists in /usr/local/bin/Main/</p></div>', 500
    
    @app.route('/docs/<filename>')
    def serve_documentation(filename):
        """Serve documentation files"""
        try:
            import markdown
            import os
            
            # Security check - only allow .md files
            if not filename.endswith('.md'):
                return abort(404)
            
            # Construct safe file path
            file_path = os.path.join('/usr/local/bin', filename)
            
            # Check if file exists
            if not os.path.exists(file_path):
                return abort(404)
            
            # Read and convert markdown to HTML
            with open(file_path, 'r') as f:
                content = f.read()
            
            html_content = markdown.markdown(
                content,
                extensions=['extra', 'codehilite', 'nl2br', 'toc']
            )
            
            # Wrap in documentation template
            return render_template('documentation.html', 
                                 content=html_content,
                                 title=filename.replace('.md', '').replace('_', ' ').title())
        except Exception as e:
            logger.error(f"Error serving documentation {filename}: {e}")
            return abort(404)
    
    return app

# Create app instance for gunicorn
app = create_app()

if __name__ == '__main__':
    app = create_app()
    
    # Create database tables if they don't exist
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created/verified")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
    
    logger.info("Starting integrated DSR Circuits application with firewall management on port 5052")
    app.run(host='0.0.0.0', port=5052, debug=False)