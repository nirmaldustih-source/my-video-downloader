import os
import requests
import yt_dlp
import urllib.parse
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.json.ensure_ascii = False

def log(msg, val=""):
    print(f"[LOG] {msg}: {val}")

@app.route('/api/download', methods=['GET'])
def get_video_info():
    url = request.args.get('url')
    if not url: return jsonify({"success": False, "error": "URL required"}), 400
    
    log("URL", url)
    ydl_opts = {'quiet': True, 'no_warnings': True, 'geo_bypass': True}
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Video')
            thumbnail = info.get('thumbnail') or "https://placehold.co/600x338/png"
            log("TITLE", title)
            
            formats_found = {}
            # 7. Quality sorting
            for f in info.get('formats', []):
                h = f.get('height')
                if h in [1080, 720, 480]:
                    size = f.get('filesize') or f.get('filesize_approx', 0)
                    size_mb = f"{round(size / (1024 * 1024), 1)} MB" if size > 0 else "---"
                    formats_found[f"{h}p"] = {"url": f.get('url'), "size": size_mb}
            
            return jsonify({
                "success": True, "title": title, 
                "thumbnail": thumbnail, "formats": dict(sorted(formats_found.items(), reverse=True))
            })
    except Exception as e:
        log("ERROR", str(e))
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/stream')
def stream():
    v_url = request.args.get('video_url')
    title = request.args.get('title', 'video')
    
    try:
        # 2 & 3. Timeout & Empty check
        req = requests.get(v_url, stream=True, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        if req.status_code != 200:
            return jsonify({"success": False, "error": f"Source returned {req.status_code}"}), 400
        
        headers = {
            'Content-Type': req.headers.get('Content-Type', 'video/mp4'),
            'Content-Disposition': f'attachment; filename*=UTF-8\'\'{urllib.parse.quote(title)}.mp4'
        }
        return Response(req.iter_content(chunk_size=1024*1024), headers=headers)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
