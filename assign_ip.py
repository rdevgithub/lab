import pynetbox

# 1. Setup Connection
NETBOX_URL = "http://localhost:8000"
try:
    with open("netbox_api.txt", "r") as f:
        token = f.read().strip()
except FileNotFoundError:
    print("Error: netbox_api.txt not found.")
    exit(1)

nb = pynetbox.api(NETBOX_URL, token=token)

def assign_ips():
    # Define the mapping for the new topology
    # Format: Device Name -> { Interface Name: IP Address }
    network_map = {
        "spine1": {
            "Ethernet2": "10.0.0.5/30"
        },
        "leaf2": {
            "Ethernet1": "10.0.0.6/30",
            "Ethernet2": "192.168.20.1/24"
        },
        "client2": {
            "eth1": "192.168.20.10/24"
        }
    }

    for device_name, interfaces in network_map.items():
        device = nb.dcim.devices.get(name=device_name)
        if not device:
            print(f"❌ Could not find {device_name} in NetBox. Run onboard_netbox.py first.")
            continue

        for iface_name, ip_addr in interfaces.items():
            # 1. Ensure Interface exists
            iface = nb.dcim.interfaces.get(device_id=device.id, name=iface_name)
            if not iface:
                print(f"Creating {iface_name} on {device_name}...")
                iface = nb.dcim.interfaces.create(
                    device=device.id,
                    name=iface_name,
                    type="1000base-t" # Standard Gigabit interface type
                )

            # 2. Create IP Address and assign to interface
            # We search for the IP first to avoid duplicates
            ip = nb.ipam.ip_addresses.get(address=ip_addr)
            if not ip:
                print(f"Assigning {ip_addr} to {device_name} {iface_name}...")
                nb.ipam.ip_addresses.create(
                    address=ip_addr,
                    assigned_object_type="dcim.interface",
                    assigned_object_id=iface.id,
                    status="active"
                )
            else:
                print(f"✅ {ip_addr} already assigned to {device_name}.")

    print("🚀 IP Assignment complete.")

if __name__ == "__main__":
    assign_ips()