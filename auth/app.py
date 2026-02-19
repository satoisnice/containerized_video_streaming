from flask import Flask, request, jsonify
import jwt
import datetime

app = Flask(__name__)
SECRET_KEY = "your_super_secret_key"

# Mock Database
USERS = {"admin": "password"}

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if USERS.get(username) == password:
        token = jwt.encode({
            "user": username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        }, SECRET_KEY, algorithm="HS256")
        return jsonify({"token": token})

    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/verify", methods=["GET"])
def verify():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"valid": False}), 401
    
    try:
        # Remove "Bearer " prefix
        actual_token = token.split(" ")[1]
        jwt.decode(actual_token, SECRET_KEY, algorithms=["HS256"])
        return jsonify({"valid": True})
    except:
        return jsonify({"valid": False}), 401

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)