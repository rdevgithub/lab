import pynetbox
import yaml

# 1. Setup Connection
NETBOX_URL = "http://localhost:8000"
try:
    with open("netbox_api.txt", "r") as f:
        token = f.read().strip()
except FileNotFoundError:
    print("Error: netbox_api.txt not found.")
    exit(1)

nb = pynetbox.api(NETBOX_URL, token=token)

def onboard():
    # 2. Load the Topology from YAML
    try:
        with open("topology.clab.yml", "r") as f:
            topo = yaml.safe_load(f)
        nodes = topo['topology']['nodes']
    except FileNotFoundError:
        print("Error: topology.clab.yml not found.")
        return

    # 3. Ensure Site exists
    site = nb.dcim.sites.get(slug="home-lab")
    if not site:
        print("Creating Site: Home-Lab...")
        site = nb.dcim.sites.create(name="Home-Lab", slug="home-lab")

    # 4. Ensure Manufacturer exists
    man = nb.dcim.manufacturers.get(slug="arista")
    if not man:
        print("Creating Manufacturer: Arista...")
        man = nb.dcim.manufacturers.create(name="Arista", slug="arista")

    # 5. Ensure Device Type exists
    dtype = nb.dcim.device_types.get(slug="ceos")
    if not dtype:
        print("Creating Device Type: cEOS...")
        dtype = nb.dcim.device_types.create(model="cEOS", slug="ceos", manufacturer=man.id)

    # 6. Process Nodes from YAML
    for node_name in nodes.keys():
        device = nb.dcim.devices.get(name=node_name)
        
        if device:
            print(f"✅ {node_name} already exists.")
        else:
            print(f"Adding {node_name}...")
            
            # Determine role and ensure it exists
            r_name = "Switch" if "leaf" in node_name or "spine" in node_name else "Server"
            role = nb.dcim.device_roles.get(name=r_name)
            if not role:
                role = nb.dcim.device_roles.create(name=r_name, slug=r_name.lower())
            
            # Create the device
            try:
                nb.dcim.devices.create(
                    name=node_name,
                    device_type=dtype.id,
                    role=role.id,
                    site=site.id,
                    status="active"
                )
                print(f"🚀 Successfully onboarded {node_name}")
            except Exception as e:
                print(f"❌ Failed to create {node_name}: {e}")

if __name__ == "__main__":
    onboard()