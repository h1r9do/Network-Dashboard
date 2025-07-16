import requests

API_KEY = "5174c907a7d57dea6a0788617287c985cc80b3c1"
ORG_NAME = "DTC-Store-Inventory-All"
TARGET_NETWORKS = ["AZP 41", "AZP 64", "AZP 05"]
HEADERS = {"X-Cisco-Meraki-API-Key": API_KEY}

# Step 1: Get Org ID
orgs = requests.get("https://api.meraki.com/api/v1/organizations", headers=HEADERS).json()
org_id = next((o["id"] for o in orgs if o["name"] == ORG_NAME), None)
if not org_id:
    print("❌ Org not found.")
    exit(1)

# Step 2: Get networks
networks = requests.get(f"https://api.meraki.com/api/v1/organizations/{org_id}/networks", headers=HEADERS).json()
target_nets = [n for n in networks if n["name"] in TARGET_NETWORKS]

# Step 3: List devices in each network
for net in target_nets:
    print(f"\n🔍 {net['name']} ({net['id']})")
    try:
        devices = requests.get(
            f"https://api.meraki.com/api/v1/networks/{net['id']}/devices",
            headers=HEADERS
        ).json()
        for d in devices:
            print(f"  📦 {d['model']} - {d['serial']} - MAC: {d['mac']}")
    except Exception as e:
        print(f"  ❌ Error fetching devices: {e}")
