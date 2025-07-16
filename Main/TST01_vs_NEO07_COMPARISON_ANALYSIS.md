# TST 01 vs NEO 07 Network Configuration Comparison

**Date:** July 10, 2025  
**Purpose:** Comprehensive comparison to identify differences before testing VLAN migration

## Executive Summary

The comparison reveals **significant differences** between TST 01 (test network) and NEO 07 (production store). TST 01 appears to be a modified test environment that doesn't fully represent a production store configuration.

## Key Differences Identified

### 1. VLAN Configuration

| Aspect | TST 01 | NEO 07 | Notes |
|--------|--------|--------|-------|
| Total VLANs | 10 | 9 | TST 01 has extra test VLANs |
| VLAN 301 | ❌ Missing | ✅ Present | NEO 07 has original scanner VLAN |
| VLAN 802/803 | ✅ Present | ❌ Missing | TST 01 has extra IoT VLANs |
| IP Ranges | Test ranges (10.255.255.x) | Production (10.24.38.x) | Different subnets |

#### VLAN Details:
- **TST 01 has migrated VLANs:** 100, 200, 400, 410 (new numbering)
- **NEO 07 has legacy VLANs:** 100, 200, 301, 400, 410 (mixed old/new)
- **IP Range Difference:** TST 01 uses test range 10.255.255.x vs NEO 07 production 10.24.38.x

### 2. Firewall Rules

| Network | Rule Count | Status |
|---------|------------|--------|
| TST 01 | 2 rules | **Minimal test config** |
| NEO 07 | 55 rules | **Full production config** |

**Critical Gap:** TST 01 has only default allow rules, missing all production security policies:
- No security blocks (scam sites, RFC1918 restrictions)
- No application-specific rules (Gmail, Office365, VoIP)
- No scanner/credit card isolation rules
- No VTV/AirWatch mobile device rules

### 3. MX Port Configuration

**Major Differences:**
- **Port 3:** TST 01 allows only VLAN 900, NEO 07 allows all VLANs
- **Ports 4-6:** TST 01 missing VLAN assignments, NEO 07 has specific VLAN lists
- **Most ports enabled in TST 01** vs **most disabled in NEO 07**

### 4. Switch Port Usage

| Metric | TST 01 | NEO 07 |
|--------|--------|--------|
| VLAN 100 usage | 7 ports | 14 ports |
| Trunk ports | 4 ports | 5 ports |
| VLAN distribution | More test VLANs | Production pattern |

### 5. Group Policies

- **TST 01:** 3 policies (test-focused)
- **NEO 07:** 4 policies (includes "Untrusted" security policy)
- **Different IDs:** Same policy names have different IDs

## Root Cause Analysis

### Why TST 01 Differs from NEO 07:

1. **Test Environment Setup:** TST 01 was configured as a test network with simplified rules
2. **IP Range Isolation:** Uses test IP ranges to avoid conflicts
3. **Security Relaxed:** Firewall rules stripped down for testing
4. **Previous Migration Test:** Shows evidence of partial VLAN migration (has both old and new VLAN numbers)

## Impact on VLAN Migration Testing

### ✅ Positive Aspects:
- VLAN migration script functionality can be tested
- Basic network structure validation works
- Port assignment logic verification possible

### ⚠️ Limitations:
- **Does not test production firewall rule complexity**
- **Missing complex trunk port configurations**
- **No real-world security policy interactions**
- **Simplified VLAN interdependencies**

## Recommendations for Better Testing

### 1. Create Production-Like Test Environment
```bash
# Copy complete NEO 07 configuration to TST 01
python3 apply_exact_config.py --source-network NEO_07 --target-network TST_01
```

### 2. Apply Production Firewall Rules
```bash
# Apply the 55 NEO 07 firewall rules to TST 01
python3 apply_firewall_template.py --template neo07_firewall_template_20250710.json --network TST_01
```

### 3. Configure Production-Like MX Ports
- Set trunk configurations matching NEO 07
- Configure proper VLAN assignments
- Test complex allowed VLAN lists

### 4. Test Migration Scenarios

#### Scenario A: Simple Test (Current)
- Minimal firewall rules
- Basic VLAN setup
- ✅ **Good for script functionality testing**

#### Scenario B: Production Replica (Recommended)
- Full 55 firewall rules
- Complex trunk port configurations
- Real VLAN interdependencies
- ✅ **Required for production readiness validation**

## Next Steps

1. **Restore TST 01 to match NEO 07 configuration exactly**
2. **Run VLAN migration on production-like setup**
3. **Test with full firewall rule complexity**
4. **Validate trunk port VLAN list updates**
5. **Verify group policy interactions**

## Files Needed for Production Testing

1. `neo07_complete_config.json` - Full NEO 07 configuration
2. `neo07_firewall_template_20250710.json` - 55 production firewall rules
3. `neo07_mx_ports_config.json` - MX port configurations
4. `neo07_switch_configs.json` - Switch port configurations

## Risk Assessment

**Current Testing:** ⚠️ **Medium Risk** - Basic functionality validated but production complexity untested

**With Production Config:** ✅ **Low Risk** - Full validation of production scenarios

---

**Conclusion:** TST 01 should be reconfigured to exactly match NEO 07 before conducting final migration validation testing.