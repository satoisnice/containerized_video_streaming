from flask import Flask, request, jsonify, Response, render_template_string, redirect, make_response
import requests
import mysql.connector
import os
import time

app = Flask(__name__)

AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://auth:8080")
FILESYSTEM_SERVICE_URL = os.environ.get("FILESYSTEM_SERVICE_URL", "http://ffs:8000")

DB_CONFIG = {
    "host": "mysql-db",
    "user": "chud",
    "password": "son",
    "database": "video"
}

def query_db(query, args=(), one=False):
    """Helper to run SQL queries"""
    for i in range(5):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, args)
            rv = cursor.fetchall()
            conn.commit()
            cursor.close()
            conn.close()
            return (rv[0] if rv else None) if one else rv
        except Exception as e:
            print(f"DB Error, retrying... {e}")
            time.sleep(2)
    return None

def get_token():
    return request.cookies.get("auth_token") or request.args.get("token")

def is_authenticated(token):
    if not token: return False
    try:
        resp = requests.get(f"{AUTH_SERVICE_URL}/verify", 
                            headers={"Authorization": f"Bearer {token}"}, timeout=2)
        return resp.status_code == 200
    except:
        return False

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        try:
            resp = requests.post(f"{AUTH_SERVICE_URL}/login", json={"username": username, "password": password})
            if resp.status_code == 200:
                token = resp.json().get("token")
                response = make_response(redirect("/"))
                response.set_cookie("auth_token", token, httponly=True)
                return response
        except: pass
        return "<h2>Invalid Credentials</h2>", 401
    return '<form method="post">User: <input name="username"><br>Pass: <input name="password" type="password"><br><button>Login</button></form>'

@app.route("/")
def index():
    token = get_token()
    if not is_authenticated(token): return redirect("/login")
    return '<h2>Video Streaming App</h2><form action="/upload" method="post" enctype="multipart/form-data"><input type="file" name="video"><button>Upload</button></form><a href="/videos">Gallery</a>'

@app.route("/upload", methods=["POST"])
def upload():
    token = get_token()
    if not is_authenticated(token): return redirect("/login")

    video_file = request.files.get('video')
    if not video_file: return "No file", 400

    fs_resp = requests.post(f"{FILESYSTEM_SERVICE_URL}/upload/", 
                            files={"file": (video_file.filename, video_file.stream, video_file.mimetype)})
    
    if fs_resp.status_code == 200:
        file_data = fs_resp.json()
        query_db("INSERT INTO videos (name, path) VALUES (%s, %s)", 
                 (file_data["filename"], file_data["filename"]))
        return redirect("/videos")
    
    return "File Upload Failed", 500

@app.route("/videos")
def list_videos():
    token = get_token()
    if not is_authenticated(token): return redirect("/login")

    videos = query_db("SELECT name, path FROM videos")
    
    if not videos:
        return "<h2>No videos yet</h2><a href='/'>Back</a>"

    links = "".join([f'<li><a href="/stream/{v["path"]}">{v["name"]}</a></li>' for v in videos])
    return f"<h2>Gallery</h2><ul>{links}</ul><a href='/'>Back</a>"

@app.route("/stream/<filename>")
def stream(filename):
    token = get_token()
    if not is_authenticated(token): return redirect("/login")
    
    fs_url = f"{FILESYSTEM_SERVICE_URL}/videos/{filename}"
    fs_resp = requests.get(fs_url, stream=True)
    return Response(fs_resp.iter_content(chunk_size=1024*1024), mimetype='video/mp4')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)