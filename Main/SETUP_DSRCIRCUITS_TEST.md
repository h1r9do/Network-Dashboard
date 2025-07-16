# Setup Instructions for DSR Circuits Test

## ✅ Completed Setup

1. **Database Tables Created**
   - ✅ `provider_mappings` table with 46 mappings
   - ✅ `provider_match_test` table for testing
   - ✅ Views: `provider_match_test_display`, `provider_test_statistics`

2. **Test Data Populated**
   - ✅ 14 test circuits with provider matching results
   - ✅ Match rate: 57% (8/14 circuits matched)
   - ✅ Sample data includes real provider mappings

3. **Code Files Ready**
   - ✅ `test_routes.py` - Flask routes to add to dsrcircuits.py
   - ✅ `dsrcircuits_test_simple.html` - HTML template
   - ✅ `simple_test_populate.py` - Script to add more test data

## 🔧 Manual Setup Required

### Step 1: Add Routes to dsrcircuits.py

Add the following routes from `test_routes.py` to your main `dsrcircuits.py` file:

```python
@app.route('/dsrcircuits-test')
@app.route('/api/circuit-matches-test/<site_name>')
@app.route('/api/test-statistics')
@app.route('/api/test-no-matches')
@app.route('/test-site/<site_name>')
```

### Step 2: Copy HTML Template

Copy the template file:
```bash
sudo cp /usr/local/bin/Main/dsrcircuits_test_simple.html /usr/local/bin/Main/templates/dsrcircuits_test.html
```

### Step 3: Restart Flask Service

```bash
sudo systemctl restart meraki-dsrcircuits.service
```

### Step 4: Test the Interface

Visit: http://neamsatcor1ld01.trtc.com:5052/dsrcircuits-test

## 📊 Current Test Results

```
Total circuits: 14
Matched: 8  
Match rate: 57.14%
Average confidence: 84.4%

Sample Matches:
- AT&T Broadband II → AT&T (100%)
- Brightspeed → CenturyLink (90%) 
- Spectrum → Charter Communications (95%)
```

## 🧪 Test Features Available

1. **Statistics Dashboard**
   - Total circuits processed
   - Match rate percentage
   - Confidence distribution

2. **Sample Results Table**
   - Site-by-site circuit matching
   - Color-coded confidence levels
   - Match reasoning display

3. **Interactive Features**
   - "No Matches" modal for analysis
   - Site-specific testing
   - Real-time statistics

4. **API Endpoints**
   - `/api/test-statistics` - Overall stats
   - `/api/test-no-matches` - Failed matches
   - `/api/circuit-matches-test/<site>` - Site-specific data

## 🔄 Add More Test Data

To populate with more real data:

```bash
python3 /usr/local/bin/Main/simple_test_populate.py
```

This will add more circuits from your production data to test the matching logic.

## 🎯 Expected Test URL

Once setup is complete, the test interface will be available at:
**http://neamsatcor1ld01.trtc.com:5052/dsrcircuits-test**

## 📝 Next Steps After Testing

1. Review test results and match accuracy
2. Adjust provider mappings as needed
3. Apply the same logic to production enrichment scripts
4. Update main dsrcircuits modal to use the enhanced matching

---

**Current Status**: Ready for manual integration into dsrcircuits.py