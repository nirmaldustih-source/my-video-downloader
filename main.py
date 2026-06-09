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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/download")
def download_video(url: str):
    # මේ තමයි පරණ වැඩ කරපු සරලම ඔප්ෂන්ස් ටික
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
        # මේක පරණම විදිහටම stream කරනවා
        req = requests.get(video_url, stream=True)
        return StreamingResponse(
            req.iter_content(chunk_size=1024*1024), 
            media_type="video/mp4",
            headers={"Content-Disposition": f'attachment; filename="video.mp4"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
