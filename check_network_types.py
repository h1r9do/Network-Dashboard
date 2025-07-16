import requests

API_KEY = "5174c907a7d57dea6a0788617287c985cc80b3c1"
ORG_ID = "436883"
TARGETS = ["AZP 41", "AZP 64", "AZP 05"]
HEADERS = {"X-Cisco-Meraki-API-Key": API_KEY}

networks = requests.get(
    f"https://api.meraki.com/api/v1/organizations/{ORG_ID}/networks",
    headers=HEADERS
).json()

for net in networks:
    if net["name"] in TARGETS:
        print(f"{net['name']} ({net['id']}) - productTypes: {net.get('productTypes')}")
