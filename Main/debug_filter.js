// Test script to debug what data the JavaScript filter is seeing
// This simulates what the DataTable filter function receives

// Test with CAL 07 data - what the JavaScript actually sees
var testData = [
    // Based on actual CAL 07 data from database
    // [Site, WAN1 Provider, WAN1 Speed, WAN1 Cost, WAN2 Provider, WAN2 Speed, WAN2 Cost, Action]
    ["CAL 07", "AT&T Broadband II", "300.0M x 300.0M", "$105.01", "VZW Cell Cell", "", "", "Configure"],
    
    // Test what happens with explicit 'Cell' speed
    ["Test Site 1", "AT&T", "Cell", "$50.00", "Verizon", "Cell", "$50.00", "Configure"],
    
    // Test low speed + cellular
    ["Test Site 2", "Comcast", "50.0M x 5.0M", "$80.00", "AT&T", "Cell", "$50.00", "Configure"],
];

// Copy the exact functions from the filter
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

function isLowSpeed(speed) {
    if (!speed) return false;
    return speed.download < 100.0 || speed.upload < 10.0;
}

function isCellular(speedStr) {
    return speedStr === 'Cell';
}

function isCellularProvider(providerStr) {
    if (!providerStr) return false;
    
    var provider = providerStr;
    if (provider.includes('<')) {
        // Simulate HTML extraction
        provider = provider.replace(/<[^>]*>/g, '');
    }
    
    provider = provider.toUpperCase();
    
    return provider.includes('AT&T') || 
           provider.includes('VERIZON') || 
           provider.includes('VZW') ||
           provider.includes('CELL') ||
           provider.includes('CELLULAR') ||
           provider.includes('WIRELESS');
}

// Test each site
testData.forEach(function(data, index) {
    var siteName = data[0];
    var wan1Speed = data[2].trim();
    var wan2Speed = data[5].trim();
    var wan1Provider = data[1].trim();
    var wan2Provider = data[4].trim();
    
    var wan1ParsedSpeed = parseSpeed(wan1Speed);
    var wan2ParsedSpeed = parseSpeed(wan2Speed);
    
    var wan1IsLowSpeed = isLowSpeed(wan1ParsedSpeed);
    var wan2IsLowSpeed = isLowSpeed(wan2ParsedSpeed);
    var wan1IsCellular = isCellular(wan1Speed) || isCellularProvider(wan1Provider);
    var wan2IsCellular = isCellular(wan2Speed) || isCellularProvider(wan2Provider);
    
    var bothCellular = wan1IsCellular && wan2IsCellular;
    var lowSpeedWithCellular = (wan1IsLowSpeed && wan2IsCellular) || (wan2IsLowSpeed && wan1IsCellular);
    var qualifies = bothCellular || lowSpeedWithCellular;
    
    console.log(`=== ${siteName} ===`);
    console.log(`WAN1: "${wan1Speed}" (${wan1Provider})`);
    console.log(`WAN2: "${wan2Speed}" (${wan2Provider})`);
    console.log(`WAN1 Parsed: ${JSON.stringify(wan1ParsedSpeed)}`);
    console.log(`WAN2 Parsed: ${JSON.stringify(wan2ParsedSpeed)}`);
    console.log(`WAN1 Low Speed: ${wan1IsLowSpeed}`);
    console.log(`WAN2 Low Speed: ${wan2IsLowSpeed}`);
    console.log(`WAN1 Cellular: ${wan1IsCellular} (speed:${isCellular(wan1Speed)}, provider:${isCellularProvider(wan1Provider)})`);
    console.log(`WAN2 Cellular: ${wan2IsCellular} (speed:${isCellular(wan2Speed)}, provider:${isCellularProvider(wan2Provider)})`);
    console.log(`Both Cellular: ${bothCellular}`);
    console.log(`Low Speed + Cellular: ${lowSpeedWithCellular}`);
    console.log(`*** FILTER RESULT: ${qualifies ? 'SHOW' : 'HIDE'} ***`);
    console.log('');
});