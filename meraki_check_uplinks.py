import requests

API_KEY = "5174c907a7d57dea6a0788617287c985cc80b3c1"
ORG_NAME = "DTC-Store-Inventory-All"
TARGET_NETWORKS = ["AZP 41", "AZP 64", "AZP 05"]
headers = {"X-Cisco-Meraki-API-Key": API_KEY}

# Step 1: Get Org ID
orgs = requests.get("https://api.meraki.com/api/v1/organizations", headers=headers).json()
org_id = next((o["id"] for o in orgs if o["name"] == ORG_NAME), None)
if not org_id:
    print("❌ Org not found.")
    exit(1)

# Step 2: Get Networks
networks = requests.get(f"https://api.meraki.com/api/v1/organizations/{org_id}/networks", headers=headers).json()
matched_nets = [n for n in networks if n["name"] in TARGET_NETWORKS]

# Step 3: Get WAN uplink statuses per network
for net in matched_nets:
    print(f"\n🔍 Checking {net['name']} ({net['id']})")
    try:
        statuses = requests.get(
            f"https://api.meraki.com/api/v1/networks/{net['id']}/appliance/uplinks/statuses",
            headers=headers
        ).json()

        for iface in statuses:
            uplink = iface.get("uplink")
            status = iface.get("status")
            ip = iface.get("publicIp")
            print(f"  {uplink}: {status}, public IP: {ip}")
    except Exception as e:
        print(f"❌ Failed to get uplinks for {net['name']}: {e}")
