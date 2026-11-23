import os
import re
import uuid
import asyncio
import tempfile
import shutil
import urllib.request
import urllib.parse
import html
import zipfile
import concurrent.futures
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import yt_dlp
import yt_dlp.extractor.tiktok as tiktok_mod
import yt_dlp.extractor.instagram as instagram_mod
import yt_dlp.extractor.twitter as twitter_mod

# --- Patch Instagram: jangan lempar error jika postingan hanya berisi foto/gambar ---
_orig_ig_raise_no_formats = instagram_mod.InstagramIE.raise_no_formats
def _patched_ig_raise_no_formats(self, msg, *args, **kwargs):
    if "no video" in str(msg).lower():
        return
    return _orig_ig_raise_no_formats(self, msg, *args, **kwargs)
instagram_mod.InstagramIE.raise_no_formats = _patched_ig_raise_no_formats

# --- Patch TikTok: ekstrak seluruh gambar dari imagePost / slideshow foto ---
_orig_tt_parse_web = tiktok_mod.TikTokIE._parse_aweme_video_web
def _patched_tt_parse_web(self, aweme_detail, webpage_url, video_id, extract_flat=False):
    res = _orig_tt_parse_web(self, aweme_detail, webpage_url, video_id, extract_flat=extract_flat)
    imgs = []
    
    # Periksa berbagai struktur kemungkinan gambar pada TikTok (imagePost, images, image_post_info)
    raw_images = (
        aweme_detail.get('imagePost', {}).get('images', []) or
        aweme_detail.get('images', []) or
        aweme_detail.get('image_post_info', {}).get('images', [])
    )
    
    for idx, img in enumerate(raw_images):
        ul = (
            img.get('imageURL', {}).get('urlList', []) or
            img.get('display_image', {}).get('url_list', []) or
            img.get('url_list', []) or
            img.get('download_url_list', [])
        )
        thumb_ul = (
            img.get('thumbnail', {}).get('url_list', []) or
            img.get('thumbnail_url_list', []) or
            ul
        )
        
        if ul:
            w = img.get('imageWidth') or img.get('width')
            h = img.get('imageHeight') or img.get('height')
            imgs.append({
                'url': ul[0],
                'thumbnail_url': thumb_ul[0] if thumb_ul else ul[0],
                'width': w,
                'height': h,
                'idx': idx + 1,
            })
            
    if imgs:
        res['image_post_images'] = imgs
    return res
tiktok_mod.TikTokIE._parse_aweme_video_web = _patched_tt_parse_web

# --- Patch TikTokVMIE: normalisasi URL hasil redirect shortlink (/photo/ -> /video/) ---
_orig_tt_vm_extract = tiktok_mod.TikTokVMIE._real_extract
def _patched_tt_vm_extract(self, url):
    res = _orig_tt_vm_extract(self, url)
    if isinstance(res, dict) and res.get('url'):
        res['url'] = re.sub(r'(tiktok\.com/(?:@[^/]+/|video/|share/))photo/(\d+)', r'\g<1>video/\2', res['url'])
    return res
tiktok_mod.TikTokVMIE._real_extract = _patched_tt_vm_extract

# --- Patch Twitter: ekstrak foto tweet beresolusi tinggi ---
_orig_tw_extract = twitter_mod.TwitterIE._real_extract
def _patched_tw_extract(self, url):
    twid, selected_index = self._match_valid_url(url).group('id', 'index')
    images = []
    status = {}
    try:
        status = self._extract_status(twid)
        media_list = status.get('extended_entities', {}).get('media', []) or status.get('entities', {}).get('media', [])
        for idx, m in enumerate(media_list):
            m_url = m.get('media_url_https') or m.get('media_url')
            if m_url:
                orig_img_url = m_url.split('?')[0] + '?name=orig'
                thumb_img_url = m_url.split('?')[0] + '?name=small'
                w = m.get('original_info', {}).get('width') or m.get('sizes', {}).get('large', {}).get('w')
                h = m.get('original_info', {}).get('height') or m.get('sizes', {}).get('large', {}).get('h')
                images.append({
                    'url': orig_img_url,
                    'thumbnail_url': thumb_img_url,
                    'width': w,
                    'height': h,
                    'idx': idx + 1,
                })
    except Exception as e:
        print(f"[RibbonSave Twitter Patch Warning]: {e}")

    try:
        info = _orig_tw_extract(self, url)
    except Exception as e:
        err_str = str(e).lower()
        if ('no video' in err_str or 'format' in err_str) and images:
            user = status.get('user') or {}
            desc = status.get('full_text') or status.get('text') or ''
            uploader = user.get('name')
            info = {
                'id': twid,
                'title': f'{uploader} - {desc[:70]}' if uploader else desc[:70] or 'Tweet',
                'description': desc,
                'uploader': uploader,
                'uploader_id': user.get('screen_name'),
                'formats': [],
                'thumbnails': [{'url': im['url'], 'width': im['width'], 'height': im['height']} for im in images],
            }
        else:
            raise

    if images:
        info['twitter_images'] = images
    return info
twitter_mod.TwitterIE._real_extract = _patched_tw_extract

# --- Resolve ffmpeg path (Cross-platform: Windows & Linux Debian) ---
FFMPEG_DIR = None

_sys_ff = shutil.which("ffmpeg")
if _sys_ff:
    FFMPEG_DIR = str(Path(_sys_ff).parent)
    print(f"[RibbonSave] ✅ ffmpeg found in system PATH: {FFMPEG_DIR}")
else:
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

app = FastAPI(title="RibbonSave API", version="1.4.0")

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

SUPPORTED_PLATFORMS = {
    "tiktok": r"tiktok\.com",
    "instagram": r"instagram\.com",
    "twitter": r"(twitter\.com|x\.com)",
    "facebook": r"(facebook\.com|fb\.watch)",
}


def normalize_url(url: str) -> str:
    """Normalisasi format URL media sosial agar dikenali oleh yt-dlp."""
    url = url.strip()

    # Resolving shortlinks (vt.tiktok.com, vm.tiktok.com, tiktok.com/t/, fb.watch, dll)
    if re.search(r'(vt\.tiktok\.com|vm\.tiktok\.com|tiktok\.com/t/|fb\.watch|fb\.me|t\.co|bit\.ly)', url, re.I):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                resolved = resp.geturl()
                if resolved:
                    url = resolved
        except Exception as e:
            print(f"[RibbonSave] URL unshorten note: {e}")

    # Ubah format TikTok photo (/photo/ -> /video/) agar dikenali oleh TikTok extractor
    url = re.sub(r'(tiktok\.com/(?:@[^/]+/|video/|share/))photo/(\d+)', r'\g<1>video/\2', url)
    return url


def detect_platform(url: str) -> str:
    for platform, pattern in SUPPORTED_PLATFORMS.items():
        if re.search(pattern, url, re.IGNORECASE):
            return platform
    return "unknown"


def _build_ydl_opts(extra_opts: dict, platform: str = "") -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "no_color": True,
        "no_cache_dir": True,
        "socket_timeout": 20,
        "retries": 5,
        "fragment_retries": 5,
        "concurrent_fragment_downloads": 1,
        "ignore_no_formats_error": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        },
    }

    if FFMPEG_DIR:
        opts["ffmpeg_location"] = FFMPEG_DIR

    opts.update(extra_opts)
    return opts


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', '_', name).strip('_')
    return name[:150] or "media"


def _get_image_headers(img_url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com/",
    }
    if "fbsbx.com" in img_url or "facebook.com" in img_url or "fbcdn.net" in img_url:
        headers["User-Agent"] = "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"
        headers["Referer"] = "https://www.facebook.com/"
    elif "cdninstagram.com" in img_url or "instagram.com" in img_url:
        headers["Referer"] = "https://www.instagram.com/"
    elif "twimg.com" in img_url or "twitter.com" in img_url or "x.com" in img_url:
        headers["Referer"] = "https://twitter.com/"
    elif "tiktokcdn.com" in img_url or "byteoversea.com" in img_url or "tiktok.com" in img_url:
        headers["Referer"] = "https://www.tiktok.com/"
    return headers


def _download_image_file(img_url: str, output_dir: Path, base_title: str) -> tuple[Path, str]:
    headers = _get_image_headers(img_url)
    req = urllib.request.Request(img_url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        content_type = resp.headers.get("Content-Type", "").lower()
        ext = "jpg"
        if "png" in content_type or ".png" in img_url.lower():
            ext = "png"
        elif "webp" in content_type or ".webp" in img_url.lower():
            ext = "webp"
        elif "jpeg" in content_type or "jpg" in content_type:
            ext = "jpg"

        out_file = output_dir / f"{base_title}.{ext}"
        with open(out_file, "wb") as f_out:
            shutil.copyfileobj(resp, f_out)
        return out_file, content_type or f"image/{ext}"


def _download_single_image_to_dir(img_data: dict, output_dir: Path, base_title: str, idx: int) -> Optional[Path]:
    """Helper untuk download satu gambar ke dalam output_dir dengan penomoran rapi."""
    img_url = img_data.get("url")
    if not img_url:
        return None
    try:
        headers = _get_image_headers(img_url)
        req = urllib.request.Request(img_url, headers=headers)
        with urllib.request.urlopen(req, timeout=25) as resp:
            content_type = resp.headers.get("Content-Type", "").lower()
            ext = img_data.get("ext") or "jpg"
            if "png" in content_type or ".png" in img_url.lower():
                ext = "png"
            elif "webp" in content_type or ".webp" in img_url.lower():
                ext = "webp"
            elif "jpeg" in content_type or "jpg" in content_type:
                ext = "jpg"

            filename = f"{base_title}_{idx:02d}.{ext}"
            out_file = output_dir / filename
            with open(out_file, "wb") as f_out:
                shutil.copyfileobj(resp, f_out)
            return out_file
    except Exception as e:
        print(f"[RibbonSave ZIP Worker Error] Image #{idx}: {e}")
        return None


def _create_zip_from_images(images: list[dict], output_dir: Path, base_title: str) -> tuple[Path, int, str]:
    """Mengunduh kumpulan gambar secara paralel lalu membungkusnya ke file .ZIP."""
    downloaded_files: list[Path] = []

    # Download paralel menggunakan ThreadPoolExecutor untuk kecepatan maksimal
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(_download_single_image_to_dir, img, output_dir, base_title, i + 1): i
            for i, img in enumerate(images)
        }
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res and res.exists() and res.stat().st_size > 0:
                downloaded_files.append(res)

    if not downloaded_files:
        raise HTTPException(status_code=500, detail="Failed to download images for ZIP archive 💔")

    # Urutkan file berdasarkan nama agar rapi di dalam arsip
    downloaded_files.sort(key=lambda p: p.name)

    zip_filename = f"{base_title}_photos.zip"
    zip_path = output_dir / zip_filename

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in downloaded_files:
            zipf.write(file_path, arcname=file_path.name)

    return zip_path, zip_path.stat().st_size, zip_filename


def _extract_facebook_photo(url: str) -> dict:
    """Ekstraksi postingan & album multi-foto Facebook yang tidak memiliki video stream."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read().decode("utf-8", errors="ignore")
        
        # Unescape escaped characters dalam script / JSON
        content_unescaped = content.replace(r'\/', '/').replace(r'\u0026', '&')

        # 1. Cari og:image meta tags
        og_images = re.findall(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', content, re.I)
        if not og_images:
            og_images = re.findall(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', content, re.I)

        title_m = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', content, re.I)
        if not title_m:
            title_m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title["\']', content, re.I)
        title = html.unescape(title_m.group(1)) if title_m else "Facebook Post"

        # 2. Cari semua kandidat scontent photo URLs dari HTML & JSON
        patterns = [
            r'https://scontent[\w.-]*\.fbcdn\.net/[^\s"\'<>\\]+',
            r'https://[a-zA-Z0-9.-]*\.fbsbx\.com/[^\s"\'<>\\]+'
        ]
        
        raw_candidates = []
        for og_im in og_images:
            raw_candidates.append(html.unescape(og_im))
            
        for pat in patterns:
            for m in re.findall(pat, content_unescaped):
                raw_candidates.append(html.unescape(m))

        clean_images = []
        seen_keys = set()

        for cand in raw_candidates:
            cand_lower = cand.lower()
            # Filter elemen non-foto postingan
            if any(bad in cand_lower for bad in [
                '/rsrc.php/', 'p50x50', 's50x50', 'p100x100', '16x16', '32x32', 
                'emoji.php', 'avatar', 'static.xx', 'blank.gif'
            ]):
                continue

            # Deduplikasi berdasarkan photo ID / base name
            file_match = re.search(r'/(\d+_\d+_\d+_[a-z0-9]+|\d+_[a-z0-9]+)\.(jpg|png|webp|jpeg)', cand, re.I)
            key = file_match.group(1) if file_match else cand.split('?')[0]
            if key not in seen_keys:
                seen_keys.add(key)
                clean_images.append(cand)

        image_formats = []
        for idx, img_url in enumerate(clean_images):
            image_formats.append({
                "format_id": f"fb_photo_{idx + 1}",
                "url": img_url,
                "thumbnail_url": img_url,
                "resolution": "HD",
                "quality_label": f"Foto {idx + 1}" if len(clean_images) > 1 else "Foto / Gambar HD",
                "ext": "jpg",
                "idx": idx + 1,
            })

        return {
            "title": title,
            "thumbnail": clean_images[0] if clean_images else None,
            "duration": None,
            "duration_formatted": None,
            "uploader": "Facebook User",
            "platform": "facebook",
            "view_count": None,
            "like_count": None,
            "video_formats": [],
            "audio_formats": [],
            "images": image_formats,
        }


def _extract_instagram_fallback(url: str) -> Optional[dict]:
    """Fallback scraping Instagram carousel / photo jika API yt-dlp membutuhkan login."""
    shortcode_m = re.search(r'instagram\.com/(?:p|reel|tv)/([^/?#&]+)', url)
    if not shortcode_m:
        return None
    
    shortcode = shortcode_m.group(1)
    embed_url = f"https://www.instagram.com/p/{shortcode}/embed/captioned/"
    
    try:
        req = urllib.request.Request(
            embed_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            content_unescaped = content.replace(r'\/', '/').replace(r'\u0026', '&')

            # Temukan gambar embed
            img_urls = re.findall(r'<img[^>]+class="[^"]*EmbeddedMediaImage[^"]*"[^>]+src="([^"]+)"', content, re.I)
            if not img_urls:
                img_urls = re.findall(r'https://scontent[\w.-]*\.cdninstagram\.com/[^\s"\'<>\\]+', content_unescaped)

            clean_urls = []
            seen = set()
            for u in img_urls:
                u_clean = html.unescape(u)
                base = u_clean.split('?')[0]
                if base not in seen and not any(b in u_clean for b in ['150x150', 's150x150', 'avatar']):
                    seen.add(base)
                    clean_urls.append(u_clean)

            # Temukan author
            uploader_m = re.search(r'<a[^>]+class="[^"]*username[^"]*"[^>]*>([^<]+)</a>', content, re.I)
            uploader = uploader_m.group(1).strip() if uploader_m else "Instagram User"

            # Temukan caption
            caption_m = re.search(r'<div[^>]+class="Caption"[^>]*>([\s\S]*?)</div>', content, re.I)
            title = "Instagram Post"
            if caption_m:
                clean_caption = re.sub(r'<[^>]+>', '', caption_m.group(1)).strip()
                if clean_caption:
                    title = clean_caption[:70]

            if clean_urls:
                image_formats = []
                for idx, iu in enumerate(clean_urls):
                    image_formats.append({
                        "format_id": f"ig_fallback_{idx + 1}",
                        "url": iu,
                        "thumbnail_url": iu,
                        "resolution": "HD",
                        "quality_label": f"Foto {idx + 1}" if len(clean_urls) > 1 else "Foto / Gambar HD",
                        "ext": "jpg",
                        "idx": idx + 1,
                    })

                return {
                    "title": title,
                    "thumbnail": clean_urls[0],
                    "duration": None,
                    "duration_formatted": None,
                    "uploader": uploader,
                    "platform": "instagram",
                    "view_count": None,
                    "like_count": None,
                    "video_formats": [],
                    "audio_formats": [],
                    "images": image_formats,
                }
    except Exception as e:
        print(f"[RibbonSave IG Fallback Note]: {e}")

    return None


class UrlRequest(BaseModel):
    url: str


class DownloadRequest(BaseModel):
    url: str
    format_id: Optional[str] = None
    type: str = "video"  # "video", "audio", "image", or "zip"
    image_url: Optional[str] = None
    title: Optional[str] = None
    images: Optional[List[Dict[str, Any]]] = None


class DownloadZipRequest(BaseModel):
    url: str
    title: Optional[str] = None
    images: Optional[List[Dict[str, Any]]] = None


@app.post("/api/info")
async def get_info(req: UrlRequest):
    raw_url = req.url.strip()
    if not raw_url:
        raise HTTPException(status_code=400, detail="URL cannot be empty 💔")

    platform = detect_platform(raw_url)
    if platform == "unknown":
        raise HTTPException(
            status_code=400,
            detail="Oops! This platform isn't supported yet 🎀 We support TikTok, Instagram, X/Twitter, and Facebook."
        )

    url = normalize_url(raw_url)
    ydl_opts = _build_ydl_opts({"skip_download": True, "format": "all"}, platform=platform)

    info = None
    loop = asyncio.get_event_loop()

    try:
        info = await loop.run_in_executor(None, _extract_info, url, ydl_opts)
    except Exception as e:
        error_msg = str(e)
        print(f"[RibbonSave Error] /api/info ({platform}): {error_msg}")

        # Fallback untuk Facebook
        if platform == "facebook":
            try:
                fb_data = await loop.run_in_executor(None, _extract_facebook_photo, raw_url)
                if fb_data and fb_data.get("images"):
                    return fb_data
            except Exception as fb_err:
                print(f"[RibbonSave FB Fallback Error]: {fb_err}")

        # Fallback untuk Instagram
        if platform == "instagram":
            try:
                ig_data = await loop.run_in_executor(None, _extract_instagram_fallback, raw_url)
                if ig_data and ig_data.get("images"):
                    return ig_data
            except Exception as ig_err:
                print(f"[RibbonSave IG Fallback Error]: {ig_err}")

        if "Private" in error_msg or "private" in error_msg:
            raise HTTPException(status_code=403, detail="This media is private 🔒 We can't access it.")
        if "unavailable" in error_msg.lower() or "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail="Media not found 😢 It may have been deleted.")
        raise HTTPException(status_code=500, detail=f"Couldn't fetch media info 💔 {error_msg[:200]}")

    if not info:
        if platform == "facebook":
            try:
                fb_data = await loop.run_in_executor(None, _extract_facebook_photo, raw_url)
                if fb_data and fb_data.get("images"):
                    return fb_data
            except Exception:
                pass
        if platform == "instagram":
            try:
                ig_data = await loop.run_in_executor(None, _extract_instagram_fallback, raw_url)
                if ig_data and ig_data.get("images"):
                    return ig_data
            except Exception:
                pass
        raise HTTPException(status_code=404, detail="Media not found or content inaccessible 💔")

    # Process formats
    video_formats = []
    audio_formats = []
    seen_resolutions = set()

    # Kumpulkan raw_formats baik dari info langsung maupun dari playlist entries jika ada video
    raw_formats = info.get("formats", []) or []
    entries_list = list(info.get("entries") or []) if info.get("entries") else []
    if not raw_formats and entries_list:
        for entry in entries_list:
            if isinstance(entry, dict) and entry.get("formats"):
                raw_formats.extend(entry["formats"])

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

        # Video formats (hanya jika ada video stream sungguhan)
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
            audio_formats.append({
                "format_id": format_id,
                "ext": ext,
                "abr": abr or 128,
                "filesize": filesize,
                "quality_label": f"{int(abr)}kbps" if abr else "Audio MP3",
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

    # Jika ada video tapi belum ada format audio terpisah (misalnya video pre-muxed mp4):
    if video_formats and not audio_formats:
        audio_formats = [{
            "format_id": "bestaudio",
            "ext": "mp3",
            "abr": 192,
            "filesize": None,
            "quality_label": "Standard MP3",
        }]

    # === EKSTRAKSI MULTI-FOTO UNIVERSAL (TikTok, Instagram, Twitter/X, Facebook) ===
    image_formats = []
    seen_img_urls = set()

    # 1. Multi-image TikTok Slideshow (dari patch imagePost)
    if info.get("image_post_images"):
        for im in info["image_post_images"]:
            u = im.get("url")
            if u and u not in seen_img_urls:
                seen_img_urls.add(u)
                w = im.get("width")
                h = im.get("height")
                res = f"{w}x{h}" if w and h else "HD"
                idx = im.get("idx", len(image_formats) + 1)
                image_formats.append({
                    "format_id": f"slide_{idx}",
                    "url": u,
                    "thumbnail_url": im.get("thumbnail_url") or u,
                    "resolution": res,
                    "quality_label": f"Foto {idx}",
                    "ext": "jpg",
                    "idx": idx,
                })

    # 2. Twitter / X Images
    if info.get("twitter_images") and not image_formats:
        for im in info["twitter_images"]:
            u = im.get("url")
            if u and u not in seen_img_urls:
                seen_img_urls.add(u)
                w = im.get("width")
                h = im.get("height")
                res = f"{w}x{h}" if w and h else "HD"
                idx = im.get("idx", len(image_formats) + 1)
                image_formats.append({
                    "format_id": f"tw_photo_{idx}",
                    "url": u,
                    "thumbnail_url": im.get("thumbnail_url") or u,
                    "resolution": res,
                    "quality_label": f"Foto {idx}" if len(info["twitter_images"]) > 1 else "Foto / Gambar HD",
                    "ext": "jpg",
                    "idx": idx,
                })

    # 3. Multi-image / Carousel entries (Instagram carousel)
    if entries_list and not image_formats:
        for idx, entry in enumerate(entries_list):
            if not isinstance(entry, dict):
                continue
            entry_thumbs = entry.get("thumbnails") or []
            best_thumb_url = None
            preview_thumb_url = None
            best_res = "HD"
            if entry_thumbs:
                sorted_et = sorted(entry_thumbs, key=lambda t: (t.get("width") or 0) * (t.get("height") or 0), reverse=True)
                best_thumb_url = sorted_et[0].get("url")
                bw = sorted_et[0].get("width")
                bh = sorted_et[0].get("height")
                if bw and bh:
                    best_res = f"{bw}x{bh}"
                # Cari thumbnail preview ukuran sedang (~300px) jika ada
                for t in sorted_et:
                    tw = t.get("width") or 0
                    if 200 <= tw <= 600:
                        preview_thumb_url = t.get("url")
                        break
            if not best_thumb_url:
                best_thumb_url = entry.get("thumbnail") or entry.get("url")

            if best_thumb_url and best_thumb_url not in seen_img_urls:
                seen_img_urls.add(best_thumb_url)
                image_formats.append({
                    "format_id": f"carousel_{idx + 1}",
                    "url": best_thumb_url,
                    "thumbnail_url": preview_thumb_url or best_thumb_url,
                    "resolution": best_res,
                    "quality_label": f"Foto {idx + 1}",
                    "ext": "jpg",
                    "idx": idx + 1,
                })

    # 4. Facebook Album / Multi-Photo Post check
    if platform == "facebook" and (not video_formats or len(image_formats) <= 1):
        try:
            fb_data = await loop.run_in_executor(None, _extract_facebook_photo, raw_url)
            if fb_data and fb_data.get("images") and len(fb_data["images"]) > len(image_formats):
                image_formats = fb_data["images"]
        except Exception as fb_err:
            print(f"[RibbonSave FB Enhanced Extract Note]: {fb_err}")

    # 5. Extract thumbnails from root info
    thumbnails = info.get("thumbnails", [])
    if thumbnails and not image_formats:
        def _thumb_score(t):
            w = t.get("width") or 0
            h = t.get("height") or 0
            pref = t.get("preference") or 0
            return (w * h, pref)

        sorted_thumbs = sorted(thumbnails, key=_thumb_score, reverse=True)
        for t in sorted_thumbs:
            t_url = t.get("url")
            if t_url and t_url not in seen_img_urls:
                seen_img_urls.add(t_url)
                w = t.get("width")
                h = t.get("height")
                res = f"{w}x{h}" if w and h else "HD"
                image_formats.append({
                    "format_id": "thumb_best",
                    "url": t_url,
                    "thumbnail_url": t_url,
                    "resolution": res,
                    "quality_label": "Foto / Gambar HD" if not video_formats else "Thumbnail / Cover HD",
                    "ext": "jpg",
                    "idx": 1,
                })
                break

    # 6. Fallback to main thumbnail
    main_thumb = info.get("thumbnail")
    if main_thumb and main_thumb not in seen_img_urls and not image_formats:
        image_formats.append({
            "format_id": "thumb_main",
            "url": main_thumb,
            "thumbnail_url": main_thumb,
            "resolution": "Original",
            "quality_label": "Foto / Gambar" if not video_formats else "Thumbnail / Cover Image",
            "ext": "jpg",
            "idx": 1,
        })

    duration = info.get("duration")
    duration_str = None
    if duration:
        mins, secs = divmod(int(duration), 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            duration_str = f"{hours}:{mins:02d}:{secs:02d}"
        else:
            duration_str = f"{mins}:{secs:02d}"

    # Tentukan preview thumbnail utama
    preview_thumb = info.get("thumbnail")
    if not preview_thumb and image_formats:
        preview_thumb = image_formats[0].get("thumbnail_url") or image_formats[0].get("url")

    return {
        "title": info.get("title", "Untitled"),
        "thumbnail": preview_thumb,
        "duration": duration,
        "duration_formatted": duration_str,
        "uploader": info.get("uploader") or info.get("channel") or info.get("creator") or "Unknown",
        "platform": platform,
        "view_count": info.get("view_count"),
        "like_count": info.get("like_count"),
        "video_formats": video_formats,
        "audio_formats": audio_formats,
        "images": image_formats,
    }


def _extract_info(url: str, ydl_opts: dict) -> dict:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)


async def _handle_zip_download(url: str, title: Optional[str], images: Optional[list], loop):
    """Fungsi pembantu terpusat untuk download semua gambar dan mengemasnya dalam file .ZIP."""
    platform = detect_platform(url)
    download_id = f"zip_{str(uuid.uuid4())[:8]}"
    output_dir = TEMP_DIR / download_id
    output_dir.mkdir(exist_ok=True)

    try:
        base_title = sanitize_filename(title or "ribbonsave_photos")
        target_images = images or []

        # Jika data gambar tidak dikirimkan langsung dari frontend, ekstrak melalui backend
        if not target_images:
            normalized_url = normalize_url(url)
            ydl_opts = _build_ydl_opts({"skip_download": True}, platform=platform)
            try:
                info = await loop.run_in_executor(None, _extract_info, normalized_url, ydl_opts)
                if info.get("image_post_images"):
                    target_images = info["image_post_images"]
                elif info.get("twitter_images"):
                    target_images = info["twitter_images"]
                elif info.get("entries"):
                    for entry in info["entries"]:
                        thumbs = entry.get("thumbnails") or []
                        if thumbs:
                            best_t = sorted(thumbs, key=lambda t: (t.get("width") or 0) * (t.get("height") or 0), reverse=True)[0]
                            target_images.append({"url": best_t["url"], "ext": "jpg"})
                        elif entry.get("thumbnail"):
                            target_images.append({"url": entry["thumbnail"], "ext": "jpg"})
                elif info.get("thumbnails"):
                    target_images = [{"url": info["thumbnails"][-1]["url"], "ext": "jpg"}]
                elif info.get("thumbnail"):
                    target_images = [{"url": info["thumbnail"], "ext": "jpg"}]
            except Exception:
                if platform == "facebook":
                    fb_data = await loop.run_in_executor(None, _extract_facebook_photo, url)
                    if fb_data and fb_data.get("images"):
                        target_images = fb_data["images"]

        if not target_images:
            raise HTTPException(status_code=404, detail="No downloadable images found for ZIP packaging 💔")

        zip_path, zip_size, zip_filename = await loop.run_in_executor(
            None, _create_zip_from_images, target_images, output_dir, base_title
        )

        safe_filename = sanitize_filename(zip_filename)
        ascii_filename = re.sub(r'[^\x20-\x7E]', '_', safe_filename)
        encoded_filename = urllib.parse.quote(safe_filename)

        async def zip_file_streamer():
            try:
                with open(zip_path, "rb") as f:
                    while chunk := f.read(1024 * 1024):  # 1MB chunks
                        yield chunk
            finally:
                try:
                    shutil.rmtree(output_dir, ignore_errors=True)
                except Exception:
                    pass

        return StreamingResponse(
            zip_file_streamer(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{encoded_filename}',
                "Content-Length": str(zip_size),
            },
        )
    except HTTPException:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise
    except Exception as e:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate ZIP 💔 {str(e)[:200]}")


@app.post("/api/download-zip")
async def download_all_zip(req: DownloadZipRequest):
    """Endpoint Universal untuk mendownload seluruh slide / album foto dalam format .ZIP."""
    raw_url = req.url.strip()
    if not raw_url:
        raise HTTPException(status_code=400, detail="URL cannot be empty 💔")
    loop = asyncio.get_event_loop()
    return await _handle_zip_download(raw_url, req.title, req.images, loop)


@app.post("/api/download")
async def download_media(req: DownloadRequest):
    raw_url = req.url.strip()
    if not raw_url:
        raise HTTPException(status_code=400, detail="URL cannot be empty 💔")

    platform = detect_platform(raw_url)
    url = normalize_url(raw_url)

    loop = asyncio.get_event_loop()

    # Dukungan khusus jika type="zip" dipanggil melalui endpoint /api/download
    if req.type == "zip":
        return await _handle_zip_download(raw_url, req.title, req.images, loop)

    download_id = str(uuid.uuid4())[:8]
    output_dir = TEMP_DIR / download_id
    output_dir.mkdir(exist_ok=True)

    try:
        if req.type == "image":
            target_img_url = req.image_url
            base_title = sanitize_filename(req.title or "photo")

            if not target_img_url:
                ydl_opts = _build_ydl_opts({"skip_download": True}, platform=platform)
                try:
                    info = await loop.run_in_executor(None, _extract_info, url, ydl_opts)
                    if not req.title:
                        base_title = sanitize_filename(info.get("title", "image"))
                    target_img_url = info.get("thumbnail")
                    if not target_img_url and info.get("thumbnails"):
                        target_img_url = info["thumbnails"][-1].get("url")
                except Exception:
                    if platform == "facebook":
                        fb_data = await loop.run_in_executor(None, _extract_facebook_photo, raw_url)
                        if fb_data and fb_data.get("images"):
                            target_img_url = fb_data["images"][0]["url"]
                            if not req.title:
                                base_title = sanitize_filename(fb_data.get("title", "image"))

            if not target_img_url:
                raise HTTPException(status_code=404, detail="No downloadable image found 💔")

            file_path, media_type = await loop.run_in_executor(
                None, _download_image_file, target_img_url, output_dir, base_title
            )
            file_size = file_path.stat().st_size
            filename = file_path.name

        elif req.type == "audio":
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

            await loop.run_in_executor(None, _download, url, ydl_opts)

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
            media_type = "audio/mpeg"

        else:
            output_template = str(output_dir / "%(title)s.%(ext)s")
            format_id = req.format_id

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

            await loop.run_in_executor(None, _download, url, ydl_opts)

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
            media_type = "video/mp4"

        safe_filename = sanitize_filename(filename)
        ascii_filename = re.sub(r'[^\x20-\x7E]', '_', safe_filename)
        encoded_filename = urllib.parse.quote(safe_filename)

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
    print("[RibbonSave] 🎀 RibbonSave Backend v1.4 (Multi-Photo, Video & Audio Downloader with ZIP) READY!")
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
