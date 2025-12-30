import pynetbox

nb = pynetbox.api('http://localhost:8000', token='fc0ece5ed87416de5481370a57e4c18dae626cb9')

# Ask NetBox for the specific device
device_name = 'leaf1'
nb_device = nb.dcim.devices.get(name=device_name)

print(f"--- Querying Source of Truth for {device_name} ---")

# Get all interfaces on this device that have an IP assigned
interfaces = nb.dcim.interfaces.filter(device_id=nb_device.id)

for iface in interfaces:
    # Look up IP addresses assigned to this interface
    ip_addrs = nb.ipam.ip_addresses.filter(interface_id=iface.id)
    
    for ip in ip_addrs:
        print(f"Interface: {iface.name}")
        print(f"Planned IP: {ip.address}")
        print(f"Status: {ip.status.label}")