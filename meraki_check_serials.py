import requests

API_KEY = "5174c907a7d57dea6a0788617287c985cc80b3c1"
ORG_NAME = "DTC-Store-Inventory-All"
TARGET_SERIALS = [
    "Q2QN-3S86-FTM7",
    "Q2KY-4NFZ-GR8K",
    "Q2KY-WSRF-D3KA"
]

headers = {"X-Cisco-Meraki-API-Key": API_KEY}

# Step 1: Get org ID
try:
    orgs = requests.get("https://api.meraki.com/api/v1/organizations", headers=headers).json()
    org_id = next((org["id"] for org in orgs if org["name"] == ORG_NAME), None)

    if not org_id:
        print(f"❌ Org '{ORG_NAME}' not found.")
        exit(1)

    print(f"✅ Found Org ID: {org_id}")
except Exception as e:
    print(f"❌ Failed to retrieve organizations: {e}")
    exit(1)

# Step 2: Get device inventory
try:
    devices = requests.get(f"https://api.meraki.com/api/v1/organizations/{org_id}/inventory/devices", headers=headers).json()
except Exception as e:
    print(f"❌ Failed to retrieve devices: {e}")
    exit(1)

# Step 3: Match serials
found = [d for d in devices if d["serial"] in TARGET_SERIALS]
missing = set(TARGET_SERIALS) - set(d["serial"] for d in found)

if found:
    print("\n✅ Found devices:")
    for d in found:
        print(f"  {d['serial']} - {d['model']} - network: {d.get('networkId', 'Unassigned')}")
else:
    print("\n⚠️ None of the target serials were found.")

if missing:
    print("\n❌ Missing serials:")
    for s in missing:
        print(f"  {s}")
