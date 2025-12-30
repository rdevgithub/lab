import pynetbox
import pyeapi

# 1. Setup NetBox Connection
with open("netbox_api.txt") as f:
    nb_token = f.read().strip()

nb = pynetbox.api("http://localhost:8000", token=nb_token)
creds = {"username": "admin", "password": "admin", "transport": "http"}

# 2. Map switch names to the PORTS you put in your YAML file
switch_ports = {
    "spine1": 8004,
    "leaf1": 8005,
    "leaf2": 8006
}

def run():
    for name, port in switch_ports.items():
        print(f"--- Starting Sync for {name} (via port {port}) ---")
        
        # Get the device object from NetBox
        device = nb.dcim.devices.get(name=name)
        if not device:
            print(f"  ❌ Error: {name} not found in NetBox.")
            continue
            
        # Get all interfaces for this device
        interfaces = nb.dcim.interfaces.filter(device_id=device.id)
        
        cmds = ["enable", "configure terminal"]
        for iface in interfaces:
            # Check NetBox for an IP address assigned to this specific interface
            addr = nb.ipam.ip_addresses.get(interface_id=iface.id)
            if addr:
                print(f"  Configuring {iface.name}: {addr.address}")
                cmds.extend([
                    f"interface {iface.name}", 
                    "no switchport", 
                    f"ip address {addr.address}", 
                    "no shutdown"
                ])
        
        try:
            # 3. Connect to 127.0.0.1 using the specific port for this switch
            node = pyeapi.client.Node(pyeapi.connect(host="127.0.0.1", port=port, **creds))
            node.config(cmds)
            node.enable("write memory")
            print(f"  ✅ {name} synchronized successfully.")
        except Exception as e:
            print(f"  ❌ {name} failed: {e}")

if __name__ == "__main__":
    run()