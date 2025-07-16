#!/usr/bin/env python3
"""
Add comprehensive debugging to the template for browser console
"""

print("=== ADDING COMPREHENSIVE BROWSER DEBUGGING ===\n")

with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    content = f.read()

# Find where to add the comprehensive debugging (before </script>)
debug_code = '''
        // ============ COMPREHENSIVE DEBUGGING SYSTEM ============
        
        // Global debug object
        window.DSRDebug = {
            // Get all provider values from the table
            getTableProviders: function() {
                console.log("=== SCANNING TABLE FOR PROVIDERS ===");
                var providers1 = {};
                var providers2 = {};
                var rowCount = 0;
                
                $('#circuitTable tbody tr').each(function() {
                    rowCount++;
                    var $row = $(this);
                    
                    // WAN1 Provider (column 2)
                    var $wan1Cell = $row.find('td').eq(1);
                    var wan1Provider = $wan1Cell.attr('data-provider') || 
                                      $wan1Cell.find('.provider-text').text().trim() || 
                                      $wan1Cell.text().trim();
                    
                    // WAN2 Provider (column 5) 
                    var $wan2Cell = $row.find('td').eq(4);
                    var wan2Provider = $wan2Cell.attr('data-provider') || 
                                      $wan2Cell.find('.provider-text').text().trim() || 
                                      $wan2Cell.text().trim();
                    
                    if (wan1Provider && wan1Provider !== 'N/A') {
                        providers1[wan1Provider] = (providers1[wan1Provider] || 0) + 1;
                    }
                    if (wan2Provider && wan2Provider !== 'N/A') {
                        providers2[wan2Provider] = (providers2[wan2Provider] || 0) + 1;
                    }
                });
                
                console.log("Total rows scanned:", rowCount);
                console.log("\\nWAN1 Providers found:");
                Object.keys(providers1).sort().forEach(function(p) {
                    console.log("  '" + p + "': " + providers1[p] + " circuits");
                });
                console.log("\\nWAN2 Providers found:");
                Object.keys(providers2).sort().forEach(function(p) {
                    console.log("  '" + p + "': " + providers2[p] + " circuits");
                });
                
                return {wan1: providers1, wan2: providers2};
            },
            
            // Check what's in the dropdowns
            getDropdownOptions: function() {
                console.log("=== DROPDOWN CONTENTS ===");
                
                console.log("\\nWAN1 Provider Dropdown:");
                $('#wan1ProviderFilter option').each(function(i) {
                    if (i === 0) return; // Skip "All" option
                    console.log("  Option " + i + ": '" + $(this).val() + "' (text: '" + $(this).text() + "')");
                });
                
                console.log("\\nWAN2 Provider Dropdown:");
                $('#wan2ProviderFilter option').each(function(i) {
                    if (i === 0) return; // Skip "All" option
                    console.log("  Option " + i + ": '" + $(this).val() + "' (text: '" + $(this).text() + "')");
                });
            },
            
            // Test filtering
            testFilter: function(provider) {
                console.log("=== TESTING FILTER FOR: '" + provider + "' ===");
                
                // Set WAN1 filter
                $('#wan1ProviderFilter').val(provider).trigger('change');
                
                setTimeout(function() {
                    var visibleRows = $('#circuitTable tbody tr:visible').length;
                    var totalRows = $('#circuitTable tbody tr').length;
                    console.log("After filtering WAN1 for '" + provider + "':");
                    console.log("  Visible rows: " + visibleRows + " / " + totalRows);
                    
                    // Check first few visible rows
                    console.log("  First 3 visible rows:");
                    $('#circuitTable tbody tr:visible').slice(0, 3).each(function(i) {
                        var site = $(this).find('td').eq(0).text();
                        var wan1 = $(this).find('td').eq(1).text().trim();
                        console.log("    " + (i+1) + ". " + site + " - WAN1: '" + wan1 + "'");
                    });
                    
                    // Reset filter
                    $('#wan1ProviderFilter').val('').trigger('change');
                }, 500);
            },
            
            // Check DataTable state
            checkDataTable: function() {
                console.log("=== DATATABLE STATE ===");
                if (typeof table !== 'undefined') {
                    console.log("DataTable initialized: YES");
                    console.log("Total rows in data: " + table.rows().count());
                    console.log("Rows after current filter: " + table.rows({search: 'applied'}).count());
                    console.log("Current page: " + (table.page() + 1));
                    console.log("Page length: " + table.page.len());
                    
                    // Check column search terms
                    console.log("\\nColumn search terms:");
                    table.columns().every(function(index) {
                        var searchTerm = this.search();
                        if (searchTerm) {
                            console.log("  Column " + index + ": '" + searchTerm + "'");
                        }
                    });
                    
                    // Check custom searches
                    console.log("\\nCustom search functions: " + $.fn.dataTable.ext.search.length);
                } else {
                    console.log("DataTable NOT initialized!");
                }
            },
            
            // Debug specific row
            debugRow: function(siteName) {
                console.log("=== DEBUGGING ROW: " + siteName + " ===");
                var found = false;
                $('#circuitTable tbody tr').each(function() {
                    var $row = $(this);
                    var site = $row.find('td').eq(0).text().trim();
                    if (site === siteName) {
                        found = true;
                        console.log("Found row for " + siteName);
                        
                        var $wan1Cell = $row.find('td').eq(1);
                        console.log("\\nWAN1 Cell HTML:");
                        console.log($wan1Cell.html());
                        console.log("data-provider: '" + $wan1Cell.attr('data-provider') + "'");
                        console.log("provider-text: '" + $wan1Cell.find('.provider-text').text() + "'");
                        console.log("full text: '" + $wan1Cell.text() + "'");
                        
                        var $wan2Cell = $row.find('td').eq(4);
                        console.log("\\nWAN2 Cell HTML:");
                        console.log($wan2Cell.html());
                        console.log("data-provider: '" + $wan2Cell.attr('data-provider') + "'");
                        console.log("provider-text: '" + $wan2Cell.find('.provider-text').text() + "'");
                        console.log("full text: '" + $wan2Cell.text() + "'");
                        
                        return false; // break
                    }
                });
                if (!found) {
                    console.log("Row not found for site: " + siteName);
                }
            },
            
            // Run all diagnostics
            runDiagnostics: function() {
                console.log("\\n========== DSR CIRCUITS FILTER DIAGNOSTICS ==========\\n");
                this.checkDataTable();
                console.log("");
                this.getTableProviders();
                console.log("");
                this.getDropdownOptions();
                console.log("\\n========== END DIAGNOSTICS ==========\\n");
                console.log("To test a specific filter, run: DSRDebug.testFilter('Starlink')");
                console.log("To debug a specific row, run: DSRDebug.debugRow('SITE NAME')");
            }
        };
        
        // Auto-run diagnostics when page loads
        $(document).ready(function() {
            setTimeout(function() {
                console.log("DSR Circuits Debug System Ready!");
                console.log("Run DSRDebug.runDiagnostics() to see full diagnostic report");
                console.log("Run DSRDebug.testFilter('Starlink') to test filtering");
            }, 1000);
        });
'''

# Replace the old debug code or add new if not exists
if 'window.debugFilters' in content:
    # Replace from window.debugFilters to the next function or closing script tag
    import re
    # Find the debug function and replace it
    pattern = r'window\.debugFilters = function\(\).*?\};'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        content = content.replace(match.group(0), '')
        print("✅ Removed old debug function")

# Add new debug code before closing script tag
content = content.replace('    </script>', debug_code + '\n    </script>')

# Write the updated content
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'w') as f:
    f.write(content)

print("✅ Added comprehensive debugging system!")
print("\nIn the browser console, you can now run:")
print("  DSRDebug.runDiagnostics()     - Full diagnostic report")
print("  DSRDebug.getTableProviders()  - List all providers in table")
print("  DSRDebug.getDropdownOptions() - List all dropdown options")
print("  DSRDebug.testFilter('Starlink') - Test filtering for a provider")
print("  DSRDebug.debugRow('AZP 63')    - Debug a specific row")
print("  DSRDebug.checkDataTable()     - Check DataTable state")