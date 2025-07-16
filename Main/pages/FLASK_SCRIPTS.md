# DSR Circuits - Flask Application Scripts Documentation

## Overview
**Main Application**: `/usr/local/bin/Main/dsrcircuits.py`  
**Framework**: Flask with SQLAlchemy ORM  
**Database**: PostgreSQL with connection pooling  
**Port**: 5052 (behind nginx reverse proxy on 8080)  
**Service**: meraki-dsrcircuits.service (systemd)

## Application Architecture

### Core Flask Application
**File**: `dsrcircuits.py`  
**Purpose**: Main application entry point and route definitions

#### Key Components
```python
# Application initialization
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://...'

# Blueprint registration
from status import status_bp
from new_stores import new_stores_bp
from reports import reports_bp
# ... additional blueprints

app.register_blueprint(status_bp)
app.register_blueprint(new_stores_bp)
app.register_blueprint(reports_bp)
```

## Database Models & ORM

### SQLAlchemy Models
**File**: `models.py` (imported across all scripts)

#### Circuit Model
```python
class Circuit(db.Model):
    __tablename__ = 'circuits'
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(255), nullable=False)
    circuit_purpose = db.Column(db.String(50))
    record_number = db.Column(db.String(255))  # NOT primary key
    # ... additional fields
    
    __table_args__ = (
        db.UniqueConstraint('site_name', 'circuit_purpose'),
    )
```

#### Key Finding: Primary Key Structure
- **Primary Key**: Auto-increment `id` field
- **Business Key**: `(site_name, circuit_purpose)` unique constraint
- **Record Number**: Regular column for reference/correlation

## Major Flask Scripts

### 1. Status Dashboard (`status.py`)
**Routes**: `/dsrdashboard`, `/api/dashboard-data`  
**Purpose**: Real-time circuit status monitoring

#### Database Operations
```python
# Get all circuits with status filtering
circuits = Circuit.query.filter(
    Circuit.status.in_(['Ready for Turn Up', 'In Progress', ...])
).all()

# Merge assignment data
assignments = CircuitAssignment.query.filter_by(status='active').all()
assignment_data = {a.site_name: {
    'sctask': a.sctask,
    'assigned_to': a.assigned_to
} for a in assignments}

# Apply assignment data to circuits
for circuit in circuits:
    site_assignment = assignment_data.get(circuit.site_name, {})
    if site_assignment.get('assigned_to'):
        circuit_dict['assigned_to'] = site_assignment['assigned_to']
```

#### Key Features
- **Assignment Data Merging**: Prioritizes data from circuit_assignments table
- **Site-based Counting**: Groups by site_name to prevent duplicates
- **Real-time Updates**: 30-second refresh interval
- **Category Filtering**: Dynamic status categorization

### 2. New Stores Management (`new_stores.py`)
**Routes**: `/new-stores`, `/api/new-store-circuits`  
**Purpose**: Store construction and manual circuit creation

#### Record Number Generation
```python
def generate_record_number(site_name, circuit_purpose):
    """Generate unique DSR-format record number"""
    clean_site = ''.join(c for c in site_name.upper() if c.isalnum())[:10]
    random_num = ''.join([str(random.randint(0, 9)) for _ in range(random.randint(8, 10))])
    record_number = f"DISCOUNT{clean_site}{random_num}_BR"
    
    if circuit_purpose.lower() != 'primary':
        record_number += "-I1"
    
    return record_number
```

#### Database Operations
```python
# Create new circuit with generated record_number
new_circuit = Circuit(
    site_name=site_name,
    site_id=site_id,
    record_number=generate_record_number(site_name, circuit_purpose),
    circuit_purpose=circuit_purpose,
    data_source='new_stores',
    manual_override=True,  # Protect from DSR overwrites
    # ... other fields
)
db.session.add(new_circuit)
db.session.commit()
```

#### Key Features
- **Auto Record Number**: Generates unique DSR-format identifiers
- **Manual Override**: Sets flag to prevent automated overwrites
- **Excel Upload**: Bulk circuit creation from spreadsheets
- **Meraki Detection**: Auto-removes when stores go live

### 3. Circuit Enablement Reports (`reports.py`)
**Routes**: `/circuit-enablement-report`, `/api/closure-data`  
**Purpose**: Performance analytics and team attribution

#### Database Queries
```python
# Get enablement data with team attribution
enablements = db.session.query(
    DailyEnablement.date,
    DailyEnablement.site_id,
    DailyEnablement.enabled_by,
    Circuit.site_name
).join(
    Circuit, DailyEnablement.site_id == Circuit.site_id
).filter(
    DailyEnablement.date >= start_date
).all()

# Aggregate by team member
team_stats = {}
for e in enablements:
    member = e.enabled_by or 'Unassigned'
    if member not in team_stats:
        team_stats[member] = defaultdict(int)
    team_stats[member][e.date] += 1
```

#### Key Features
- **Multi-tab Interface**: Different views of enablement data
- **Date Range Filtering**: Flexible time period selection
- **Team Attribution**: Links enablements to team members
- **Chart Generation**: Dynamic Chart.js visualizations

### 4. Circuit Management (`dsrcircuits.py` routes)
**Routes**: `/dsrcircuits`, `/api/circuits/*`  
**Purpose**: Circuit viewing, editing, and Meraki integration

#### Database Operations
```python
# Update circuit with validation
circuit = Circuit.query.filter_by(
    site_name=site_name,
    circuit_purpose=circuit_purpose
).first()

if circuit:
    # Update fields
    circuit.desired_cktid = new_cktid
    circuit.status = new_status
    circuit.last_updated = datetime.now()
    
    # Create history record
    history = CircuitHistory(
        circuit_id=circuit.id,
        field_name='status',
        old_value=old_status,
        new_value=new_status
    )
    db.session.add(history)
    db.session.commit()
```

#### Meraki Integration
```python
# Push configuration to Meraki
def push_to_meraki(circuit_data):
    # Get device from inventory
    device = MerakiInventory.query.filter_by(
        site_name=circuit_data['site_name']
    ).first()
    
    if device:
        # Update Meraki via API
        dashboard.devices.updateDevice(
            serial=device.serial,
            notes=f"Provider: {circuit_data['provider']}"
        )
```

### 5. Inventory Management Scripts
**Files**: `inventory.py`, `inventory_details.py`  
**Purpose**: Device tracking and EOL management

#### Database Queries
```python
# Get inventory summary with counts
summary = db.session.query(
    MerakiInventory.model,
    func.count(MerakiInventory.id).label('count')
).group_by(
    MerakiInventory.model
).all()

# EOL device detection
eol_devices = MerakiInventory.query.filter(
    MerakiInventory.model.in_(EOL_MODELS)
).all()
```

### 6. System Monitoring (`system_health.py`)
**Routes**: `/system-health`, `/api/system-status`  
**Purpose**: Infrastructure monitoring and diagnostics

#### Health Checks
```python
# Database connectivity
try:
    db.session.execute('SELECT 1')
    db_status = 'healthy'
except:
    db_status = 'error'

# Service status checks
services = ['postgresql', 'redis', 'nginx']
for service in services:
    status = check_service_status(service)
```

## API Endpoint Patterns

### RESTful Design
```python
# Standard CRUD operations
GET    /api/circuits          # List circuits
GET    /api/circuits/<id>     # Get specific circuit
POST   /api/circuits          # Create circuit
PUT    /api/circuits/<id>     # Update circuit
DELETE /api/circuits/<id>     # Delete circuit
```

### Response Format
```python
# Standard API response structure
{
    "success": true,
    "data": {...},
    "message": "Operation successful",
    "timestamp": "2025-07-03T14:30:00Z"
}
```

## Database Connection Management

### Connection Pooling
```python
# SQLAlchemy configuration
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}
```

### Transaction Handling
```python
# Proper transaction management
try:
    # Multiple operations
    db.session.add(new_circuit)
    db.session.add(history_record)
    db.session.commit()
except Exception as e:
    db.session.rollback()
    log.error(f"Transaction failed: {e}")
    raise
```

## Authentication & Security

### Current Implementation
- No authentication layer (internal network only)
- CSRF protection via Flask-WTF
- SQL injection protection via SQLAlchemy ORM
- Input validation on all forms

### Security Considerations
```python
# Input sanitization example
def sanitize_input(value):
    if not value:
        return None
    return str(value).strip()[:255]  # Limit length
```

## Performance Optimizations

### Caching Strategy
```python
# Redis caching for expensive queries
@cache.memoize(timeout=300)
def get_dashboard_data():
    return expensive_database_query()
```

### Query Optimization
```python
# Eager loading to prevent N+1 queries
circuits = Circuit.query.options(
    joinedload(Circuit.assignments),
    joinedload(Circuit.history)
).all()
```

### Pagination
```python
# Efficient pagination for large datasets
page = request.args.get('page', 1, type=int)
per_page = 50
circuits = Circuit.query.paginate(
    page=page, 
    per_page=per_page,
    error_out=False
)
```

## Error Handling

### Global Error Handlers
```python
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Resource not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500
```

### Logging Configuration
```python
# Comprehensive logging
logging.basicConfig(
    filename='/var/log/dsrcircuits.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)
```

## Frontend Integration

### Template Rendering
```python
@app.route('/dsrdashboard')
def dashboard():
    return render_template('dsrdashboard.html',
        title='Circuit Status Dashboard',
        last_updated=get_last_update_time()
    )
```

### AJAX Communication
```javascript
// Frontend API calls
fetch('/api/dashboard-data')
    .then(response => response.json())
    .then(data => updateDashboard(data));
```

## Deployment Configuration

### SystemD Service
```ini
[Unit]
Description=DSR Circuits Flask Application
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/usr/local/bin/Main
ExecStart=/usr/bin/python3 dsrcircuits.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Environment Variables
```python
# Configuration management
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://...')
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
```

## Key Findings & Recommendations

### Primary Key Architecture
**Current Implementation is Correct**:
- Business logic operates on site_name + circuit_purpose
- Record_number serves as reference field only
- Allows flexibility in record number changes

### Performance Recommendations
1. **Add Database Indexes**:
   ```sql
   CREATE INDEX idx_circuits_record_number ON circuits(record_number);
   CREATE INDEX idx_circuits_status ON circuits(status);
   ```

2. **Implement Request Caching**:
   - Cache dashboard data (30 seconds)
   - Cache inventory summaries (5 minutes)
   - Cache static reports (1 hour)

3. **Optimize Queries**:
   - Use SELECT with specific columns
   - Implement lazy loading where appropriate
   - Add query result pagination

### Security Enhancements
1. **Add Authentication Layer**:
   - Implement Flask-Login
   - Add role-based access control
   - Secure API endpoints

2. **API Rate Limiting**:
   - Implement Flask-Limiter
   - Protect against abuse
   - Monitor usage patterns

---
*Last Updated: July 3, 2025*  
*Comprehensive Flask application database logic documentation*  
*Part of DSR Circuits Documentation Suite*