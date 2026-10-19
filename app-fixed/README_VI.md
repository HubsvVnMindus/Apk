# TST-TOOL NOVA DARK — Android project

Đây là **bản chuyển đổi giao diện ban đầu** từ `tst-tool.py` sang Kivy Android:
- Giữ file logic gốc trong `tst_tool_core.py`; chỉ bỏ đoạn tự chạy `pip install` khi import vì thư viện được đóng gói cùng APK.
- Giao diện NOVA DARK cung cấp vùng log và ô nhập liệu để tương tác với các `Prompt.ask()` / `input()` cũ.
- Dữ liệu runtime lưu trong vùng riêng của ứng dụng Android.

## Build trên Linux / WSL
Cần Ubuntu/WSL, Java 17, Android SDK/NDK theo Buildozer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install buildozer cython
buildozer android debug
```

APK đầu ra nằm trong `bin/`.

## Quan trọng — tình trạng chuyển đổi
Đây là lớp giao diện tương thích ban đầu, **chưa thể cam kết mọi màn hình Rich Live hoạt động như giao diện Android native**. Những vùng sử dụng `rich.Live(screen=True)`, cập nhật dashboard thời gian thực hoặc nhập liệu lồng nhau cần kiểm thử trên thiết bị và có thể cần viết adapter chuyên biệt. Logic gốc được giữ lại để tránh tự ý thay đổi thuật toán.

## Thiết lập bảo mật trước khi phát hành
File nguồn có thông tin cấu hình Supabase và mã quản trị được nhúng trực tiếp. Không nên phát hành APK công khai với quyền quản trị / bí mật nằm trong client. Hãy chuyển thao tác quản trị nhạy cảm sang backend có xác thực và dùng policy/RLS phù hợp. Không đưa service-role key vào APK.

## Thiết bị mục tiêu
Cấu hình hiện tại nhắm `arm64-v8a`. Kiểm tra các thư viện native (đặc biệt `cryptography`) trong lần build thực tế; nếu recipe hoặc phiên bản Android NDK không tương thích, cần điều chỉnh cấu hình theo log build.

## Build APK tự động bằng GitHub Actions

1. Đưa toàn bộ nội dung thư mục dự án lên repository GitHub (nhớ giữ thư mục `.github/workflows/build.yml`).
2. Mở tab **Actions** của repository và bật workflow nếu GitHub yêu cầu.
3. Chọn **Build TST-TOOL NOVA DARK APK** → **Run workflow** → **Run workflow**.
4. Chờ job hoàn tất, mở lần chạy thành công và tải APK ở mục **Artifacts**.

Khi muốn tạo GitHub Release tự động: tạo và push một tag bắt đầu bằng `v`, ví dụ `v1.0.0`. Workflow sẽ build APK và đính kèm APK vào Release tương ứng.

**Lưu ý:** Đây là workflow build thử nghiệm. Lần build đầu có thể lâu vì Buildozer phải tải Android SDK/NDK và các gói phụ thuộc. Nếu build thất bại, mở log của bước **Build debug APK** để xem lỗi cụ thể. Workflow không thể đảm bảo source tương thích Android chỉ bằng việc tạo file cấu hình; cần sửa theo log nếu có lỗi.
