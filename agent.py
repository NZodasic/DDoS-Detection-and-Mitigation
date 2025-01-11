import asyncio
import websockets
import json
import uuid
from scapy.all import sniff, IP, wrpcap

def generate_machine_id():
    return str(uuid.uuid4())

def create_pcap_file(filename, duration=60):
    print(f"Bắt đầu bắt gói tin trong {duration} giây...")
    try:
        packets = sniff(timeout=duration)
        wrpcap(filename, packets)
        print(f"Đã tạo file PCAP: {filename}")
        return len(packets) > 0
    except Exception as e:
        print(f"Lỗi khi tạo file PCAP: {str(e)}")
        return False

def extract_features(pcap_file):
    from pyflowmeter.utils.reader import Reader
    
    features = []
    try:
        reader = Reader(pcap_file)
        for flow in reader:
            features.append({
                "packet_count": flow.packet_count,
                "byte_count": flow.byte_count,
                "flow_duration": flow.duration,
            })
    except Exception as e:
        print(f"Lỗi khi trích xuất đặc trưng: {e}")
    return features

async def connect_to_server(machine_id, pcap_file, server_uri):
    try:
        if not create_pcap_file(pcap_file):
            print("Không thể tạo file PCAP")
            return

        features = extract_features(pcap_file)
        if not features:
            print("Không tìm thấy đặc trưng hợp lệ")
            return

        async with websockets.connect(server_uri) as websocket:
            await websocket.send(json.dumps({"machine_id": machine_id}))
            response = json.loads(await websocket.recv())

            if response.get("status") == "approved":
                print("Đã kết nối với server, bắt đầu gửi dữ liệu...")
                for feature in features:
                    await websocket.send(json.dumps(feature))
                    print(await websocket.recv())
            else:
                print("Kết nối bị từ chối bởi server.")

    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    pcap_file = "traffic.pcap"
    server_uri = "ws://192.168.1.100:8765"  # Point to the Ubuntu server
    machine_id = generate_machine_id()

    asyncio.run(connect_to_server(machine_id, pcap_file, server_uri))
