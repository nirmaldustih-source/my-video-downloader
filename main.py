from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import yt_dlp
import requests
import urllib.parse

app = FastAPI()

# CORS දාපන් බ්‍රව්සර් එකේ එරර් නොඑන්න
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/download")
def download_video(url: str):
    # YouTube/TikTok ලෝඩ් වෙන්න ඕනේ නිසා මේ 'user_agent' එක අනිවාර්යයි
    ydl_opts = {
        'format': 'best', 
        'quiet': True, 
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'geo_bypass': True,
        'nocheckcertificate': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "success": True,
                "title": info.get('title', 'Video'),
                "thumbnail": info.get('thumbnail', 'https://placehold.co/600x338/png'),
                "video_url": info.get('url')
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/stream")
def stream_video(video_url: str, title: str = "video"):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        req = requests.get(video_url, headers=headers, stream=True)
        
        # ඕනෑම භාෂාවක නමක් වුණත් ගැටලුවක් නැති වෙන්න UTF-8 Encode කරනවා
        encoded_title = urllib.parse.quote(title)
        
        return StreamingResponse(
            req.iter_content(chunk_size=1024*1024), 
            media_type="video/mp4",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_title}.mp4"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
