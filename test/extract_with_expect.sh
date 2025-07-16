#\!/bin/bash
# Extract SNMP config using expect for slow typing

extract_device_config() {
    local hostname=$1
    local ip=$2
    local device_type=$3
    
    echo "Connecting to $hostname ($ip)..."
    
    # Create expect script
    expect << EXPECT_SCRIPT
set timeout 60
spawn ssh mbambic@$ip
expect {
    "Password:" {
        sleep 2
        send "A"
        sleep 0.1
        send "u"
        sleep 0.1
        send "d"
        sleep 0.1
        send "\!"
        sleep 0.1
        send "o"
        sleep 0.1
        send "\!"
        sleep 0.1
        send "9"
        sleep 0.1
        send "9"
        sleep 0.1
        send "4"
        sleep 0.1
        send "\r"
        exp_continue
    }
    "#" {
        send "show version  < /dev/null |  include Version\r"
        expect "#"
        send "show running-config | include snmp-server\r"
        expect "#"
        send "show ip access-lists\r"
        expect "#"
        send "exit\r"
        expect eof
    }
    timeout {
        puts "Connection timeout"
        exit 1
    }
}
EXPECT_SCRIPT

    echo "✅ Completed extraction from $hostname"
}

# Test devices
echo "=================================="
echo "SNMP CONFIG EXTRACTION WITH EXPECT"
echo "=================================="

extract_device_config "EQX-CldTrst-8500-01" "10.44.158.41" "Catalyst 8500"
sleep 5
extract_device_config "FP-DAL-ASR1001-01" "10.42.255.16" "ASR1001"
sleep 5
extract_device_config "DMZ-7010-01" "192.168.255.4" "ASA 7010"

echo "Extraction complete!"
