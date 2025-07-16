# Production Issues and Required Fixes

## Critical Issues Found

### 1. Template Directory Mismatch
**Current Situation:**
- Flask app is configured to serve templates from: `/usr/local/bin/templates/`
- Actual development work happens in: `/usr/local/bin/Main/templates/`
- This means Flask may be serving old/different templates than what's being edited

**Evidence:**
```python
# In dsrcircuits.py
app = Flask(__name__, 
    template_folder='/usr/local/bin/templates',
    static_folder='/usr/local/bin/static')
```

### 2. Static Files Directory Mismatch
**Current Situation:**
- Flask serves static files from: `/usr/local/bin/static/`
- Development static files are in: `/usr/local/bin/Main/static/`
- CSS/JS changes in Main/static may not be reflected in production

### 3. Mixed Production and Development Files
**Current Situation:**
- Main directory has 316 Python files
- Only ~30 are actual production modules
- 250+ are development/test/utility scripts
- 63 backup files (.bak, .backup, etc.)

## Required Fixes - Step by Step

### Phase 1: Document Current State
1. **Check which templates Flask is actually serving**
   - Compare `/usr/local/bin/templates/` vs `/usr/local/bin/Main/templates/`
   - Identify any differences
   - Document which version is "live"

2. **Check static files**
   - Compare `/usr/local/bin/static/` vs `/usr/local/bin/Main/static/`
   - Identify differences
   - Document which version is "live"

3. **Verify systemd service**
   - Confirm which dsrcircuits.py is running
   - Check working directory
   - Verify all imports are working

### Phase 2: Fix Template/Static Serving
**Option A: Update Flask Configuration (Recommended)**
```python
# Update dsrcircuits.py to use Main directory
app = Flask(__name__, 
    template_folder='/usr/local/bin/Main/templates',
    static_folder='/usr/local/bin/Main/static')
```

**Option B: Move Files to Expected Location**
- Copy Main/templates/* to /usr/local/bin/templates/
- Copy Main/static/* to /usr/local/bin/static/
- Remove Main/templates and Main/static

### Phase 3: Clean Production Directory
1. **Move Development Scripts**
   ```
   /usr/local/bin/Main/dev_scripts/  (new directory)
   - Move all test_*.py files
   - Move all analyze_*.py files
   - Move all check_*.py files
   - Move all utility scripts
   ```

2. **Archive Backup Files**
   ```
   /usr/local/bin/Main/archive/
   - Move all *.bak files
   - Move all *.backup files
   - Move all *_backup_* files
   ```

3. **Keep Only Production Files in Main**
   - Core application files
   - Active blueprint modules
   - Nightly scripts in nightly/
   - Templates in templates/
   - Static files in static/

### Phase 4: Create Clean Dev Environment
As per original plan, but with corrected structure:
```
/usr/local/bin/Dev/
├── dsrcircuits.py (port 5053)
├── [all production modules]
├── templates/ (clean copy)
├── static/ (clean copy)
├── nightly/ (not scheduled)
└── scripts/ (dev utilities)
```

## Verification Checklist

### Before Making Changes:
- [ ] Backup current production state
- [ ] Document which templates are actually being served
- [ ] Test current production is working
- [ ] Check all blueprint imports
- [ ] Verify nightly scripts are running

### After Changes:
- [ ] Production app starts correctly
- [ ] All pages load with correct templates
- [ ] Static files (CSS/JS) load correctly
- [ ] All blueprints still work
- [ ] Nightly scripts still function
- [ ] Dev environment works independently

## Risk Assessment

### High Risk Items:
1. **Template Path Change** - Could break all page rendering
2. **Static Path Change** - Could break CSS/JS loading
3. **Import Path Issues** - Moved files might break imports

### Mitigation:
1. Test changes during low-traffic period
2. Have rollback plan ready
3. Test thoroughly in dev first
4. Keep backups of working state

## Recommended Approach

1. **First**: Fix the template/static serving issue in production
2. **Second**: Clean up Main directory by moving non-production files
3. **Third**: Create clean Dev environment with proper structure
4. **Fourth**: Document the new structure for future developers

This ensures production is stable and properly organized before creating the development environment.