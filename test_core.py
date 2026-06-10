"""Quick test script for MediaDL core modules."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from mediadl.utils import (
    format_size, format_duration, detect_platform, get_platform_icon,
    is_valid_url, sanitize_filename, format_speed, format_eta,
    get_default_download_dir,
)

print("=" * 55)
print("  MediaDL - Core Module Tests")
print("=" * 55)

# Test format_size
print("\n--- Test format_size ---")
tests = [
    (0, "N/A"), (512, "512 B"), (1024, "1.0 KB"),
    (1536000, "1.5 MB"), (1073741824, "1.0 GB"), (None, "N/A"),
]
for val, expected in tests:
    result = format_size(val)
    status = "OK" if result == expected else f"FAIL (got {result})"
    print(f"  {str(val):>14s} -> {result:>10s}  [{status}]")

# Test format_duration
print("\n--- Test format_duration ---")
tests = [(30, "0:30"), (90, "1:30"), (3661, "1:01:01"), (None, "N/A")]
for val, expected in tests:
    result = format_duration(val)
    status = "OK" if result == expected else f"FAIL (got {result})"
    print(f"  {str(val):>6s} -> {result:>10s}  [{status}]")

# Test detect_platform
print("\n--- Test detect_platform ---")
urls = {
    "https://www.youtube.com/watch?v=abc": "YouTube",
    "https://youtu.be/abc": "YouTube",
    "https://www.tiktok.com/@user/video/1": "TikTok",
    "https://vm.tiktok.com/abc": "TikTok",
    "https://www.facebook.com/video/1": "Facebook",
    "https://fb.watch/abc": "Facebook",
    "https://www.instagram.com/p/abc/": "Instagram",
    "https://x.com/user/status/1": "Twitter/X",
    "https://twitter.com/user/status/1": "Twitter/X",
    "https://www.reddit.com/r/test/": "Reddit",
    "https://vimeo.com/123": "Vimeo",
    "https://soundcloud.com/artist/track": "SoundCloud",
    "https://example.com/video": "Other",
}
for url, expected in urls.items():
    result = detect_platform(url)
    icon = get_platform_icon(result)
    status = "OK" if result == expected else f"FAIL (got {result})"
    print(f"  {icon} {result:12s} <- {url[:45]:45s} [{status}]")

# Test is_valid_url
print("\n--- Test is_valid_url ---")
tests = [
    ("https://youtube.com", True),
    ("http://example.com/path", True),
    ("not-a-url", False),
    ("", False),
    ("ftp://files.com", False),
]
for url, expected in tests:
    result = is_valid_url(url)
    status = "OK" if result == expected else f"FAIL (got {result})"
    print(f"  {url:30s} -> {str(result):5s}  [{status}]")

# Test sanitize_filename
print("\n--- Test sanitize_filename ---")
tests = [
    ('hello/world:test', 'hello_world_test'),
    ('normal name', 'normal name'),
    ('', 'download'),
    ('a' * 250, 'a' * 200),
]
for val, expected in tests:
    result = sanitize_filename(val)
    status = "OK" if result == expected else f"FAIL (got {result})"
    display = val[:30] + "..." if len(val) > 30 else val
    print(f"  {display:35s} -> {result[:30]:30s}  [{status}]")

# Test format_speed & format_eta
print("\n--- Test format_speed ---")
print(f"  5242880 B/s -> {format_speed(5242880)}")
print(f"  None       -> {format_speed(None)}")

print("\n--- Test format_eta ---")
tests = [(45, "45s"), (150, "2m 30s"), (3700, "1h 01m"), (None, "N/A")]
for val, expected in tests:
    result = format_eta(val)
    status = "OK" if result == expected else f"FAIL (got {result})"
    print(f"  {str(val):>6s} -> {result:>8s}  [{status}]")

# Test default download dir
print("\n--- Test get_default_download_dir ---")
dl_dir = get_default_download_dir()
print(f"  Default dir: {dl_dir}")
import os
print(f"  Exists: {os.path.isdir(dl_dir)}")

# Test Downloader import
print("\n--- Test Downloader import ---")
from mediadl.downloader import Downloader, MediaInfo, FormatInfo
dl = Downloader()
print(f"  Downloader created, dir: {dl.download_dir}")

# Test App import
print("\n--- Test App import ---")
from mediadl.app import MediaDLApp
print(f"  MediaDLApp imported successfully")

print("\n" + "=" * 55)
print("  All tests passed!")
print("=" * 55)
