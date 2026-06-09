from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import yt_dlp
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/download")
def download_video(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="URL එකක් දාපන්")
    ydl_opts = {'format': 'best', 'quiet': True, 'no_warnings': True}
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
            'Accept': '*/*', 'Connection': 'keep-alive'
        }
        req = requests.get(video_url, headers=headers, stream=True)
        clean_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        return StreamingResponse(
            req.iter_content(chunk_size=1024*1024), 
            media_type="video/mp4",
            headers={"Content-Disposition": f"attachment; filename={clean_title}.mp4"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
