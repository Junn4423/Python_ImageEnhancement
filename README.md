# Python Image Enhancement

Ứng dụng Python nâng cao chất lượng ảnh: Histogram Equalization, CLAHE và Gaussian Blur

---

## Tổng quan

Kho lưu trữ **Python Image Enhancement** cung cấp một ứng dụng toàn diện để cải thiện chất lượng ảnh số thông qua các kỹ thuật xử lý ảnh khác nhau. Mục tiêu của README này là giới thiệu về kiến trúc hệ thống, các tính năng chính và thành phần cấu thành ứng dụng.

## Mục đích và phạm vi

Ứng dụng này được phát triển nhằm:

* Cải thiện độ tương phản và chất lượng ảnh bằng ba kỹ thuật chính:

  * **Histogram Equalization**
  * **CLAHE** (Contrast Limited Adaptive Histogram Equalization)
  * **Gaussian Blur**
* Cung cấp giao diện đồ họa (GUI) với khả năng:

  * Tải và xử lý ảnh ở nhiều định dạng khác nhau
  * Tùy chỉnh tham số của các thuật toán nâng cao
  * So sánh ảnh gốc và ảnh đã xử lý song song
  * Quản lý lịch sử thao tác với khả năng undo/redo
  * Hiển thị biểu đồ histogram và thông số ảnh
  * Lưu ảnh đã nâng cao chất lượng

## Kiến trúc hệ thống

### Sơ đồ kiến trúc tổng thể

Ứng dụng được xây dựng xung quanh lớp `UngDungXuLyAnh`, đóng vai trò là bộ điều khiển chính:

1. **Giao diện GUI**: Sử dụng Tkinter, với bố cục hai khung hình (dual-panel) và các tab điều khiển.
2. **Xử lý ảnh**: Cơ chế áp dụng các thuật toán nâng cao và biến đổi ảnh.
3. **Quản lý lịch sử**: Theo dõi các trạng thái ảnh để hỗ trợ undo/redo.
4. **Thao tác tệp**: Mở, lưu ảnh ở nhiều định dạng khác nhau.

### Cấu trúc GUI

* **Khung trái**: Hiển thị ảnh với các tab cho chế độ gốc, đã xử lý và so sánh.
* **Khung phải**: Chứa các tab điều khiển thông tin ảnh, biểu đồ histogram và cấu hình tham số.
* **Thanh công cụ**: Nút mở, lưu, undo, redo, zoom.
* **Menu Bar**: Các chức năng bổ sung qua dropdown menu.

## Luồng xử lý và quản lý

### Luồng xử lý ảnh

1. Người dùng tải ảnh qua hàm `open_image()`.
2. Ảnh gốc được lưu vào `self.original_image` và nhân bản thành `self.current_image`.
3. Khi áp dụng thuật toán, ảnh kết quả được lưu vào `self.processed_image` và thêm vào lịch sử.
4. Ảnh đã xử lý trở thành `self.current_image` cho các thao tác tiếp theo.
5. Người dùng có thể điều hướng lịch sử qua `undo()` và `redo()`.

### Quản lý lịch sử

* Cho phép **undo** trở về trạng thái trước.
* Cho phép **redo** sau khi undo.
* Bắt đầu nhánh lịch sử mới từ bất kỳ điểm nào.
* Reset về ảnh gốc.

## Tính năng chính

### Các kỹ thuật nâng cao

| Kỹ thuật               | Hàm                        | Mô tả                                              | Tham số chính             |
| ---------------------- | -------------------------- | -------------------------------------------------- | ------------------------- |
| Histogram Equalization | `histogram_equalization()` | Phân phối lại cường độ điểm ảnh để tăng tương phản | `color_channels` flag     |
| CLAHE                  | `clahe()`                  | Histogram Equalization có giới hạn cường độ        | `clip_limit`, `grid_size` |
| Gaussian Blur          | `apply_gaussian_blur()`    | Làm mờ ảnh bằng bộ lọc Gauss                       | `kernel_size`, `sigma`    |

Tất cả các hàm xử lý đều nằm trong lớp `UngDungXuLyAnh` và hỗ trợ xử lý ảnh xám lẫn ảnh màu (riêng biệt hoặc chuyển đổi không gian màu HSV/LAB).

### Công cụ trực quan hóa

* **Thông tin ảnh**: Hiển thị metadata, kích thước và thống kê cơ bản.
* **Histogram thời gian thực**: Biểu diễn tần suất cường độ điểm ảnh.
* **So sánh trước/sau**: Xem song song ảnh gốc và ảnh xử lý.
* **Điều khiển phóng to**: Xem chi tiết ở nhiều mức độ.

## Công nghệ sử dụng

* **Tkinter**: Xây dựng giao diện đồ họa.
* **Pillow (PIL)**: Tải, lưu và thao tác cơ bản với ảnh.
* **OpenCV (cv2)**: Các thuật toán xử lý ảnh tối ưu.
* **NumPy**: Phép toán số học nhanh trên dữ liệu ảnh.
* **Matplotlib**: Vẽ biểu đồ histogram và hiển thị kết quả.

## Kết luận

Ứng dụng **Python Image Enhancement** mang đến giải pháp hoàn chỉnh cho việc nâng cao chất lượng ảnh thông qua giao diện trực quan và các thuật toán mạnh mẽ. Thiết kế module rõ ràng giúp dễ dàng mở rộng và bảo trì.

---
DOCS: [![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/Junn4423/Python_ImageEnhancement)
*Updated: May 18, 2025*
