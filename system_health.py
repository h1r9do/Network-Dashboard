"""
System Health Blueprint - Server statistics and system information
"""

import os
import psutil
import platform
import subprocess
import socket
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify
from sqlalchemy import create_engine, text
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

system_health_bp = Blueprint('system_health', __name__)

def run_command(command):
    """Run shell command and return output"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else None
    except (subprocess.TimeoutExpired, Exception):
        return None

def get_system_info():
    """Get comprehensive system information"""
    info = {}
    
    # Basic system info
    info['hostname'] = socket.gethostname()
    info['platform'] = platform.platform()
    info['system'] = platform.system()
    info['node'] = platform.node()
    info['machine'] = platform.machine()
    info['processor'] = platform.processor()
    
    # RHEL/OS specific info
    try:
        with open('/etc/os-release', 'r') as f:
            os_release = {}
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os_release[key] = value.strip('"')
            info['os_name'] = os_release.get('PRETTY_NAME', 'Unknown')
            info['os_version'] = os_release.get('VERSION', 'Unknown')
            info['os_id'] = os_release.get('ID', 'Unknown')
    except:
        info['os_name'] = platform.system()
        info['os_version'] = platform.release()
        info['os_id'] = 'unknown'
    
    # Kernel info
    info['kernel'] = platform.release()
    info['architecture'] = platform.architecture()[0]
    
    # Uptime
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            uptime_delta = timedelta(seconds=uptime_seconds)
            info['uptime'] = str(uptime_delta).split('.')[0]  # Remove microseconds
            info['uptime_seconds'] = uptime_seconds
    except:
        info['uptime'] = 'Unknown'
        info['uptime_seconds'] = 0
    
    # Load average
    try:
        load_avg = os.getloadavg()
        info['load_avg'] = {
            '1min': load_avg[0],
            '5min': load_avg[1],
            '15min': load_avg[2]
        }
    except:
        info['load_avg'] = {'1min': 0, '5min': 0, '15min': 0}
    
    return info

def get_cpu_info():
    """Get CPU information"""
    cpu_info = {}
    
    # Basic CPU info
    cpu_info['count'] = psutil.cpu_count()
    cpu_info['count_logical'] = psutil.cpu_count(logical=True)
    cpu_info['count_physical'] = psutil.cpu_count(logical=False)
    
    # CPU usage
    cpu_info['usage_percent'] = psutil.cpu_percent(interval=1)
    cpu_info['usage_per_cpu'] = psutil.cpu_percent(interval=1, percpu=True)
    
    # CPU frequency
    try:
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            cpu_info['frequency'] = {
                'current': cpu_freq.current,
                'min': cpu_freq.min,
                'max': cpu_freq.max
            }
    except:
        cpu_info['frequency'] = None
    
    # CPU times
    cpu_times = psutil.cpu_times()
    cpu_info['times'] = {
        'user': cpu_times.user,
        'system': cpu_times.system,
        'idle': cpu_times.idle,
        'iowait': getattr(cpu_times, 'iowait', 0),
        'irq': getattr(cpu_times, 'irq', 0),
        'softirq': getattr(cpu_times, 'softirq', 0)
    }
    
    # CPU model info from /proc/cpuinfo
    try:
        cpu_model = run_command("grep 'model name' /proc/cpuinfo | head -1 | cut -d':' -f2")
        cpu_info['model'] = cpu_model.strip() if cpu_model else 'Unknown'
    except:
        cpu_info['model'] = 'Unknown'
    
    return cpu_info

def get_memory_info():
    """Get memory information"""
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    return {
        'total': memory.total,
        'available': memory.available,
        'used': memory.used,
        'free': memory.free,
        'percent': memory.percent,
        'buffers': getattr(memory, 'buffers', 0),
        'cached': getattr(memory, 'cached', 0),
        'swap': {
            'total': swap.total,
            'used': swap.used,
            'free': swap.free,
            'percent': swap.percent
        }
    }

def get_disk_info():
    """Get disk usage information"""
    disks = []
    
    # Get all disk partitions
    partitions = psutil.disk_partitions()
    
    for partition in partitions:
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disk_info = {
                'device': partition.device,
                'mountpoint': partition.mountpoint,
                'fstype': partition.fstype,
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent': (usage.used / usage.total) * 100 if usage.total > 0 else 0
            }
            disks.append(disk_info)
        except PermissionError:
            # Skip partitions we can't access
            continue
    
    # Disk I/O statistics
    try:
        disk_io = psutil.disk_io_counters()
        io_stats = {
            'read_count': disk_io.read_count,
            'write_count': disk_io.write_count,
            'read_bytes': disk_io.read_bytes,
            'write_bytes': disk_io.write_bytes,
            'read_time': disk_io.read_time,
            'write_time': disk_io.write_time
        }
    except:
        io_stats = None
    
    return {'partitions': disks, 'io_stats': io_stats}

def get_network_info():
    """Get network interface information"""
    interfaces = []
    
    # Get network interfaces
    net_if_addrs = psutil.net_if_addrs()
    net_if_stats = psutil.net_if_stats()
    
    for interface, addresses in net_if_addrs.items():
        if_info = {
            'name': interface,
            'addresses': [],
            'stats': {}
        }
        
        # Get addresses for this interface
        for addr in addresses:
            addr_info = {
                'family': str(addr.family),
                'address': addr.address,
                'netmask': addr.netmask,
                'broadcast': addr.broadcast
            }
            if addr.family.name == 'AF_INET':
                addr_info['family'] = 'IPv4'
            elif addr.family.name == 'AF_INET6':
                addr_info['family'] = 'IPv6'
            elif addr.family.name == 'AF_PACKET':
                addr_info['family'] = 'MAC'
            
            if_info['addresses'].append(addr_info)
        
        # Get interface statistics
        if interface in net_if_stats:
            stats = net_if_stats[interface]
            if_info['stats'] = {
                'isup': stats.isup,
                'duplex': str(stats.duplex),
                'speed': stats.speed,
                'mtu': stats.mtu
            }
        
        interfaces.append(if_info)
    
    # Network I/O statistics
    try:
        net_io = psutil.net_io_counters()
        io_stats = {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv,
            'errin': net_io.errin,
            'errout': net_io.errout,
            'dropin': net_io.dropin,
            'dropout': net_io.dropout
        }
    except:
        io_stats = None
    
    return {'interfaces': interfaces, 'io_stats': io_stats}

def get_process_info():
    """Get running process information"""
    processes = []
    
    # Get top 10 processes by CPU usage
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username']):
        try:
            proc_info = proc.info
            proc_info['cpu_percent'] = proc.cpu_percent()
            processes.append(proc_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    # Sort by CPU usage
    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
    
    return {
        'top_cpu': processes[:10],
        'total_count': len(list(psutil.process_iter()))
    }

def get_database_info():
    """Get database connection and status information"""
    try:
        from flask import current_app
        from models import db
        
        # Use the existing Flask app database connection
        with current_app.app_context():
            # Test connection
            result = db.session.execute(text('SELECT version()'))
            db_version = result.scalar()
            
            # Get database size
            result = db.session.execute(text("""
                SELECT pg_size_pretty(pg_database_size('dsrcircuits')) as size
            """))
            db_size = result.scalar()
            
            # Get table sizes
            result = db.session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 10
            """))
            tables = [dict(row._mapping) for row in result]
            
            # Get connection count
            result = db.session.execute(text("""
                SELECT count(*) as active_connections
                FROM pg_stat_activity 
                WHERE state = 'active'
            """))
            active_connections = result.scalar()
            
            return {
                'status': 'connected',
                'version': db_version,
                'size': db_size,
                'active_connections': active_connections,
                'tables': tables
            }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def get_service_info():
    """Get systemd service information"""
    services = [
        'dsrcircuits.service', 
        'postgresql.service', 
        'redis.service', 
        'nginx.service',
        'gitea.service',      # Git service
        'k3s.service'         # K3s (includes AWX)
    ]
    service_status = []
    
    for service in services:
        try:
            result = run_command(f"systemctl is-active {service}")
            status = result if result else 'unknown'
            
            # Get detailed info
            result = run_command(f"systemctl show {service} --property=MainPID,ActiveState,LoadState,SubState")
            details = {}
            if result:
                for line in result.split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        details[key] = value
            
            service_status.append({
                'name': service,
                'status': status,
                'details': details
            })
        except:
            service_status.append({
                'name': service,
                'status': 'unknown',
                'details': {}
            })
    
    return service_status

def get_awx_info():
    """Get AWX/Ansible information"""
    try:
        awx_info = {}
        
        # Check AWX pods via kubectl
        awx_pods_cmd = "kubectl get pods -n awx -o json"
        awx_pods_result = run_command(awx_pods_cmd)
        
        if awx_pods_result:
            import json
            try:
                pods_data = json.loads(awx_pods_result)
                awx_pods = []
                for pod in pods_data.get('items', []):
                    pod_info = {
                        'name': pod['metadata']['name'],
                        'status': pod['status']['phase'],
                        'ready': 'Unknown'
                    }
                    
                    # Check if pod is ready
                    if 'conditions' in pod['status']:
                        for condition in pod['status']['conditions']:
                            if condition['type'] == 'Ready':
                                pod_info['ready'] = condition['status']
                                break
                    
                    awx_pods.append(pod_info)
                
                awx_info['pods'] = awx_pods
                awx_info['total_pods'] = len(awx_pods)
                awx_info['ready_pods'] = len([p for p in awx_pods if p['ready'] == 'True'])
            except json.JSONDecodeError:
                awx_info['error'] = 'Could not parse kubectl output'
        else:
            awx_info['error'] = 'kubectl command failed'
        
        # Check AWX web accessibility
        awx_web_cmd = "curl -s -o /dev/null -w '%{http_code}' http://localhost:30483 --connect-timeout 5"
        awx_web_result = run_command(awx_web_cmd)
        awx_info['web_status'] = awx_web_result if awx_web_result else 'unreachable'
        
        # Get k3s cluster info
        cluster_info_cmd = "kubectl cluster-info --request-timeout=5s"
        cluster_info = run_command(cluster_info_cmd)
        awx_info['cluster_accessible'] = bool(cluster_info and 'running' in cluster_info.lower())
        
        return awx_info
        
    except Exception as e:
        return {'error': str(e)}

def get_git_info():
    """Get Git/Gitea service information"""
    try:
        git_info = {}
        
        # Check Gitea web accessibility
        gitea_web_cmd = "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 --connect-timeout 5"
        gitea_web_result = run_command(gitea_web_cmd)
        git_info['web_status'] = gitea_web_result if gitea_web_result else 'unreachable'
        
        # Check git repository accessibility
        repo_check_cmd = "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/mbambic/usr-local-bin --connect-timeout 5"
        repo_result = run_command(repo_check_cmd)
        git_info['repo_accessible'] = repo_result == '200'
        
        # Get Gitea version if accessible
        if git_info['web_status'] == '200':
            # Try to get version from API
            version_cmd = "curl -s http://localhost:3000/api/v1/version --connect-timeout 5"
            version_result = run_command(version_cmd)
            if version_result:
                try:
                    import json
                    version_data = json.loads(version_result)
                    git_info['version'] = version_data.get('version', 'Unknown')
                except:
                    git_info['version'] = 'Unknown'
        
        return git_info
        
    except Exception as e:
        return {'error': str(e)}

@system_health_bp.route('/system-health')
def system_health_page():
    """System health dashboard page"""
    return render_template('system_health.html')

@system_health_bp.route('/api/system-health/all')
def system_health_data():
    """Get all system health data"""
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'system': get_system_info(),
        'cpu': get_cpu_info(),
        'memory': get_memory_info(),
        'disk': get_disk_info(),
        'network': get_network_info(),
        'processes': get_process_info(),
        'database': get_database_info(),
        'services': get_service_info(),
        'awx': get_awx_info(),
        'git': get_git_info()
    })

@system_health_bp.route('/api/system-health/summary')
def system_health_summary():
    """Get system health summary for other pages"""
    system = get_system_info()
    cpu = get_cpu_info()
    memory = get_memory_info()
    disk = get_disk_info()
    
    # Calculate overall health score
    health_score = 100
    alerts = []
    
    # CPU check
    if cpu['usage_percent'] > 80:
        health_score -= 20
        alerts.append(f"High CPU usage: {cpu['usage_percent']:.1f}%")
    
    # Memory check
    if memory['percent'] > 85:
        health_score -= 20
        alerts.append(f"High memory usage: {memory['percent']:.1f}%")
    
    # Disk space check
    for partition in disk['partitions']:
        if partition['percent'] > 90:
            health_score -= 15
            alerts.append(f"Low disk space on {partition['mountpoint']}: {partition['percent']:.1f}% used")
    
    # Load average check
    if system['load_avg']['1min'] > cpu['count'] * 2:
        health_score -= 15
        alerts.append(f"High system load: {system['load_avg']['1min']:.2f}")
    
    health_score = max(0, health_score)
    
    return jsonify({
        'health_score': health_score,
        'status': 'healthy' if health_score >= 80 else 'warning' if health_score >= 60 else 'critical',
        'alerts': alerts,
        'summary': {
            'hostname': system['hostname'],
            'os': system['os_name'],
            'uptime': system['uptime'],
            'cpu_usage': cpu['usage_percent'],
            'memory_usage': memory['percent'],
            'load_avg': system['load_avg']['1min']
        }
    })