from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/data", methods=["POST"])
def receive_data():
    data = request.json
    print("Nhận dữ liệu từ Intermediate Node:", data)
    # Lưu trữ hoặc xử lý dữ liệu
    return jsonify({"status": "success", "message": "Dữ liệu đã được nhận"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
