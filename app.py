from flask import Flask, request, jsonify, send_file
import requests
import os

app = Flask(__name__)

DB_SERVICE_URL = os.environ.get("DB_SERVICE_URL","http://db-service:5002")
FILESYSTEM_SERVICE_URL = os.environ.get("FILESYSTEM_SERVICE_URL", "http://filesystem-service:5003")


# HOME PAGE - Upload Form
@app.route("/", methods=["GET"])
def index():
    return '''
        <h2>Upload Video</h2>
        <form action="/upload" method="POST" enctype="multipart/form-data">
            <input type="file" name="video" accept="video/*">
            <button type="submit">Upload</button>
        </form>
        <br>
        <a href="/videos">View All Videos</a>
    '''


'''VIDEO UPLOAD'''
@app.route("/upload", methods=["POST"])
def upload_video():
    video_file = request.files.get("video")
    video_name = video_file.filename

    fs_resp = requests.post(
        f"{FILESYSTEM_SERVICE_URL}/upload",
        files={"file": (video_name, video_file.stream, video_file.mimetype)}
    )
    file_path = fs_resp.json().get("path")

    requests.post(
        f"{DB_SERVICE_URL}/videos",
        json={"name": video_name, "path": file_path}
    )

    return '''
        <h2>Upload Successful!</h2>
        <a href="/">Upload Another</a> | <a href="/videos">View All Videos</a>
    '''


'''All Videos'''
@app.route("/videos", methods=["GET"])
def list_videos():
    db_resp = requests.get(f"{DB_SERVICE_URL}/videos")
    videos = db_resp.json().get("videos", [])

    video_links = "".join(
        f'<li><a href="/stream/{v["id"]}">{v["name"]}</a></li>'
        for v in videos
    )

    return f'''
        <h2>All Videos</h2>
        <ul>{video_links}</ul>
        <br>
        <a href="/">Upload a Video</a>
    '''


'''Streaming'''
@app.route("/stream/<int:video_id>", methods=["GET"])
def stream_video(video_id):
    db_resp = requests.get(f"{DB_SERVICE_URL}/videos/{video_id}")
    file_path = db_resp.json().get("path")

    fs_resp = requests.get(
        f"{FILESYSTEM_SERVICE_URL}/read",
        params={"path": file_path}
    )

    temp_path = f"temp_{video_id}.mp4"
    with open(temp_path, "wb") as f:
        f.write(fs_resp.content)

    return send_file(temp_path, mimetype="video/mp4")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)