import os
import re
import requests
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)  # Frontend connection allowance

# Flask 3+ වල සිංහල අකුරු ප්‍රශ්නාර්ථ ලකුණු (???) නොවී හරියට යවන්න:
app.json.ensure_ascii = False

@app.route('/')
def home():
    return jsonify({"status": "live", "message": "Social Media Downloader API is working perfectly!"})

# 1. FETCH VIDEO DATA & DYNAMIC SIZES ENDPOINT
@app.route('/api/download', methods=['GET'])
def get_video_info():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"success": False, "error": "වීඩියෝ ලින්ක් එකක් ඇතුලත් කරලා නැහැ බොක්කා!"}), 400

    # Facebook/Instagram bypass headers
    ydl_opts = {
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            title = info.get('title', 'Social_Media_Video')
            thumbnail = info.get('thumbnail', '')
            formats_dict = {}

            # Filter formats safely
            formats = info.get('formats', [])
            
            # 1080p Check
            f_1080 = next((f for f in formats if f.get('height') == 1080 and f.get('vcodec') != 'none'), None)
            if f_1080:
                size_mb = f"{round(f_1080['filesize'] / (1024*1024), 2)} MB" if f_1080.get('filesize') else "Unknown Size"
                formats_dict["1080p"] = {"url": f_1080.get('url'), "size": size_mb}
            else:
                formats_dict["1080p"] = {"url": "None", "size": "Not Available"}

            # 720p Check
            f_720 = next((f for f in formats if f.get('height') == 720 and f.get('vcodec') != 'none'), None)
            if f_720:
                size_mb = f"{round(f_720['filesize'] / (1024*1024), 2)} MB" if f_720.get('filesize') else "Unknown Size"
                formats_dict["720p"] = {"url": f_720.get('url'), "size": size_mb}
            else:
                # Fallback to best available if 720p directly not found
                f_best = info.get('url')
                formats_dict["720p"] = {"url": f_best if f_best else "None", "size": "Best Quality"}

            # 480p Check
            f_480 = next((f for f in formats if f.get('height') == 480 and f.get('vcodec') != 'none'), None)
            if f_480:
                size_mb = f"{round(f_480['filesize'] / (1024*1024), 2)} MB" if f_480.get('filesize') else "Unknown Size"
                formats_dict["480p"] = {"url": f_480.get('url'), "size": size_mb}
            else:
                formats_dict["480p"] = {"url": "None", "size": "Not Available"}

            return jsonify({
                "success": True,
                "title": title,
                "thumbnail": thumbnail,
                "formats": formats_dict
            })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# 2. SAFE CHUNKED STREAMING DOWNLOAD ENDPOINT (RAM එක කුඩු වෙන්නේ නැති වෙන්න)
@app.route('/api/stream')
def stream_video():
    video_url = request.args.get('video_url')
    title = request.args.get('title', 'video')

    if not video_url or video_url == "None":
        return jsonify({"success": False, "error": "Invalid Video URL passed"}), 400

    # Clean title for file system headers
    clean_title = re.sub(r'[^\w\-_\. ]', '_', title)

    try:
        # Stream=True මඟින් මුළු වීඩියෝවම එකපාර RAM එකට ලෝඩ් වීම වළක්වයි
        req = requests.get(video_url, stream=True, timeout=30)
        
        headers = {
            'Content-Type': req.headers.get('Content-Type', 'video/mp4'),
            'Content-Disposition': f'attachment; filename="{clean_title}.mp4"',
            'Content-Length': req.headers.get('Content-Length')
        }

        # සර්වර් එකේ RAM එක පිරෙන්නේ නැතුව 1MB බැගින් බ්‍රව්සර් එකට Stream කරයි
        def generate():
            for chunk in req.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    yield chunk

        return Response(generate(), headers=headers)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# 3. SAFE THUMBNAIL DOWNLOAD ENDPOINT
@app.route('/api/download-thumbnail')
def download_thumbnail():
    image_url = request.args.get('image_url')
    if not image_url:
        return jsonify({"success": False, "error": "Image URL is required"}), 400

    try:
        req = requests.get(image_url, stream=True, timeout=15)
        headers = {
            'Content-Type': req.headers.get('Content-Type', 'image/jpeg'),
            'Content-Disposition': 'attachment; filename="thumbnail.jpg"'
        }
        return Response(req.content, headers=headers)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
