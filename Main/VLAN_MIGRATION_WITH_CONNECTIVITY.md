# VLAN Migration with Connectivity Monitoring

**Critical Addition:** Device connectivity monitoring before, during, and after migration  
**Purpose:** Ensure zero device loss during VLAN migration

## Updated Migration Process with Connectivity Monitoring

### Pre-Migration Steps

1. **Capture Connectivity Baseline** (NEW - CRITICAL!)
   ```bash
   # Capture current state of all online devices
   python3 vlan_migration_connectivity_monitor.py \
     --network-id L_XXXXXXXXX \
     --action baseline
   ```
   
   This captures:
   - All online clients with IP addresses
   - Network devices (switches, APs)
   - DHCP reservations
   - Ping test results for all IPs

2. **Review Baseline Results**
   ```bash
   # Check the baseline file
   cat connectivity_baseline_L_XXXXXXXXX_*.json | jq '.connectivity | length'
   
   # See summary of reachable devices
   cat connectivity_baseline_L_XXXXXXXXX_*.json | jq '.connectivity | to_entries | map(select(.value.ping_result.reachable == true)) | length'
   ```

### During Migration

3. **Optional: Run Continuous Monitoring**
   ```bash
   # In a separate terminal, monitor connectivity every 30 seconds
   python3 vlan_migration_connectivity_monitor.py \
     --network-id L_XXXXXXXXX \
     --action monitor \
     --interval 30 \
     --duration 1800  # 30 minutes
   ```

4. **Execute VLAN Migration**
   ```bash
   # Run the migration as normal
   python3 vlan_number_migration.py --network-id L_XXXXXXXXX
   ```

### Post-Migration Verification

5. **Verify All Devices Are Back Online** (NEW - CRITICAL!)
   ```bash
   # Wait 2-3 minutes for devices to reconnect, then verify
   python3 vlan_migration_connectivity_monitor.py \
     --network-id L_XXXXXXXXX \
     --action verify
   ```
   
   This checks:
   - All previously reachable devices are still reachable
   - Identifies any devices that lost connectivity
   - Reports devices that became reachable

## Complete Migration Workflow

```bash
#!/bin/bash
# complete_vlan_migration_with_monitoring.sh

NETWORK_ID="L_XXXXXXXXX"

echo "=== VLAN Migration with Connectivity Monitoring ==="
echo "Network: $NETWORK_ID"
echo ""

# Step 1: Capture baseline
echo "Step 1: Capturing connectivity baseline..."
python3 vlan_migration_connectivity_monitor.py \
  --network-id $NETWORK_ID \
  --action baseline

echo ""
echo "Baseline captured. Review the results:"
echo "- Check total device count"
echo "- Note any currently unreachable devices"
echo ""
read -p "Press Enter to continue with migration..."

# Step 2: Start monitoring (optional - in background)
echo "Step 2: Starting background connectivity monitor..."
python3 vlan_migration_connectivity_monitor.py \
  --network-id $NETWORK_ID \
  --action monitor \
  --interval 30 \
  --duration 1800 > monitor_log.txt 2>&1 &
MONITOR_PID=$!
echo "Monitor running in background (PID: $MONITOR_PID)"

# Step 3: Run migration
echo ""
echo "Step 3: Running VLAN migration..."
python3 vlan_number_migration.py --network-id $NETWORK_ID

# Step 4: Wait for devices to reconnect
echo ""
echo "Step 4: Waiting for devices to reconnect..."
echo "Waiting 3 minutes for DHCP renewals..."
sleep 180

# Step 5: Verify connectivity
echo ""
echo "Step 5: Verifying connectivity..."
python3 vlan_migration_connectivity_monitor.py \
  --network-id $NETWORK_ID \
  --action verify

# Stop monitor
kill $MONITOR_PID 2>/dev/null

echo ""
echo "=== Migration Complete ==="
echo "Check verification results above for any devices that lost connectivity"
```

## Connectivity Report Interpretation

### Baseline Report Shows:
```json
{
  "connectivity": {
    "10.1.67.50": {
      "type": "client",
      "name": "Workstation-01",
      "ping_result": {
        "reachable": true,
        "rtt": 2.5
      }
    }
  }
}
```

### Verification Report Categories:

1. **Still Reachable** ✅
   - Device was online before and after
   - This is the desired state for all devices

2. **Became Reachable** ✅
   - Device was offline before but came online
   - Usually good unless unexpected

3. **Lost Connectivity** ❌
   - Device was online before but offline after
   - **CRITICAL - Requires immediate investigation**

4. **Still Unreachable** ⚠️
   - Device was offline before and after
   - Expected for powered-off devices

## Troubleshooting Lost Connectivity

If devices lose connectivity after migration:

1. **Check VLAN Assignment**
   ```bash
   # Check which VLAN the device is on
   curl -X GET \
     "https://api.meraki.com/api/v1/networks/$NETWORK_ID/clients?mac=XX:XX:XX:XX:XX:XX" \
     -H "X-Cisco-Meraki-API-Key: $API_KEY"
   ```

2. **Verify DHCP is Working**
   ```bash
   # Check DHCP settings on new VLAN
   curl -X GET \
     "https://api.meraki.com/api/v1/networks/$NETWORK_ID/appliance/vlans/100" \
     -H "X-Cisco-Meraki-API-Key: $API_KEY"
   ```

3. **Check Switch Port Configuration**
   - Ensure port is assigned to new VLAN
   - Verify voice VLAN updated (101 → 200)

4. **Force DHCP Renewal**
   - May need to bounce switch port
   - Or wait for DHCP lease to expire

## Important Connectivity Considerations

### Device Types That Need Special Attention:

1. **Static IP Devices**
   - Printers, servers, network equipment
   - Won't automatically get new DHCP
   - May need manual intervention

2. **Long DHCP Leases**
   - Devices with 24-hour leases
   - May take time to get new IP
   - Consider shorter lease during migration

3. **Voice Phones**
   - Need correct voice VLAN (200)
   - Require DHCP options for boot server
   - May need reboot after migration

4. **IoT Devices**
   - Often have connectivity watchdogs
   - May reboot if they lose connection
   - Should reconnect automatically

### Timing Considerations:

- **DHCP Lease Time**: Affects how quickly devices get new config
- **ARP Cache**: 5-10 minutes to clear
- **Switch MAC Tables**: Update within seconds
- **Client Reconnect**: Most within 1-3 minutes

## Success Metrics

A successful migration shows:
- ✅ 95%+ devices "Still Reachable"
- ✅ 0-5% devices "Became Reachable" (were just offline temporarily)
- ✅ 0% devices "Lost Connectivity"
- ✅ Few devices "Still Unreachable" (expected for offline devices)

## Emergency Rollback

If too many devices lose connectivity:

1. **Stop the migration immediately**
2. **Use the rollback procedure** from backup
3. **Investigate root cause** before retry
4. **Consider migrating in smaller batches**

---

**Key Point:** Never complete a migration with devices showing "Lost Connectivity" without investigation and resolution.