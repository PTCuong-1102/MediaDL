# 📥 MediaDL - Universal Media Downloader TUI

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg?style=flat-round&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=flat-round)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-lightgrey.svg?style=flat-round)](https://github.com/PTCuong-1102/MediaDL)
[![Release](https://img.shields.io/github/v/release/PTCuong-1102/MediaDL?style=flat-round&color=orange)](https://github.com/PTCuong-1102/MediaDL/releases)

**MediaDL** là một ứng dụng Terminal User Interface (TUI) mạnh mẽ, hiện đại và dễ sử dụng để tải video/âm thanh từ hơn 1000 trang web (YouTube, TikTok, Facebook, Instagram, Twitter/X, SoundCloud, v.v.). Giao diện được xây dựng trên nền tảng **Textual** và **Rich**, sử dụng **yt-dlp** làm bộ máy tải xuống mạnh mẽ ở phía sau.

---

## 💾 Tải xuống & Cài đặt nhanh (Dành cho Người Dùng)

Đối với người dùng Windows, bạn không cần phải cài đặt Python hay chạy các dòng lệnh phức tạp. Chỉ cần tải xuống file cài đặt `.msi` đã được đóng gói sẵn:

### 🚀 Tải Installer (.msi)
Để tải phiên bản ổn định mới nhất của MediaDL cho Windows:

👉 **[Tải xuống MediaDL-1.0.0-win64.msi từ GitHub Releases](https://github.com/PTCuong-1102/MediaDL/releases/latest/download/MediaDL-1.0.0-win64.msi)**

*Hoặc bạn có thể truy cập trang **[GitHub Releases](https://github.com/PTCuong-1102/MediaDL/releases)** để xem tất cả phiên bản.*

### 🛠️ Hướng dẫn cài đặt trên Windows:
1. Tải file `MediaDL-1.0.0-win64.msi` từ link trên.
2. Click đúp vào file `.msi` để chạy trình cài đặt.
3. Làm theo hướng dẫn trên màn hình. Trình cài đặt sẽ tự động tạo:
   - Shortcut trên màn hình Desktop.
   - Shortcut trong Menu Start.
4. Mở **MediaDL** từ Desktop và bắt đầu tải xuống video của bạn!

---

## ✨ Các Tính Năng Nổi Bật

- 🎨 **Giao diện Terminal Tuyệt đẹp (TUI):** Hỗ trợ Dark Mode dịu mắt, hiệu ứng mượt mà và trực quan được thiết kế bằng thư viện `Textual`.
- 🌐 **Hỗ trợ hơn 1000+ Websites:** Nhào nặn từ sức mạnh của `yt-dlp`, bạn có thể tải video từ YouTube (bao gồm cả Shorts và Playlists), TikTok (không watermark), Facebook (Video, Reels), Instagram, Twitter/X, Reddit, SoundCloud, Twitch và nhiều nơi khác.
- 📊 **Tùy chọn chất lượng chi tiết:** Hiển thị danh sách đầy đủ các định dạng video/âm thanh hiện có cùng với thông tin về độ phân giải (quality), codec và dung lượng ước tính để bạn dễ dàng lựa chọn.
- 📥 **Thanh Tiến Trình Trực Quan:** Cung cấp thông tin thời gian thực về phần trăm hoàn thành, tốc độ tải hiện tại (MB/s) và thời gian hoàn thành dự kiến (ETA).
- ⌨️ **Tối ưu hóa phím tắt:** Thiết kế để sử dụng hoàn toàn bằng bàn phím mà không cần chuột, tăng tối đa tốc độ thao tác.
- 📁 **Quản lý thư mục tải thông minh:** Tự động tạo thư mục lưu tại `~/Downloads/MediaDL/` để sắp xếp dữ liệu ngăn nắp.

---

## 💻 Cài đặt & Chạy từ Source Code (Dành cho Lập Trình Viên)

Nếu bạn muốn đóng góp hoặc chạy trực tiếp từ mã nguồn:

### Yêu cầu hệ thống:
- **Python 3.8** trở lên.
- Đã cài đặt **FFmpeg** trên hệ thống (để gộp video và âm thanh chất lượng cao).

### Các bước thiết lập:

1. **Clone project về máy:**
   ```bash
   git clone https://github.com/PTCuong-1102/MediaDL.git
   cd MediaDL
   ```

2. **Tạo virtual environment (khuyên dùng):**
   ```bash
   python -m venv venv
   # Kích hoạt trên Windows:
   venv\Scripts\activate
   # Kích hoạt trên macOS/Linux:
   source venv/bin/activate
   ```

3. **Cài đặt các thư viện cần thiết:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Chạy ứng dụng:**
   ```bash
   python run.py
   ```

---

## 📦 Hướng dẫn Đóng gói thành File Cài đặt (.msi)

Dự án sử dụng `cx_Freeze` để đóng gói mã nguồn Python thành ứng dụng Windows `.exe` độc lập và xuất ra file cài đặt `.msi`.

Để đóng gói trên máy của bạn, hãy chạy lệnh sau:
```bash
python setup.py bdist_msi
```
Sau khi tiến trình hoàn thành:
- Bộ cài đặt `.msi` sẽ nằm trong thư mục `dist/`.
- Bản build không cần cài đặt (dạng folder chứa `.exe`) sẽ nằm trong thư mục `build/`.

---

## 🎮 Hướng Dẫn Sử Dụng Chi Tiết

1. **Nhập URL:** Sao chép đường dẫn video/âm thanh và dán vào ô input trên cùng của ứng dụng.
2. **Phân tích:** Nhấn `Enter` hoặc chọn nút **Analyze** để ứng dụng bắt đầu quét thông tin các luồng (formats) tải từ trang web.
3. **Lựa chọn định dạng:**
   - Một bảng định dạng sẽ hiện ra hiển thị chi tiết: ID định dạng, Loại (Video + Audio / Video / Audio), Độ phân giải, Codec, và Dung lượng.
   - Sử dụng phím mũi tên lên/xuống `↑`/`↓` để di chuyển và nhấn `Enter` trên định dạng bạn muốn tải xuống.
4. **Theo dõi tiến trình:** Màn hình sẽ chuyển sang chế độ tải với thanh tiến trình chi tiết. Khi hoàn tất, file sẽ tự động được lưu vào mục `Tải xuống` (`Downloads/MediaDL`).

---

## ⌨️ Bảng Phím Tắt Tiện Lợi

| Phím Tắt | Chức năng |
| :--- | :--- |
| `Enter` | Phân tích URL hoặc Bắt đầu tải định dạng được chọn |
| `Ctrl + O` | Mở trực tiếp thư mục lưu video tải xuống |
| `Ctrl + L` | Xóa nhật ký log hiển thị trên màn hình |
| `Esc` | Hủy thao tác hiện tại hoặc quay về màn hình phân tích |
| `Ctrl + Q` | Thoát ứng dụng an toàn |

---

## 📁 Cấu Trúc Mã Nguồn

```text
MediaDL/
├── mediadl/
│   ├── __init__.py      # Khai báo package
│   ├── app.py           # Logic giao diện TUI chính (Textual App)
│   ├── downloader.py    # Wrapper xử lý tải xuống thông qua yt-dlp
│   ├── styles.tcss      # File CSS tạo kiểu dáng giao diện cho Terminal
│   └── utils.py         # Các hàm tiện ích hỗ trợ định dạng dung lượng, path
├── requirements.txt     # Danh sách các thư viện phụ thuộc
├── run.py               # File chạy chính của ứng dụng
├── setup.py             # Script cấu hình đóng gói msi bằng cx_Freeze
└── README.md            # Tài liệu hướng dẫn sử dụng này
```

---

## 🤝 Đóng Góp Ý Kiến & Báo Lỗi

Mọi đóng góp, báo cáo lỗi (issues) hoặc yêu cầu tính năng mới đều được chào đón! Bạn có thể tạo issue hoặc pull request trực tiếp tại kho lưu trữ GitHub:

🔗 **GitHub Repository:** [https://github.com/PTCuong-1102/MediaDL](https://github.com/PTCuong-1102/MediaDL)
