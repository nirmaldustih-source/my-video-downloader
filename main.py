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

def get_live_filesize(url: str):
    """Facebook CDN ලින්ක් එකෙන් ඇත්තම File Size එක ඇදලා ගන්නා සුපිරි ලොජික් එක"""
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        size_bytes = response.headers.get('Content-Length')
        if size_bytes:
            size_mb = round(int(size_bytes) / (1024 * 1024), 1)
            return f"{size_mb} MB"
    except Exception:
        pass
    return "Unknown Size"

@app.get("/api/download")
def download_video(url: str):
    ydl_opts = {'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            # MP3 කොටස සම්පූර්ණයෙන්ම අයින් කරලා තියෙන්නේ මචං
            data_contract = {
                "1080p": {"url": None, "size": "Not Available"},
                "720p": {"url": None, "size": "Not Available"},
                "480p": {"url": None, "size": "Not Available"}
            }
            
            hd_url, sd_url = None, None
            
            # HD සහ SD ලින්ක්ස් වෙන් කරගැනීම
            for f in formats:
                f_url = f.get('url')
                if not f_url:
                    continue
                if f.get('format_id') == 'hd':
                    hd_url = f_url
                elif f.get('format_id') == 'sd':
                    sd_url = f_url

            title = info.get('title', 'Facebook_Video')
            encoded_title = urllib.parse.quote(title)

            # බ්‍රව්සර් එකේ ප්ලේ නොවී කෙලින්ම බාගන්න අපේම සර්වර් එකේ ප්‍රොක්සි ලින්ක් එකක් හදනවා
            if hd_url:
                hd_size = get_live_filesize(hd_url)
                proxy_hd_link = f"/api/download-file?video_url={urllib.parse.quote(hd_url)}&title={encoded_title}"
                data_contract["1080p"] = {"url": proxy_hd_link, "size": hd_size}
                data_contract["720p"] = {"url": proxy_hd_link, "size": hd_size}
                
            if sd_url:
                sd_size = get_live_filesize(sd_url)
                proxy_sd_link = f"/api/download-file?video_url={urllib.parse.quote(sd_url)}&title={encoded_title}"
                data_contract["480p"] = {"url": proxy_sd_link, "size": sd_size}
            elif hd_url and not sd_url:
                data_contract["480p"] = data_contract["720p"]

            return {
                "success": True,
                "title": title,
                "thumbnail": info.get('thumbnail', 'https://placehold.co/600x338/png'),
                "formats": data_contract
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/download-file")
def download_file(video_url: str, title: str = "video"):
    """මෙන්න මචං වීඩියෝ එක බ්‍රව්සර් එකේ play නොවී ශනිකව download කරවන තැන"""
    try:
        req = requests.get(video_url, stream=True, timeout=30)
        if req.status_code != 200:
            raise HTTPException(status_code=400, detail="වීඩියෝව බාගත නොහැක")
        
        # attachment දාපු නිසා බ්‍රව්සර් එකෙන් කෙලින්ම ෆයිල් එකක් විදිහට බානවා
        return StreamingResponse(
            req.iter_content(chunk_size=1024*1024),
            media_type="video/mp4",
            headers={"Content-Disposition": f"attachment; filename=\"{title}.mp4\""}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download-thumbnail")
def download_thumbnail(image_url: str):
    try:
        req = requests.get(image_url, stream=True, timeout=15)
        if req.status_code != 200:
            raise HTTPException(status_code=400, detail="පින්තූරය ලබාගත නොහැක")
            
        return StreamingResponse(
            req.iter_content(chunk_size=1024),
            media_type="image/jpeg",
            headers={"Content-Disposition": "attachment; filename=\"fb_thumbnail.jpg\""}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
