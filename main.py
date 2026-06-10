import os
import requests
from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
import yt_dlp

app = Flask(__name__, template_folder=".")
CORS(app)

@app.route('/')
def home():
    return render_template('index-1.html')

@app.route('/api/extract', methods=['POST'])
def extract_video():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'කරුණාකර URL එකක් ඇතුළත් කරන්න මචන්!'}), 400

    # Facebook සහ අනෙකුත් වීඩියෝ Extract කිරීමට අවශ්‍ය සෙටින්ග්ස්
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
                # වීඩියෝ සහ ඕඩියෝ දෙකම තියෙන direct links විතරක් පෙරා ගන්නවා
                if f.get('url') and f.get('acodec') != 'none' and f.get('vcodec') != 'none':
                    height = f.get('height')
                    resolution = f"{height}p" if height else f.get('format_note', 'MP4 Video')
                    
                    # ඇත්තම ෆයිල් සයිස් එක ගන්නවා (නැත්නම් ලඟම අගය ගන්නවා)
                    filesize = f.get('filesize') or f.get('filesize_approx')
                    size_str = f"{round(filesize / (1024 * 1024), 1)} MB" if filesize else "Dynamic Size"
                    
                    formats_list.append({
                        'resolution': resolution,
                        'size': size_str,
                        'url': f.get('url')
                    })
            
            # කිසිම format එකක් සෙට් වුණේ නැත්නම් fallback එකක් දානවා
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

# වෙන ටැබ් වලට නොයා "බුක් ගාලා" ඩවුන්ලෝඩ් වෙන්න හදපු සුපිරි ප්‍රොක්සි රවුට් එක
@app.route('/api/download')
def download_file():
    file_url = request.args.get('url')
    filename = request.args.get('filename', 'download.mp4')
    
    if not file_url:
        return "URL එක අඩුයි මචන්", 400
        
    try:
        # ෆයිල් එක සර්වර් එකට ස්ට්‍රීම් කරලා කෙලින්ම ක්ලයන්ට්ගේ බ්‍රවුසර් එකට ඇටෑච්මන්ට් එකක් විදිහට යවනවා
        req = requests.get(file_url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
        response = Response(req.iter_content(chunk_size=1024*1024), content_type=req.headers.get('Content-Type'))
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        return f"Download Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
