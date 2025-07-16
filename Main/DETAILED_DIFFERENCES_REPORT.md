# Detailed Differences Report: TST 01 vs NEO 07

**Generated:** July 10, 2025  
**Purpose:** Document exact differences before any configuration changes

## 1. VLAN Differences

### VLANs Present in Both Networks
| VLAN ID | TST 01 Name | NEO 07 Name | TST 01 Subnet | NEO 07 Subnet | Match |
|---------|-------------|-------------|---------------|---------------|-------|
| 100 | Data | Data | 10.255.255.0/26 | 10.24.38.0/25 | ❌ Different subnets |
| 200 | Voice | Voice | 10.255.255.128/27 | 10.24.38.128/27 | ❌ Different subnets |
| 300 | AP Mgmt | Net Mgmt | 10.255.255.176/28 | 10.24.38.176/28 | ❌ Different names & subnets |
| 400 | Ccard | IoT | 10.255.255.160/28 | 172.16.40.0/24 | ❌ Different names & subnets |
| 410 | Scanner | Ccard | 10.255.255.192/28 | 10.24.38.160/28 | ❌ Different names & subnets |
| 800 | Guest | Guest | 172.13.0.0/30 | 172.16.80.0/24 | ❌ Different subnets |
| 801 | IOT | IoT Wireless | 172.14.0.0/24 | 172.16.81.0/24 | ❌ Different names & subnets |
| 900 | Mgmt | Mgmt | 10.255.255.252/30 | 10.24.38.252/30 | ❌ Different subnets |

### VLANs Only in TST 01
| VLAN ID | Name | Subnet | Purpose |
|---------|------|--------|---------|
| 802 | IoT Network | 172.21.0.0/24 | Extra test VLAN |
| 803 | IoT Wireless | 172.22.0.0/24 | Extra test VLAN |

### VLANs Only in NEO 07
| VLAN ID | Name | Subnet | Purpose |
|---------|------|--------|---------|
| 301 | Scanner | 10.24.38.192/28 | Original scanner VLAN (pre-migration) |

## 2. Critical VLAN Analysis

### TST 01 Status: Post-Migration State
- ✅ Has new VLAN numbers (100, 200, 400, 410)
- ❌ Missing original VLAN 301 (scanner)
- ✅ Uses test IP ranges (10.255.255.x)

### NEO 07 Status: Pre-Migration State  
- ✅ Has original VLAN 301 (scanner)
- ✅ Has some new VLAN numbers (100, 200, 400, 410)
- ❌ Mixed migration state - **INCONSISTENT**
- ✅ Uses production IP ranges (10.24.38.x)

**⚠️ IMPORTANT:** NEO 07 appears to be in a **mixed migration state** with both old (301) and new (410) scanner VLANs present.

## 3. Firewall Rules Comparison

### TST 01: Minimal Configuration
- **Rule Count:** 2 rules
- **Type:** Default allow rules only
- **Security:** ❌ No production security policies
- **VLAN References:** None

### NEO 07: Full Production Configuration
- **Rule Count:** 55 rules
- **Type:** Complete security policy set
- **Security:** ✅ Production-grade restrictions
- **VLAN References:** Extensive (100, 200, 300, 301, 400, 410, 800)

#### NEO 07 Firewall Rule Categories:
1. **Security Blocks** (3 rules)
   - Scam website blocking
   - Guest network isolation
   - RFC1918 restrictions

2. **Application Access** (15 rules)
   - Gmail, Office365, MS Teams
   - VoIP (Polycom) configurations
   - VTV mobile app APIs

3. **Network Segmentation** (12 rules)
   - VLAN-to-VLAN access control
   - Scanner and credit card isolation
   - IoT network restrictions

4. **Infrastructure** (8 rules)
   - Meraki cloud communication
   - NTP, DHCP, DNS services
   - Backup and monitoring

5. **Default Policies** (17 rules)
   - Final deny rules
   - Default allow fallback

## 4. MX Port Configuration Differences

### Port-by-Port Analysis:

| Port | TST 01 | NEO 07 | Key Differences |
|------|--------|--------|-----------------|
| 3 | Trunk, enabled, VLAN 900 only | Trunk, **disabled**, all VLANs | Status & VLAN scope |
| 4 | Trunk, enabled, **no VLANs** | Trunk, enabled, specific VLAN list | Missing VLAN config |
| 5 | Trunk, enabled, **no VLANs** | Trunk, enabled, specific VLAN list | Missing VLAN config |
| 6 | Trunk, enabled, **no VLANs** | Trunk, enabled, specific VLAN list | Missing VLAN config |
| 7 | Trunk, disabled, all VLANs | Trunk, disabled, all VLANs | ✅ **MATCH** |
| 8 | Trunk, enabled, **no VLANs** | Trunk, **disabled**, all VLANs | Status difference |
| 9 | **Access**, enabled, no VLAN | **Trunk**, disabled, all VLANs | Type mismatch |
| 10 | Trunk, enabled, **no VLANs** | Trunk, **disabled**, all VLANs | Status difference |
| 11 | Trunk, disabled, all VLANs | Trunk, disabled, all VLANs | ✅ **MATCH** |
| 12 | Trunk, enabled, **no VLANs** | Trunk, **disabled**, all VLANs | Status difference |

**Critical Issues:**
- TST 01 ports 4, 5, 6, 10, 12 have **no VLAN assignments**
- Most ports have wrong enabled/disabled status
- Port 9 has wrong type (access vs trunk)

## 5. Switch Port Usage Patterns

### VLAN Distribution:
| Network | VLAN 100 | VLAN 300 | VLAN 400/410 | Other |
|---------|----------|----------|--------------|-------|
| TST 01 | 7 ports | 4 ports | 3 ports | 14 ports |
| NEO 07 | 14 ports | 5 ports | 5 ports | 4 ports |

**Analysis:** NEO 07 has more balanced production usage patterns.

## 6. Group Policy Differences

### Policy Comparison:
| Policy Name | TST 01 ID | NEO 07 ID | Status |
|-------------|-----------|-----------|--------|
| Guest Network | 102 | 100 | Different IDs |
| Indeed.com | 101 | 101 | ✅ Same ID |
| Ebay Access | 100 | 102 | Different IDs |
| Untrusted | ❌ Missing | 103 | NEO 07 only |

## 7. Configuration State Analysis

### TST 01: Test Environment
- **IP Ranges:** Isolated test ranges (10.255.255.x)
- **Security:** Relaxed for testing
- **VLANs:** Post-migration numbering
- **Complexity:** Simplified configuration

### NEO 07: Production Store
- **IP Ranges:** Production ranges (10.24.38.x)  
- **Security:** Full production policies
- **VLANs:** **Mixed migration state** ⚠️
- **Complexity:** Full production complexity

## 8. Migration Testing Implications

### Current State Issues:
1. **TST 01 doesn't represent true pre-migration state**
2. **NEO 07 appears partially migrated already**
3. **Testing won't validate production firewall complexity**
4. **MX port configurations don't match production patterns**

### For Realistic Testing, TST 01 Needs:
1. ✅ All 55 production firewall rules
2. ✅ Proper MX port trunk configurations  
3. ✅ Production-like VLAN usage patterns
4. ✅ All group policies including "Untrusted"
5. ✅ Original pre-migration VLAN state (301 instead of 410)

## 9. Recommended Actions

### Option A: Test Current Script Functionality ✅
- Keep TST 01 as-is
- Validates basic migration mechanics
- ⚠️ Limited production scenario coverage

### Option B: Create Production Replica ✅ Recommended
- Copy NEO 07 complete config to TST 01
- Use test IP ranges (10.255.255.x)
- Test with full production complexity
- Validate all edge cases

### Option C: Test on True Pre-Migration State
- Reset NEO 07 VLAN 410 back to 301
- Copy that pre-migration state to TST 01
- Test complete legacy → new migration

---

**Decision Point:** Which testing approach do you want to pursue for the next round of VLAN migration testing?