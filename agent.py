import asyncio
import websockets
import json
import uuid
import os
from scapy.all import rdpcap, IP
import sys

def generate_machine_id():
    return str(uuid.uuid4())

def verify_pcap_file(pcap_file):
    if not os.path.exists(pcap_file):
        raise FileNotFoundError(f"PCAP file not found: {pcap_file}")
    try:
        packets = rdpcap(pcap_file)
        return len(packets) > 0
    except Exception as e:
        raise Exception(f"Error reading PCAP file: {str(e)}")

def extract_features(pcap_file):
    packets = rdpcap(pcap_file)
    extracted_data = []
    for packet in packets:
        if IP in packet:
            extracted_data.append({
                "src_ip": packet[IP].src,
                "dst_ip": packet[IP].dst,
                "protocol": packet[IP].proto,
                "packet_count": 1,
                "byte_count": len(packet),
                "flow_duration": float(packet.time)  # Convert to float for JSON serialization
            })
    return extracted_data

async def connect_to_server(machine_id, pcap_file, server_uri):
    print(f"Machine ID: {machine_id}")
    print(f"Attempting to connect to server at {server_uri}")
    
    try:
        # Verify PCAP file before attempting connection
        if not verify_pcap_file(pcap_file):
            print("Error: PCAP file is empty")
            return

        async with websockets.connect(server_uri, ping_interval=None, timeout=30) as websocket:
            print("Connected to WebSocket server")
            
            # Send authentication
            auth_message = {"machine_id": machine_id}
            print("Sending authentication...")
            await websocket.send(json.dumps(auth_message))
            
            response = await websocket.recv()
            response_data = json.loads(response)

            if response_data.get("status") == "approved":
                print("Authentication approved. Processing PCAP data...")
                features = extract_features(pcap_file)
                
                if not features:
                    print("No valid IP packets found in PCAP file")
                    return
                
                print(f"Sending {len(features)} packet features to server...")
                for i, feature in enumerate(features, 1):
                    await websocket.send(json.dumps(feature))
                    server_response = await websocket.recv()
                    if i % 100 == 0:  # Progress update every 100 packets
                        print(f"Processed {i}/{len(features)} packets")
                
                print("All data sent successfully")
            else:
                print(f"Connection rejected by server: {response_data.get('message', 'No reason provided')}")

    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed unexpectedly: {str(e)}")
    except websockets.exceptions.WebSocketException as e:
        print(f"WebSocket error: {str(e)}")
    except json.JSONDecodeError as e:
        print(f"Error parsing server response: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    # Configuration
    pcap_file = "traffic.pcap"
    server_uri = "ws://192.168.1.2:8765"  # Changed to localhost for testing
    machine_id = generate_machine_id()

    try:
        asyncio.run(connect_to_server(machine_id, pcap_file, server_uri))
    except KeyboardInterrupt:
        print("\nShutting down agent...")
        sys.exit(0)