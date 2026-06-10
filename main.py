import os
import requests
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
# Desktop HTML එකේ ඉඳන් එන රික්වෙස්ට් බ්ලොක් නොවී වැඩ කරන්න CORS හදනවා
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.route('/')
def home():
    return "Temporary Name Downloader API is Running Successfully! 🔥"

@app.route('/api/extract', methods=['POST'])
def extract_video():
    data = request.json
    if not data:
        return jsonify({'error': 'No data received!'}), 400
        
    url = data.get('url')
    if not url:
        return jsonify({'error': 'කරුණාකර URL එකක් ඇතුළත් කරන්න මචන්!'}), 400

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'Facebook Video')
            thumbnail = info.get('thumbnail', 'https://placehold.co/600x338/png')
            
            formats_list = []
            formats = info.get('formats', [])
            
            for f in formats:
                if f.get('url') and f.get('acodec') != 'none' and f.get('vcodec') != 'none':
                    height = f.get('height')
                    resolution = f"{height}p" if height else f.get('format_note', 'MP4 Video')
                    
                    filesize = f.get('filesize') or f.get('filesize_approx')
                    size_str = f"{round(filesize / (1024 * 1024), 1)} MB" if filesize else "Dynamic Size"
                    
                    formats_list.append({
                        'resolution': resolution,
                        'size': size_str,
                        'url': f.get('url')
                    })
            
            if not formats_list and info.get('url'):
                formats_list.append({
                    'resolution': 'Normal Quality',
                    'size': 'Dynamic Size',
                    'url': info.get('url')
                })

            return jsonify({
                'title': title,
                'thumbnail': thumbnail,
                'formats': formats_list,
                'jpg_url': thumbnail
            })

    except Exception as e:
        return jsonify({'error': f'වීඩියෝ විස්තර ගන්න බැරි වුණා: {str(e)}'}), 500

@app.route('/api/download')
def download_file():
    file_url = request.args.get('url')
    filename = request.args.get('filename', 'download.mp4')
    
    if not file_url:
        return "URL එක අඩුයි මචන්", 400
        
    try:
        req = requests.get(file_url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
        response = Response(req.iter_content(chunk_size=1024*1024), content_type=req.headers.get('Content-Type'))
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        # වෙන සයිට් එකක ඉඳන් බාගන්න දෙන නිසා මෙතනටත් header එකක් ඕනේ
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        return f"Download Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
