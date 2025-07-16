import requests

API_KEY = "5174c907a7d57dea6a0788617287c985cc80b3c1"
ORG_NAME = "DTC-Store-Inventory-All"
TARGET_NAMES = ["AZP 41", "AZP 05", "AZP 64"]

headers = {"X-Cisco-Meraki-API-Key": API_KEY}

# Step 1: Get Org ID
orgs = requests.get("https://api.meraki.com/api/v1/organizations", headers=headers).json()
org_id = next((o["id"] for o in orgs if o["name"] == ORG_NAME), None)
if not org_id:
    print("❌ Org not found.")
    exit(1)

# Step 2: Get all networks
networks = requests.get(f"https://api.meraki.com/api/v1/organizations/{org_id}/networks", headers=headers).json()
matched = [net for net in networks if net["name"] in TARGET_NAMES]

if not matched:
    print("❌ No matching networks found.")
    exit(1)

# Step 3: Get devices for each matching network
print("🔍 Matching Networks and MX Devices:")
for net in matched:
    devices = requests.get(f"https://api.meraki.com/api/v1/networks/{net['id']}/devices", headers=headers).json()
    for d in devices:
        if d["model"].startswith("MX"):
            print(f"{net['name']} - {d['model']} - {d['serial']}")
