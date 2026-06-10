"""Test the auto-merge audio feature."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import asyncio
from mediadl.downloader import Downloader


async def test():
    dl = Downloader()
    url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    print(f"Analyzing: {url}\n")

    info = await dl.extract_info(url)
    print(f"Title: {info.title}")
    print(f"Formats: {len(info.formats)} available\n")

    header = f"{'#':<4} {'Quality':<20} {'Ext':<6} {'Size':<10} {'Codec':<16} {'V':^3} {'A':^3} {'Type'}"
    print(header)
    print("-" * len(header))

    for i, f in enumerate(info.formats):
        v = "V" if f.has_video else ""
        a = "A" if f.has_audio else ""
        fmt_type = ""
        if f.format_id in ("bestvideo+bestaudio/best", "bestaudio/best"):
            fmt_type = "** RECOMMENDED **"
        elif f.has_video and f.has_audio:
            fmt_type = "Video+Audio"
        elif f.has_video:
            fmt_type = "+Audio auto-merge"
        else:
            fmt_type = "Audio only"
        print(f"{i+1:<4} {f.quality:<20} {f.extension:<6} {f.filesize:<10} {f.codec:<16} {v:^3} {a:^3} {fmt_type}")

    # Test _resolve_format
    print("\n--- Test _resolve_format ---")

    # Video-only format should get +bestaudio
    for f in info.formats:
        if f.has_video and not f.has_audio and f.format_id not in ("bestvideo+bestaudio/best",):
            resolved, is_audio = dl._resolve_format(f.format_id, info.formats)
            print(f"  Video-only '{f.format_id}' -> '{resolved}' (audio_only={is_audio})")
            assert "+bestaudio" in resolved, "Should auto-merge audio!"
            print("  OK - audio will be auto-merged")
            break

    # Best format stays as-is
    resolved, is_audio = dl._resolve_format("bestvideo+bestaudio/best", info.formats)
    print(f"  Best format -> '{resolved}' (audio_only={is_audio})")
    assert resolved == "bestvideo+bestaudio/best"
    print("  OK")

    # Audio-only format stays as-is
    resolved, is_audio = dl._resolve_format("bestaudio/best", info.formats)
    print(f"  Best audio -> '{resolved}' (audio_only={is_audio})")
    assert is_audio == True
    print("  OK")

    # Combined format stays as-is
    for f in info.formats:
        if f.has_video and f.has_audio and "best" not in f.format_id:
            resolved, is_audio = dl._resolve_format(f.format_id, info.formats)
            print(f"  Combined '{f.format_id}' -> '{resolved}' (audio_only={is_audio})")
            assert "+" not in resolved, "Combined should not be modified!"
            print("  OK - no merge needed")
            break

    print("\nAll auto-merge tests passed!")


asyncio.run(test())
