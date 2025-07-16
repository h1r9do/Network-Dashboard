# VLAN Migration - Quick Reference Guide

## 🚀 Quick Migration Steps

### 1. Navigate to Scripts Directory
```bash
cd /usr/local/bin/Main/
```

### 2. Run Migration (Choose One)

**Interactive Mode (with confirmation):**
```bash
python3 vlan_migration_complete.py --network-id <NETWORK_ID>
```

**Automated Mode (no confirmation):**
```bash
SKIP_CONFIRMATION=1 python3 vlan_migration_complete.py --network-id <NETWORK_ID>
```

### 3. Validate Results
```bash
python3 detailed_rule_comparison.py
```

Expected: 55 rules, 100% match

---

## 📋 Pre-Flight Checklist

- [ ] Network ID identified (e.g., L_3790904986339115852)
- [ ] File present: `neo07_54_rule_template_20250710_105817.json`
- [ ] Maintenance window scheduled (3-5 minutes)
- [ ] Backup created (optional but recommended)

---

## 🔄 VLAN Mapping Reference

| Old → New | Purpose |
|-----------|---------|
| 1 → 100 | Data |
| 101 → 200 | Voice |
| 801 → 400 | IoT |
| 201 → 410 | Credit Card |

---

## 🛟 Emergency Rollback

**If something goes wrong:**
```bash
# Option 1: Quick restore (if backup exists)
python3 restore_tst01_production_ready.py

# Option 2: From migration backup
python3 restore_from_backup.py --backup-file complete_vlan_backup_*.json
```

---

## ✅ Success Indicators

1. **Rule Count:** Exactly 55 rules
2. **Match Rate:** 100% when compared to NEO 07
3. **VLANs:** Shows 100, 200, 400, 410 (not 1, 101, 801, 201)
4. **No Errors:** Migration completes without errors

---

## 📞 Common Network IDs

- **TST 01:** L_3790904986339115852
- **NEO 07:** L_3790904986339115847
- **AZP 30:** L_3790904986339114669

---

**Migration Time:** ~2-3 minutes  
**Tested:** July 10, 2025  
**Success Rate:** 100%