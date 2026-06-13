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

# Browsers supported by yt-dlp for cookie extraction (yt-dlp internal names)
SUPPORTED_BROWSERS = [
    "chrome",
    "firefox",
    "edge",
    "coccoc",
    "brave",
    "opera",
    "vivaldi",
    "chromium",
    "safari",
    "whale",
]

# Human-readable display names for each yt-dlp browser identifier
BROWSER_DISPLAY_NAMES: dict[str, str] = {
    "chrome":   "Google Chrome",
    "firefox":  "Mozilla Firefox",
    "edge":     "Microsoft Edge",
    "coccoc":   "Cốc Cốc",
    "brave":    "Brave",
    "opera":    "Opera",
    "vivaldi":  "Vivaldi",
    "chromium": "Chromium",
    "safari":   "Safari",
    "whale":    "NAVER Whale",
}


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
    """Scan the current machine and return yt-dlp browser names that are installed.

    Detection strategy (in order):
    1. Executable on PATH
    2. Common Windows install paths under Program Files
    3. User-local AppData paths (for per-user installs)
    4. Chromium-based user profile directories

    Returns:
        Ordered list of yt-dlp browser name strings for browsers that were
        found (e.g. ['edge', 'coccoc', 'chrome']).
    """
    available: list[str] = []
    home = os.path.expanduser("~")

    # ── PATH executable names ────────────────────────────────────
    exe_map: dict[str, list[str]] = {
        "chrome":   ["google-chrome", "google-chrome-stable", "chrome"],
        "firefox":  ["firefox"],
        "edge":     ["msedge", "microsoft-edge", "microsoft-edge-stable"],
        "coccoc":   ["coccoc", "coc_coc_browser"],
        "brave":    ["brave-browser", "brave"],
        "opera":    ["opera"],
        "vivaldi":  ["vivaldi", "vivaldi-stable"],
        "chromium": ["chromium", "chromium-browser"],
        "safari":   ["safari"],
        "whale":    ["whale"],
    }

    # ── Windows install paths ────────────────────────────────────
    win_absolute: dict[str, list[str]] = {
        "chrome": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.join(home, r"AppData\Local\Google\Chrome\Application\chrome.exe"),
        ],
        "firefox": [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        ],
        "edge": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            os.path.join(home, r"AppData\Local\Microsoft\Edge\Application\msedge.exe"),
        ],
        "coccoc": [
            # System-wide install
            r"C:\Program Files\CocCoc\Browser\Application\browser.exe",
            r"C:\Program Files (x86)\CocCoc\Browser\Application\browser.exe",
            # Per-user install — Stable
            os.path.join(home, r"AppData\Local\CocCoc\Browser\Application\browser.exe"),
            # Per-user install — Beta
            os.path.join(home, r"AppData\Local\CocCoc\Browser Beta\Application\browser.exe"),
        ],
        "brave": [
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
            os.path.join(home, r"AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"),
        ],
        "opera": [
            r"C:\Program Files\Opera\launcher.exe",
            r"C:\Program Files (x86)\Opera\launcher.exe",
            os.path.join(home, r"AppData\Local\Programs\Opera\launcher.exe"),
        ],
        "vivaldi": [
            r"C:\Program Files\Vivaldi\Application\vivaldi.exe",
            r"C:\Program Files (x86)\Vivaldi\Application\vivaldi.exe",
            os.path.join(home, r"AppData\Local\Vivaldi\Application\vivaldi.exe"),
        ],
        "chromium": [
            r"C:\Program Files\Chromium\Application\chrome.exe",
            os.path.join(home, r"AppData\Local\Chromium\Application\chrome.exe"),
        ],
        "whale": [
            r"C:\Program Files\Naver\Naver Whale\whale.exe",
            os.path.join(home, r"AppData\Local\Naver\Naver Whale\whale.exe"),
        ],
    }

    # ── Cookie/profile profile dirs (fallback: browser is installed if
    #   its profile directory exists even if exe path is non-standard) ──
    win_profile_dirs: dict[str, list[str]] = {
        "chrome":   [os.path.join(home, r"AppData\Local\Google\Chrome\User Data")],
        "edge":     [os.path.join(home, r"AppData\Local\Microsoft\Edge\User Data")],
        "coccoc":   [
            os.path.join(home, r"AppData\Local\CocCoc\Browser\User Data"),
            os.path.join(home, r"AppData\Local\CocCoc\Browser Beta\User Data"),
            # Root dir fallback: any CocCoc install creates this dir
            os.path.join(home, r"AppData\Local\CocCoc"),
        ],
        "brave":    [os.path.join(home, r"AppData\Local\BraveSoftware\Brave-Browser\User Data")],
        "opera":    [
            os.path.join(home, r"AppData\Roaming\Opera Software\Opera Stable"),
            os.path.join(home, r"AppData\Local\Programs\Opera"),
        ],
        "vivaldi":  [os.path.join(home, r"AppData\Local\Vivaldi\User Data")],
        "chromium": [os.path.join(home, r"AppData\Local\Chromium\User Data")],
        "whale":    [os.path.join(home, r"AppData\Local\Naver\Naver Whale\User Data")],
        "firefox":  [os.path.join(home, r"AppData\Roaming\Mozilla\Firefox\Profiles")],
    }

    for browser in SUPPORTED_BROWSERS:
        found = False

        # 1. Check PATH
        for exe in exe_map.get(browser, [browser]):
            if shutil.which(exe):
                found = True
                break

        # 2. Check absolute Windows paths
        if not found and sys.platform == "win32":
            for path in win_absolute.get(browser, []):
                if os.path.exists(path):
                    found = True
                    break

        # 3. Check profile directories (browser is usable even if exe moved)
        if not found and sys.platform == "win32":
            for prof_dir in win_profile_dirs.get(browser, []):
                if os.path.isdir(prof_dir):
                    found = True
                    break

        if found:
            available.append(browser)

    return available


def get_coccoc_profile_path() -> str | None:
    """Get the path to Cốc Cốc User Data directory if it exists."""
    if sys.platform != "win32":
        return None
    home = os.path.expanduser("~")
    possible_paths = [
        os.path.join(home, r"AppData\Local\CocCoc\Browser\User Data"),
        os.path.join(home, r"AppData\Local\CocCoc\Browser Beta\User Data"),
    ]
    for path in possible_paths:
        if os.path.isdir(path):
            return path
    return None
