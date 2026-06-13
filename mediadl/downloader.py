"""yt-dlp wrapper for MediaDL - handles URL analysis and downloading."""

import asyncio
import re
import os
from dataclasses import dataclass, field
from typing import Callable

import yt_dlp

from mediadl.utils import (
    detect_platform,
    format_duration,
    format_size,
    get_default_download_dir,
    get_platform_icon,
    sanitize_filename,
)


@dataclass
class FormatInfo:
    """Represents a downloadable format option."""

    format_id: str
    quality: str
    extension: str
    filesize: str
    filesize_bytes: int
    codec: str
    note: str
    has_video: bool = True
    has_audio: bool = True


@dataclass
class MediaInfo:
    """Represents extracted media information."""

    url: str
    title: str
    platform: str
    platform_icon: str
    duration: str
    uploader: str
    description: str
    thumbnail: str
    formats: list[FormatInfo] = field(default_factory=list)
    webpage_url: str = ""
    is_live: bool = False


class Downloader:
    """Wrapper around yt-dlp for extracting info and downloading media."""

    def __init__(self, download_dir: str | None = None):
        """Initialize the downloader.

        Args:
            download_dir: Directory to save downloads. Defaults to ~/Downloads/MediaDL/.
        """
        self.download_dir = download_dir or get_default_download_dir()
        os.makedirs(self.download_dir, exist_ok=True)

    async def extract_info(self, url: str) -> MediaInfo:
        """Extract media information from a URL without downloading.

        Args:
            url: The media URL to analyze.

        Returns:
            MediaInfo object with video details and available formats.

        Raises:
            Exception: If URL cannot be analyzed.
        """
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "no_color": True,
        }

        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(None, self._extract_sync, url, ydl_opts)
        return self._parse_info(url, info)

    def _extract_sync(self, url: str, ydl_opts: dict) -> dict:
        """Synchronous extraction (runs in executor)."""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    def _parse_info(self, url: str, info: dict) -> MediaInfo:
        """Parse raw yt-dlp info dict into MediaInfo."""
        platform = detect_platform(url)
        platform_icon = get_platform_icon(platform)

        # Extract formats
        formats = self._parse_formats(info.get("formats", []))

        return MediaInfo(
            url=url,
            title=info.get("title", "Unknown Title"),
            platform=platform,
            platform_icon=platform_icon,
            duration=format_duration(info.get("duration")),
            uploader=info.get("uploader", info.get("channel", "Unknown")),
            description=(info.get("description", "") or "")[:200],
            thumbnail=info.get("thumbnail", ""),
            formats=formats,
            webpage_url=info.get("webpage_url", url),
            is_live=info.get("is_live", False),
        )

    def _parse_formats(self, raw_formats: list[dict]) -> list[FormatInfo]:
        """Parse and filter formats into a clean list.

        Groups formats intelligently:
        - Video+Audio combined formats (preferred)
        - Video-only formats
        - Audio-only formats
        """
        combined = []
        video_only = []
        audio_only = []

        for f in raw_formats:
            format_id = f.get("format_id", "")
            ext = f.get("ext", "?")
            vcodec = f.get("vcodec", "none")
            acodec = f.get("acodec", "none")
            has_video = vcodec not in ("none", None)
            has_audio = acodec not in ("none", None)

            # Skip storyboard/manifest formats
            if ext in ("mhtml", "json"):
                continue
            protocol = f.get("protocol", "")
            if protocol in ("mhtml", "m3u8", "m3u8_native") and not has_video:
                continue

            # Determine quality label
            height = f.get("height")
            width = f.get("width")
            tbr = f.get("tbr")  # total bitrate
            abr = f.get("abr")  # audio bitrate
            fps = f.get("fps")

            if has_video and height:
                quality = f"{height}p"
                if fps and fps > 30:
                    quality += f"{int(fps)}"
            elif has_video and width:
                quality = f"{width}w"
            elif has_audio and not has_video:
                if abr:
                    quality = f"Audio {int(abr)}kbps"
                else:
                    quality = "Audio"
            else:
                quality = f.get("format_note", format_id)

            # File size
            filesize_bytes = f.get("filesize") or f.get("filesize_approx") or 0

            # Codec info
            if has_video and has_audio:
                codec = f"{vcodec.split('.')[0]}+{acodec.split('.')[0]}"
            elif has_video:
                codec = vcodec.split(".")[0]
            elif has_audio:
                codec = acodec.split(".")[0]
            else:
                codec = "?"

            format_info = FormatInfo(
                format_id=format_id,
                quality=quality,
                extension=ext,
                filesize=format_size(filesize_bytes),
                filesize_bytes=filesize_bytes,
                codec=codec,
                note=f.get("format_note", ""),
                has_video=has_video,
                has_audio=has_audio,
            )

            if has_video and has_audio:
                combined.append(format_info)
            elif has_video:
                video_only.append(format_info)
            elif has_audio:
                audio_only.append(format_info)

        # Sort by quality (height descending for video, bitrate for audio)
        combined.sort(key=lambda x: self._quality_sort_key(x), reverse=True)
        video_only.sort(key=lambda x: self._quality_sort_key(x), reverse=True)
        audio_only.sort(key=lambda x: self._quality_sort_key(x), reverse=True)

        # Remove duplicates (same quality + ext)
        seen = set()
        deduped_combined = []
        deduped_video = []
        deduped_audio = []
        for f in combined:
            key = (f.quality, f.extension)
            if key not in seen:
                seen.add(key)
                deduped_combined.append(f)
        for f in video_only:
            key = (f.quality, f.extension)
            if key not in seen:
                seen.add(key)
                deduped_video.append(f)
        for f in audio_only:
            key = (f.quality, f.extension)
            if key not in seen:
                seen.add(key)
                deduped_audio.append(f)

        # Build final list with a "Best" auto option at the top
        result = []

        # Add "Best" auto-merge option
        if deduped_combined or deduped_video:
            best_quality = "Best"
            if deduped_video:
                best_quality = f"Best ({deduped_video[0].quality})"
            elif deduped_combined:
                best_quality = f"Best ({deduped_combined[0].quality})"

            result.append(FormatInfo(
                format_id="bestvideo+bestaudio/best",
                quality=best_quality,
                extension="mp4",
                filesize="Auto",
                filesize_bytes=0,
                codec="auto",
                note="Best video + best audio merged",
                has_video=True,
                has_audio=True,
            ))

        # Add "Best Audio" option if audio formats exist
        if deduped_audio:
            result.append(FormatInfo(
                format_id="bestaudio/best",
                quality=f"Best Audio ({deduped_audio[0].quality})",
                extension="m4a",
                filesize="Auto",
                filesize_bytes=0,
                codec="auto",
                note="Best audio only",
                has_video=False,
                has_audio=True,
            ))

        result.extend(deduped_combined)
        result.extend(deduped_video)
        result.extend(deduped_audio)

        return result

    @staticmethod
    def _quality_sort_key(fmt: FormatInfo) -> int:
        """Generate a sort key for format quality (higher = better)."""
        quality = fmt.quality
        # Extract numeric height from quality string like "1080p", "720p60"
        match = re.match(r"(\d+)p", quality)
        if match:
            return int(match.group(1))
        # Audio bitrate
        match = re.search(r"(\d+)kbps", quality)
        if match:
            return int(match.group(1))
        return 0

    def _resolve_format(self, format_id: str, formats: list[FormatInfo]) -> tuple[str, bool]:
        """Resolve format ID, auto-merging audio for video-only formats.

        Args:
            format_id: The requested format ID.
            formats: The list of available formats.

        Returns:
            Tuple of (resolved_format_string, is_audio_only).
        """
        # Already a merge expression (e.g. bestvideo+bestaudio/best)
        if "+" in format_id or "/" in format_id:
            is_audio_only = format_id.startswith("bestaudio") and "video" not in format_id
            return format_id, is_audio_only

        # Find the format in our list
        target = None
        for f in formats:
            if f.format_id == format_id:
                target = f
                break

        if target is None:
            return format_id, False

        # Audio-only: download as-is
        if not target.has_video:
            return format_id, True

        # Video+Audio combined: download as-is
        if target.has_video and target.has_audio:
            return format_id, False

        # Video-only: auto-merge with best audio
        return f"{format_id}+bestaudio", False

    async def download(
        self,
        url: str,
        format_id: str,
        formats: list[FormatInfo] | None = None,
        progress_callback: Callable | None = None,
        output_dir: str | None = None,
    ) -> str:
        """Download media with the specified format.

        If a video-only format is selected, automatically merges with
        the best available audio stream so the output always has sound.

        Args:
            url: The media URL.
            format_id: The yt-dlp format ID to download.
            formats: The list of available formats (used to detect video-only).
            progress_callback: Optional callback(dict) for progress updates.
                Dict keys: status, downloaded_bytes, total_bytes, speed, eta, filename
            output_dir: Override download directory.

        Returns:
            Path to the downloaded file.
        """
        save_dir = output_dir or self.download_dir
        os.makedirs(save_dir, exist_ok=True)

        # Auto-merge audio for video-only formats
        resolved_format, is_audio_only = self._resolve_format(
            format_id, formats or []
        )

        downloaded_file = None

        def progress_hook(d):
            nonlocal downloaded_file
            if d.get("status") == "finished":
                downloaded_file = d.get("filename", "")
            if progress_callback:
                progress_callback(d)

        ydl_opts = {
            "format": resolved_format,
            "outtmpl": os.path.join(save_dir, "%(title)s.%(ext)s"),
            "progress_hooks": [progress_hook],
            "quiet": True,
            "no_warnings": True,
            "no_color": True,
            # Windows-safe filenames
            "restrictfilenames": False,
            "windowsfilenames": True,
        }

        # Only merge to mp4 if downloading video; audio stays as m4a/webm
        if not is_audio_only:
            ydl_opts["merge_output_format"] = "mp4"
        else:
            # Extract audio to m4a for best compatibility
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "m4a",
            }]

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._download_sync, url, ydl_opts)

        return downloaded_file or save_dir

    def _download_sync(self, url: str, ydl_opts: dict):
        """Synchronous download (runs in executor)."""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    async def download_best(
        self,
        url: str,
        progress_callback: Callable | None = None,
        output_dir: str | None = None,
    ) -> str:
        """Download media in best available quality.

        Args:
            url: The media URL.
            progress_callback: Optional callback for progress updates.
            output_dir: Override download directory.

        Returns:
            Path to the downloaded file.
        """
        return await self.download(
            url=url,
            format_id="bestvideo+bestaudio/best",
            progress_callback=progress_callback,
            output_dir=output_dir,
        )
