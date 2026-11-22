import os
import re
import uuid
import asyncio
import tempfile
import shutil
import urllib.parse
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import yt_dlp

# --- Resolve ffmpeg path (Cross-platform: Windows & Linux Debian) ---
FFMPEG_DIR = None

# 1. First, check system PATH (standard on Linux / Debian via `apt install ffmpeg`)
_sys_ff = shutil.which("ffmpeg")
if _sys_ff:
    FFMPEG_DIR = str(Path(_sys_ff).parent)
    print(f"[RibbonSave] ✅ ffmpeg found in system PATH: {FFMPEG_DIR}")
else:
    # 2. Fallback to local / imageio_ffmpeg
    try:
        _backend_bin = Path(__file__).resolve().parent / "bin"
        _local_ffmpeg = _backend_bin / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
        if not _local_ffmpeg.exists():
            import imageio_ffmpeg
            _img_exe = imageio_ffmpeg.get_ffmpeg_exe()
            if _img_exe and Path(_img_exe).exists():
                _backend_bin.mkdir(parents=True, exist_ok=True)
                shutil.copy2(_img_exe, str(_local_ffmpeg))
        if _local_ffmpeg.exists():
            FFMPEG_DIR = str(_backend_bin)
    except Exception as e:
        print(f"[RibbonSave] ffmpeg note: {e}")

if FFMPEG_DIR:
    os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")
    print(f"[RibbonSave] ✅ ffmpeg configured at: {FFMPEG_DIR}")
else:
    print("[RibbonSave] ⚠️ WARNING: ffmpeg not found! Downloads may fail.")

# Add Deno and local bin to PATH
for _extra_bin in [Path.home() / ".deno" / "bin", Path.home() / ".local" / "bin", Path("/usr/local/bin")]:
    if _extra_bin.exists():
        os.environ["PATH"] = str(_extra_bin) + os.pathsep + os.environ.get("PATH", "")
        if (_extra_bin / "deno").exists():
            print(f"[RibbonSave] ✅ Deno JS runtime configured at: {_extra_bin}")

app = FastAPI(title="RibbonSave API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Length"],
)

TEMP_DIR = Path(tempfile.gettempdir()) / "ribbonsave_downloads"
TEMP_DIR.mkdir(exist_ok=True)

# Check multiple possible locations for cookies.txt
_possible_cookie_paths = [
    Path(__file__).resolve().parent / "cookies.txt",
    Path(__file__).resolve().parent / " cookies.txt",
    Path.cwd() / "cookies.txt",
    Path.cwd() / " cookies.txt",
    Path.cwd() / "backend" / "cookies.txt",
    Path.cwd() / "backend" / " cookies.txt",
    Path(__file__).resolve().parent.parent / "cookies.txt",
]
# Scan otomatis file apapun yang namanya mengandung 'cookie'
for _dir in [Path(__file__).resolve().parent, Path.cwd(), Path.cwd() / "backend"]:
    if _dir.exists() and _dir.is_dir():
        for _f in _dir.glob("*cookie*.txt"):
            if _f not in _possible_cookie_paths:
                _possible_cookie_paths.append(_f)

COOKIE_FILE = None
for _cp in _possible_cookie_paths:
    if _cp.exists() and _cp.is_file() and _cp.stat().st_size > 0:
        COOKIE_FILE = _cp
        break

if not COOKIE_FILE:
    COOKIE_FILE = Path(__file__).resolve().parent / "cookies.txt"

if COOKIE_FILE.exists():
    print(f"[RibbonSave] 🍪 Cookies DETECTED: {COOKIE_FILE} ({COOKIE_FILE.stat().st_size} bytes)")
else:
    print(f"[RibbonSave] ⚠️ No cookies.txt found. Checked paths: {[str(p) for p in _possible_cookie_paths]}")

SUPPORTED_PLATFORMS = {
    "youtube": r"(youtube\.com|youtu\.be)",
    "tiktok": r"tiktok\.com",
    "instagram": r"instagram\.com",
    "twitter": r"(twitter\.com|x\.com)",
    "facebook": r"(facebook\.com|fb\.watch)",
}


def detect_platform(url: str) -> str:
    for platform, pattern in SUPPORTED_PLATFORMS.items():
        if re.search(pattern, url, re.IGNORECASE):
            return platform
    return "unknown"


def _build_ydl_opts(extra_opts: dict, platform: str = "") -> dict:
    opts = {
        "quiet": False,
        "no_warnings": True,
        "noplaylist": True,
        "no_color": True,
        "no_cache_dir": True,
        "socket_timeout": 20,
        "retries": 5,
        "fragment_retries": 5,
        "concurrent_fragment_downloads": 1,
        "remote_components": ["ejs:github"],
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        },
    }
    
    # Gunakan cookies.txt jika ada
    if COOKIE_FILE and COOKIE_FILE.exists():
        opts["cookiefile"] = str(COOKIE_FILE)
        print(f"[RibbonSave] 🍪 Menggunakan cookiefile: {COOKIE_FILE} ({COOKIE_FILE.stat().st_size} bytes)")
    
    if FFMPEG_DIR:
        opts["ffmpeg_location"] = FFMPEG_DIR
        
    opts.update(extra_opts)
    return opts


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    return name[:200]


class UrlRequest(BaseModel):
    url: str


class DownloadRequest(BaseModel):
    url: str
    format_id: Optional[str] = None
    type: str = "video"  # "video" or "audio"


@app.post("/api/info")
async def get_info(req: UrlRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty 💔")

    platform = detect_platform(url)
    if platform == "unknown":
        raise HTTPException(
            status_code=400,
            detail="Oops! This platform isn't supported yet 🎀 We support YouTube, TikTok, Instagram, X/Twitter, and Facebook."
        )

    ydl_opts = _build_ydl_opts({"skip_download": True, "format": "all"}, platform=platform)

    try:
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, _extract_info, url, ydl_opts)
    except Exception as e:
        error_msg = str(e)
        print(f"[RibbonSave Error] /api/info: {error_msg}")
        
        # Fallback otomatis untuk YouTube tanpa cookies via pytubefix (ANDROID_VR)
        if platform == "youtube" and ("bot" in error_msg.lower() or "sign in" in error_msg.lower() or "format is not available" in error_msg.lower()):
            try:
                print("[RibbonSave] 🔄 Mengaktifkan fallback pytubefix (ANDROID_VR)...")
                info = await loop.run_in_executor(None, _extract_pytubefix, url)
                return info
            except Exception as pt_err:
                print(f"[RibbonSave Fallback Error]: {pt_err}")

        if "Private" in error_msg or "private" in error_msg:
            raise HTTPException(status_code=403, detail="This video is private 🔒 We can't access it.")
        if "unavailable" in error_msg.lower() or "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail="Video not found 😢 It may have been deleted.")
        raise HTTPException(status_code=500, detail=f"Couldn't fetch video info 💔 {error_msg[:200]}")

    # Process formats
    video_formats = []
    audio_formats = []
    seen_resolutions = set()

    raw_formats = info.get("formats", [])

    for f in raw_formats:
        ext = f.get("ext", "")
        vcodec = f.get("vcodec", "none")
        acodec = f.get("acodec", "none")
        height = f.get("height")
        filesize = f.get("filesize") or f.get("filesize_approx")
        format_id = f.get("format_id", "")
        tbr = f.get("tbr", 0) or 0

        has_video = vcodec != "none" and vcodec is not None
        has_audio = acodec != "none" and acodec is not None

        # Video formats
        if has_video and (height is None or height >= 240):
            h = height or 360
            label = f"{h}p" if height else "Default"
            if label not in seen_resolutions:
                seen_resolutions.add(label)
                video_formats.append({
                    "format_id": str(h),
                    "ext": "mp4",
                    "resolution": label,
                    "height": h,
                    "filesize": filesize,
                    "has_audio": has_audio,
                    "has_video": has_video,
                    "quality_label": f"{label} {'HD' if h >= 720 else 'SD'}" if height else "Standard",
                    "tbr": tbr,
                })

        # Audio-only formats
        if has_audio and not has_video:
            abr = f.get("abr", 0) or 0
            if abr >= 48:
                audio_formats.append({
                    "format_id": format_id,
                    "ext": ext,
                    "abr": abr,
                    "filesize": filesize,
                    "quality_label": f"{int(abr)}kbps",
                })

    # Sort video by height desc, audio by abr desc
    video_formats.sort(key=lambda x: x.get("height", 0), reverse=True)
    audio_formats.sort(key=lambda x: x.get("abr", 0), reverse=True)

    # Deduplicate video formats - keep highest tbr for each resolution
    deduped_video = {}
    for vf in video_formats:
        res = vf["resolution"]
        if res not in deduped_video or vf["tbr"] > deduped_video[res]["tbr"]:
            deduped_video[res] = vf
    video_formats = sorted(deduped_video.values(), key=lambda x: x.get("height", 0), reverse=True)

    # Always ensure at least 1 video format exists
    if not video_formats:
        video_formats = [{
            "format_id": "best",
            "ext": "mp4",
            "resolution": "720p",
            "height": 720,
            "filesize": None,
            "has_audio": True,
            "has_video": True,
            "quality_label": "720p HD",
            "tbr": 0,
        }]

    # Always ensure at least 1 audio format exists
    if not audio_formats:
        audio_formats = [{
            "format_id": "bestaudio",
            "ext": "mp3",
            "abr": 192,
            "filesize": None,
            "quality_label": "Standard MP3",
        }]

    duration = info.get("duration")
    duration_str = None
    if duration:
        mins, secs = divmod(int(duration), 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            duration_str = f"{hours}:{mins:02d}:{secs:02d}"
        else:
            duration_str = f"{mins}:{secs:02d}"

    return {
        "title": info.get("title", "Untitled"),
        "thumbnail": info.get("thumbnail"),
        "duration": duration,
        "duration_formatted": duration_str,
        "uploader": info.get("uploader") or info.get("channel") or info.get("creator") or "Unknown",
        "platform": platform,
        "view_count": info.get("view_count"),
        "like_count": info.get("like_count"),
        "video_formats": video_formats,
        "audio_formats": audio_formats,
    }


def _get_pytubefix_yt(url: str):
    """
    Inisialisasi pytubefix dengan client yang aman di server Linux/VPS.
    Menghindari client 'WEB' yang memicu canvas.getContext error di Node headless.
    """
    from pytubefix import YouTube as PTYouTube
    errors = []
    # ANDROID_VR tidak butuh PoToken/canvas dan sangat stabil di server VPS
    for client_name in ["ANDROID_VR", "ANDROID", "IOS"]:
        try:
            yt = PTYouTube(url, client=client_name)
            _ = yt.streams.first()
            print(f"[RibbonSave] ✅ pytubefix berhasil terhubung via client: {client_name}")
            return yt
        except Exception as e:
            errors.append(f"{client_name}: {e}")
            continue
    raise RuntimeError(f"Semua client pytubefix gagal: {'; '.join(errors)}")


def _extract_pytubefix(url: str) -> dict:
    yt = _get_pytubefix_yt(url)
    
    video_formats = []
    seen_res = set()
    
    for s in yt.streams.filter(type="video"):
        res = getattr(s, 'resolution', None) or f"{getattr(s, 'height', 720)}p"
        if res and res not in seen_res:
            seen_res.add(res)
            h = int(re.sub(r'\D', '', res)) if re.sub(r'\D', '', res) else 720
            video_formats.append({
                "format_id": str(s.itag),
                "ext": getattr(s, 'subtype', 'mp4'),
                "resolution": res,
                "height": h,
                "filesize": getattr(s, 'filesize', None),
                "has_audio": getattr(s, 'is_progressive', True),
                "has_video": True,
                "quality_label": f"{res} HD" if ("1080" in res or "720" in res) else res,
                "tbr": 0,
            })
            
    video_formats.sort(key=lambda x: x["height"], reverse=True)
    if not video_formats:
        video_formats = [{
            "format_id": "best",
            "ext": "mp4",
            "resolution": "720p",
            "height": 720,
            "filesize": None,
            "has_audio": True,
            "has_video": True,
            "quality_label": "720p HD",
            "tbr": 0,
        }]

    audio_formats = [{
        "format_id": "bestaudio",
        "ext": "mp3",
        "abr": 128,
        "filesize": None,
        "quality_label": "128kbps",
    }]

    duration = getattr(yt, 'length', None)
    mins, secs = divmod(int(duration or 0), 60)
    hours, mins = divmod(mins, 60)
    duration_str = f"{hours}:{mins:02d}:{secs:02d}" if hours > 0 else f"{mins}:{secs:02d}"

    return {
        "title": getattr(yt, 'title', "YouTube Video") or "YouTube Video",
        "thumbnail": getattr(yt, 'thumbnail_url', None),
        "duration": duration,
        "duration_formatted": duration_str,
        "uploader": getattr(yt, 'author', "YouTube Creator") or "Unknown",
        "platform": "youtube",
        "view_count": getattr(yt, 'views', None),
        "like_count": None,
        "video_formats": video_formats,
        "audio_formats": audio_formats,
    }


def _download_pytubefix(url: str, format_id: Optional[str], dl_type: str, output_dir: Path):
    yt = _get_pytubefix_yt(url)
    title = sanitize_filename(getattr(yt, 'title', 'video') or 'video')

    if dl_type == "audio":
        stream = yt.streams.get_audio_only()
        if not stream:
            stream = yt.streams.filter(only_audio=True).first()
        if not stream:
            stream = yt.streams.first()
        dl_file = stream.download(output_path=str(output_dir), filename=f"{title}.m4a")

        if FFMPEG_DIR:
            mp3_path = output_dir / f"{title}.mp3"
            ffmpeg_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
            ffmpeg_bin = Path(FFMPEG_DIR) / ffmpeg_name
            import subprocess
            cmd = [
                str(ffmpeg_bin), "-y", "-i", str(dl_file),
                "-vn", "-c:a", "libmp3lame", "-b:a", "192k", str(mp3_path)
            ]
            try:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                if mp3_path.exists():
                    try:
                        os.remove(dl_file)
                    except Exception:
                        pass
            except Exception as e:
                print(f"[RibbonSave] ffmpeg conversion note: {e}")
    else:
        stream = None
        if format_id and format_id not in ("best", "bestvideo"):
            try:
                stream = yt.streams.get_by_itag(int(format_id))
            except Exception:
                pass
        if not stream:
            stream = yt.streams.get_highest_resolution()
        if not stream:
            stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
        if not stream:
            stream = yt.streams.first()
        stream.download(output_path=str(output_dir), filename=f"{title}.mp4")


def _extract_info(url: str, ydl_opts: dict) -> dict:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


@app.post("/api/download")
async def download_media(req: DownloadRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty 💔")

    platform = detect_platform(url)
    download_id = str(uuid.uuid4())[:8]
    output_dir = TEMP_DIR / download_id
    output_dir.mkdir(exist_ok=True)

    try:
        if req.type == "audio":
            output_template = str(output_dir / "%(title)s.%(ext)s")
            format_spec = "ba/ba*/b/bestaudio/best"
            print(f"[RibbonSave] 📥 Download Audio: format={format_spec}")
            ydl_opts = _build_ydl_opts({
                "outtmpl": output_template,
                "format": format_spec,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }],
            }, platform=platform)
        else:
            output_template = str(output_dir / "%(title)s.%(ext)s")
            format_id = req.format_id

            # Selector fleksibel menggunakan bv* (menerima video murni maupun pre-muxed)
            height_match = re.search(r'(\d{3,4})', str(format_id or ''))
            if height_match:
                h = int(height_match.group(1))
                format_spec = f"bv*[height<={h}]+ba/b[height<={h}]/bv*+ba/b/best"
            elif format_id and format_id not in ("best", "bestvideo"):
                format_spec = f"{format_id}+ba/{format_id}/bv*+ba/b/best"
            else:
                format_spec = "bv*+ba/b/best"

            print(f"[RibbonSave] 📥 Download Video: format_id={format_id} -> format_spec={format_spec}")

            ydl_opts = _build_ydl_opts({
                "outtmpl": output_template,
                "format": format_spec,
                "merge_output_format": "mp4",
            }, platform=platform)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _download, url, ydl_opts)

        # Find the downloaded file
        downloaded_files = [
            f for f in output_dir.iterdir()
            if f.is_file() and not f.name.endswith(('.part', '.ytdl', '.temp', '.aria2'))
        ]
        downloaded_files.sort(key=lambda x: x.stat().st_size, reverse=True)

        if not downloaded_files or downloaded_files[0].stat().st_size == 0:
            raise HTTPException(status_code=500, detail="Download failed — no valid media file was produced 💔")

        file_path = downloaded_files[0]
        file_size = file_path.stat().st_size
        filename = file_path.name

        safe_filename = sanitize_filename(filename)
        ascii_filename = re.sub(r'[^\x20-\x7E]', '_', safe_filename)
        encoded_filename = urllib.parse.quote(safe_filename)
        media_type = "audio/mpeg" if req.type == "audio" else "video/mp4"

        async def file_streamer():
            try:
                with open(file_path, "rb") as f:
                    while chunk := f.read(1024 * 1024):  # 1MB chunks
                        yield chunk
            finally:
                try:
                    shutil.rmtree(output_dir, ignore_errors=True)
                except Exception:
                    pass

        return StreamingResponse(
            file_streamer(),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{encoded_filename}',
                "Content-Length": str(file_size),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Download failed 💔 {str(e)[:200]}")


def _download(url: str, ydl_opts: dict):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


@app.on_event("startup")
async def startup_cleanup():
    """Clean up any leftover temp files from previous runs."""
    print("[RibbonSave] 🎀 RibbonSave Backend v1.2 (Flexible Format Selector + Deno JS) READY!")
    if TEMP_DIR.exists():
        for item in TEMP_DIR.iterdir():
            if item.is_dir():
                try:
                    shutil.rmtree(item, ignore_errors=True)
                except Exception:
                    pass


@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "RibbonSave API is running 🎀"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
