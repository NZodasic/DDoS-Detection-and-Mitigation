import asyncio
import websockets
import psutil
import json
import socket
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SERVER_URL = os.getenv("SERVER_URL", "ws://localhost:5000/ws")
API_KEY = os.getenv("API_KEY", "default-api-key")
MACHINE_ID = os.getenv("MACHINE_ID", "default-machine-id")

# Configure logging
LOG_FILE = Path("agent.log")
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format="%(asctime)s %(levelname)s: %(message)s")


async def get_network_metrics():
    """Collects network metrics using psutil."""
    stats = psutil.net_io_counters()
    return {
        "bytes_sent": stats.bytes_sent,
        "bytes_recv": stats.bytes_recv,
        "packets_sent": stats.packets_sent,
        "packets_recv": stats.packets_recv
    }


async def connect_to_server():
    """Establishes WebSocket connection and communicates with the server."""
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)

    try:
        async with websockets.connect(SERVER_URL) as websocket:
            # Send initial connection message
            connect_message = json.dumps({
                "type": "connect",
                "api_key": API_KEY,
                "machine_id": MACHINE_ID,
                "hostname": hostname,
                "ip": ip_address
            })
            await websocket.send(connect_message)
            logging.info(f"Connected to server with Machine ID: {MACHINE_ID}")

            # Main loop for sending metrics and receiving commands
            while True:
                # Send network metrics
                metrics = await get_network_metrics()
                message = json.dumps({
                    "type": "data",
                    "api_key": API_KEY,
                    "machine_id": MACHINE_ID,
                    "data": metrics
                })
                await websocket.send(message)
                logging.info(f"Data sent from Machine ID: {
                             MACHINE_ID}: {metrics}")

                # Wait for commands or control messages from the server
                try:
                    server_response = await websocket.recv()
                    response = json.loads(server_response)

                    if response.get("command") == "stop":
                        logging.info("Received stop command. Shutting down...")
                        break
                    elif response.get("command") == "update":
                        logging.info(
                            "Received update command. Placeholder for update logic.")
                        # Add update logic if needed

                except websockets.ConnectionClosed as e:
                    logging.error(f"Connection closed unexpectedly: {
                                  e}. Reconnecting in 5 seconds...")
                    await asyncio.sleep(5)
                    break

        # Reconnect logic
        logging.info("Reconnecting to server...")
        await asyncio.sleep(5)
        await connect_to_server()

    except Exception as e:
        logging.error(f"Failed to connect to server: {
                      e}. Retrying in 5 seconds...")
        await asyncio.sleep(5)
        await connect_to_server()


async def main():
    """Main loop for connecting the agent to the server."""
    while True:
        try:
            await connect_to_server()
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
