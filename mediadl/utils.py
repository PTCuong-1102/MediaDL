"""Utility functions for MediaDL."""

import re
import os
from urllib.parse import urlparse


# Platform detection patterns
PLATFORM_PATTERNS = {
    "YouTube": [
        r"(?:youtube\.com|youtu\.be)",
    ],
    "TikTok": [
        r"(?:tiktok\.com|vm\.tiktok\.com)",
    ],
    "Facebook": [
        r"(?:facebook\.com|fb\.watch|fb\.com)",
    ],
    "Instagram": [
        r"(?:instagram\.com|instagr\.am)",
    ],
    "Twitter/X": [
        r"(?:twitter\.com|x\.com)",
    ],
    "Reddit": [
        r"reddit\.com",
    ],
    "Vimeo": [
        r"vimeo\.com",
    ],
    "Dailymotion": [
        r"dailymotion\.com",
    ],
    "Twitch": [
        r"(?:twitch\.tv|clips\.twitch\.tv)",
    ],
    "SoundCloud": [
        r"soundcloud\.com",
    ],
    "Bilibili": [
        r"bilibili\.com",
    ],
    "Pinterest": [
        r"pinterest\.com",
    ],
}

# Platform icons (emoji)
PLATFORM_ICONS = {
    "YouTube": "🔴",
    "TikTok": "🎵",
    "Facebook": "🔵",
    "Instagram": "📸",
    "Twitter/X": "🐦",
    "Reddit": "🟠",
    "Vimeo": "🎬",
    "Dailymotion": "🎥",
    "Twitch": "💜",
    "SoundCloud": "🟧",
    "Bilibili": "📺",
    "Pinterest": "📌",
    "Other": "🌐",
}


def detect_platform(url: str) -> str:
    """Detect the platform from a URL.

    Args:
        url: The URL to analyze.

    Returns:
        Platform name string (e.g., 'YouTube', 'TikTok', or 'Other').
    """
    for platform, patterns in PLATFORM_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return platform
    return "Other"


def get_platform_icon(platform: str) -> str:
    """Get emoji icon for a platform."""
    return PLATFORM_ICONS.get(platform, "🌐")


def format_size(size_bytes: float | int | None) -> str:
    """Convert bytes to human-readable size string.

    Args:
        size_bytes: Size in bytes, or None.

    Returns:
        Formatted string like '120.5 MB' or 'N/A'.
    """
    if size_bytes is None or size_bytes <= 0:
        return "N/A"

    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    return f"{size:.1f} {units[unit_index]}"


def format_duration(seconds: float | int | None) -> str:
    """Convert seconds to human-readable duration string.

    Args:
        seconds: Duration in seconds, or None.

    Returns:
        Formatted string like '5:30' or '1:23:45' or 'N/A'.
    """
    if seconds is None or seconds <= 0:
        return "N/A"

    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def sanitize_filename(name: str) -> str:
    """Sanitize a string to be safe as a Windows filename.

    Args:
        name: The raw filename string.

    Returns:
        A cleaned filename string safe for Windows.
    """
    # Remove or replace characters invalid in Windows filenames
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, "_", name)

    # Remove control characters
    sanitized = re.sub(r"[\x00-\x1f\x7f]", "", sanitized)

    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip(" .")

    # Truncate to reasonable length (Windows max is 255)
    if len(sanitized) > 200:
        sanitized = sanitized[:200]

    # Fallback if empty
    if not sanitized:
        sanitized = "download"

    return sanitized


def get_default_download_dir() -> str:
    """Get the default download directory.

    Returns:
        Path to ~/Downloads/MediaDL/, created if it doesn't exist.
    """
    download_dir = os.path.join(os.path.expanduser("~"), "Downloads", "MediaDL")
    os.makedirs(download_dir, exist_ok=True)
    return download_dir


def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL.

    Args:
        url: The string to validate.

    Returns:
        True if the string appears to be a valid URL.
    """
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def format_speed(bytes_per_second: float | None) -> str:
    """Convert download speed to human-readable string.

    Args:
        bytes_per_second: Speed in bytes/second, or None.

    Returns:
        Formatted string like '2.5 MB/s'.
    """
    if bytes_per_second is None or bytes_per_second <= 0:
        return "N/A"
    return f"{format_size(bytes_per_second)}/s"


def format_eta(seconds: float | None) -> str:
    """Convert ETA seconds to human-readable string.

    Args:
        seconds: ETA in seconds, or None.

    Returns:
        Formatted string like '2m 30s' or 'N/A'.
    """
    if seconds is None or seconds <= 0:
        return "N/A"

    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}m {secs:02d}s"
    else:
        hours = seconds // 3600
        mins = (seconds % 3600) // 60
        return f"{hours}h {mins:02d}m"


def open_directory(path: str) -> None:
    """Open a directory in the default system file manager (cross-platform)."""
    import sys
    import subprocess
    if not os.path.exists(path):
        return

    if sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def is_ffmpeg_installed() -> bool:
    """Check if FFmpeg is installed and accessible on the system PATH."""
    import shutil
    return shutil.which("ffmpeg") is not None

