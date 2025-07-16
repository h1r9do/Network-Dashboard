#!/bin/bash
# Test the nightly inventory pipeline

echo "Testing Nightly Inventory Pipeline"
echo "================================="
echo ""
echo "This will run the production pipeline and update the inventory_web_format table."
echo "The existing data will be replaced with freshly processed data."
echo ""
read -p "Continue? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running pipeline..."
    python3 /usr/local/bin/Main/nightly_inventory_complete_pipeline.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Pipeline completed successfully!"
        echo ""
        echo "Checking results..."
        psql -h localhost -U dsruser -d dsrcircuits -c "
            SELECT 
                COUNT(CASE WHEN parent_hostname = '' THEN 1 END) as parent_devices,
                COUNT(CASE WHEN position LIKE 'FEX%' THEN 1 END) as fex_devices,
                COUNT(DISTINCT CASE WHEN position LIKE 'FEX%' THEN serial_number END) as unique_fex,
                COUNT(*) as total_rows
            FROM inventory_web_format
        "
    else
        echo ""
        echo "❌ Pipeline failed! Check logs for details."
    fi
else
    echo "Cancelled."
fi