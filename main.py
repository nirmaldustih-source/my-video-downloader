import os
import re
import requests
import urllib.parse
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)  # Frontend එක බ්ලොක් නොවී කනෙක්ට් වෙන්න

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

    # Facebook/Instagram බ්ලොක් නොවී වැඩකරන්න headers
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

            # 480p, 720p, 1080p වෙන වෙනම සයිස් ටික නිවැරදිව ෆ්ලෝ වෙන්න හදපු ලොජික් එක
            for f in formats:
                url = f.get('url')
                if not url:
                    continue
                
                # බයිට්ස් ගාණ ලස්සනට MB වලට හරවනවා
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

                # එකම කොලිටි එකේ ෆෝමැට් කිහිපයක් තිබ්බොත්, සයිස් එක තියෙන එකට මුල් තැන දෙනවා
                if height == 1080 or "1080" in format_id:
                    if "1080p" not in formats_dict or size_str != "HQ Size":
                        formats_dict["1080p"] = {"size": size_str, "url": url}
                elif height == 720 or "720" in format_id or "hd" in format_id:
                    if "720p" not in formats_dict or size_str != "HQ Size":
                        formats_dict["720p"] = {"size": size_str, "url": url}
                elif height == 480 or "480" in format_id or "sd" in format_id:
                    if "480p" not in formats_dict or size_str != "HQ Size":
                        formats_dict["480p"] = {"size": size_str, "url": url}

            # යම් හෙයකින් සයිස් එකක් මිස් වුණොත් විතරක් පාවිච්චි වෙන Fallback එකක්
            fallback_url = info.get('url') or video_url
            
            # 720p තියෙනවා නම් ඒක 1080p එකට fallback එකක් විදිහට දෙනවා (හැබැයි 720p සයිස් එක වෙනස් වෙන්නේ නෑ)
            if "720p" in formats_dict and "1080p" not in formats_dict:
                formats_dict["1080p"] = {"size": formats_dict["720p"]["size"], "url": formats_dict["720p"]["url"]}
            if "480p" in formats_dict and "720p" not in formats_dict:
                formats_dict["720p"] = {"size": formats_dict["480p"]["size"], "url": formats_dict["480p"]["url"]}

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
        return jsonify({"success": False, "error": f"තොරතුරු ලබාගැනීම අසාර්ථකයි! ({str(e)})"}), 500


# 2. CRITICAL DIRECT DOWNLOAD RESOLVER (Unicode Error එක සදහටම පලවා හැරීම)
@app.route('/api/stream', methods=['GET'])
def stream_video():
    video_url = request.args.get('video_url')
    title = request.args.get('title', 'video')

    if not video_url or video_url == "None":
        return "වීඩියෝ ලින්ක් එකක් නැත!", 400

    # සිංහල අකුරු හෙඩර් එක ඇතුලට සුරක්ෂිතව දාන්න Latin-1 Crash එක වළක්වන Encoding එක
    clean_title = re.sub(r'[^\w\-_.]', '_', title)
    encoded_filename = urllib.parse.quote(f"{clean_title}.mp4")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    }

    try:
        req = requests.get(video_url, headers=headers, stream=True, timeout=30)
        
        def generate():
            for chunk in req.iter_content(chunk_size=1024 * 1024):  # 1MB Chunks වලින් බ්‍රව්සර් එකට Stream කරනවා
                if chunk:
                    yield chunk

        # filename* එක භාවිතයෙන් UTF-8 අකුරු සුරක්ෂිතව බ්‍රව්සර් එකට පාස් කරනවා (සර්වර් එක Crash වෙන්නේ නෑ)
        return Response(
            generate(),
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                "Content-Type": "video/mp4"
            }
        )
    except Exception as e:
        print(f"Streaming error: {str(e)}")
        return f"බාගත වීමේදී දෝෂයක් ඇතිවිය: {str(e)}", 500


# 3. THUMBNAIL DOWNLOAD ENDPOINT
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
        return f"තම්බ්නේල් බාගත කිරීම අසාර්ථකයි: {str(e)}", 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
