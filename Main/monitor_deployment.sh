#!/bin/bash
# Monitor DDNS deployment progress

echo "=== DDNS Deployment Monitor ==="
echo "Started monitoring at: $(date)"
echo

while true; do
    # Check if process is still running
    if pgrep -f "bulk_enable_ddns_no_hubs.py" > /dev/null; then
        echo "$(date '+%H:%M:%S') - Deployment RUNNING"
        
        # Show recent progress
        if [ -f ddns_full_deployment.log ]; then
            echo "Recent progress:"
            tail -3 ddns_full_deployment.log | sed 's/^/  /'
        fi
        
        echo "----------------------------------------"
        sleep 30
    else
        echo "$(date '+%H:%M:%S') - Deployment COMPLETED"
        echo
        echo "Final summary:"
        if [ -f ddns_full_deployment.log ]; then
            tail -20 ddns_full_deployment.log
        fi
        break
    fi
done