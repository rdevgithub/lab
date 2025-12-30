import pynetbox
import pyeapi

# Initialize NetBox API
token = open("netbox_api.txt").read().strip()
nb = pynetbox.api("http://localhost:8000", token=token)

def get_config(name):
    dev = nb.dcim.devices.get(name=name)
    asn = dev.config_context.get("bgp", {}).get("asn")
    
    # Set Router ID based on device name
    rid = "1.1.1.1" if "spine" in name else "2.2.2.1"
    if "leaf2" in name: rid = "2.2.2.2"

    # Base BGP configuration
    cmds = [
        "ip routing", 
        f"router bgp {asn}", 
        "no shutdown", 
        f"router-id {rid}", 
        "no bgp default ipv4-unicast"
    ]
    
    neighbor_ips = []
    # Filter for interfaces that are physically "cabled" in NetBox
    ifaces = nb.dcim.interfaces.filter(device_id=dev.id, connected=True)
    
    for i in ifaces:
        if "Management" in i.name: continue
        for end in i.connected_endpoints:
            # Get the full remote device object to access its config_context (ASN)
            remote_dev = nb.dcim.devices.get(end.device.id)
            p_asn = remote_dev.config_context.get("bgp", {}).get("asn")
            
            # Get the IP address of the peer interface
            p_ip_obj = nb.ipam.ip_addresses.get(interface_id=end.id)
            
            if p_ip_obj and p_asn:
                p_ip = str(p_ip_obj.address).split("/")[0]
                cmds.append(f"neighbor {p_ip} remote-as {p_asn}")
                neighbor_ips.append(p_ip)
    
    # Address Family configuration to activate neighbors and share routes
    if neighbor_ips:
        cmds.append("address-family ipv4")
        cmds.append("redistribute connected")
        for ip in neighbor_ips:
            cmds.append(f"neighbor {ip} activate")
        cmds.append("exit")
        
    return cmds

# --- DEPLOYMENT SECTION ---
devices = {"spine1": 8004, "leaf1": 8005, "leaf2": 8006}

for name, port in devices.items():
    print(f"Deploying to {name}...")
    my_cmds = get_config(name)
    conn = pyeapi.connect(transport="http", host="127.0.0.1", port=port, username="admin", password="admin")
    pyeapi.client.Node(conn).config(my_cmds)
    print(f"Success! Applied {len(my_cmds)} commands to {name}.")

print("\nFabric configuration complete.")