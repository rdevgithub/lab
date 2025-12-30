import pynetbox
import pyeapi

# 1. NetBox Setup
NETBOX_URL = 'http://localhost:8000'
NETBOX_TOKEN = 'fc0ece5ed87416de5481370a57e4c18dae626cb9' 
nb = pynetbox.api(NETBOX_URL, token=NETBOX_TOKEN)

# 2. Arista Setup
connection = pyeapi.connect(
    host='172.20.20.4', 
    username='admin', 
    password='admin', 
    transport='http', 
    port=80
)
node = pyeapi.client.Node(connection)

def run_report():
    print(f"\n--- Running Compliance Report for leaf1 ---")

    # --- STEP A: Get Intent from NetBox ---
    try:
        nb_device = nb.dcim.devices.get(name='leaf1')
        nb_iface = nb.dcim.interfaces.get(device_id=nb_device.id, name='Ethernet1')
        nb_ip_obj = nb.ipam.ip_addresses.get(interface_id=nb_iface.id)
        intended_ip = str(nb_ip_obj.address) if nb_ip_obj else "None"
    except Exception as e:
        print(f"NetBox Error: {e}")
        return

    # --- STEP B: Get Reality from Switch (JSON Mode) ---
    try:
        # We use a command that returns clean JSON by default
        # This avoids the 'Incomplete token' error found in text-based config commands
        response = node.run_commands(['show ip interface Ethernet1'])
        
        # Navigate the Arista JSON structure safely
        # response[0] is the result of 'show ip interface Ethernet1'
        intf_data = response[0]['interfaces'].get('Ethernet1', {})
        addr_info = intf_data.get('interfaceAddress', {}).get('primaryIp', {})
        
        ip = addr_info.get('address')
        mask = addr_info.get('maskLen')
        
        if ip and mask:
            actual_ip = f"{ip}/{mask}"
        else:
            actual_ip = "None"
            
    except Exception as e:
        actual_ip = f"Switch Error: {e}"

    # --- STEP C: Compare and Report ---
    print(f"\nINTERFACE: Ethernet1")
    print(f"  [INTENTION]: {intended_ip}")
    print(f"  [ACTUAL]   : {actual_ip}")

    if intended_ip == actual_ip and intended_ip != "None":
        print(f"  RESULT     : ✅ COMPLIANT")
    else:
        print(f"  RESULT     : ❌ NON-COMPLIANT (Drift Detected)")
    
    print("-" * 45 + "\n")

if __name__ == "__main__":
    run_report()