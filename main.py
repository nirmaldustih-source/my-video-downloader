import os
import re
import requests
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

# Flask 3+ වල සිංහල අකුරු ප්‍රශ්නාර්ථ නොවී ලස්සනට යවන්න:
app.json.ensure_ascii = False

@app.route('/')
def home():
    return jsonify({"status": "live", "message": "Social Media Downloader API is working perfectly!"})

# 1. FETCH VIDEO DATA & DYNAMIC SIZES ENDPOINT
@app.route('/api/download', methods=['GET'])
def get_video_info():
    video_url = request.args.get('url')
    
    if not video_url:
        return jsonify({"success": False, "error": "වීඩියෝ ලින්ක් එකක් ඇතුලත් කරලා නැහැ මචං!"}), 400

    ydl_opts = {
        'nocheckcertificate': True,
        'geo_bypass': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-Fetch-Mode': 'navigate',
        },
        'skip_download': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            title = info.get('title', 'Social Media Video')
            thumbnail = info.get('thumbnail', 'https://placehold.co/600x338/png')
            
            formats_dict = {}
            formats = info.get('formats', [])
            duration = info.get('duration')

            for f in formats:
                url = f.get('url')
                if not url:
                    continue
                
                bytes_size = f.get('filesize') or f.get('filesize_approx') or 0
                if bytes_size > 0:
                    mb_size = round(bytes_size / (1024 * 1024), 2)
                    size_str = f"{mb_size} MB"
                elif duration and f.get('tbr'):
                    est_bytes = (f.get('tbr') * 1000 * duration) / 8
                    size_str = f"{round(est_bytes / (1024 * 1024), 2)} MB"
                else:
                    size_str = "HQ Size"

                height = f.get('height') or 0
                format_id = f.get('format_id', '')

                if height >= 1080 or "1080" in format_id:
                    formats_dict["1080p"] = {"size": size_str, "url": url}
                elif height >= 720 or "720" in format_id or "hd" in format_id:
                    formats_dict["720p"] = {"size": size_str, "url": url}
                elif height <= 480 or "480" in format_id or "sd" in format_id:
                    formats_dict["480p"] = {"size": size_str, "url": url}

            if "720p" in formats_dict and "1080p" not in formats_dict:
                formats_dict["1080p"] = formats_dict["720p"]
            
            if "480p" in formats_dict:
                if "720p" not in formats_dict: formats_dict["720p"] = formats_dict["480p"]
                if "1080p" not in formats_dict: formats_dict["1080p"] = formats_dict["480p"]

            fallback_url = info.get('url') or video_url
            for slot in ["1080p", "720p", "480p"]:
                if slot not in formats_dict:
                    formats_dict[slot] = {"size": "HQ Download", "url": fallback_url}

            return jsonify({
                "success": True,
                "title": title,
                "thumbnail": thumbnail,
                "formats": formats_dict
            })

    except Exception as e:
        print(f"Error extracting info: {str(e)}")
        return jsonify({"success": False, "error": f"වීඩියෝ තොරතුරු ලබාගන්න බැරි වුණා මචං! ({str(e)})"}), 500


# 2. CRITICAL DIRECT DOWNLOAD RESOLVER (එකම ටැබ් එකේ බලෙන්ම බාන කෑල්ල)
@app.route('/api/stream', methods=['GET'])
def stream_video():
    video_url = request.args.get('video_url')
    title = request.args.get('title', 'video')

    if not video_url or video_url == "None":
        return "වීඩියෝ ලින්ක් එකක් නැත!", 400

    clean_title = re.sub(r'[^\w\-_.]', '_', title)
    filename = f"{clean_title}.mp4"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    }

    try:
        req = requests.get(video_url, headers=headers, stream=True, timeout=30)
        
        def generate():
            for chunk in req.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    yield chunk

        return Response(
            generate(),
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
                "Content-Type": "video/mp4"
            }
        )
    except Exception as e:
        print(f"Streaming error: {str(e)}")
        return f"ඩවුන්ලෝඩ් එක මැදදී බිඳ වැටුණා මචං: {str(e)}", 500


# 3. THUMBNAIL DOWNLOAD ENDPOINT (JPG Photo බටන් එකට)
@app.route('/api/download-thumbnail', methods=['GET'])
def download_thumbnail():
    image_url = request.args.get('image_url')
    if not image_url:
        return "Image URL missing", 400
        
    try:
        req = requests.get(image_url, stream=True, timeout=15)
        return Response(
            req.iter_content(chunk_size=4096),
            headers={
                "Content-Disposition": "attachment; filename=thumbnail.jpg",
                "Content-Type": "image/jpeg"
            }
        )
    except Exception as e:
        return f"පින්තූරය බාන්න බැරි වුණා: {str(e)}", 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
