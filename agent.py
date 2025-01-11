import asyncio
import websockets
import json
import uuid
import os
from scapy.all import rdpcap, IP, wrpcap, sniff
import sys
import time

def generate_machine_id():
    return str(uuid.uuid4())

def create_pcap_file(filename, duration=60):
    print(f"Bắt đầu bắt gói tin trong {duration} giây...")
    try:
        packets = sniff(timeout=duration)
        wrpcap(filename, packets)
        print(f"Đã tạo file PCAP: {filename}")
        print(f"Số lượng gói tin đã bắt: {len(packets)}")
        return True
    except Exception as e:
        print(f"Ởi khi tạo file PCAP: {str(e)}")
        return False

def verify_pcap_file(pcap_file):
    if not os.path.exists(pcap_file):
        raise FileNotFoundError(f"Không tìm thấy file PCAP: {pcap_file}")
    try:
        packets = rdpcap(pcap_file)
        return len(packets) > 0
    except Exception as e:
        raise Exception(f"Ởi khi đọc file PCAP: {str(e)}")

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
                "flow_duration": float(packet.time)
            })
    return extracted_data

async def connect_to_server(machine_id, pcap_file, server_uri):
    print(f"ID máy: {machine_id}")
    print(f"Đang thử kết nối đến server tại {server_uri}")
    try:
        if not create_pcap_file(pcap_file):
            print("Không thể tạo file PCAP mới")
            return
        if not verify_pcap_file(pcap_file):
            print("Lỗi: File PCAP trống")
            return

        # Remove timeout
        async with websockets.connect(server_uri, ping_interval=None) as websocket:
            print("Đã kết nối tới WebSocket server")

            auth_message = {"machine_id": machine_id}
            print("Đang gửi xác thực...")
            await websocket.send(json.dumps(auth_message))

            response = await websocket.recv()
            response_data = json.loads(response)

            if response_data.get("status") == "approved":
                print("Xác thực thành công. Đang xử lý dữ liệu PCAP...")
                features = extract_features(pcap_file)

                if not features:
                    print("Không tìm thấy gói tin IP hợp lệ trong file PCAP")
                    return

                print(f"Đang gửi {len(features)} đặc trưng gói tin tới server...")
                for i, feature in enumerate(features, 1):
                    await websocket.send(json.dumps(feature))
                    server_response = await websocket.recv()
                    if i % 100 == 0:
                        print(f"Đã xử lý {i}/{len(features)} gói tin")

                print("Đã gửi tất cả dữ liệu thành công")
            else:
                print(f"Server từ chối kết nối: {response_data.get('message', 'Không có lý do')}")

    except FileNotFoundError as e:
        print(f"Lỗi: {str(e)}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Kết nối bị đóng đột ngột: {str(e)}")
    except websockets.exceptions.WebSocketException as e:
        print(f"Lỗi WebSocket: {str(e)}")
    except json.JSONDecodeError as e:
        print(f"Lỗi phân tích phản hồi từ server: {str(e)}")
    except Exception as e:
        print(f"Lỗi không mong đợi: {str(e)}")

if __name__ == "__main__":
    pcap_file = "traffic.pcap"
    server_uri = "ws://192.168.1.2:8765"
    machine_id = generate_machine_id()

    try:
        asyncio.run(connect_to_server(machine_id, pcap_file, server_uri))
    except KeyboardInterrupt:
        print("\nĐang tắt agent...")
        sys.exit(0)
