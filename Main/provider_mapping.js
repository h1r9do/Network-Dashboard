/**
 * Provider Mapping JavaScript Module
 * Handles provider matching logic for the DSR Circuits modal
 */

const ProviderMapping = {
    // Core provider mappings (subset for client-side performance)
    mappings: {
        // Rebrands
        'brightspeed': 'centurylink',
        'sparklight': 'cable one',
        'cincinnati bell': 'altafiber',
        'lumen': 'centurylink',
        
        // Business divisions
        'comcast workplace': 'comcast',
        'comcast workplace cable': 'comcast',
        'cox business/boi': 'cox communications',
        'cox business boi': 'cox communications',
        'cox business': 'cox communications',
        'at&t broadband ii': 'at&t',
        'at&t abf': 'at&t',
        'at&t adi': 'at&t',
        'verizon business': 'verizon',
        
        // Brand names
        'spectrum': 'charter communications',
        'charter': 'charter communications',
        'altice west': 'optimum',
        'lightpath': 'optimum',
        
        // Aliases
        'transworld': 'fairnet llc',
        'mediacom/boi': 'mediacom',
        'centurylink/embarq': 'centurylink',
        'centurylink/qwest': 'centurylink',
        'verizon cell': 'verizon',
        'cell': 'verizon',
        'vzw cell': 'verizon',
        
        // Service suffixes
        'centurylink fiber plus': 'centurylink',
        'agg comcast': 'comcast',
        'comcastagg comcast': 'comcast',
        'wyyerd fiber': 'wyyerd group llc'
    },
    
    // Normalize provider name
    normalizeProvider(provider) {
        if (!provider) return '';
        
        let normalized = provider.toLowerCase().trim();
        
        // Handle EB2- prefix
        if (normalized.startsWith('eb2-')) {
            normalized = normalized.substring(4);
            normalized = normalized.replace(/\s*(dsl|fiber|cable|kinetic)$/, '');
        }
        
        // Remove other prefixes
        normalized = normalized.replace(/^(dsr|agg|comcastagg|not\s+dsr|--|-)\s+/, '');
        
        // Remove service suffixes
        normalized = normalized.replace(/\s*(extended\s+cable|workplace|broadband\s+ii|fiber\s+plus|\/boi|\/embarq|\/qwest|cable|dsl|fiber)$/, '');
        
        // Clean special characters
        normalized = normalized.replace(/[^\w\s&\/-]/g, ' ');
        normalized = normalized.replace(/\s+/g, ' ').trim();
        
        return normalized;
    },
    
    // Match providers with enhanced logic
    matchProviders(dsrProvider, arinProvider, circuitPurpose = 'Primary') {
        if (!dsrProvider || !arinProvider) {
            return { match: false, confidence: 0, reason: 'Missing provider data' };
        }
        
        // Direct match
        if (dsrProvider.toLowerCase().trim() === arinProvider.toLowerCase().trim()) {
            return { match: true, confidence: 100, reason: 'Direct match' };
        }
        
        // Check mappings
        const dsrNorm = this.normalizeProvider(dsrProvider);
        const arinNorm = this.normalizeProvider(arinProvider);
        
        // Check if DSR provider has a mapping
        if (this.mappings[dsrNorm]) {
            const mappedProvider = this.mappings[dsrNorm];
            if (mappedProvider.toLowerCase() === arinNorm) {
                return { match: true, confidence: 95, reason: 'Mapped provider' };
            }
        }
        
        // Normalized match
        if (dsrNorm === arinNorm) {
            return { match: true, confidence: 90, reason: 'Normalized match' };
        }
        
        // Handle secondary circuit conflicts
        if (circuitPurpose === 'Secondary') {
            // Common conflict patterns
            if (dsrNorm.includes('comcast') && arinProvider === 'AT&T') {
                return { match: true, confidence: 70, reason: 'Secondary circuit (trust DSR)' };
            }
            if (dsrNorm.includes('cox') && ['AT&T', 'Verizon'].includes(arinProvider)) {
                return { match: true, confidence: 70, reason: 'Secondary circuit (trust DSR)' };
            }
            if (dsrNorm.includes('spectrum') && arinProvider === 'AT&T') {
                return { match: true, confidence: 70, reason: 'Secondary circuit (trust DSR)' };
            }
        }
        
        // Simple fuzzy match (Levenshtein distance approximation)
        const similarity = this.calculateSimilarity(dsrNorm, arinNorm);
        if (similarity >= 0.8) {
            return { match: true, confidence: Math.round(similarity * 100), reason: 'Fuzzy match' };
        }
        
        return { match: false, confidence: 0, reason: 'No match found' };
    },
    
    // Simple similarity calculation
    calculateSimilarity(str1, str2) {
        const longer = str1.length > str2.length ? str1 : str2;
        const shorter = str1.length > str2.length ? str2 : str1;
        
        if (longer.length === 0) return 1.0;
        
        const distance = this.levenshteinDistance(longer, shorter);
        return (longer.length - distance) / longer.length;
    },
    
    // Levenshtein distance calculation
    levenshteinDistance(str1, str2) {
        const matrix = [];
        
        for (let i = 0; i <= str2.length; i++) {
            matrix[i] = [i];
        }
        
        for (let j = 0; j <= str1.length; j++) {
            matrix[0][j] = j;
        }
        
        for (let i = 1; i <= str2.length; i++) {
            for (let j = 1; j <= str1.length; j++) {
                if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
                    matrix[i][j] = matrix[i - 1][j - 1];
                } else {
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j - 1] + 1,
                        matrix[i][j - 1] + 1,
                        matrix[i - 1][j] + 1
                    );
                }
            }
        }
        
        return matrix[str2.length][str1.length];
    },
    
    // Load full mappings from server (optional)
    async loadMappingsFromServer() {
        try {
            const response = await fetch('/api/provider-mappings');
            if (response.ok) {
                const data = await response.json();
                // Merge server mappings with local ones
                Object.assign(this.mappings, data.mappings);
                console.log(`Loaded ${Object.keys(data.mappings).length} provider mappings from server`);
            }
        } catch (error) {
            console.warn('Could not load provider mappings from server:', error);
        }
    }
};