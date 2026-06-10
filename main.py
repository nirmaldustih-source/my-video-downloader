import os
import re
import requests
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

# Flask 3+ වල සිංහල අකුරු ප්‍රශ්නාර්ථ ලකුණු (???) නොවී හරියට යවන්න:
app.json.ensure_ascii = False

def calculate_size(format_obj):
    # filesize හෝ filesize_approx කියන දෙකෙන් තියෙන එකක් අරන් MB වලට හරවනවා
    bytes_size = format_obj.get('filesize') or format_obj.get('filesize_approx')
    if bytes_size:
        return f"{round(bytes_size / (1024 * 1024), 2)} MB"
    return "Dynamic Size"

@app.route('/')
def home():
    return jsonify({"status": "live", "message": "Social Media Downloader API is working perfectly!"})

# 1. FETCH VIDEO DATA & DYNAMIC SIZES ENDPOINT
@app.route('/api/download', methods=['GET'])
def get_video_info():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"success": False, "error": "වීඩියෝ ලින්ක් එකක් ඇතුලත් කරලා නැහැ බොක්කා!"}), 400

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
            formats = info.get('formats', [])

            # Frontend එක බලාපොරොත්තු වන Default ව්‍යුහය
            formats_dict = {
                "1080p": {"url": "None", "size": "Not Available"},
                "720p": {"url": "None", "size": "Not Available"},
                "480p": {"url": "None", "size": "Not Available"}
            }

            # වැඩ කරන වීඩියෝ Format ටික විතරක් පෙරලා ගන්නවා
            valid_formats = [f for f in formats if f.get('url') and f.get('vcodec') != 'none']

            if valid_formats:
                # Resolution එක අනුව වැඩිම එකේ සිට අඩුම එකට Sort කරනවා
                valid_formats.sort(key=lambda x: x.get('height') or x.get('tbr') or 0, reverse=True)
                
                # තියෙන හොඳම වීඩියෝ එක මුලින්ම ගන්නවා
                best_format = valid_formats[0]
                best_size = calculate_size(best_format)
                
                # Facebook/Instagram වල HD සහ SD ලෙඩේ හරියටම බෙදනවා
                for f in valid_formats:
                    f_height = f.get('height', 0)
                    f_id = str(f.get('format_id', '')).lower()
                    f_size = calculate_size(f)

                    if f_height == 1080 or '1080' in f_id:
                        if formats_dict["1080p"]["url"] == "None":
                            formats_dict["1080p"] = {"url": f['url'], "size": f_size}
                    elif f_height == 720 or 'hd' in f_id or '720' in f_id:
                        if formats_dict["720p"]["url"] == "None":
                            formats_dict["720p"] = {"url": f['url'], "size": f_size}
                    elif f_height == 480 or 'sd' in f_id or '480' in f_id:
                        if formats_dict["480p"]["url"] == "None":
                            formats_dict["480p"] = {"url": f['url'], "size": f_size}

                # කිසිම කොලිටි එකක් Match වුණේ නැත්නම් තියෙන හොඳම එක 720p/1080p වලට Fallback කරනවා
                if formats_dict["720p"]["url"] == "None" and formats_dict["1080p"]["url"] == "None":
                    formats_dict["720p"] = {"url": best_format['url'], "size": best_size}
                
                if formats_dict["480p"]["url"] == "None":
                    lowest_format = valid_formats[-1]
                    formats_dict["480p"] = {"url": lowest_format['url'], "size": calculate_size(lowest_format)}
            else:
                # එකම එක ලින්ක් එකක් විතරක් ආවොත් (Fallback)
                single_url = info.get('url')
                if single_url:
                    formats_dict["720p"] = {"url": single_url, "size": "Dynamic Size"}

            return jsonify({
                "success": True,
                "title": title,
                "thumbnail": thumbnail,
                "formats": formats_dict
            })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# 2. DYNAMIC CHUNKED STREAMING ENDPOINT (වීඩියෝ/ෆොටෝ ලෙඩේ සදහටම ඉවරයි)
@app.route('/api/stream')
def stream_video():
    video_url = request.args.get('video_url')
    title = request.args.get('title', 'download')

    if not video_url or video_url == "None":
        return jsonify({"success": False, "error": "Invalid URL passed"}), 400

    clean_title = re.sub(r'[^\w\-_\. ]', '_', title)

    try:
        req = requests.get(video_url, stream=True, timeout=30)
        content_type = req.headers.get('Content-Type', '').lower()
        
        # ලින්ක් එක Photo එකක්ද වීඩියෝ එකක්ද කියලා සර්වර් එකෙන්ම බලාගෙන Extension එක සෙට් කරනවා
        if 'image' in content_type:
            ext = 'png' if 'png' in content_type else 'jpg'
        else:
            ext = 'mp4'
            
        headers = {
            'Content-Type': content_type if content_type else 'video/mp4',
            'Content-Disposition': f'attachment; filename="{clean_title}.{ext}"',
            'Content-Length': req.headers.get('Content-Length')
        }

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
            'Content-Type': 'image/jpeg',
            'Content-Disposition': 'attachment; filename="thumbnail.jpg"'
        }
        return Response(req.content, headers=headers)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
