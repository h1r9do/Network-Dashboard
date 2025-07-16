# Template Directory Analysis

## Current Situation

Flask is configured to serve from: `/usr/local/bin/templates/`
Development happens in: `/usr/local/bin/Main/templates/`

## Critical Findings

### 1. BOTH Directories Exist with Different Contents

**Files in `/usr/local/bin/templates/` but NOT in `/usr/local/bin/Main/templates/`:**
- dsrcircuits_blueprint.py (75KB - July 12) - **This is a Python file in templates!**
- collected_inventory.html (17KB - July 4)
- dsrcircuits_beta_no_roles.html (58KB - July 9)

**Files in `/usr/local/bin/Main/templates/` but NOT in `/usr/local/bin/templates/`:**
- documentation_index.html (4KB - July 3)
- dsrcircuits_beta.html (53KB - July 9)

### 2. Files That Exist in BOTH But May Differ

| File | /usr/local/bin/templates/ | /usr/local/bin/Main/templates/ | Same? |
|------|---------------------------|--------------------------------|-------|
| dsrcircuits.html | 98097 bytes (Jul 13 12:17) | 98097 bytes (Jul 13 12:17) | YES |
| dsrcircuits_edit.html | 94794 bytes (Jul 13 11:42) | 94794 bytes (Jul 13 11:42) | YES |
| circuit_enablement_report.html | 65264 bytes (Jul 7 07:36) | 65264 bytes (Jul 7 07:33) | Likely YES |
| dsrallcircuits.html | 15921 bytes (Jul 11 18:09) | 24681 bytes (Jul 11 17:47) | **NO - Different!** |

### 3. Issues Found

1. **Python file in templates directory**: `dsrcircuits_blueprint.py` is in `/usr/local/bin/templates/` - this should NOT be there!
2. **Different versions**: `dsrallcircuits.html` has different versions in each location
3. **Missing templates**: Some templates only exist in one location or the other
4. **Inconsistent updates**: Files are being edited in different locations

## Which Templates is Flask Actually Using?

Flask is configured to use `/usr/local/bin/templates/`, so:
- ✅ Using: `/usr/local/bin/templates/dsrcircuits.html`
- ✅ Using: `/usr/local/bin/templates/circuit_enablement_report.html`
- ❌ NOT Using: `/usr/local/bin/Main/templates/dsrcircuits_beta.html`
- ⚠️ Using OLD version: `/usr/local/bin/templates/dsrallcircuits.html` (smaller/older file)

## Immediate Actions Required

### 1. Remove Non-Template Files
```bash
# This Python file should NOT be in templates directory
rm /usr/local/bin/templates/dsrcircuits_blueprint.py
```

### 2. Sync Critical Templates
```bash
# Copy newer dsrallcircuits.html to production location
cp /usr/local/bin/Main/templates/dsrallcircuits.html /usr/local/bin/templates/
```

### 3. Decision Required
**Option A**: Change Flask to use Main/templates (Recommended)
- Update dsrcircuits.py to point to /usr/local/bin/Main/templates/
- Remove /usr/local/bin/templates/ directory entirely
- All development continues in Main/templates/

**Option B**: Keep using /usr/local/bin/templates/
- Copy all templates from Main/templates/ to /usr/local/bin/templates/
- Remove Main/templates/ directory
- Update development workflow to use /usr/local/bin/templates/

## Static Files Analysis Needed

Similar issue likely exists with static files:
- Flask uses: `/usr/local/bin/static/`
- Development in: `/usr/local/bin/Main/static/`

Need to check which CSS/JS files are actually being served.