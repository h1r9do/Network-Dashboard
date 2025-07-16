# Not Vision Ready Filter - Bug Fixes (July 14, 2025)

## Issues Fixed

### 1. **Incorrect Speed Logic (Critical)**
**Problem**: The `isLowSpeed()` function was using AND logic instead of OR logic.
- **Previous**: `speed.download < 100.0 && speed.upload < 10.0` (both must be low)
- **Fixed**: `speed.download < 100.0 || speed.upload < 10.0` (either can be low)

**Impact**: Sites with good download but low upload (e.g., 150M x 5M) were not being identified as "Not Vision Ready", even though 5M upload is insufficient for Vision technology.

### 2. **Null Handling Bug (Critical)**
**Problem**: When speed was "Cell" or couldn't be parsed, the function returned `null`, causing boolean operations to fail.
- **Previous**: `return speed && (condition)` - could return `null`
- **Fixed**: `if (!speed) return false;` - always returns boolean

**Impact**: Sites with cellular connections were not being properly evaluated, causing the filter to return `undefined` instead of `true/false`.

### 3. **Upload Speed Threshold (Minor)**
**Problem**: Used `<= 10.0` instead of `< 10.0` for upload speed.
- **Previous**: `speed.upload <= 10.0` (included 10M as "low")
- **Fixed**: `speed.upload < 10.0` (10M meets minimum requirement)

## Filter Logic (Corrected)

### Scenarios that Match "Not Vision Ready":

1. **Both circuits are cellular**
   - Speed field = "Cell" OR provider contains AT&T/Verizon/VZW/Cell/Cellular/Wireless
   - Example: AT&T Broadband (300M) + VZW Cell

2. **Low speed + cellular combination**
   - One circuit has speed < 100M download OR < 10M upload
   - Other circuit is cellular
   - Examples:
     - 10M x 10M (low download) + AT&T Cell ✅
     - 100M x 5M (low upload) + AT&T Cell ✅ 
     - 100M x 10M (good) + AT&T Cell ❌

### Exclusions:
- Satellite connections (excluded entirely)
- Sites without Discount-Tire tag
- Hub/lab/voice/test sites
- Sites without IP addresses

## Files Updated

### 1. `/usr/local/bin/templates/dsrcircuits.html` (Production)
```javascript
// Fixed function
function isLowSpeed(speed) {
    if (!speed) return false;
    return speed.download < 100.0 || speed.upload < 10.0;
}
```

### 2. `/usr/local/bin/Main/templates/dsrcircuits.html` (Development)
- Applied same fix for consistency

## Test Results

Created comprehensive test suite that validates:
- ✅ Both cellular scenarios
- ✅ Low download + cellular  
- ✅ Low upload + cellular
- ✅ Good speeds (no match)
- ✅ Edge cases (100M x 10M = good)
- ✅ Satellite exclusion

## Validation Examples

| Site | WAN1 | WAN2 | Result | Reason |
|------|------|------|---------|---------|
| CAL 07 | AT&T (300M x 30M) | VZW Cell | ✅ Match | Both cellular |
| AZP 56 | Comcast (10M x 10M) | AT&T Cell | ✅ Match | Low download + cellular |
| COD 06 | Lumen (100M x 5M) | AT&T Cell | ✅ Match | Low upload + cellular |
| Good Site | Comcast (200M x 20M) | Charter (100M x 10M) | ❌ No match | Meets requirements |
| Edge Case | Comcast (100M x 10M) | Charter (100M x 10M) | ❌ No match | Meets requirements |

## Service Restart

Flask service restarted to apply changes:
```bash
sudo systemctl restart meraki-dsrcircuits.service
```

**Status**: ✅ All fixes applied and tested. Filter now correctly identifies sites that are not ready for Vision technology deployment.