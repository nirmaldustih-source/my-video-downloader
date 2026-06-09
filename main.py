import os
import requests
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import yt_dlp
from urllib.parse import quote  # 🚀 සිංහල අකුරු ප්‍රශ්නය විසඳන්න මේක අනිවාර්යයි!

app = Flask(__name__)
# 🌍 වෙනත් Origins (Frontend) වල ඉඳන් එන Requests බ්ලොක් නොවෙන්න CORS දානවා
CORS(app)

def format_size(bytes_size):
    """Bytes ගාණ ලස්සනට MB වලට හරවන ෆන්ක්ෂන් එක"""
    if not bytes_size:
        return "Unknown Size"
    try:
        mb = bytes_size / (1024 * 1024)
        return f"{mb:.1f} MB"
    except:
        return "Unknown Size"

@app.route('/')
def home():
    return jsonify({"status": "Server is running smoothly!", "developer": "Sarada"})

# 🧠 1. VIDEO METADATA & REAL SIZES EXTRACTOR
@app.route('/api/download', methods=['GET'])
def download_video():
    url = request.args.get('url')
    if not url:
        return jsonify({"success": False, "error": "URL එකක් දාලා නැහැ මචං!"}), 400

    # yt-dlp settings (වීඩියෝ එක ඩවුන්ලෝඩ් කරන්නේ නැතුව විස්තර විතරක් ගන්නවා)
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

            # UI එකට යවන්න ලෑස්ති කරන Format Structure එක
            res_formats = {
                "1080p": {"url": "None", "size": "-- MB"},
                "720p": {"url": "None", "size": "-- MB"},
                "480p": {"url": "None", "size": "-- MB"}
            }

            # 🧠 වීඩියෝ එකේ තියෙන Formats ටික පීරලා 1080, 720, 480 වලට ගැලපෙන ඒවා වෙන් කරගන්නවා
            for f in formats_data:
                # Video සහ Audio දෙකම එකට තියෙන (acodec සහ vcodec තියෙන) ඒවා විතරක් ගන්නවා
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

            # 💡 සමහර සයිට් වල (උදා: Facebook) නිශ්චිතව 1080p/720p වෙන් කරලා නැත්නම් තියෙන හොඳම වීඩියෝ එක Default දෙනවා
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


# 🧠 2. CRITICAL PROXY STREAMER (සිංහල අකුරු සහ බ්‍රව්සර් ප්ලේ ලෙඩේ සුව කළ එක)
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
        # CDN එකෙන් වීඩියෝ එක Stream එකක් විදිහට ඇදලා ගන්නවා
        req = requests.get(video_url, headers=headers, stream=True, timeout=15)
        
        # 👑 FIX: සිංහල අකුරු / ඉමෝජි නිසා 'latin-1' crash වෙන එක නවත්වන්න UTF-8 URL Encode කරනවා!
        # filename*=UTF-8'' කියන එකෙන් ඕනෑම භාෂාවක නමක් බ්‍රව්සර් එකට කියවන්න පුළුවන් වෙනවා.
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


# 🧠 3. THUMBNAIL DOWNLOADER ENDPOINT (සිංහල මාතෘකා FIX එක සහිතයි)
@app.route('/api/download-thumbnail')
def download_thumbnail():
    image_url = request.args.get('image_url')
    title = request.args.get('title', 'thumbnail')
    
    if not image_url:
        return "Error: No Image URL", 400
        
    try:
        req = requests.get(image_url, stream=True, timeout=10)
        
        # මෙතනත් Thumbnail බාද්දී සිංහල තිබ්බොත් ලෙඩ නොදෙන්න Fix එක දැම්මා
        encoded_filename = quote(f"{title}.jpg")
        
        download_headers = {
            'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}",
            'Content-Type': 'image/jpeg'
        }
        return Response(req.content, headers=download_headers)
    except Exception as e:
        return f"Thumbnail Error: {str(e)}", 500


if __name__ == '__main__':
    # Render එකෙන් දෙන පෝට් එකට සෙට් වෙන්න දාපු ලොජික් එක
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
