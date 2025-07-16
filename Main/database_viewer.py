#!/usr/bin/env python3
"""
Database Viewer Blueprint
Allows viewing and browsing all database tables with search and export functionality
"""

from flask import Blueprint, render_template, jsonify, request, Response
from sqlalchemy import inspect, text, create_engine
from datetime import datetime
import json
import csv
import io
from config import Config

database_viewer_bp = Blueprint('database_viewer', __name__)

def get_db_connection():
    """Get direct database connection"""
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    return engine

@database_viewer_bp.route('/database-viewer')
def database_viewer():
    """Main database viewer page"""
    return render_template('database_viewer.html')

@database_viewer_bp.route('/api/database/tables')
def get_tables():
    """Get list of all database tables with metadata"""
    try:
        engine = get_db_connection()
        inspector = inspect(engine)
        
        tables = []
        for table_name in sorted(inspector.get_table_names()):
            # Skip backup tables
            if '_backup' in table_name or table_name.startswith('temp_'):
                continue
                
            # Get table info
            columns = inspector.get_columns(table_name)
            pk = inspector.get_pk_constraint(table_name)
            
            # Get row count
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = result.scalar()
            
            tables.append({
                'name': table_name,
                'column_count': len(columns),
                'row_count': row_count,
                'primary_key': pk['constrained_columns'] if pk else []
            })
        
        return jsonify({
            'success': True,
            'tables': tables,
            'total_tables': len(tables)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@database_viewer_bp.route('/api/database/table/<table_name>/schema')
def get_table_schema(table_name):
    """Get detailed schema information for a specific table"""
    try:
        engine = get_db_connection()
        inspector = inspect(engine)
        
        # Check if table exists
        if table_name not in inspector.get_table_names():
            return jsonify({
                'success': False,
                'error': f'Table {table_name} not found'
            }), 404
        
        # Get columns
        columns = []
        for col in inspector.get_columns(table_name):
            columns.append({
                'name': col['name'],
                'type': str(col['type']),
                'nullable': col['nullable'],
                'default': str(col['default']) if col['default'] else None,
                'primary_key': False  # Will be updated below
            })
        
        # Get primary key
        pk = inspector.get_pk_constraint(table_name)
        if pk and pk['constrained_columns']:
            for col in columns:
                if col['name'] in pk['constrained_columns']:
                    col['primary_key'] = True
        
        # Get foreign keys
        foreign_keys = []
        for fk in inspector.get_foreign_keys(table_name):
            foreign_keys.append({
                'columns': fk['constrained_columns'],
                'referred_table': fk['referred_table'],
                'referred_columns': fk['referred_columns']
            })
        
        # Get indexes
        indexes = []
        for idx in inspector.get_indexes(table_name):
            indexes.append({
                'name': idx['name'],
                'columns': idx['column_names'],
                'unique': idx['unique']
            })
        
        return jsonify({
            'success': True,
            'table_name': table_name,
            'columns': columns,
            'foreign_keys': foreign_keys,
            'indexes': indexes
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@database_viewer_bp.route('/api/database/table/<table_name>/data')
def get_table_data(table_name):
    """Get paginated data from a specific table"""
    try:
        engine = get_db_connection()
        inspector = inspect(engine)
        
        # Check if table exists
        if table_name not in inspector.get_table_names():
            return jsonify({
                'success': False,
                'error': f'Table {table_name} not found'
            }), 404
        
        # Get parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        search = request.args.get('search', '')
        sort_column = request.args.get('sort_column', '')
        sort_order = request.args.get('sort_order', 'asc')
        
        # Validate per_page
        per_page = min(max(per_page, 10), 1000)
        
        # Get columns
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        with engine.connect() as conn:
            # Build query
            query = f"SELECT * FROM {table_name}"
            count_query = f"SELECT COUNT(*) FROM {table_name}"
            params = {}
            
            # Add search if provided
            if search:
                search_conditions = []
                for i, col in enumerate(columns):
                    search_conditions.append(f"CAST({col} AS TEXT) ILIKE :search{i}")
                    params[f'search{i}'] = f'%{search}%'
                
                where_clause = f" WHERE {' OR '.join(search_conditions)}"
                query += where_clause
                count_query += where_clause
            
            # Add sorting
            if sort_column and sort_column in columns:
                query += f" ORDER BY {sort_column} {sort_order.upper()}"
            else:
                # Try to sort by primary key or first column
                pk = inspector.get_pk_constraint(table_name)
                if pk and pk['constrained_columns']:
                    query += f" ORDER BY {pk['constrained_columns'][0]}"
                else:
                    query += f" ORDER BY {columns[0]}"
            
            # Add pagination
            offset = (page - 1) * per_page
            query += f" LIMIT {per_page} OFFSET {offset}"
            
            # Get total count
            total = conn.execute(text(count_query), params).scalar()
            
            # Get data
            result = conn.execute(text(query), params)
            rows = []
            for row in result:
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # Convert datetime objects to string
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    row_dict[col] = value
                rows.append(row_dict)
        
        return jsonify({
            'success': True,
            'columns': columns,
            'data': rows,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@database_viewer_bp.route('/api/database/table/<table_name>/export/<format>')
def export_table_data(table_name, format):
    """Export table data in various formats"""
    try:
        engine = get_db_connection()
        inspector = inspect(engine)
        
        # Check if table exists
        if table_name not in inspector.get_table_names():
            return jsonify({
                'success': False,
                'error': f'Table {table_name} not found'
            }), 404
        
        # Get columns
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        with engine.connect() as conn:
            # Get all data (be careful with large tables)
            result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 10000"))
            
            if format == 'csv':
                # Create CSV
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow(columns)
                
                # Write data
                for row in result:
                    writer.writerow(row)
                
                # Return as download
                return Response(
                    output.getvalue(),
                    mimetype='text/csv',
                    headers={
                        'Content-Disposition': f'attachment; filename={table_name}.csv'
                    }
                )
                
            elif format == 'json':
                # Create JSON
                rows = []
                for row in result:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        if isinstance(value, datetime):
                            value = value.isoformat()
                        row_dict[col] = value
                    rows.append(row_dict)
                
                return Response(
                    json.dumps(rows, indent=2),
                    mimetype='application/json',
                    headers={
                        'Content-Disposition': f'attachment; filename={table_name}.json'
                    }
                )
            else:
                return jsonify({
                    'success': False,
                    'error': f'Unsupported format: {format}'
                }), 400
                
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@database_viewer_bp.route('/api/database/query', methods=['POST'])
def execute_query():
    """Execute a custom SQL query (READ-ONLY)"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'No query provided'
            }), 400
        
        # Only allow SELECT queries
        if not query.upper().startswith('SELECT'):
            return jsonify({
                'success': False,
                'error': 'Only SELECT queries are allowed'
            }), 403
        
        engine = get_db_connection()
        
        with engine.connect() as conn:
            result = conn.execute(text(query))
            
            # Get column names
            columns = list(result.keys())
            
            # Get data
            rows = []
            for row in result:
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    row_dict[col] = value
                rows.append(row_dict)
            
            return jsonify({
                'success': True,
                'columns': columns,
                'data': rows,
                'row_count': len(rows)
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500