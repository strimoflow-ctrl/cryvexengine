import os
import re
import subprocess
import yt_dlp
import imageio_ffmpeg

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()


class YouTubeWorker:
    """YouTube Channel Scraper and 1080p Video Downloader using yt-dlp and FFmpeg"""

    @staticmethod
    def normalize_channel_url(channel_input):
        """Converts @handle or plain name to full YouTube channel URL."""
        channel_input = channel_input.strip()
        if channel_input.startswith("http://") or channel_input.startswith("https://"):
            return channel_input
        if channel_input.startswith("@"):
            return f"https://www.youtube.com/{channel_input}"
        return f"https://www.youtube.com/@{channel_input}"

    @classmethod
    def get_channel_info_and_videos(cls, channel_input, max_results=40):
        """
        Fetches channel title, avatar, and latest videos & shorts using fast flat extraction.
        Returns (channel_meta, list_of_videos)
        """
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

        # Try videos feed
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

        # Also probe Shorts feed for variety
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

        channel_meta = {
            "channel_url": channel_url,
            "channel_name": channel_name,
            "total_found": len(videos)
        }

        return channel_meta, videos

    @classmethod
    def download_video_1080p(cls, video_url_or_id, output_dir):
        """
        Downloads YouTube video in crisp 1080p MP4 format.
        Extracts full Title, Description, and Thumbnail.
        Returns dict with video details and local paths.
        """
        os.makedirs(output_dir, exist_ok=True)

        if not video_url_or_id.startswith("http"):
            video_url = f"https://www.youtube.com/watch?v={video_url_or_id}"
        else:
            video_url = video_url_or_id

        output_template = os.path.join(output_dir, "%(id)s.%(ext)s")

        ydl_opts = {
            # Highest quality up to 1080p MP4
            "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
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
