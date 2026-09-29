# Odoo To Sheet

Dùng GPT Desktop để lấy báo cáo bán hàng từ Odoo và lưu thành file CSV trên máy tính. Plugin chỉ đọc dữ liệu Odoo; nó không sửa đơn hàng hay thông tin khách hàng.

## Dùng nhanh

1. Mở GPT Desktop, tạo cuộc trò chuyện mới, rồi chọn **Odoo To Sheet** trong menu `+` → **More**. Nếu có ô chọn plugin, cũng có thể gọi `@Odoo To Sheet`.
2. Lần đầu tiên, nhập `/odoo2sheet-connect` hoặc nhắn **Kết nối Odoo**. Chuẩn bị địa chỉ Odoo, email đăng nhập, API key và tên cơ sở dữ liệu nếu Odoo hỏi.
3. Để lấy báo cáo, nhập `/odoo2sheet-salereport` kèm yêu cầu, ví dụ: **Lấy báo cáo bán hàng tháng này gồm ngày, đơn hàng, khách hàng, sản phẩm và doanh thu**.

Plugin sẽ hỏi có dùng lại bộ lọc và cột đã lưu hay chọn cấu hình mới. Bạn có thể chọn các gợi ý hoặc tự mô tả điều kiện/cột muốn lấy. Sau khi tải xong, GPT Desktop sẽ báo vị trí file CSV.

## File được lưu ở đâu?

Hồ sơ kết nối mới lưu CSV vào thư mục `odoo2sheet-output` trong thư mục cá nhân của bạn. Ví dụ:

- macOS/Linux: `~/odoo2sheet-output`
- Windows: `C:\Users\Tên-của-bạn\odoo2sheet-output`

Plugin tự tạo thư mục khi xuất lần đầu. Bạn có thể chọn thư mục khác lúc kết nối. Tên file có tên báo cáo và thời điểm xuất, ví dụ `odoo2sheet-sale-report-20260929-143015.csv`. Nếu trùng tên, plugin thêm số thứ tự để không ghi đè file cũ.

## Bảo vệ tài khoản Odoo

API key được lưu trên máy của bạn trong hồ sơ Odoo để không phải nhập lại. File cấu hình không được mã hóa; đừng gửi file này cho người khác hoặc nhập API key trong cuộc trò chuyện được chia sẻ. Plugin không đưa API key vào file CSV và không ghi lại key trong kết quả.

## Cài lần đầu

Nếu bạn không thấy **Odoo To Sheet** trong GPT Desktop, nhờ người quản lý không gian làm việc cài plugin từ [repo Odoo To Sheet trên GitHub](https://github.com/JocelynVN/odoo-to-sheet). Xem [hướng dẫn cài lần đầu](INSTALL.md). Repo GitHub là nguồn cài đặt; plugin chưa nằm trong danh mục công khai để mọi tài khoản tự cài.

Plugin này dành cho ứng dụng GPT Desktop. Do cần chạy phần kết nối trên máy người dùng, plugin có thể không dùng được trên GPT web hoặc điện thoại.

## Cập nhật và gỡ

- Cập nhật: người quản lý GPT Desktop đồng bộ phiên bản mới từ GitHub. Nếu bạn là người quản lý, xem mục **Cập nhật** trong [hướng dẫn cài lần đầu](INSTALL.md).
- Xóa hồ sơ Odoo: dùng `/odoo2sheet-uninstall` và chọn có giữ thông tin kết nối hay không. File CSV đã xuất không bị xóa. Để gỡ plugin khỏi không gian làm việc, nhờ người quản lý tắt hoặc gỡ plugin.

## Hỗ trợ

Nếu kết nối hoặc xuất báo cáo không thành công, gửi cho người hỗ trợ nội dung lỗi mà GPT Desktop hiển thị. Không gửi API key, file cấu hình, hay dữ liệu CSV chứa thông tin nhạy cảm.
