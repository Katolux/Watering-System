from flask import Flask, request

#Flask test for andruino_send_test.

app = Flask(__name__)

@app.route("/ping", methods=["POST"])
def ping():
    print("Received from ESP32:", request.json)
    return {"status": "ok"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
