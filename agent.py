import asyncio
import websockets
import json
import uuid
from scapy.all import rdpcap, IP

# Tạo machine_id duy nhất cho từng agent
def generate_machine_id():
    return str(uuid.uuid4())  # Sử dụng UUID ngẫu nhiên

# Trích xuất đặc trưng từ file PCAP
def extract_features(pcap_file):
    packets = rdpcap(pcap_file)  # Đọc file PCAP
    extracted_data = []
    for packet in packets:
        if IP in packet:  # Chỉ xử lý các gói có lớp IP
            extracted_data.append({
                "src_ip": packet[IP].src,
                "dst_ip": packet[IP].dst,
                "protocol": packet[IP].proto,
                "packet_count": 1,  # Mỗi packet tính là 1 gói
                "byte_count": len(packet),  # Kích thước gói (byte)
                "flow_duration": packet.time  # Thời gian gói được gửi
            })
    return extracted_data

# Kết nối tới server qua WebSocket
async def connect_to_server(machine_id, pcap_file, server_uri):
    print(f"Machine ID: {machine_id}")
    print("Provide this Machine ID to the server to authorize this agent.")

    async with websockets.connect(server_uri) as websocket:
        # Gửi machine_id để server xác thực
        await websocket.send(json.dumps({"machine_id": machine_id}))
        response = await websocket.recv()
        response_data = json.loads(response)

        if response_data.get("status") == "approved":
            print("Connection approved by server. Sending data...")
            # Gửi dữ liệu lưu lượng mạng nếu được server phê duyệt
            features = extract_features(pcap_file)
            for feature in features:
                await websocket.send(json.dumps(feature))
                server_response = await websocket.recv()
                print(f"Server response: {server_response}")
        else:
            print("Connection rejected by server.")

# Hàm main khởi chạy agent
if __name__ == "__main__":
    # Cấu hình file PCAP và server WebSocket
    pcap_file = "traffic.pcap"  # Đường dẫn tới file PCAP
    server_uri = "ws://192.168.1.2:8765"  # Địa chỉ server (thay đổi IP phù hợp)
    machine_id = generate_machine_id()

    # Chạy agent
    asyncio.run(connect_to_server(machine_id, pcap_file, server_uri))
