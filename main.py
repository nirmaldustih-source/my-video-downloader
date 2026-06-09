from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import yt_dlp
import requests

app = FastAPI()

# Frontend එකට Data ගන්න CORS Middleware එක
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def format_size(bytes_size):
    """Bytes ගණන MB වලට හරවා ගන්නා පොඩි Function එකක්"""
    if bytes_size:
        return f"{round(bytes_size / (1024 * 1024), 1)} MB"
    return "Unknown Size"

@app.get("/api/download")
def download_video(url: str):
    ydl_opts = {'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            # UI එකේ ටැබ් 5ට අදාල දත්ත ව්‍යුහය
            data_contract = {
                "1080p": {"url": None, "size": "Not Available"},
                "720p": {"url": None, "size": "Not Available"},
                "480p": {"url": None, "size": "Not Available"},
                "mp3": {"url": None, "size": "Not Available"}
            }
            
            hd_url, sd_url = None, None
            hd_size, sd_size = "Unknown Size", "Unknown Size"
            
            # FB වල තියෙන HD සහ SD ලින්ක්ස් සහ Size වෙන් කර ගැනීම
            for f in formats:
                f_url = f.get('url')
                filesize = f.get('filesize') or f.get('filesize_approx')
                size_str = format_size(filesize)
                
                if f.get('format_id') == 'hd':
                    hd_url = f_url
                    hd_size = size_str
                elif f.get('format_id') == 'sd':
                    sd_url = f_url
                    sd_size = size_str

            # UI එකේ ටැබ් වලට ලින්ක්ස් සහ සයිස් ආදේශ කිරීම
            # FB වල සාමාන්‍යයෙන් HD කියන්නේ 720p හෝ 1080p වලටයි
            if hd_url:
                data_contract["1080p"] = {"url": hd_url, "size": hd_size}
                data_contract["720p"] = {"url": hd_url, "size": hd_size}
            if sd_url:
                data_contract["480p"] = {"url": sd_url, "size": sd_size}
            elif hd_url and not sd_url:
                data_contract["480p"] = {"url": hd_url, "size": hd_size}
                
            # MP3 ටැබ් එක සඳහා Audio/Video ලින්ක් එකක් සෙට් කිරීම
            if sd_url:
                data_contract["mp3"] = {"url": sd_url, "size": sd_size}
            elif hd_url:
                data_contract["mp3"] = {"url": hd_url, "size": hd_size}

            return {
                "success": True,
                "title": info.get('title', 'Facebook Video'),
                "thumbnail": info.get('thumbnail', 'https://placehold.co/600x338/png'),
                "formats": data_contract
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/download-thumbnail")
def download_thumbnail(image_url: str):
    """JPG බටන් එක එබුවම පින්තූරය වෙනම ටැබ් එකක පෙන්වන්නේ නැතුව කෙලින්ම ඩවුන්ලෝඩ් කරවන Endpoint එක"""
    try:
        req = requests.get(image_url, stream=True)
        if req.status_code != 200:
            raise HTTPException(status_code=400, detail="පින්තූරය ලබාගත නොහැක")
            
        return StreamingResponse(
            req.iter_content(chunk_size=1024),
            media_type="image/jpeg",
            headers={"Content-Disposition": "attachment; filename=fb_thumbnail.jpg"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
