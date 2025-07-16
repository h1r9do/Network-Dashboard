# DSR Circuits - Quick Reference Card

## 🚀 Essential Information

**System URL**: http://10.46.0.3:5052  
**Service**: `dsrcircuits.service`  
**Version**: 2.0.0-production-database  
**Location**: `/usr/local/bin/Main/`  

## 🔧 Most Common Commands

```bash
# Service Management
systemctl status dsrcircuits.service
systemctl restart dsrcircuits.service
journalctl -u dsrcircuits.service -f

# Quick Health Check
curl http://localhost:5052/api/health | jq .
curl http://localhost:5052/api/stats/quick | jq .

# Database Access
psql -U dsradmin -d dsrcircuits -h localhost
```

## 📍 Key Pages

- **Main Circuits**: `/dsrcircuits`
- **Dashboard**: `/dsrdashboard`
- **Historical**: `/dsrhistorical`
- **Firewall**: `/firewall`
- **Reports**: `/circuit-enablement-report`

## 📁 Important Files

- **Main App**: `dsrcircuits_integrated.py`
- **Config**: `config.py`
- **Models**: `models.py`
- **Firewall Script**: `nightly_meraki_db.py`

## 🆘 Emergency Recovery

1. Stop service: `systemctl stop dsrcircuits.service`
2. Test manually: `cd /usr/local/bin/Main && python3 dsrcircuits_integrated.py`
3. Check logs: `tail -100 /var/log/dsrcircuits.log`
4. Rollback plan: See `MIGRATION_ROLLBACK_PLAN.md`

## 📊 Database Info

- **Database**: dsrcircuits
- **User**: dsradmin
- **Main Tables**: circuits, circuit_history, firewall_rules
- **Total Circuits**: 4,171+
- **Firewall Rules**: 55 (NEO 07 template)

---
*For detailed information, see CLAUDE.md*