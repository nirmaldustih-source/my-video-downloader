from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import yt_dlp
import requests
import urllib.parse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# හැම සයිට් එකක්ම රවට්ටන්න පට්ටම User-Agent එක
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

@app.get("/api/download")
def download_video(url: str):
    # YouTube, TikTok ඔක්කොටම මේ Configs ටික දාපන්
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'user_agent': HEADERS['User-Agent'],
        'geo_bypass': True,
        'nocheckcertificate': True,
        'http_headers': HEADERS
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            # direct video URL එක ගන්නවා
            video_url = info.get('url') or (info.get('formats', [{}])[0].get('url'))
            return {
                "success": True,
                "title": info.get('title', 'video'),
                "thumbnail": info.get('thumbnail', ''),
                "video_url": video_url
            }
    except Exception as e:
        # මෙතනින් තමයි ඇත්තම Error එක එන්නේ
        return {"success": False, "error": str(e)}

@app.get("/api/stream")
def stream_video(video_url: str, title: str = "video"):
    try:
        # Stream කරනකොටත් එම Headers පාවිච්චි කරනවා
        req = requests.get(video_url, headers=HEADERS, stream=True)
        
        if req.status_code != 200:
            raise HTTPException(status_code=req.status_code, detail="වීඩියෝ එක බාගන්න බැරි වුණා!")

        # සිංහල අකුරු ප්‍රශ්නේ විසඳන්න UTF-8 Encode කරනවා
        filename = urllib.parse.quote(title)
        
        return StreamingResponse(
            req.iter_content(chunk_size=1024*1024), 
            media_type="video/mp4",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{filename}.mp4"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
