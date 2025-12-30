import pynetbox

nb = pynetbox.api('http://localhost:8000', token='fc0ece5ed87416de5481370a57e4c18dae626cb9')

# Define the nodes we want to update
nodes = ['spine1', 'leaf1']

# Define the interfaces we want every switch to have
interface_list = [
    {'name': 'Management1', 'type': '1000base-t'},
    {'name': 'Ethernet1', 'type': '10gbase-x-sfpp'},
    {'name': 'Ethernet2', 'type': '10gbase-x-sfpp'},
]

for node_name in nodes:
    device = nb.dcim.devices.get(name=node_name)
    if device:
        for iface in interface_list:
            # Check if interface already exists
            existing_iface = nb.dcim.interfaces.get(device_id=device.id, name=iface['name'])
            
            if not existing_iface:
                nb.dcim.interfaces.create(
                    device=device.id,
                    name=iface['name'],
                    type=iface['type']
                )
                print(f"Added {iface['name']} to {node_name}")
            else:
                print(f"{iface['name']} already exists on {node_name}")