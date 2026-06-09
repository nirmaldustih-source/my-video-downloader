import os
import re
from flask import Flask, request, jsonify, send_file, after_this_request
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)  # Frontend එක බ්ලොක් නොවී කනෙක්ට් වෙන්න

# සිංහල අකුරු ප්‍රශ්නාර්ථ ලකුණු වෙන්නේ නැතුව ලස්සනට යවන්න මේක අනිවාර්යයි!
app.config['JSON_AS_ASCII'] = False

# ඩවුන්ලෝඩ් කරන වීඩියෝ තාවකාලිකව සේව් කරන්න ෆෝල්ඩර් එක
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@app.route('/')
def home():
    return jsonify({"status": "working", "message": "වීඩියෝ ඩවුන්ලෝඩර් සර්වර් එක සුපිරියටම වැඩ මචං!"})

@app.route('/get_info', methods=['POST'])
def get_info():
    data = request.json or {}
    video_url = data.get('url')

    if not video_url:
        return jsonify({"error": "මචං වීඩියෝ ලින්ක් එකක් ඇතුලත් කරලා නැහැ!"}), 400

    # Facebook බ්ලොක් නොකරන්න ඇත්තම බ්‍රව්සර් එකක Headers දාමු
    ydl_opts = {
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.facebook.com/',
        },
        'skip_download': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            title = info.get('title', 'Facebook Video')
            thumbnail = info.get('thumbnail', '')
            
            formats_list = []
            formats = info.get('formats', [])
            
            for f in formats:
                # සද්දෙයි වීඩියෝ එකයි දෙකම තියෙන ඒව විතරක් පෙන්නමු
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    
                    # සයිස් එක ගන්න සේෆ් ක්‍රමයක් (filesize නැත්නම් filesize_approx ගනී)
                    bytes_size = f.get('filesize') or f.get('filesize_approx') or 0
                    if bytes_size > 0:
                        mb_size = round(bytes_size / (1024 * 1024), 2)
                        size_str = f"{mb_size} MB"
                    else:
                        size_str = "Unknown Size"

                    formats_list.append({
                        'format_id': f.get('format_id'),
                        'ext': f.get('ext', 'mp4'),
                        'resolution': f.get('resolution') or f"{f.get('width')}x{f.get('height')}",
                        'size': size_str
                    })

            # ලැයිස්තුව හිස්නම් හොඳම එක ඔටෝ සෙට් කරමු
            if not formats_list:
                formats_list.append({
                    'format_id': 'best',
                    'ext': info.get('ext', 'mp4'),
                    'resolution': 'Best Quality',
                    'size': 'Unknown Size'
                })

            return jsonify({
                'title': title,
                'thumbnail': thumbnail,
                'formats': formats_list
            })

    except Exception as e:
        print(f"Info Error: {str(e)}")
        return jsonify({"error": f"වීඩියෝ තොරතුරු ලබාගන්න බැරි වුණා මචං! (ලෙඩේ: {str(e)})"}), 500

@app.route('/download', methods=['POST'])
def download_video():
    data = request.json or {}
    video_url = data.get('url')
    format_id = data.get('format_id', 'best')

    if not video_url:
        return jsonify({"error": "මචං වීඩියෝ ලින්ක් එකක් නැහැ!"}), 400

    outtmpl = os.path.join(DOWNLOAD_DIR, '%(title)s_%(id)s.%(ext)s')
    
    ydl_opts = {
        'format': format_id,
        'outtmpl': outtmpl,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.facebook.com/',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            file_path = ydl.prepare_filename(info)
            
            # Extension මාරු වුණොත් සේෆ් වෙන්න ඇත්තම ෆයිල් එක චෙක් කරමු
            if not os.path.exists(file_path):
                base_path, _ = os.path.splitext(file_path)
                for f in os.listdir(DOWNLOAD_DIR):
                    if f.startswith(os.path.basename(base_path)):
                        file_path = os.path.join(DOWNLOAD_DIR, f)
                        break

            if os.path.exists(file_path):
                # වීඩියෝ එක යැව්වට පස්සේ සර්වර් එකෙන් ඔටෝ මකන්න (Disk එක පිරෙන්නේ නැති වෙන්න)
                @after_this_request
                def remove_file(response):
                    try:
                        os.remove(file_path)
                    except Exception as error:
                        print(f"File delete error: {error}")
                    return response

                return send_file(file_path, as_attachment=True)
            else:
                return jsonify({"error": "සර්වර් එක ඇතුලේ වීඩියෝ ෆයිල් එක හොයාගන්න බැරි වුණා!"}), 404

    except Exception as e:
        print(f"Download Error: {str(e)}")
        return jsonify({"error": f"ඩවුන්ලෝඩ් එක ෆේල් වුණා මචං! (ලෙඩේ: {str(e)})"}), 500

if __name__ == '__main__':
    # Render එකේ පෝට් එක ඔටෝ අල්ලගන්න දාන කෑල්ල
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
