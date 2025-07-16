// Test the cell detection logic from dsrcircuits.html

function parseSpeed(speedStr) {
    if (!speedStr || speedStr === 'N/A' || speedStr === 'null' || speedStr === '') {
        return null;
    }
    
    var match = speedStr.match(/^(\d+\.?\d*)M\s*x\s*(\d+\.?\d*)M$/i);
    if (match) {
        return {
            download: parseFloat(match[1]),
            upload: parseFloat(match[2])
        };
    }
    
    return null;
}

function isLowSpeed(speed) {
    if (!speed) return false;
    return speed.download < 100.0 || speed.upload < 10.0;
}

function isCellular(speedStr) {
    return speedStr === 'Cell';
}

function isCellularProvider(providerStr) {
    if (!providerStr) return false;
    
    // Extract text from HTML if needed (simplified for Node.js)
    var provider = providerStr;
    
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

// Test data from database
var testCases = [
    {
        name: "CAL 07",
        wan1Speed: "300.0M x 300.0M",
        wan2Speed: "",
        wan1Provider: "AT&T Broadband II",
        wan2Provider: "VZW Cell Cell"
    },
    {
        name: "VAR 02",
        wan1Speed: "250.0M x 25.0M",
        wan2Speed: "Cell",
        wan1Provider: "Comcast Workplace",
        wan2Provider: "VZW Cell"
    },
    {
        name: "Perfect Cell/Cell Test",
        wan1Speed: "Cell",
        wan2Speed: "Cell", 
        wan1Provider: "AT&T",
        wan2Provider: "Verizon"
    },
    {
        name: "Low Speed + Cell Test",
        wan1Speed: "50.0M x 5.0M",
        wan2Speed: "Cell",
        wan1Provider: "Comcast",
        wan2Provider: "AT&T"
    }
];

console.log("=== Cell/Cell Detection Test Results ===\n");

testCases.forEach(function(testCase) {
    var wan1ParsedSpeed = parseSpeed(testCase.wan1Speed);
    var wan2ParsedSpeed = parseSpeed(testCase.wan2Speed);
    
    var wan1IsLowSpeed = isLowSpeed(wan1ParsedSpeed);
    var wan2IsLowSpeed = isLowSpeed(wan2ParsedSpeed);
    var wan1IsCellular = isCellular(testCase.wan1Speed) || isCellularProvider(testCase.wan1Provider);
    var wan2IsCellular = isCellular(testCase.wan2Speed) || isCellularProvider(testCase.wan2Provider);
    
    var bothCellular = wan1IsCellular && wan2IsCellular;
    var lowSpeedWithCellular = (wan1IsLowSpeed && wan2IsCellular) || (wan2IsLowSpeed && wan1IsCellular);
    var qualifies = bothCellular || lowSpeedWithCellular;
    
    console.log(`Site: ${testCase.name}`);
    console.log(`WAN1: ${testCase.wan1Speed} (${testCase.wan1Provider})`);
    console.log(`WAN2: ${testCase.wan2Speed} (${testCase.wan2Provider})`);
    console.log(`WAN1 Parsed Speed: ${JSON.stringify(wan1ParsedSpeed)}`);
    console.log(`WAN2 Parsed Speed: ${JSON.stringify(wan2ParsedSpeed)}`);
    console.log(`WAN1 Low Speed: ${wan1IsLowSpeed}`);
    console.log(`WAN2 Low Speed: ${wan2IsLowSpeed}`);
    console.log(`WAN1 Cellular: ${wan1IsCellular}`);
    console.log(`WAN2 Cellular: ${wan2IsCellular}`);
    console.log(`Both Cellular: ${bothCellular}`);
    console.log(`Low Speed + Cellular: ${lowSpeedWithCellular}`);
    console.log(`*** QUALIFIES FOR NOT VISION READY: ${qualifies} ***`);
    console.log('---\n');
});