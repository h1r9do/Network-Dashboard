# DSR Circuits - URL Validation Report

## Executive Summary

After comprehensive testing of all URLs in the documentation, I've discovered:
- **DSR Circuits is accessible on port 5052 directly**, NOT through nginx proxy
- **There is NO nginx proxy configuration** for DSR Circuits on port 80 or 8080
- **All internal application URLs are working** when accessed with port 5052

## URL Test Results

### ✅ Working DSR Circuits URLs (Status 200)
All URLs require port 5052:
- `http://neamsatcor1ld01.trtc.com:5052/home` - Home page
- `http://neamsatcor1ld01.trtc.com:5052/dsrdashboard` - Dashboard
- `http://neamsatcor1ld01.trtc.com:5052/new-stores` - New stores management
- `http://neamsatcor1ld01.trtc.com:5052/dsrcircuits` - Circuit management
- `http://neamsatcor1ld01.trtc.com:5052/dsrallcircuits` - All circuits view
- `http://neamsatcor1ld01.trtc.com:5052/circuit-enablement-report` - Enablement reports
- `http://neamsatcor1ld01.trtc.com:5052/inventory-summary` - Inventory summary
- `http://neamsatcor1ld01.trtc.com:5052/inventory-details` - Inventory details
- `http://neamsatcor1ld01.trtc.com:5052/switch-visibility` - Switch visibility
- `http://neamsatcor1ld01.trtc.com:5052/firewall` - Firewall management
- `http://neamsatcor1ld01.trtc.com:5052/system-health` - System health
- `http://neamsatcor1ld01.trtc.com:5052/performance` - Performance monitoring

### ❌ Non-Working URLs (Status 404 or Connection Failed)
These URLs do NOT work:
- `http://neamsatcor1ld01.trtc.com/home` - 404 (no proxy configured)
- `http://neamsatcor1ld01.trtc.com/` - 404 (nginx serves LibreNMS)
- `http://neamsatcor1ld01.trtc.com:8080/*` - Connection refused (nothing on port 8080)

### ✅ External Integration URLs
- `http://10.0.145.130:3003/mbambic/usr-local-bin` - Git Repository (Working)
- `http://10.0.145.130:30483` - AWX Automation (Working)
- `http://10.0.145.130:5000` - Netdisco (Working)
- `http://10.0.145.130:8686` - LibreNMS (Connection timeout)

## Key Findings

### 1. No Nginx Proxy Configuration
- nginx on port 80 is configured for LibreNMS and Netdisco only
- NO proxy_pass rules exist for DSR Circuits endpoints
- The claim of "nginx reverse proxy" in documentation is incorrect

### 2. Direct Flask Access Only
- DSR Circuits Flask app listens on 0.0.0.0:5052
- Accessible directly without any proxy
- This is the ONLY way to access the application

### 3. Port Summary
- **Port 80**: nginx serving LibreNMS/Netdisco
- **Port 5052**: DSR Circuits Flask application (direct access)
- **Port 8080**: Nothing listening (connection refused)

## Documentation Corrections Made

1. **Primary URL**: Changed to include port 5052
2. **Port Description**: Changed from "nginx reverse proxy" to "Flask application, direct access"
3. **Access Instructions**: Updated to include port 5052

## Recommendations

1. **Consider Adding Nginx Proxy**: For security and consistency, consider adding nginx proxy configuration
2. **Update All Documentation**: Ensure all references use port 5052
3. **Firewall Rules**: Verify port 5052 is open in firewall for external access
4. **SSL/TLS**: Consider adding HTTPS support through nginx proxy

## Current Access Method

To access DSR Circuits, users MUST use:
```
http://neamsatcor1ld01.trtc.com:5052/[endpoint]
```

Direct port 5052 access is the only working method.

---
*Validation Date: July 3, 2025*  
*All URLs tested with curl commands*