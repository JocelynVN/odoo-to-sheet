# Odoo To Sheet

Dùng ChatGPT Desktop để lấy báo cáo bán hàng từ Odoo và lưu thành file CSV trên máy tính. Plugin chỉ đọc dữ liệu Odoo; nó không sửa đơn hàng hay thông tin khách hàng.

## Dùng nhanh

1. Mở ChatGPT Desktop, tạo cuộc trò chuyện mới, rồi chọn **Odoo To Sheet** trong menu `+` → **More**. Nếu có ô chọn plugin, cũng có thể gọi `@Odoo To Sheet`.
2. Lần đầu tiên, nhập `/odoo2sheet-start` hoặc nhắn **Bắt đầu với Odoo To Sheet**. Plugin kiểm tra cấu hình, chỉ hỏi URL/email/API key còn thiếu, tự tìm database và tự lưu nếu chỉ có một. Nếu có nhiều database, bạn chọn bằng HITL trong chat. Nếu auth sai, plugin hỏi nhập lại email/API key.
3. Để lấy báo cáo, nhập `/odoo2sheet-salereport` kèm yêu cầu, ví dụ: **Lấy báo cáo bán hàng tháng này gồm ngày, đơn hàng, khách hàng, sản phẩm và doanh thu**.

Sau khi kết nối thành công, plugin báo cấu hình hoàn tất và hỏi bạn muốn dùng skill nào tiếp theo. Bạn có thể chọn xuất báo cáo bán hàng, hỏi cách sử dụng, quản lý hồ sơ, cập nhật plugin hoặc gỡ/xóa hồ sơ. Gọi `/odoo2sheet-help` nếu bạn muốn mở hộp lựa chọn các hướng dẫn phổ biến. Khi xuất báo cáo, bạn có thể nêu khoảng thời gian, điều kiện lọc và cột cần lấy ngay trong một yêu cầu; plugin hỏi phần còn thiếu, đưa cấu hình báo cáo đã lưu ra để bạn xác nhận, rồi chờ xác nhận trước khi tạo CSV.

## File được lưu ở đâu?

Hồ sơ kết nối mới lưu CSV vào thư mục `odoo2sheet-output` trong thư mục cá nhân của bạn. Ví dụ:

- macOS/Linux: `~/odoo2sheet-output`
- Windows: `C:\Users\Tên-của-bạn\odoo2sheet-output`

Plugin tự tạo thư mục khi xuất lần đầu. Bạn có thể chọn thư mục khác lúc kết nối. Tên file có tên báo cáo và thời điểm xuất, ví dụ `odoo2sheet-sale-report-20260929-143015.csv`. Nếu trùng tên, plugin thêm số thứ tự để không ghi đè file cũ.

## Bảo vệ tài khoản Odoo

API key được nhập trong chat riêng, có thể còn trong lịch sử cuộc trò chuyện, rồi lưu trên máy để dùng lần sau. File cấu hình không được mã hóa; đừng gửi file này cho người khác hoặc nhập key trong cuộc trò chuyện được chia sẻ. Plugin không đưa API key vào CSV và không ghi lại key trong kết quả.

## Cài lần đầu

Nếu bạn không thấy **Odoo To Sheet** trong ChatGPT Desktop, nhờ người quản lý không gian làm việc cài plugin từ [repo Odoo To Sheet trên GitHub](https://github.com/JocelynVN/odoo-to-sheet). Xem [hướng dẫn cài lần đầu](INSTALL.md). Repo GitHub là nguồn cài đặt; plugin chưa nằm trong danh mục công khai để mọi tài khoản tự cài.

Plugin này dành cho ứng dụng ChatGPT Desktop vì phần kết nối Odoo chạy trên máy người dùng; plugin không dùng được trên ChatGPT web hoặc điện thoại.

## Môi trường chạy tool

Trước khi các tool Odoo To Sheet được nạp, launcher tự kiểm tra và dùng lại môi trường Python `.odoo2shet-env`; nếu chưa có thì tự tạo, sau đó chỉ cài các gói còn thiếu được khai báo trong `requirements.txt`. Hiện kết nối Odoo dùng thư viện chuẩn Python nên tệp này chưa cần gói bên thứ ba. Người dùng không phải mở Terminal hay tự cài môi trường.

## Cập nhật và gỡ

- Cập nhật: người quản lý ChatGPT Desktop đồng bộ phiên bản mới từ GitHub. Nếu bạn là người quản lý, xem mục **Cập nhật** trong [hướng dẫn cài lần đầu](INSTALL.md).
- Dọn dữ liệu và gỡ Odoo To Sheet: dùng `/odoo2sheet-uninstall`. Skill sẽ xem trước cấu hình, CSV và `.odoo2shet-env`, yêu cầu bạn sao lưu CSV và xác nhận trong chat trước khi xóa. Sau khi dọn cục bộ, plugin hướng dẫn gỡ trong danh mục Plugins nếu có nút **Uninstall plugin**; plugin workspace cần quản trị viên xử lý.

## Hỗ trợ

Nếu kết nối hoặc xuất báo cáo không thành công, gửi cho người hỗ trợ nội dung lỗi mà ChatGPT Desktop hiển thị. Không gửi API key, file cấu hình, hay dữ liệu CSV chứa thông tin nhạy cảm.
