from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

ROOT_SERVER_URL = "http://<root_server_ip>:5000/data"

@app.route("/data", methods=["POST"])
def receive_data():
    data = request.json
    print("Nhận dữ liệu từ Agent:", data)
    try:
        # Gửi dữ liệu lên Root Server
        response = requests.post(ROOT_SERVER_URL, json=data)
        return jsonify({"status": "forwarded", "root_response": response.json()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000)
