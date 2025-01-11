import asyncio
import websockets
import json
import uuid
import platform
from pyflowmeter.utils import read_pcap

# Tạo machine_id duy nhất dựa trên thông tin hệ thống
def generate_machine_id():
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, platform.node()))

# Trích xuất lưu lượng mạng từ file pcap hoặc giao diện trực tiếp
def extract_features(pcap_file):
    flows = read_pcap(pcap_file)
    extracted_data = []
    for flow in flows:
        extracted_data.append({
            "src_ip": flow.src_ip,
            "dst_ip": flow.dst_ip,
            "protocol": flow.protocol,
            "packet_count": flow.packet_count,
            "byte_count": flow.byte_count,
            "flow_duration": flow.flow_duration,
        })
    return extracted_data

async def connect_to_server(machine_id, pcap_file, server_uri):
    print(f"Machine ID: {machine_id}")
    async with websockets.connect(server_uri) as websocket:
        # Gửi machine_id để server xác thực
        await websocket.send(json.dumps({"machine_id": machine_id}))
        response = await websocket.recv()
        response_data = json.loads(response)

        if response_data.get("status") == "approved":
            print("Connection approved by server. Sending data...")
            # Gửi dữ liệu nếu được server phê duyệt
            features = extract_features(pcap_file)
            for feature in features:
                await websocket.send(json.dumps(feature))
                server_response = await websocket.recv()
                print(f"Server response: {server_response}")
        else:
            print("Connection rejected by server.")

# Khởi chạy Agent
if __name__ == "__main__":
    pcap_file = "traffic.pcap"  # Thay bằng đường dẫn tới file pcap của bạn
    server_uri = "ws://localhost:8765"  # Địa chỉ WebSocket của server
    machine_id = generate_machine_id()
    asyncio.run(connect_to_server(machine_id, pcap_file, server_uri))
