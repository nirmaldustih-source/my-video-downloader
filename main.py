import os
import requests
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import yt_dlp
from urllib.parse import quote

app = Flask(__name__)
CORS(app)

def format_size(bytes_size):
    if not bytes_size:
        return "Unknown Size"
    try:
        mb = bytes_size / (1024 * 1024)
        return f"{mb:.1f} MB"
    except:
        return "Unknown Size"

# 👑 මෙතනින් උඹේ නම අයින් කරලා "Social Media Downloader API" කියලා දැම්මා මචං!
@app.route('/')
def home():
    return jsonify({"status": "Server is running smoothly!", "service": "Social Media Downloader API"})

@app.route('/api/download', methods=['GET'])
def download_video():
    url = request.args.get('url')
    if not url:
        return jsonify({"success": False, "error": "URL එකක් දාලා නැහැ මචං!"}), 400

    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'Social Media Video')
            thumbnail = info.get('thumbnail', 'https://placehold.co/600x338/png')
            formats_data = info.get('formats', [])

            res_formats = {
                "1080p": {"url": "None", "size": "-- MB"},
                "720p": {"url": "None", "size": "-- MB"},
                "480p": {"url": "None", "size": "-- MB"}
            }

            for f in formats_data:
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    height = f.get('height')
                    f_url = f.get('url')
                    f_size = f.get('filesize') or f.get('filesize_approx')

                    if height == 1080:
                        res_formats["1080p"] = {"url": f_url, "size": format_size(f_size)}
                    elif height == 720:
                        res_formats["720p"] = {"url": f_url, "size": format_size(f_size)}
                    elif height == 480 or (height and 360 <= height <= 480 and res_formats["480p"]["url"] == "None"):
                        res_formats["480p"] = {"url": f_url, "size": format_size(f_size)}

            best_url = info.get('url')
            best_size = info.get('filesize') or info.get('filesize_approx')
            
            if res_formats["720p"]["url"] == "None" and best_url:
                res_formats["720p"] = {"url": best_url, "size": format_size(best_size)}

            return jsonify({
                "success": True,
                "title": title,
                "thumbnail": thumbnail,
                "formats": res_formats
            })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/stream')
def stream_video():
    video_url = request.args.get('video_url')
    title = request.args.get('title', 'video')
    
    if not video_url or video_url == "None":
        return "Error: වලංගු වීඩියෝ ලින්ක් එකක් නැත!", 400
        
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        req = requests.get(video_url, headers=headers, stream=True, timeout=15)
        
        encoded_filename = quote(f"{title}.mp4")
        
        download_headers = {
            'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}",
            'Content-Type': 'video/mp4',
            'Cache-Control': 'no-cache'
        }
        
        def generate():
            for chunk in req.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
                    
        return Response(generate(), headers=download_headers)
        
    except Exception as e:
        return f"ප්‍රොක්සි කිරීමේ දෝෂයක් මචං: {str(e)}", 500

@app.route('/api/download-thumbnail')
def download_thumbnail():
    image_url = request.args.get('image_url')
    title = request.args.get('title', 'thumbnail')
    
    if not image_url:
        return "Error: No Image URL", 400
        
    try:
        req = requests.get(image_url, stream=True, timeout=10)
        encoded_filename = quote(f"{title}.jpg")
        
        download_headers = {
            'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}",
            'Content-Type': 'image/jpeg'
        }
        return Response(req.content, headers=download_headers)
    except Exception as e:
        return f"Thumbnail Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
