import requests

def get_organization_name(ip):
    """Retrieve the organization name from ARIN RDAP."""
    url = f"https://rdap.arin.net/registry/ip/{ip}"
    response = requests.get(url)
    data = response.json()

    # Find the registrant entity
    for entity in data.get('entities', []):
        if 'registrant' in entity.get('roles', []):
            # Check if the entity is an organization
            if entity.get('kind') == 'org':
                # Extract the organization name from vcardArray
                vcard_array = entity.get('vcardArray', [])
                if len(vcard_array) > 1 and isinstance(vcard_array[1], list):
                    for vcard in vcard_array[1]:
                        if vcard[0] == 'fn':
                            return vcard[3].strip()

    return None

# Example usage
ip = '108.241.236.49'
org_name = get_organization_name(ip)
print(f"Organization name for IP {ip}: {org_name}")

