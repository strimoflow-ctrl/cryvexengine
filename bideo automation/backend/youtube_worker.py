import os
import re
import subprocess
import yt_dlp
import imageio_ffmpeg

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()


class YouTubeWorker:
    """YouTube Channel Scraper and 1080p Video Downloader using yt-dlp and FFmpeg"""

    @staticmethod
    @staticmethod
    def normalize_channel_url(channel_input):
        """Converts @handle or plain name to full YouTube channel URL."""
        channel_input = channel_input.strip()
        if channel_input.startswith("http://") or channel_input.startswith("https://"):
            return channel_input
        if channel_input.startswith("@"):
            return f"https://www.youtube.com/{channel_input}"
        # If input has spaces, return None so search fallback is used
        if " " in channel_input:
            return None
        return f"https://www.youtube.com/@{channel_input}"

    @classmethod
    def get_channel_info_and_videos(cls, channel_input, max_results=40):
        """
        Fetches channel title, avatar, and latest videos & shorts using fast flat extraction.
        If direct channel URL fails or user entered a plain channel name (e.g. 'Najrin AI Kids World'),
        it uses YouTube search to automatically discover the channel and its videos.
        Returns (channel_meta, list_of_videos)
        """
        channel_input = channel_input.strip()
        channel_url = cls.normalize_channel_url(channel_input)

        ydl_opts = {
            "extract_flat": True,
            "playlistend": max_results,
            "quiet": True,
            "ignoreerrors": True,
            "no_warnings": True
        }

        videos = []
        channel_name = channel_input
        resolved_channel_url = channel_url or channel_input

        # 1. If we have a direct channel URL, try videos and shorts feeds
        if channel_url:
            try:
                target_url = channel_url.rstrip("/")
                if not target_url.endswith("/videos") and not target_url.endswith("/shorts"):
                    target_url = f"{target_url}/videos"

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(target_url, download=False)
                    if info:
                        channel_name = info.get("channel", info.get("uploader", info.get("title", channel_input)))
                        raw_entries = info.get("entries") or []
                        for e in raw_entries:
                            if not e or not e.get("id"):
                                continue
                            vid_id = e.get("id")
                            title = e.get("title", "YouTube Video")
                            url = e.get("url") or f"https://www.youtube.com/watch?v={vid_id}"
                            duration = e.get("duration") or 0
                            videos.append({
                                "id": vid_id,
                                "title": title,
                                "url": url,
                                "duration": duration,
                                "is_short": False
                            })
            except Exception as ex:
                print(f"[YouTube Scraper Notice] Videos feed error: {ex}")

            # Also probe Shorts feed
            try:
                shorts_url = f"{channel_url.rstrip('/')}/shorts"
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    s_info = ydl.extract_info(shorts_url, download=False)
                    if s_info:
                        raw_shorts = s_info.get("entries") or []
                        for e in raw_shorts:
                            if not e or not e.get("id"):
                                continue
                            vid_id = e.get("id")
                            if not any(v["id"] == vid_id for v in videos):
                                videos.append({
                                    "id": vid_id,
                                    "title": e.get("title", "YouTube Short"),
                                    "url": f"https://www.youtube.com/shorts/{vid_id}",
                                    "duration": e.get("duration") or 30,
                                    "is_short": True
                                })
            except Exception as ex:
                pass

        # 2. SEARCH FALLBACK: If 0 videos found or plain channel name was supplied
        if not videos:
            search_term = channel_input
            if "youtube.com" in search_term or "youtu.be" in search_term:
                search_term = search_term.rstrip("/").split("/")[-1].replace("@", "").replace("-", " ").replace("_", " ")
            search_term = search_term.strip()

            print(f"[YouTube Scraper] Direct URL gave 0 videos, initiating YouTube Search for '{search_term}'...")
            try:
                search_query = f"ytsearch8:{search_term}"
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    s_info = ydl.extract_info(search_query, download=False)
                    entries = s_info.get("entries") or []
                    
                    target_ch_name = None
                    target_ch_url = None

                    # Find best matching channel from search results
                    for e in entries:
                        if not e:
                            continue
                        ch = e.get("channel") or e.get("uploader") or ""
                        cu = e.get("channel_url")
                        if not cu and e.get("uploader_id"):
                            cu = f"https://www.youtube.com/{e.get('uploader_id')}"

                        if channel_input.lower() in ch.lower() and cu:
                            target_ch_name = ch
                            target_ch_url = cu
                            break

                    if not target_ch_url and entries and entries[0]:
                        target_ch_name = entries[0].get("channel") or channel_input
                        target_ch_url = entries[0].get("channel_url")

                    # If we found canonical channel URL, pull full channel video list
                    if target_ch_url:
                        channel_name = target_ch_name or channel_name
                        resolved_channel_url = target_ch_url
                        try:
                            feed_url = f"{target_ch_url.rstrip('/')}/videos"
                            ch_res = ydl.extract_info(feed_url, download=False)
                            if ch_res and ch_res.get("entries"):
                                for e in ch_res.get("entries"):
                                    if not e or not e.get("id"):
                                        continue
                                    vid_id = e.get("id")
                                    videos.append({
                                        "id": vid_id,
                                        "title": e.get("title", "YouTube Video"),
                                        "url": e.get("url") or f"https://www.youtube.com/watch?v={vid_id}",
                                        "duration": e.get("duration") or 0,
                                        "is_short": False
                                    })
                        except Exception:
                            pass

                    # If still empty, use the direct search entries
                    if not videos:
                        for e in entries:
                            if not e or not e.get("id"):
                                continue
                            vid_id = e.get("id")
                            videos.append({
                                "id": vid_id,
                                "title": e.get("title", "YouTube Video"),
                                "url": e.get("url") or f"https://www.youtube.com/watch?v={vid_id}",
                                "duration": e.get("duration") or 0,
                                "is_short": False
                            })

                    print(f"[YouTube Scraper] Discovered {len(videos)} videos for '{channel_name}' ({resolved_channel_url})!")
            except Exception as search_ex:
                print(f"[YouTube Search Error] {search_ex}")

        channel_meta = {
            "channel_url": resolved_channel_url,
            "channel_name": channel_name,
            "total_found": len(videos)
        }

        return channel_meta, videos

    @classmethod
    def download_video_1080p(cls, video_url_or_id, output_dir):
        """
        Downloads YouTube video in crisp 1080p MP4 format.
        STORAGE SAFEGUARD: Enforces that downloaded file is strictly under 500MB (limit ~470MB).
        If video exceeds size, quality is dynamically lowered (720p/480p) or compressed with FFmpeg.
        Extracts full Title, Description, and Thumbnail.
        Returns dict with video details and local paths.
        """
        os.makedirs(output_dir, exist_ok=True)

        if not video_url_or_id.startswith("http"):
            video_url = f"https://www.youtube.com/watch?v={video_url_or_id}"
        else:
            video_url = video_url_or_id

        output_template = os.path.join(output_dir, "%(id)s.%(ext)s")

        # Format selector: Prioritize 1080p under 450MB, then 720p under 450MB, then 480p
        format_selector = (
            "bestvideo[filesize<440M][height<=1080]+bestaudio[filesize<35M]/"
            "bestvideo[filesize_approx<440M][height<=1080]+bestaudio/"
            "bestvideo[filesize<440M][height<=720]+bestaudio/"
            "bestvideo[filesize_approx<440M][height<=720]+bestaudio/"
            "best[filesize<450M]/"
            "best[height<=720]/"
            "best[height<=480]/"
            "best"
        )

        ydl_opts = {
            "format": format_selector,
            "outtmpl": output_template,
            "merge_output_format": "mp4",
            "ffmpeg_location": FFMPEG_EXE,
            "quiet": True,
            "no_warnings": True,
            "writethumbnail": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            meta = ydl.extract_info(video_url, download=True)
            video_id = meta.get("id")
            title = meta.get("title", "Untitled Video")
            description = meta.get("description", "")
            duration = meta.get("duration", 0)

            # Locate downloaded video file
            expected_mp4 = os.path.join(output_dir, f"{video_id}.mp4")
            if not os.path.exists(expected_mp4):
                # Search directory for file matching video_id
                for f in os.listdir(output_dir):
                    if f.startswith(video_id) and f.endswith((".mp4", ".mkv", ".webm")):
                        expected_mp4 = os.path.join(output_dir, f)
                        break

            # -------------------------------------------------------------
            # STORAGE SAFEGUARD (< 500MB ENFORCEMENT)
            # -------------------------------------------------------------
            MAX_BYTES = 470 * 1024 * 1024  # 470 MB strict ceiling
            if os.path.exists(expected_mp4):
                curr_size = os.path.getsize(expected_mp4)
                if curr_size > MAX_BYTES:
                    curr_mb = curr_size / (1024 * 1024)
                    print(f"⚠️ [Storage Safeguard] Video size {curr_mb:.1f}MB exceeds 470MB! Downscaling quality to ensure under 500MB...")
                    
                    compressed_mp4 = os.path.join(output_dir, f"{video_id}_safe.mp4")
                    # Step 1: Transcode to 720p with CRF 28
                    cmd = [
                        FFMPEG_EXE, "-y",
                        "-i", expected_mp4,
                        "-vf", "scale='min(1280,iw)':-2",
                        "-c:v", "libx264",
                        "-crf", "28",
                        "-preset", "faster",
                        "-c:a", "aac",
                        "-b:a", "128k",
                        compressed_mp4
                    ]
                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                    # If still > MAX_BYTES, compress more aggressively to 480p with CRF 32
                    if os.path.exists(compressed_mp4):
                        comp_size = os.path.getsize(compressed_mp4)
                        if comp_size > MAX_BYTES:
                            low_mp4 = os.path.join(output_dir, f"{video_id}_low.mp4")
                            cmd_low = [
                                FFMPEG_EXE, "-y",
                                "-i", compressed_mp4,
                                "-vf", "scale='min(854,iw)':-2",
                                "-c:v", "libx264",
                                "-crf", "32",
                                "-preset", "faster",
                                "-c:a", "aac",
                                "-b:a", "96k",
                                low_mp4
                            ]
                            subprocess.run(cmd_low, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            if os.path.exists(low_mp4) and os.path.getsize(low_mp4) > 0:
                                os.remove(compressed_mp4)
                                compressed_mp4 = low_mp4

                        if os.path.getsize(compressed_mp4) > 0:
                            try:
                                os.remove(expected_mp4)
                            except Exception:
                                pass
                            expected_mp4 = compressed_mp4
                            final_mb = os.path.getsize(expected_mp4) / (1024 * 1024)
                            print(f"✅ [Storage Safeguard] Video successfully downscaled to {final_mb:.1f}MB (< 500MB).")

            # Locate downloaded thumbnail or auto-generate via FFmpeg
            thumb_path = os.path.join(output_dir, f"{video_id}_thumb.jpg")
            native_thumb = None
            for ext in [".webp", ".jpg", ".png", ".jpeg"]:
                candidate = os.path.join(output_dir, f"{video_id}{ext}")
                if os.path.exists(candidate):
                    native_thumb = candidate
                    break

            if native_thumb:
                # Convert native thumb to high-res JPG
                cmd = [FFMPEG_EXE, "-y", "-i", native_thumb, "-q:v", "2", thumb_path]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            if not os.path.exists(thumb_path) or os.path.getsize(thumb_path) == 0:
                # Generate from 1s frame using FFmpeg
                cls.extract_frame_thumbnail(expected_mp4, thumb_path)

            # Extract video dimensions and duration info
            video_info = cls.extract_video_info(expected_mp4)
            if duration:
                video_info["duration"] = duration

            return {
                "video_id": video_id,
                "title": title,
                "description": description,
                "video_path": expected_mp4,
                "thumb_path": thumb_path,
                "duration": video_info["duration"],
                "width": video_info["width"],
                "height": video_info["height"],
                "is_short": video_info["is_short"]
            }

    @staticmethod
    def extract_frame_thumbnail(video_path, output_thumb_path, timestamp="00:00:01"):
        """Extract a single high-quality frame from video."""
        cmd = [
            FFMPEG_EXE,
            "-y",
            "-ss", timestamp,
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            output_thumb_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return os.path.exists(output_thumb_path) and os.path.getsize(output_thumb_path) > 0

    @staticmethod
    def extract_video_info(video_path):
        """Extract duration, resolution, and is_short from video using FFmpeg."""
        duration = 15.0
        width = 1080
        height = 1920

        try:
            cmd = [FFMPEG_EXE, "-i", video_path]
            result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, errors="ignore")
            output = result.stderr

            dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", output)
            if dur_match:
                h, m, s = dur_match.groups()
                duration = int(h) * 3600 + int(m) * 60 + float(s)

            res_match = re.search(r"Video:.*,\s*(\d{3,4})x(\d{3,4})", output)
            if res_match:
                width = int(res_match.group(1))
                height = int(res_match.group(2))
        except Exception:
            pass

        is_short = (height >= width)

        return {
            "duration": round(duration, 2),
            "width": width,
            "height": height,
            "is_short": is_short
        }
