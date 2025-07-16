# DSR Circuits System Shutdown Log - July 2, 2025

## Services Stopped for Migration

### 1. Application Services
- **dsrcircuits.service** - Main Flask application (Port 5052)
  - Status: STOPPED and DISABLED
  - Command: `systemctl stop dsrcircuits.service && systemctl disable dsrcircuits.service`

### 2. Database Services  
- **postgresql.service** - PostgreSQL database
  - Status: STOPPED and DISABLED
  - Command: `systemctl stop postgresql && systemctl disable postgresql`
  
- **redis.service** - Redis cache
  - Status: STOPPED and DISABLED (process killed)
  - Command: `systemctl stop redis && systemctl disable redis`
  
- **mariadb.service** - MariaDB database
  - Status: STOPPED and DISABLED
  - Command: `systemctl stop mariadb && systemctl disable mariadb`

### 3. Web/Infrastructure Services
- **gitea.service** - Git repository server (Port 3000)
  - Status: STOPPED and DISABLED
  - Command: `systemctl stop gitea.service && systemctl disable gitea.service`
  
- **k3s.service** - Kubernetes cluster (AWX on port 30483)
  - Status: STOPPED and DISABLED
  - Command: `systemctl stop k3s.service && systemctl disable k3s.service`
  
- **nginx.service** - Was already stopped (Port 8080)

### 4. Scheduled Jobs
- **Crontab** - All scheduled jobs removed
  - Backup saved to: `/tmp/crontab_backup_20250702.txt`
  - Command: `crontab -r`

## Services Still Running (Required for Transfer)
- **sshd** - SSH daemon (Port 22) - ACTIVE for file transfers
- **systemd** - System management
- **NetworkManager** - Network connectivity

## Important Files/Directories for Migration

### Application Code
- `/usr/local/bin/Main/` - All Python scripts and templates
- `/usr/local/bin/templates/` - HTML templates
- `/etc/systemd/system/dsrcircuits.service` - Service configuration

### Database Backups Needed
- PostgreSQL database: `dsrcircuits`
- Database user: `dsradmin`

### Data Directories
- `/var/www/html/circuitinfo/` - CSV tracking data
- `/var/www/html/meraki-data/` - JSON/EOL data
- `/var/log/` - All DSR-related log files

### Configuration Files
- `/usr/local/bin/meraki.env` - Environment variables
- `/usr/local/bin/Main/config.py` - Database configuration

## Migration Steps (For New Server)

1. Transfer all files from `/usr/local/bin/`
2. Backup and restore PostgreSQL database
3. Install Python dependencies from requirements
4. Copy systemd service file
5. Update configuration for new server IPs/hostnames
6. Re-enable services on new server
7. Restore crontab from backup

## Verification Commands
```bash
# Check no web services are listening
netstat -tlnp | grep LISTEN

# Verify SSH is still accessible
systemctl status sshd

# Check disk usage for transfer planning
df -h /usr/local/bin
du -sh /usr/local/bin/Main
```

---
**Shutdown completed at:** July 2, 2025 12:32 PM EDT
**System ready for migration**