"""MediaDL - Universal Media Downloader with Terminal UI.

Main application module using Textual framework.
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Input,
    Label,
    ProgressBar,
    RichLog,
    Select,
    Static,
)

from mediadl import __version__
from mediadl.downloader import Downloader, MediaInfo
from mediadl.utils import (
    detect_platform,
    format_eta,
    format_size,
    format_speed,
    get_available_browsers,
    get_platform_icon,
    is_ffmpeg_installed,
    is_valid_url,
    open_directory,
)


# ── Logging setup ────────────────────────────────────────────────
log_dir = os.path.join(os.path.expanduser("~"), ".mediadl")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "mediadl.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger("MediaDL")


# ── ASCII Banner ─────────────────────────────────────────────────
BANNER = """\
 ╔╦╗╔═╗╔╦╗╦╔═╗╔╦╗╦
 ║║║║╣  ║║║╠═╣ ║║║
 ╩ ╩╚═╝═╩╝╩ ╩═╩╝╩═╝  v{version}  ✦ Universal Media Downloader"""

WELCOME_TEXT = """\
[bold #cba6f7]Dán URL vào ô phía trên rồi nhấn [green]⏎ Enter[/green] hoặc nút [green]Analyze[/green] để bắt đầu.[/bold #cba6f7]

[dim #6c7086]▶  YouTube  •  TikTok  •  Facebook  •  Instagram  •  Twitter/X[/dim #6c7086]
[dim #6c7086]▶  Reddit   •  Vimeo   •  Twitch    •  SoundCloud •  1000+ sites[/dim #6c7086]

[dim #45475a]💡 Tip: Nếu video yêu cầu đăng nhập, hãy bật Cookie qua [bold #f9e2af]Ctrl+K[/bold #f9e2af][/dim #45475a]\
"""


class MediaDLApp(App):
    """Main TUI application for MediaDL."""

    TITLE = "MediaDL"
    SUB_TITLE = f"v{__version__} — Universal Media Downloader"

    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True, priority=True),
        Binding("ctrl+s", "change_folder", "Save Folder", show=True),
        Binding("ctrl+k", "toggle_cookie", "Cookies", show=True),
        Binding("ctrl+l", "clear_log", "Clear Log", show=True),
        Binding("ctrl+o", "open_folder", "Open Folder", show=True),
        Binding("escape", "cancel", "Cancel", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.downloader = Downloader()
        self.current_info: MediaInfo | None = None
        self.is_downloading = False
        self.is_analyzing = False
        self.analysis_worker = None
        self.download_worker = None
        self._available_browsers = get_available_browsers()

    # ── Helpers ──────────────────────────────────────────────────

    def _cookie_status_label(self) -> str:
        if self.downloader.cookie_browser:
            return f"[bold #a6e3a1]🍪 Cookie: {self.downloader.cookie_browser.capitalize()}[/bold #a6e3a1]"
        return "[dim #6c7086]🍪 Cookie: Off[/dim #6c7086]"

    def _ffmpeg_status_label(self) -> str:
        if is_ffmpeg_installed():
            return "[dim #6c7086]⚙ FFmpeg: OK[/dim #6c7086]"
        return "[bold #f38ba8]⚠ FFmpeg: Missing[/bold #f38ba8]"

    # ── Layout ───────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        """Build the UI layout."""
        # ── Header
        yield Static(
            BANNER.format(version=__version__),
            id="app-header",
        )

        # ── Status bar (FFmpeg + Cookie)
        with Horizontal(id="status-bar"):
            yield Label("", id="status-ffmpeg")
            yield Label(" │ ", id="status-sep")
            yield Label("", id="status-cookie")

        # ── URL Input row
        with Horizontal(id="url-container"):
            yield Input(
                placeholder="  Dán URL vào đây... (YouTube, TikTok, Facebook, Instagram, Vimeo, ...)",
                id="url-input",
            )
            yield Button("⏎ Analyze", id="analyze-btn", variant="success")

        # ── Save-dir row (always visible)
        with Horizontal(id="savedir-container"):
            yield Label("  📂 Lưu vào:", id="savedir-icon")
            yield Label(self.downloader.download_dir, id="savedir-label")
            yield Button("✏ Đổi", id="savedir-btn", variant="default")

        # ── Save-dir input row (hidden until toggled)
        with Horizontal(id="savedir-input-container", classes="--hidden"):
            yield Input(
                placeholder="  Nhập đường dẫn thư mục mới...",
                id="savedir-input",
            )
            yield Button("✔ OK", id="savedir-ok-btn", variant="success")
            yield Button("✖ Hủy", id="savedir-cancel-btn", variant="error")

        # ── Cookie settings row (hidden until Ctrl+K)
        with Horizontal(id="cookie-container", classes="--hidden"):
            yield Label("  🍪 Cookie từ browser:", id="cookie-label")
            browser_options = [(b.capitalize(), b) for b in self._available_browsers]
            if not browser_options:
                browser_options = [("Không tìm thấy browser", "__none__")]
            yield Select(
                options=browser_options,
                id="cookie-select",
                allow_blank=True,
                prompt="-- Tắt cookie --",
            )
            yield Button("✔ Áp dụng", id="cookie-ok-btn", variant="success")
            yield Button("✖ Đóng", id="cookie-close-btn", variant="default")

        # ── Main content
        with Vertical(id="main-content"):
            # Welcome panel
            with Container(id="welcome-panel"):
                yield Static(WELCOME_TEXT, id="welcome-text")

            # Media info panel (hidden initially)
            with Container(id="info-panel", classes="--hidden"):
                with Horizontal(classes="info-row"):
                    yield Label("  Platform:", classes="info-label")
                    yield Label("", id="info-platform", classes="info-value-highlight")
                with Horizontal(classes="info-row"):
                    yield Label("  Title:", classes="info-label")
                    yield Label("", id="info-title", classes="info-value")
                with Horizontal(classes="info-row"):
                    yield Label("  Uploader:", classes="info-label")
                    yield Label("", id="info-uploader", classes="info-value")
                with Horizontal(classes="info-row"):
                    yield Label("  Duration:", classes="info-label")
                    yield Label("", id="info-duration", classes="info-value")

            # Format table (hidden initially)
            with Container(id="format-container", classes="--hidden"):
                yield DataTable(id="format-table", cursor_type="row", zebra_stripes=True)

            # Log panel
            yield RichLog(id="log-panel", highlight=True, markup=True)

        # ── Progress bar (hidden initially)
        with Container(id="progress-container", classes="--hidden"):
            yield ProgressBar(id="progress-bar", total=100, show_eta=False)
            yield Label("", id="progress-status")

        # ── Footer
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app after the DOM is ready."""
        log = self.query_one("#log-panel", RichLog)
        log.border_title = "📋 Log"
        log.write(f"[bold #cba6f7]MediaDL v{__version__}[/bold #cba6f7]  Universal Media Downloader")
        log.write(f"[dim]Download folder: {self.downloader.download_dir}[/dim]")
        log.write("[dim #45475a]──────────────────────────────────────────[/dim #45475a]")
        log.write("")

        logger.info("MediaDL started. Version: %s", __version__)
        logger.info("Download folder: %s", self.downloader.download_dir)

        # Update status labels
        self._refresh_status_bar()

        # Warn if FFmpeg missing
        if not is_ffmpeg_installed():
            self._log_warning("FFmpeg không tìm thấy! Gộp Video+Audio chất lượng cao có thể thất bại.")
            logger.warning("FFmpeg not found in PATH.")

        if not self._available_browsers:
            logger.info("No supported browsers detected for cookie extraction.")

        # Focus URL input
        self.query_one("#url-input", Input).focus()

    # ── Status bar ───────────────────────────────────────────────

    def _refresh_status_bar(self) -> None:
        """Update the status bar labels."""
        self.query_one("#status-ffmpeg", Label).update(self._ffmpeg_status_label())
        self.query_one("#status-cookie", Label).update(self._cookie_status_label())

    # ── Event Handlers ───────────────────────────────────────────

    @on(Input.Submitted, "#url-input")
    def on_url_submitted(self, event: Input.Submitted) -> None:
        self._start_analysis()

    @on(Button.Pressed, "#analyze-btn")
    def on_analyze_pressed(self, event: Button.Pressed) -> None:
        self._start_analysis()

    @on(Button.Pressed, "#savedir-btn")
    def on_savedir_btn_pressed(self, event: Button.Pressed) -> None:
        self._toggle_savedir_input()

    @on(Input.Submitted, "#savedir-input")
    def on_savedir_submitted(self, event: Input.Submitted) -> None:
        self._apply_savedir()

    @on(Button.Pressed, "#savedir-ok-btn")
    def on_savedir_ok_pressed(self, event: Button.Pressed) -> None:
        self._apply_savedir()

    @on(Button.Pressed, "#savedir-cancel-btn")
    def on_savedir_cancel_pressed(self, event: Button.Pressed) -> None:
        self.query_one("#savedir-input-container").add_class("--hidden")
        self.query_one("#url-input", Input).focus()

    @on(Button.Pressed, "#cookie-ok-btn")
    def on_cookie_ok_pressed(self, event: Button.Pressed) -> None:
        self._apply_cookie_setting()

    @on(Button.Pressed, "#cookie-close-btn")
    def on_cookie_close_pressed(self, event: Button.Pressed) -> None:
        self.query_one("#cookie-container").add_class("--hidden")
        self.query_one("#url-input", Input).focus()

    @on(DataTable.RowSelected, "#format-table")
    def on_format_selected(self, event: DataTable.RowSelected) -> None:
        if self.is_downloading or self.current_info is None:
            return

        format_id = event.row_key.value
        selected_format = next(
            (fmt for fmt in self.current_info.formats if fmt.format_id == format_id),
            None,
        )
        if selected_format is not None:
            self.download_worker = self._start_download(
                selected_format.format_id, selected_format.quality
            )

    # ── Core Logic ───────────────────────────────────────────────

    def _start_analysis(self) -> None:
        url = self.query_one("#url-input", Input).value.strip()

        if not url:
            self._log_error("Vui lòng nhập URL!")
            return
        if not is_valid_url(url):
            self._log_error(f"URL không hợp lệ: {url}")
            return
        if self.is_analyzing:
            self._log_warning("Đang phân tích... vui lòng đợi.")
            return
        if self.is_downloading:
            self._log_warning("Đang tải... nhấn Esc để hủy trước.")
            return

        self.analysis_worker = self._analyze_url(url)

    @work(exclusive=True, thread=False)
    async def _analyze_url(self, url: str) -> None:
        log = self.query_one("#log-panel", RichLog)
        btn = self.query_one("#analyze-btn", Button)

        self.is_analyzing = True
        btn.label = "⏳ ..."
        btn.add_class("-analyzing")

        platform = detect_platform(url)
        icon = get_platform_icon(platform)

        log.write(f"\n[bold #585b70]{'─' * 52}[/bold #585b70]")
        log.write(f"[bold]🔍 Đang phân tích...[/bold]")
        log.write(f"[dim]   {url[:80]}{'…' if len(url) > 80 else ''}[/dim]")
        log.write(f"   {icon} [bold #cba6f7]{platform}[/bold #cba6f7]")
        if self.downloader.cookie_browser:
            log.write(f"   [dim #a6e3a1]🍪 Cookie từ {self.downloader.cookie_browser.capitalize()}[/dim #a6e3a1]")
        logger.info("Analyzing URL: %s (platform=%s)", url, platform)

        try:
            info = await self.downloader.extract_info(url)
            self.current_info = info

            self._show_info_panel(info)
            self._populate_format_table(info)

            log.write(f"[bold #a6e3a1]✅ Phân tích thành công![/bold #a6e3a1]")
            log.write(f"   📌 {info.title[:80]}")
            log.write(f"   👤 {info.uploader}  ⏱ {info.duration}")
            log.write(
                f"   📊 Tìm thấy [bold #89b4fa]{len(info.formats)}[/bold #89b4fa] định dạng"
            )
            log.write(
                "[bold #f9e2af]👆 Chọn định dạng trong bảng trên rồi nhấn Enter để tải[/bold #f9e2af]"
            )
            logger.info("Analysis OK: %s", info.title)

        except asyncio.CancelledError:
            self._log_warning("Đã hủy phân tích URL.")
            logger.info("Analysis cancelled.")
        except Exception as e:
            error_msg = str(e)
            logger.error("Analysis failed: %s", error_msg, exc_info=True)
            self._handle_extract_error(error_msg, platform)

        finally:
            self.is_analyzing = False
            btn.label = "⏎ Analyze"
            btn.remove_class("-analyzing")

    def _handle_extract_error(self, error_msg: str, platform: str) -> None:
        """Map yt-dlp error messages to user-friendly Vietnamese messages."""
        msg_lower = error_msg.lower()

        # Platforms that commonly need cookies to even be recognized
        cookie_required_platforms = {"Facebook", "Instagram", "TikTok"}
        needs_cookie_hint = not self.downloader.cookie_browser

        if "login.php" in error_msg or "accounts.instagram.com/accounts/login" in error_msg:
            # Facebook/Instagram redirect to login page → definitely needs cookies
            self._log_error(
                f"{platform} yêu cầu đăng nhập — đã chuyển về trang login thay vì video."
            )
            if needs_cookie_hint:
                self._log_warning(
                    f"💡 Nhấn [bold #f9e2af]Ctrl+K[/bold #f9e2af] → chọn browser "
                    f"bạn đang dùng để đăng nhập {platform} → Áp dụng, rồi thử lại."
                )
            else:
                self._log_warning(
                    f"Cookie đã bật ({self.downloader.cookie_browser}) nhưng vẫn bị redirect login. "
                    f"Hãy đảm bảo bạn đã đăng nhập {platform} trong browser đó và không dùng incognito."
                )
        elif "is not a valid url" in msg_lower or "unsupported url" in msg_lower:
            if platform in cookie_required_platforms:
                # For these platforms, 'unsupported' almost always means cookies needed
                self._log_error(
                    f"Không thể truy cập {platform} — nền tảng này yêu cầu đăng nhập "
                    "để phân tích URL này."
                )
                if needs_cookie_hint:
                    self._log_warning(
                        f"💡 Nhấn [bold #f9e2af]Ctrl+K[/bold #f9e2af] → chọn browser "
                        f"bạn đang dùng để đăng nhập {platform} → Áp dụng, rồi thử lại."
                    )
                else:
                    self._log_warning(
                        f"Cookie đã bật ({self.downloader.cookie_browser}) nhưng yt-dlp "
                        "vẫn không nhận URL. Hãy đảm bảo bạn đã đăng nhập vào "
                        f"{platform} trong browser đó và thử lại."
                    )
            else:
                self._log_error(
                    "URL không được hỗ trợ. Kiểm tra lại URL hoặc thử một link khác."
                )
        elif "video unavailable" in msg_lower or "this video is unavailable" in msg_lower:
            self._log_error("Video không khả dụng (bị xóa hoặc bị ẩn riêng tư).")
        elif "private" in msg_lower or "restricted" in msg_lower:
            self._log_error("Video/bài đăng ở chế độ riêng tư hoặc bị hạn chế.")
            if needs_cookie_hint:
                self._log_warning(
                    "💡 Nhấn [bold #f9e2af]Ctrl+K[/bold #f9e2af] → chọn browser "
                    "đã đăng nhập vào nền tảng này → Áp dụng, rồi thử lại."
                )
        elif "login" in msg_lower or "sign in" in msg_lower or "log in" in msg_lower:
            self._log_error(f"Video yêu cầu đăng nhập ({platform}).")
            if needs_cookie_hint:
                self._log_warning(
                    "💡 Nhấn [bold #f9e2af]Ctrl+K[/bold #f9e2af] → chọn browser "
                    "đã đăng nhập vào nền tảng này → Áp dụng, rồi thử lại."
                )
        elif "geo" in msg_lower or "country" in msg_lower or "region" in msg_lower:
            self._log_error("Video bị chặn theo vùng địa lý.")
        elif "copyright" in msg_lower or "removed" in msg_lower:
            self._log_error("Video bị xóa do vi phạm bản quyền.")
        elif "403" in error_msg or "forbidden" in msg_lower:
            self._log_error("Truy cập bị từ chối (403 Forbidden).")
            if needs_cookie_hint:
                self._log_warning(
                    "💡 Thử bật Cookie qua [bold #f9e2af]Ctrl+K[/bold #f9e2af]."
                )
        elif "429" in error_msg or "too many" in msg_lower:
            self._log_error("Quá nhiều yêu cầu — bị rate-limit (429). Thử lại sau vài phút.")
        elif "network" in msg_lower or "connection" in msg_lower or "timeout" in msg_lower:
            self._log_error("Lỗi mạng. Kiểm tra kết nối internet và thử lại.")
        else:
            self._log_error(f"Lỗi phân tích: {error_msg[:200]}")

    def _show_info_panel(self, info: MediaInfo) -> None:
        self.query_one("#welcome-panel").add_class("--hidden")
        self.query_one("#info-panel").remove_class("--hidden")
        self.query_one("#format-container").remove_class("--hidden")

        self.query_one("#info-panel").border_title = "📋 Media Info"
        self.query_one("#info-platform", Label).update(
            f"{info.platform_icon} {info.platform}"
        )
        title_display = info.title if len(info.title) <= 80 else info.title[:77] + "…"
        self.query_one("#info-title", Label).update(title_display)
        self.query_one("#info-uploader", Label).update(info.uploader)
        self.query_one("#info-duration", Label).update(info.duration)

    def _populate_format_table(self, info: MediaInfo) -> None:
        table = self.query_one("#format-table", DataTable)
        format_container = self.query_one("#format-container")
        format_container.border_title = (
            f"🎯 Chọn định dạng  ({len(info.formats)} kết quả)  — Enter để tải"
        )

        table.clear(columns=True)
        table.add_column("#", width=4, key="index")
        table.add_column("Quality", width=16, key="quality")
        table.add_column("Ext", width=6, key="ext")
        table.add_column("Size", width=10, key="size")
        table.add_column("Codec", width=16, key="codec")
        table.add_column("Type", width=15, key="type")

        for i, fmt in enumerate(info.formats):
            if fmt.format_id in ("bestvideo+bestaudio/best", "bestaudio/best"):
                type_str = "⭐ Best" if fmt.has_video else "⭐ Best Audio"
            elif fmt.has_video and fmt.has_audio:
                type_str = "🎬 Video+Audio"
            elif fmt.has_video:
                type_str = "🔀 +Audio auto"
            else:
                type_str = "🎵 Audio only"

            table.add_row(
                str(i + 1),
                fmt.quality,
                fmt.extension,
                fmt.filesize,
                fmt.codec,
                type_str,
                key=fmt.format_id,
            )

        table.move_cursor(row=0)
        table.focus()

    @work(exclusive=True, thread=False)
    async def _start_download(self, format_id: str, quality: str) -> None:
        if self.current_info is None:
            return

        log = self.query_one("#log-panel", RichLog)
        progress_container = self.query_one("#progress-container")
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        progress_status = self.query_one("#progress-status", Label)

        self.is_downloading = True
        progress_container.remove_class("--hidden")
        progress_bar.update(progress=0)

        log.write(f"\n[bold #a6e3a1]⬇  Bắt đầu tải...[/bold #a6e3a1]")
        log.write(f"   Định dạng: [bold]{quality}[/bold]  |  ID: [dim]{format_id}[/dim]")
        log.write(f"   💾 {self.downloader.download_dir}")
        logger.info("Download started: format=%s quality=%s", format_id, quality)

        last_percent = -1

        def progress_hook(d: dict) -> None:
            nonlocal last_percent
            status = d.get("status", "")

            if status == "downloading":
                downloaded = d.get("downloaded_bytes", 0)
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                speed = d.get("speed")
                eta = d.get("eta")

                if total > 0:
                    percent = min(int(downloaded / total * 100), 100)
                    if percent != last_percent:
                        last_percent = percent
                        self.call_from_thread(progress_bar.update, progress=percent)
                    speed_str = format_speed(speed)
                    eta_str = format_eta(eta)
                    size_str = f"{format_size(downloaded)} / {format_size(total)}"
                    self.call_from_thread(
                        progress_status.update,
                        f"  ⬇  {size_str}  │  🚀 {speed_str}  │  ⏱ ETA: {eta_str}",
                    )
                else:
                    self.call_from_thread(
                        progress_status.update,
                        f"  ⬇  {format_size(downloaded)}  │  🚀 {format_speed(speed)}",
                    )
            elif status == "finished":
                self.call_from_thread(progress_bar.update, progress=100)
                self.call_from_thread(progress_status.update, "  ✅ Đang xử lý file...")

        try:
            filepath = await self.downloader.download(
                url=self.current_info.url,
                format_id=format_id,
                formats=self.current_info.formats,
                progress_callback=progress_hook,
            )

            log.write(f"[bold #a6e3a1]✅ Tải thành công![/bold #a6e3a1]")
            log.write(f"   📁 {filepath}")
            progress_status.update(
                f"  ✅ Hoàn thành!  {os.path.basename(str(filepath))}"
            )
            logger.info("Download complete: %s", filepath)

        except asyncio.CancelledError:
            self._log_warning("Đã hủy tải xuống.")
            progress_status.update("  ❌ Đã hủy!")
            logger.info("Download cancelled.")
        except Exception as e:
            error_msg = str(e)
            self._log_error(f"Lỗi tải: {error_msg[:200]}")
            progress_status.update("  ❌ Tải thất bại!")
            logger.error("Download failed: %s", error_msg, exc_info=True)

        finally:
            self.is_downloading = False
            await asyncio.sleep(2.0)
            progress_container.add_class("--hidden")
            progress_bar.update(progress=0)

            if self.current_info is not None:
                self._populate_format_table(self.current_info)
                log.write(
                    "[bold #f9e2af]🔄 Chọn định dạng khác từ bảng trên, hoặc dán URL mới.[/bold #f9e2af]"
                )
            else:
                self.query_one("#url-input", Input).focus()

    # ── Helper methods ───────────────────────────────────────────

    def _log_error(self, message: str) -> None:
        self.query_one("#log-panel", RichLog).write(f"[bold #f38ba8]❌ {message}[/bold #f38ba8]")
        logger.error(message)

    def _log_warning(self, message: str) -> None:
        self.query_one("#log-panel", RichLog).write(f"[bold #f9e2af]⚠  {message}[/bold #f9e2af]")
        logger.warning(message)

    def _log_success(self, message: str) -> None:
        self.query_one("#log-panel", RichLog).write(f"[bold #a6e3a1]✅ {message}[/bold #a6e3a1]")
        logger.info(message)

    # ── Save-dir methods ─────────────────────────────────────────

    def _toggle_savedir_input(self) -> None:
        container = self.query_one("#savedir-input-container")
        savedir_input = self.query_one("#savedir-input", Input)
        if "--hidden" in container.classes:
            container.remove_class("--hidden")
            savedir_input.value = self.downloader.download_dir
            savedir_input.focus()
        else:
            container.add_class("--hidden")
            self.query_one("#url-input", Input).focus()

    def _apply_savedir(self) -> None:
        savedir_input = self.query_one("#savedir-input", Input)
        new_path = os.path.expanduser(savedir_input.value.strip())

        if not new_path:
            self._log_warning("Đường dẫn không được để trống!")
            return
        try:
            os.makedirs(new_path, exist_ok=True)
        except OSError as e:
            self._log_error(f"Không thể tạo thư mục: {e}")
            return
        if not os.path.isdir(new_path):
            self._log_error(f"Không phải thư mục hợp lệ: {new_path}")
            return

        self.downloader.download_dir = new_path
        self.query_one("#savedir-label", Label).update(new_path)
        self.query_one("#savedir-input-container").add_class("--hidden")
        self._log_success(f"Đã đổi thư mục lưu: {new_path}")
        logger.info("Download dir changed to: %s", new_path)
        self.query_one("#url-input", Input).focus()

    # ── Cookie methods ───────────────────────────────────────────

    def _apply_cookie_setting(self) -> None:
        sel = self.query_one("#cookie-select", Select)
        value = sel.value  # may be Select.BLANK or a browser string

        if value is Select.BLANK or value == "__none__":
            self.downloader.clear_cookie_browser()
            self._log_success("Đã tắt Cookie — yt-dlp sẽ không dùng session browser.")
        else:
            self.downloader.set_cookie_browser(str(value))
            self._log_success(
                f"Đã bật Cookie từ [bold]{str(value).capitalize()}[/bold] — "
                "nội dung yêu cầu đăng nhập sẽ được truy cập qua session browser của bạn."
            )
            logger.info("Cookie browser set to: %s", value)

        self._refresh_status_bar()
        self.query_one("#cookie-container").add_class("--hidden")
        self.query_one("#url-input", Input).focus()

    # ── Actions ──────────────────────────────────────────────────

    def action_change_folder(self) -> None:
        self._toggle_savedir_input()

    def action_toggle_cookie(self) -> None:
        container = self.query_one("#cookie-container")
        if "--hidden" in container.classes:
            container.remove_class("--hidden")
            # Show helpful message first time
            if not self._available_browsers:
                self._log_warning(
                    "Không tìm thấy browser nào được hỗ trợ trên hệ thống. "
                    "Cài Chrome, Firefox hoặc Edge để dùng tính năng này."
                )
        else:
            container.add_class("--hidden")
        self.query_one("#url-input", Input).focus()

    def action_clear_log(self) -> None:
        log = self.query_one("#log-panel", RichLog)
        log.clear()
        log.write("[dim]Log cleared.[/dim]")
        logger.info("TUI log cleared.")

    def action_open_folder(self) -> None:
        dl_dir = self.downloader.download_dir
        if os.path.exists(dl_dir):
            open_directory(dl_dir)
            self.query_one("#log-panel", RichLog).write(
                f"[dim]📂 Mở thư mục: {dl_dir}[/dim]"
            )
            logger.info("Opened download directory: %s", dl_dir)

    def action_cancel(self) -> None:
        if self.is_analyzing or self.is_downloading:
            log = self.query_one("#log-panel", RichLog)
            log.write("[bold #f9e2af]⚠  Đang hủy...[/bold #f9e2af]")
            logger.info("Cancel requested.")

            if self.analysis_worker is not None:
                self.analysis_worker.cancel()
                self.analysis_worker = None
            if self.download_worker is not None:
                self.download_worker.cancel()
                self.download_worker = None

            self.is_analyzing = False
            self.is_downloading = False
            self.query_one("#progress-container").add_class("--hidden")
            btn = self.query_one("#analyze-btn", Button)
            btn.label = "⏎ Analyze"
            btn.remove_class("-analyzing")

        # Close any open overlay rows
        self.query_one("#savedir-input-container").add_class("--hidden")
        self.query_one("#cookie-container").add_class("--hidden")
        self.query_one("#url-input", Input).focus()
