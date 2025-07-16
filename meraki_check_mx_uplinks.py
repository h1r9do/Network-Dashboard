import requests

API_KEY = "5174c907a7d57dea6a0788617287c985cc80b3c1"
HEADERS = {"X-Cisco-Meraki-API-Key": API_KEY}
STORES = [
    {"store": "AZP 41", "serial": "Q2QN-3S86-FTM7"},
    {"store": "AZP 64", "serial": "Q2KY-4NFZ-GR8K"},
    {"store": "AZP 05", "serial": "Q2KY-WSRF-D3KA"},
]

print("🔍 Fetching MX uplink info...\n")
for s in STORES:
    print(f"📡 {s['store']} - {s['serial']}")
    try:
        r = requests.get(
            f"https://api.meraki.com/api/v1/devices/{s['serial']}/uplinks",
            headers=HEADERS
        )
        r.raise_for_status()
        uplinks = r.json()
        for u in uplinks:
            print(f"  {u['interface']} - {u['status']}, IP: {u.get('ip')}, Gateway: {u.get('gateway')}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    print()
