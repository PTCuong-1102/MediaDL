"""Utility functions for MediaDL."""

import re
import os
import shutil
import sys
from urllib.parse import urlparse


# Latest Chrome User-Agent for bypassing bot detection
CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

# Browsers supported for cookie extraction
SUPPORTED_BROWSERS = ["chrome", "firefox", "edge", "opera", "safari", "brave", "chromium"]


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
    return shutil.which("ffmpeg") is not None


def get_platform_headers(url: str) -> dict:
    """Return HTTP headers tailored to bypass bot-detection for a given URL.

    Sets a modern Chrome User-Agent and a platform-specific Referer so yt-dlp
    appears as a legitimate browser request rather than a bot.

    Args:
        url: The media URL to analyse.

    Returns:
        Dict of HTTP headers to pass to yt-dlp's ``http_headers`` option.
    """
    platform = detect_platform(url)

    # Per-platform Referer values
    referer_map = {
        "TikTok": "https://www.tiktok.com/",
        "Instagram": "https://www.instagram.com/",
        "Facebook": "https://www.facebook.com/",
        "Twitter/X": "https://x.com/",
        "Reddit": "https://www.reddit.com/",
        "YouTube": "https://www.youtube.com/",
        "Twitch": "https://www.twitch.tv/",
        "Bilibili": "https://www.bilibili.com/",
        "SoundCloud": "https://soundcloud.com/",
        "Vimeo": "https://vimeo.com/",
        "Dailymotion": "https://www.dailymotion.com/",
        "Pinterest": "https://www.pinterest.com/",
    }

    headers = {
        "User-Agent": CHROME_UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }

    if platform in referer_map:
        headers["Referer"] = referer_map[platform]

    return headers


def get_available_browsers() -> list[str]:
    """Return list of browsers whose cookies can be extracted on the current OS.

    Checks which browsers are actually installed by looking for their executables
    or profile directories.

    Returns:
        List of browser name strings (e.g. ['chrome', 'firefox', 'edge']).
    """
    available: list[str] = []

    # Executable names per browser (checked on PATH)
    exe_map = {
        "chrome": ["google-chrome", "chrome", "google-chrome-stable"],
        "firefox": ["firefox"],
        "edge": ["msedge", "microsoft-edge"],
        "opera": ["opera"],
        "brave": ["brave-browser", "brave"],
        "chromium": ["chromium", "chromium-browser"],
    }

    # On Windows, also check common install paths
    win_paths = {
        "chrome": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ],
        "firefox": [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        ],
        "edge": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ],
        "brave": [
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        ],
    }

    for browser in SUPPORTED_BROWSERS:
        found = False
        # Check PATH executables
        for exe in exe_map.get(browser, [browser]):
            if shutil.which(exe):
                found = True
                break
        # Check Windows install paths
        if not found and sys.platform == "win32":
            for path in win_paths.get(browser, []):
                if os.path.exists(path):
                    found = True
                    break
        if found:
            available.append(browser)

    return available
