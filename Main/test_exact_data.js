// Test the exact data that the JavaScript filter sees for CAL 07

// Simulate the exact row data that DataTables passes to the filter
var cal07Data = ["CAL 07", "AT&T Broadband II", "300.0M x 300.0M", "$105.01", "VZW Cell", "Cell", "$0.00", "Edit"];

// Copy the EXACT filter function from dsrcircuits.html
function testNotVisionReadyFilter(data) {
    var wan1Speed = data[2].trim();
    var wan2Speed = data[5].trim();
    var wan1Provider = data[1].trim();
    var wan2Provider = data[4].trim();
    
    // Parse speed values (e.g., "100.0M x 10.0M" -> {download: 100.0, upload: 10.0})
    function parseSpeed(speedStr) {
        if (!speedStr || speedStr === 'N/A' || speedStr === 'null' || 
            speedStr === 'Cell' || speedStr === 'Satellite' || 
            speedStr === 'TBD' || speedStr === 'Unknown') {
            return null;
        }
        
        var match = speedStr.match(/^([\d.]+)M\s*[xX]\s*([\d.]+)M$/);
        if (match) {
            return {
                download: parseFloat(match[1]),
                upload: parseFloat(match[2])
            };
        }
        return null;
    }
    
    // Check if speed is considered "low" (under 100M download OR under 10M upload)
    function isLowSpeed(speed) {
        if (!speed) return false;
        return speed.download < 100.0 || speed.upload < 10.0;
    }
    
    // Check if connection is cellular
    function isCellular(speedStr) {
        return speedStr === 'Cell';
    }
    
    // Check if provider indicates cellular service
    function isCellularProvider(providerStr) {
        if (!providerStr) return false;
        
        // Extract text from HTML if needed
        var provider = providerStr;
        if (provider.includes('<')) {
            var tempDiv = document.createElement('div');
            tempDiv.innerHTML = provider;
            provider = tempDiv.textContent || tempDiv.innerText || '';
        }
        
        // Convert to uppercase for case-insensitive comparison
        provider = provider.toUpperCase();
        
        // Check for cellular indicators in provider name
        return provider.includes('AT&T') || 
               provider.includes('VERIZON') || 
               provider.includes('VZW') ||
               provider.includes('CELL') ||
               provider.includes('CELLULAR') ||
               provider.includes('WIRELESS');
    }
    
    // Parse speeds
    var wan1ParsedSpeed = parseSpeed(wan1Speed);
    var wan2ParsedSpeed = parseSpeed(wan2Speed);
    
    // Exclude satellite
    if (wan1Speed === 'Satellite' || wan2Speed === 'Satellite') {
        return false;
    }
    
    // Check if one has low speed and the other is cellular
    var wan1IsLowSpeed = isLowSpeed(wan1ParsedSpeed);
    var wan2IsLowSpeed = isLowSpeed(wan2ParsedSpeed);
    var wan1IsCellular = isCellular(wan1Speed) || isCellularProvider(wan1Provider);
    var wan2IsCellular = isCellular(wan2Speed) || isCellularProvider(wan2Provider);
    
    // Site qualifies if:
    // Scenario 1: BOTH WAN1 and WAN2 are cellular
    // Scenario 2: WAN1 has low speed AND WAN2 is cellular
    // Scenario 3: WAN2 has low speed AND WAN1 is cellular
    var bothCellular = wan1IsCellular && wan2IsCellular;
    var lowSpeedWithCellular = (wan1IsLowSpeed && wan2IsCellular) || (wan2IsLowSpeed && wan1IsCellular);
    
    console.log("=== CAL 07 Filter Analysis ===");
    console.log("WAN1 Speed:", wan1Speed);
    console.log("WAN2 Speed:", wan2Speed);
    console.log("WAN1 Provider:", wan1Provider);
    console.log("WAN2 Provider:", wan2Provider);
    console.log("WAN1 Parsed Speed:", JSON.stringify(wan1ParsedSpeed));
    console.log("WAN2 Parsed Speed:", JSON.stringify(wan2ParsedSpeed));
    console.log("WAN1 Low Speed:", wan1IsLowSpeed);
    console.log("WAN2 Low Speed:", wan2IsLowSpeed);
    console.log("WAN1 Cellular:", wan1IsCellular, "(speed:", isCellular(wan1Speed), "provider:", isCellularProvider(wan1Provider), ")");
    console.log("WAN2 Cellular:", wan2IsCellular, "(speed:", isCellular(wan2Speed), "provider:", isCellularProvider(wan2Provider), ")");
    console.log("Both Cellular:", bothCellular);
    console.log("Low Speed + Cellular:", lowSpeedWithCellular);
    console.log("*** FILTER RESULT:", bothCellular || lowSpeedWithCellular, "***");
    
    return bothCellular || lowSpeedWithCellular;
}

// Test CAL 07
var result = testNotVisionReadyFilter(cal07Data);
console.log("\nFINAL RESULT: CAL 07 should", result ? "SHOW" : "HIDE", "in Not Vision Ready filter");

// Test a few other examples that should work
console.log("\n=== Testing Other Examples ===");

// Test ALB 03 (has VZW Cell secondary)
var alb03Data = ["ALB 03", "Spectrum", "600.0M x 35.0M", "$172.23", "VZW Cell", "Cell", "$0.00", "Edit"];
var alb03Result = testNotVisionReadyFilter(alb03Data);
console.log("ALB 03 should", alb03Result ? "SHOW" : "HIDE", "in Not Vision Ready filter");

// Test perfect Cell/Cell example
var testData = ["TEST 01", "AT&T", "Cell", "$50.00", "Verizon", "Cell", "$50.00", "Edit"];
var testResult = testNotVisionReadyFilter(testData);
console.log("TEST CELL/CELL should", testResult ? "SHOW" : "HIDE", "in Not Vision Ready filter");