"""MediaDL - Universal Media Downloader with Terminal UI.

Main application module using Textual framework.
"""

from __future__ import annotations

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
    Static,
)

from mediadl.downloader import Downloader, MediaInfo
from mediadl.utils import (
    detect_platform,
    format_eta,
    format_size,
    format_speed,
    get_platform_icon,
    is_valid_url,
)


# ── ASCII Banner ────────────────────────────────────────────────
BANNER = r"""
 ╔╦╗╔═╗╔╦╗╦╔═╗╔╦╗╦  
 ║║║║╣  ║║║╠═╣ ║║║  
 ╩ ╩╚═╝═╩╝╩ ╩═╩╝╩═╝
  Universal Media Downloader
"""

WELCOME_TEXT = """[bold cyan]Dán URL vào ô phía trên rồi nhấn Enter hoặc nút [green]⏎ Analyze[/green] để bắt đầu.[/bold cyan]

[dim]Hỗ trợ: YouTube • TikTok • Facebook • Instagram • Twitter/X
Reddit • Vimeo • Dailymotion • SoundCloud • 1000+ trang khác[/dim]"""


class MediaDLApp(App):
    """Main TUI application for MediaDL."""

    TITLE = "MediaDL - Universal Media Downloader"
    SUB_TITLE = "yt-dlp powered"

    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True, priority=True),
        Binding("ctrl+s", "change_folder", "Save Folder", show=True),
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

    def compose(self) -> ComposeResult:
        """Build the UI layout."""
        # ── Header
        yield Static(BANNER, id="app-header")

        # ── URL Input
        with Horizontal(id="url-container"):
            yield Input(
                placeholder="  Dán URL video vào đây... (YouTube, TikTok, Facebook, Instagram, ...)",
                id="url-input",
            )
            yield Button("⏎ Analyze", id="analyze-btn", variant="success")

        # ── Save Directory (always visible)
        with Horizontal(id="savedir-container"):
            yield Label("  📂 Lưu vào:", id="savedir-icon")
            yield Label(self.downloader.download_dir, id="savedir-label")
            yield Button("✏ Đổi", id="savedir-btn", variant="default")

        # ── Save Directory Input (hidden, toggled by Ctrl+S or button)
        with Horizontal(id="savedir-input-container", classes="--hidden"):
            yield Input(
                placeholder="  Nhập đường dẫn thư mục lưu...",
                id="savedir-input",
            )
            yield Button("✔ OK", id="savedir-ok-btn", variant="success")

        # ── Main Content Area
        with Vertical(id="main-content"):
            # Welcome message (shown initially)
            with Container(id="welcome-panel"):
                yield Static(WELCOME_TEXT, id="welcome-text")

            # Info panel (hidden initially)
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

            # Format selection table (hidden initially)
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
        """Initialize app on mount."""
        log = self.query_one("#log-panel", RichLog)
        log.border_title = "📋 Log"
        log.write("[bold cyan]MediaDL v1.0.0[/bold cyan] - Universal Media Downloader")
        log.write(f"[dim]Download folder: {self.downloader.download_dir}[/dim]")
        log.write("[dim]──────────────────────────────────────────[/dim]")
        log.write("")

        # Focus the URL input
        self.query_one("#url-input", Input).focus()

    # ── Event Handlers ──────────────────────────────────────────

    @on(Input.Submitted, "#url-input")
    def on_url_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in URL input."""
        self._start_analysis()

    @on(Button.Pressed, "#analyze-btn")
    def on_analyze_pressed(self, event: Button.Pressed) -> None:
        """Handle Analyze button press."""
        self._start_analysis()

    @on(Button.Pressed, "#savedir-btn")
    def on_savedir_btn_pressed(self, event: Button.Pressed) -> None:
        """Toggle the save directory input."""
        self._toggle_savedir_input()

    @on(Input.Submitted, "#savedir-input")
    def on_savedir_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter in save directory input."""
        self._apply_savedir()

    @on(Button.Pressed, "#savedir-ok-btn")
    def on_savedir_ok_pressed(self, event: Button.Pressed) -> None:
        """Handle OK button for save directory."""
        self._apply_savedir()

    @on(DataTable.RowSelected, "#format-table")
    def on_format_selected(self, event: DataTable.RowSelected) -> None:
        """Handle format selection from table."""
        if self.is_downloading or self.current_info is None:
            return

        row_key = event.row_key
        table = self.query_one("#format-table", DataTable)

        # Get the row index from row_key
        row_index = None
        for i, key in enumerate(table.rows):
            if key == row_key:
                row_index = i
                break

        if row_index is not None and row_index < len(self.current_info.formats):
            selected_format = self.current_info.formats[row_index]
            self._start_download(selected_format.format_id, selected_format.quality)

    # ── Core Logic ──────────────────────────────────────────────

    def _start_analysis(self) -> None:
        """Begin URL analysis."""
        url_input = self.query_one("#url-input", Input)
        url = url_input.value.strip()

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
            self._log_warning("Đang tải... vui lòng đợi hoàn thành hoặc nhấn Esc để hủy.")
            return

        self._analyze_url(url)

    @work(exclusive=True, thread=False)
    async def _analyze_url(self, url: str) -> None:
        """Analyze URL in background worker."""
        log = self.query_one("#log-panel", RichLog)
        btn = self.query_one("#analyze-btn", Button)

        self.is_analyzing = True
        btn.label = "⏳ ..."
        btn.add_class("-analyzing")

        # Detect platform
        platform = detect_platform(url)
        icon = get_platform_icon(platform)

        log.write(f"\n[bold cyan]{'─' * 50}[/bold cyan]")
        log.write(f"[bold]🔍 Đang phân tích URL...[/bold]")
        log.write(f"[dim]   {url}[/dim]")
        log.write(f"   Platform: {icon} [bold]{platform}[/bold]")

        try:
            info = await self.downloader.extract_info(url)
            self.current_info = info

            # Update info panel
            self._show_info_panel(info)

            # Populate format table
            self._populate_format_table(info)

            log.write(f"[green]✅ Phân tích thành công![/green]")
            log.write(f"   📌 {info.title}")
            log.write(f"   👤 {info.uploader} | ⏱ {info.duration}")
            log.write(f"   📊 Tìm thấy [bold cyan]{len(info.formats)}[/bold cyan] định dạng")
            log.write(f"[bold yellow]👆 Chọn định dạng từ bảng phía trên rồi nhấn Enter để tải[/bold yellow]")

        except Exception as e:
            error_msg = str(e)
            # Clean up yt-dlp error messages
            if "is not a valid URL" in error_msg:
                self._log_error(f"URL không hợp lệ hoặc không được hỗ trợ")
            elif "Video unavailable" in error_msg:
                self._log_error("Video không khả dụng (có thể đã bị xóa hoặc ở chế độ riêng tư)")
            elif "Sign in" in error_msg:
                self._log_error("Video yêu cầu đăng nhập để xem")
            elif "geo" in error_msg.lower() or "country" in error_msg.lower():
                self._log_error("Video bị chặn theo vùng địa lý")
            else:
                self._log_error(f"Lỗi phân tích: {error_msg[:150]}")

        finally:
            self.is_analyzing = False
            btn.label = "⏎ Analyze"
            btn.remove_class("-analyzing")

    def _show_info_panel(self, info: MediaInfo) -> None:
        """Show and populate the info panel."""
        # Hide welcome, show info
        self.query_one("#welcome-panel").add_class("--hidden")
        self.query_one("#info-panel").remove_class("--hidden")
        self.query_one("#format-container").remove_class("--hidden")

        # Set border title
        info_panel = self.query_one("#info-panel")
        info_panel.border_title = f"📋 Media Info"

        # Update labels
        self.query_one("#info-platform", Label).update(
            f"{info.platform_icon} {info.platform}"
        )
        # Truncate title if too long
        title_display = info.title if len(info.title) <= 80 else info.title[:77] + "..."
        self.query_one("#info-title", Label).update(title_display)
        self.query_one("#info-uploader", Label).update(info.uploader)
        self.query_one("#info-duration", Label).update(info.duration)

    def _populate_format_table(self, info: MediaInfo) -> None:
        """Fill the format table with available formats."""
        table = self.query_one("#format-table", DataTable)
        format_container = self.query_one("#format-container")
        format_container.border_title = (
            f"🎯 Chọn định dạng ({len(info.formats)} kết quả) — Nhấn Enter để tải"
        )

        # Fully reset table: clear rows AND columns, then re-add columns
        # This ensures cursor/selection state is completely reset
        table.clear(columns=True)
        table.add_column("#", width=4, key="index")
        table.add_column("Quality", width=16, key="quality")
        table.add_column("Ext", width=6, key="ext")
        table.add_column("Size", width=10, key="size")
        table.add_column("Codec", width=16, key="codec")
        table.add_column("Type", width=12, key="type")

        for i, fmt in enumerate(info.formats):
            # Type column - make it clear what the output will be
            if fmt.format_id in ("bestvideo+bestaudio/best", "bestaudio/best"):
                type_str = "⭐ Recommended" if fmt.has_video else "⭐ Best Audio"
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

        # Move cursor to first row and focus the table
        table.move_cursor(row=0)
        table.focus()

    @work(exclusive=True, thread=False)
    async def _start_download(self, format_id: str, quality: str) -> None:
        """Start downloading in background worker."""
        if self.current_info is None:
            return

        log = self.query_one("#log-panel", RichLog)
        progress_container = self.query_one("#progress-container")
        progress_bar = self.query_one("#progress-bar", ProgressBar)
        progress_status = self.query_one("#progress-status", Label)

        self.is_downloading = True

        # Show progress
        progress_container.remove_class("--hidden")
        progress_bar.update(progress=0)

        log.write(f"\n[bold green]⬇ Bắt đầu tải...[/bold green]")
        log.write(f"   Định dạng: [bold]{quality}[/bold] | Format ID: {format_id}")
        log.write(f"   Lưu vào: [dim]{self.downloader.download_dir}[/dim]")

        last_percent = -1

        def progress_hook(d):
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
                    status_text = f"  ⬇ {size_str}  |  🚀 {speed_str}  |  ⏱ ETA: {eta_str}"
                    self.call_from_thread(progress_status.update, status_text)
                else:
                    speed_str = format_speed(speed)
                    size_str = format_size(downloaded)
                    status_text = f"  ⬇ {size_str}  |  🚀 {speed_str}"
                    self.call_from_thread(progress_status.update, status_text)

            elif status == "finished":
                self.call_from_thread(progress_bar.update, progress=100)
                self.call_from_thread(
                    progress_status.update,
                    "  ✅ Đang xử lý file..."
                )

        try:
            filepath = await self.downloader.download(
                url=self.current_info.url,
                format_id=format_id,
                formats=self.current_info.formats,
                progress_callback=progress_hook,
            )

            log.write(f"[bold green]✅ Tải thành công![/bold green]")
            log.write(f"   📁 {filepath}")
            progress_status.update(f"  ✅ Hoàn thành! File: {os.path.basename(str(filepath))}")

        except Exception as e:
            error_msg = str(e)
            self._log_error(f"Lỗi tải: {error_msg[:150]}")
            progress_status.update(f"  ❌ Tải thất bại!")

        finally:
            self.is_downloading = False

            # Hide progress bar after a moment
            progress_container.add_class("--hidden")
            progress_bar.update(progress=0)

            # If we still have format info, reset table and let user pick again
            if self.current_info is not None:
                self._populate_format_table(self.current_info)
                log.write("[bold yellow]🔄 Chọn định dạng khác từ bảng phía trên, hoặc dán URL mới.[/bold yellow]")
            else:
                self.query_one("#url-input", Input).focus()

    # ── Helper Methods ──────────────────────────────────────────

    def _log_error(self, message: str) -> None:
        """Write an error message to the log."""
        log = self.query_one("#log-panel", RichLog)
        log.write(f"[bold red]❌ {message}[/bold red]")

    def _log_warning(self, message: str) -> None:
        """Write a warning message to the log."""
        log = self.query_one("#log-panel", RichLog)
        log.write(f"[bold yellow]⚠ {message}[/bold yellow]")

    def _log_success(self, message: str) -> None:
        """Write a success message to the log."""
        log = self.query_one("#log-panel", RichLog)
        log.write(f"[bold green]✅ {message}[/bold green]")

    # ── Save Directory Methods ──────────────────────────────────

    def _toggle_savedir_input(self) -> None:
        """Show or hide the save directory input field."""
        container = self.query_one("#savedir-input-container")
        savedir_input = self.query_one("#savedir-input", Input)

        if "--hidden" in container.classes:
            # Show input, pre-fill with current path
            container.remove_class("--hidden")
            savedir_input.value = self.downloader.download_dir
            savedir_input.focus()
        else:
            # Hide input
            container.add_class("--hidden")
            self.query_one("#url-input", Input).focus()

    def _apply_savedir(self) -> None:
        """Apply the new save directory from input."""
        savedir_input = self.query_one("#savedir-input", Input)
        new_path = savedir_input.value.strip()

        if not new_path:
            self._log_warning("Đường dẫn không được để trống!")
            return

        # Expand user home shortcut
        new_path = os.path.expanduser(new_path)

        # Try to create directory if it doesn't exist
        try:
            os.makedirs(new_path, exist_ok=True)
        except OSError as e:
            self._log_error(f"Không thể tạo thư mục: {e}")
            return

        if not os.path.isdir(new_path):
            self._log_error(f"Đường dẫn không phải là thư mục: {new_path}")
            return

        # Apply new path
        self.downloader.download_dir = new_path
        self.query_one("#savedir-label", Label).update(new_path)

        # Hide input and log
        self.query_one("#savedir-input-container").add_class("--hidden")
        log = self.query_one("#log-panel", RichLog)
        log.write(f"[green]✅ Đã đổi thư mục lưu:[/green] [bold]{new_path}[/bold]")

        self.query_one("#url-input", Input).focus()

    # ── Actions ─────────────────────────────────────────────────

    def action_change_folder(self) -> None:
        """Toggle the save directory input (Ctrl+S)."""
        self._toggle_savedir_input()

    def action_clear_log(self) -> None:
        """Clear the log panel."""
        log = self.query_one("#log-panel", RichLog)
        log.clear()
        log.write("[dim]Log cleared.[/dim]")

    def action_open_folder(self) -> None:
        """Open the download folder in Windows Explorer."""
        download_dir = self.downloader.download_dir
        if os.path.exists(download_dir):
            os.startfile(download_dir)
            log = self.query_one("#log-panel", RichLog)
            log.write(f"[dim]📂 Mở thư mục: {download_dir}[/dim]")

    def action_cancel(self) -> None:
        """Cancel current operation and reset UI."""
        if self.is_analyzing or self.is_downloading:
            log = self.query_one("#log-panel", RichLog)
            log.write("[yellow]⚠ Đang hủy...[/yellow]")
            self.is_analyzing = False
            self.is_downloading = False

            # Hide progress
            self.query_one("#progress-container").add_class("--hidden")

            # Reset button
            btn = self.query_one("#analyze-btn", Button)
            btn.label = "⏎ Analyze"
            btn.remove_class("-analyzing")

        # Also hide savedir input if open
        self.query_one("#savedir-input-container").add_class("--hidden")

        # Focus back to URL input
        self.query_one("#url-input", Input).focus()
