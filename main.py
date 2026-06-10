import os
import requests
import yt_dlp
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import urllib.parse

app = Flask(__name__)
CORS(app)
app.json.ensure_ascii = False

# 6. Logging - පේනවනේ පට්ට ලේසියි Render logs බලන්න
def log(msg, val=""):
    print(f"[LOG] {msg}: {val}")

@app.route('/api/download', methods=['GET'])
def get_video_info():
    url = request.args.get('url')
    if not url: return jsonify({"success": False, "error": "URL required"}), 400
    
    log("URL", url)
    
    # 4. Better yt-dlp options
    ydl_opts = {'quiet': True, 'no_warnings': True, 'geo_bypass': True}
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'Facebook Video')
            # 5. Preview fallback
            thumbnail = info.get('thumbnail') or "https://placehold.co/600x338/png"
            log("TITLE", title)
            
            formats_found = {}
            for f in info.get('formats', []):
                h = f.get('height')
                if h in [1080, 720, 480]:
                    size = f.get('filesize') or f.get('filesize_approx')
                    size_mb = f"{round(size / (1024 * 1024), 1)} MB" if size else "Unknown"
                    formats_found[f"{h}p"] = {"url": f.get('url'), "size": size_mb}
            
            # 7. Quality sorting (1080 -> 720 -> 480)
            sorted_formats = dict(sorted(formats_found.items(), reverse=True))
            
            return jsonify({
                "success": True, "title": title, 
                "thumbnail": thumbnail, "formats": sorted_formats
            })
    except Exception as e:
        log("ERROR", str(e))
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/stream')
def stream():
    v_url = request.args.get('url')
    title = request.args.get('title', 'video')
    
    # 2. Render timeout & 3. Empty response check
    try:
        req = requests.get(v_url, stream=True, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        if req.status_code != 200:
            return jsonify({"success": False, "error": f"Source returned {req.status_code}"}), 400
        
        headers = {
            'Content-Type': req.headers.get('Content-Type'),
            'Content-Disposition': f'attachment; filename*=UTF-8\'\'{urllib.parse.quote(title)}.mp4'
        }
        return Response(req.iter_content(chunk_size=1024*1024), headers=headers)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
