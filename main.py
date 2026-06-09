from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import yt_dlp
import requests
import urllib.parse

app = FastAPI()

# CORS දාන්න ඕන බ්‍රව්සර් එකෙන් API එකට සම්බන්ධ වෙන්න
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# මේකෙන් තමයි වීඩියෝ එකේ තොරතුරු (Title, Thumbnail, URL) ගන්නේ
@app.get("/api/download")
def download_video(url: str):
    # TikTok/YT බ්ලොක් නොවෙන්න මේ User Agent එක පට්ට වැදගත්
    ydl_opts = {
        'format': 'best', 
        'quiet': True, 
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
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

# මේකෙන් තමයි වීඩියෝ එක කෙලින්ම සර්වර් එක හරහා Stream කරන්නේ
@app.get("/api/stream")
def stream_video(video_url: str, title: str = "video"):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        req = requests.get(video_url, headers=headers, stream=True)
        
        # අකුරු අවුල් යන්නේ නැති වෙන්න UTF-8 Encode කරනවා
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
