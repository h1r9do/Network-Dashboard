# Production Cleanup Action Plan

## Executive Summary
The production environment has template and static files in TWO different locations, causing confusion and potential bugs. We need to consolidate and clean up before creating the dev environment.

## Current State

### Templates
- **Flask serves from**: `/usr/local/bin/templates/`
- **Development in**: `/usr/local/bin/Main/templates/`
- **Issues**: Different versions of files, missing templates, Python file wrongly placed

### Static Files  
- **Flask serves from**: `/usr/local/bin/static/`
- **Development in**: `/usr/local/bin/Main/static/`
- **Issues**: Missing files between directories

### Python Scripts
- **Production modules**: Mixed with 250+ development scripts in Main/
- **No clear separation**: Test scripts, backups, utilities all mixed together

## Recommended Solution

### Phase 1: Immediate Fixes (Do First)

1. **Fix Wrong File Placement**
   ```bash
   # Remove Python file from templates directory
   sudo rm /usr/local/bin/templates/dsrcircuits_blueprint.py
   ```

2. **Update Flask Configuration**
   ```python
   # In /usr/local/bin/Main/dsrcircuits.py, change:
   app = Flask(__name__, 
       template_folder='/usr/local/bin/Main/templates',
       static_folder='/usr/local/bin/Main/static')
   ```

3. **Remove Old Directories** (after Flask update)
   ```bash
   # Backup first
   sudo tar -czf /tmp/old_templates_backup.tar.gz /usr/local/bin/templates/
   sudo tar -czf /tmp/old_static_backup.tar.gz /usr/local/bin/static/
   
   # Then remove
   sudo rm -rf /usr/local/bin/templates/
   sudo rm -rf /usr/local/bin/static/
   ```

### Phase 2: Clean Main Directory

1. **Create Organization Structure**
   ```bash
   # In /usr/local/bin/Main/
   mkdir -p dev_scripts
   mkdir -p archive
   mkdir -p utilities
   mkdir -p test_scripts
   ```

2. **Move Non-Production Files**
   ```bash
   # Move test scripts
   mv test_*.py test_scripts/
   
   # Move analysis scripts
   mv analyze_*.py dev_scripts/
   mv check_*.py dev_scripts/
   
   # Move backups
   mv *.bak archive/
   mv *.backup archive/
   mv *_backup_* archive/
   
   # Move utilities
   mv fix_*.py utilities/
   mv update_*.py utilities/
   mv create_*.py utilities/
   ```

3. **Production Structure**
   ```
   /usr/local/bin/Main/
   ├── dsrcircuits.py (main app)
   ├── config.py
   ├── models.py
   ├── utils.py
   ├── credential_manager.py
   ├── [blueprint modules - 16 files]
   ├── templates/ (all HTML templates)
   ├── static/ (CSS, JS, images)
   ├── nightly/ (scheduled scripts)
   ├── dev_scripts/ (development only)
   ├── test_scripts/ (testing only)
   ├── utilities/ (one-off scripts)
   └── archive/ (old backups)
   ```

### Phase 3: Create Dev Environment

After Main is clean, create Dev environment:

```bash
# Copy clean production to Dev
sudo cp -r /usr/local/bin/Main /usr/local/bin/Dev

# Update Dev configuration
# - Change port to 5053
# - Change database to dsrcircuits_dev
# - Add DEV indicator to UI
```

### Phase 4: Database Setup

1. **Create sync script** `/usr/local/bin/Dev/scripts/sync_prod_to_dev.py`
2. **Create dev database** with schema matching production
3. **Test sync process**

## Verification Steps

### Before Changes:
- [ ] Backup everything
- [ ] Document current production URL/port
- [ ] Test production is working
- [ ] Note which templates are actually in use

### After Each Phase:
- [ ] Production still works
- [ ] All pages load correctly
- [ ] No 404 errors for templates/static
- [ ] Check logs for errors

### Final Verification:
- [ ] Production runs from Main/ with clean structure
- [ ] Dev runs from Dev/ on port 5053
- [ ] Both can run simultaneously
- [ ] Database sync works
- [ ] No mixed files between environments

## Risk Mitigation

1. **Do changes during low traffic** (evening/weekend)
2. **Test each change immediately**
3. **Keep backups of working state**
4. **Have rollback commands ready**
5. **Monitor logs during changes**

## Rollback Plan

If issues occur:
```bash
# Revert Flask configuration
# Restore template/static directories from backup
sudo tar -xzf /tmp/old_templates_backup.tar.gz -C /
sudo tar -xzf /tmp/old_static_backup.tar.gz -C /

# Restart service
sudo systemctl restart meraki-dsrcircuits
```

## Benefits After Cleanup

1. **Clear separation**: Production vs Development
2. **Consistent paths**: Templates and static in Main/
3. **Clean structure**: Easy to understand and maintain
4. **Safe development**: Changes in Dev don't affect Prod
5. **Easy deployment**: Clear what files are production

## Next Steps

1. Review this plan
2. Schedule maintenance window
3. Execute Phase 1 (template/static fix)
4. Test production thoroughly
5. Execute Phase 2 (directory cleanup)
6. Execute Phase 3 (create Dev)
7. Document new structure

**Estimated Time**: 2-3 hours total
**Risk Level**: Medium (due to template path changes)
**Impact**: Temporary downtime possible during Flask restart