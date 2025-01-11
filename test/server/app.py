from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import logging

app = Flask(__name__)
socketio = SocketIO(app)

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s: %(message)s")

# Mocked database of users
users_db = {
    "default-machine-id": {
        "api_key": "default-api-key",
        "ip": "127.0.0.1"
    }
}

# Active clients
clients = {}


@app.route('/')
def index():
    """Renders the index page."""
    return render_template('index.html', clients=clients)


@app.route('/api/agent/connect', methods=['POST'])
def connect_agent():
    """Handles agent connection."""
    data = request.json
    api_key = data.get("api_key")
    machine_id = data.get("machine_id")
    ip = data.get("ip")

    if validate_agent(api_key, machine_id):
        logging.info(f"Agent connected: {ip} with Machine ID: {machine_id}")
        return jsonify({"message": "Connected successfully"}), 200
    else:
        logging.warning(f"Invalid connection attempt: {data}")
        return jsonify({"error": "Invalid API key or Machine ID"}), 403


@app.route('/api/agent/command', methods=['POST'])
def send_command():
    """Sends a command to the agent."""
    data = request.json
    machine_id = data.get("machine_id")
    command = data.get("command")

    client_sid = get_client_sid_by_machine_id(machine_id)
    if client_sid:
        emit("control", {"command": command}, room=client_sid, namespace="/")
        logging.info(f"Command '{command}' sent to Machine ID: {machine_id}")
        return jsonify({"message": f"Command '{command}' sent to agent {machine_id}"}), 200
    else:
        logging.warning(f"Machine ID {machine_id} not connected.")
        return jsonify({"error": "Agent not connected"}), 404


@socketio.on('connect', namespace='/ws')
def on_connect():
    """Handles WebSocket connection."""
    machine_id = request.args.get('machine_id')
    clients[request.sid] = {"machine_id": machine_id, "sid": request.sid}
    logging.info(f"Client connected: {
                 request.sid} with Machine ID: {machine_id}")


@socketio.on('disconnect', namespace='/ws')
def on_disconnect():
    """Handles WebSocket disconnection."""
    if request.sid in clients:
        machine_id = clients[request.sid]["machine_id"]
        del clients[request.sid]
        logging.info(f"Client disconnected: {
                     request.sid} with Machine ID: {machine_id}")


@socketio.on('control', namespace='/ws')
def control_agent(data):
    """Receives and processes control commands."""
    command = data.get("command")
    machine_id = data.get("machine_id")

    client_sid = get_client_sid_by_machine_id(machine_id)
    if client_sid:
        emit("control", {"command": command}, room=client_sid)
        logging.info(f"Sent command '{command}' to Machine ID: {machine_id}")
    else:
        logging.warning(f"Cannot send command. Machine ID {
                        machine_id} not connected.")


def validate_agent(api_key, machine_id):
    """Validates the agent's API key and machine ID."""
    user = users_db.get(machine_id)
    return user and user["api_key"] == api_key


def get_client_sid_by_machine_id(machine_id):
    """Gets the WebSocket SID for a given machine ID."""
    for sid, client in clients.items():
        if client["machine_id"] == machine_id:
            return sid
    return None


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
