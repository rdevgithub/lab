import pynetbox
import pyeapi
import os

# --- 1. LOAD TOKEN FROM FILE ---
def get_token():
    try:
        with open("netbox_api.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("❌ Error: netbox_api.txt not found!")
        return None

token = get_token()

# --- 2. SETTINGS ---
NETBOX_URL = "http://localhost:8000"
nb = pynetbox.api(NETBOX_URL, token=token)

# Matches your specific Docker PS output
device_map = {
    "spine1": 8004,
    "leaf1": 8005,
    "leaf2": 8006
}

def check_compliance(device_name, port):
    print(f"\n--- Checking Compliance for {device_name} ---")
    
    try:
        # --- 3. GET INTENTION (NETBOX) ---
        nb_device = nb.dcim.devices.get(name=device_name)
        if not nb_device:
            print(f"⚠️ Device {device_name} not found in NetBox.")
            return

        nb_interfaces = nb.dcim.interfaces.filter(device_id=nb_device.id)
        
        intended_state = {}
        for iface in nb_interfaces:
            # Look for IP addresses assigned to this interface
            ip_objs = nb.ipam.ip_addresses.filter(interface_id=iface.id)
            for ip in ip_objs:
                # Store just the IP part (e.g., '10.0.0.1')
                intended_state[iface.name] = str(ip.address).split('/')[0]

        # --- 4. GET REALITY (ARISTA) ---
        connection = pyeapi.connect(
            transport='http', 
            host='127.0.0.1',
            username='admin', 
            password='admin',
            port=port
        )
        node = pyeapi.client.Node(connection)
        actual_output = node.enable("show ip interface brief")
        actual_interfaces = actual_output[0]['result']['interfaces']

        # --- 5. COMPARE ---
        if not intended_state:
            print(f"ℹ️ No IPs documented in NetBox for {device_name}.")
        else:
            for iface_name, intended_ip in intended_state.items():
                iface_data = actual_interfaces.get(iface_name, {})
                
                # Dig into the 'interfaceAddress' dictionary returned by Arista
                raw_ip_data = iface_data.get('interfaceAddress', {}).get('ipAddr', 'Not Configured')
                
                # Fix: Properly handle the dictionary vs string logic
                if isinstance(raw_ip_data, dict):
                    actual_ip = raw_ip_data.get('address', 'Not Configured')
                else:
                    actual_ip = raw_ip_data

                if actual_ip == intended_ip:
                    print(f"✅ {iface_name}: Match ({actual_ip})")
                else:
                    print(f"❌ {iface_name}: MISMATCH! NetBox: {intended_ip} | Switch: {actual_ip}")

    except Exception as e:
        print(f"💥 Error checking {device_name}: {e}")

# --- 6. EXECUTE ---
if token:
    for device, port in device_map.items():
        check_compliance(device, port)