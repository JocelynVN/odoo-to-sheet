# Cài Odoo To Sheet vào ChatGPT Desktop

Hướng dẫn này dành cho người dùng và người quản lý ChatGPT Desktop. Người dùng cuối không cần dùng Terminal hoặc biết lập trình. Plugin chỉ hoạt động trong ChatGPT Desktop, không dùng trong ChatGPT web hoặc điện thoại.

## Nếu bạn chỉ muốn sử dụng plugin

Người quản lý không gian làm việc cần cài plugin một lần trước. Khi họ báo đã cài:

1. Mở ChatGPT Desktop và tạo cuộc trò chuyện mới.
2. Chọn **Odoo To Sheet** trong menu `+` → **More**. Nếu ChatGPT Desktop hỏi xác nhận cài đặt, chọn **Install plugin**.
3. Nếu không thấy plugin, nhờ người quản lý kiểm tra rằng plugin đã được bật cho tài khoản của bạn.
4. Gõ `/odoo2sheet-start` hoặc nhắn **Bắt đầu với Odoo To Sheet** để bắt đầu.

Nếu bạn không có quyền quản trị workspace, nhờ quản trị viên cài và bật plugin cho tài khoản của bạn. Chỉ tải repo trên GitHub về máy thì plugin chưa tự xuất hiện trong ChatGPT Desktop.

### Môi trường Python của tool

Khi plugin khởi động MCP server, launcher kiểm tra `.odoo2shet-env` trước khi nạp tool. Môi trường có sẵn sẽ được dùng lại; nếu chưa có, plugin tự tạo rồi kiểm tra `requirements.txt` và chỉ cài thư viện còn thiếu. Phiên bản hiện tại dùng thư viện chuẩn Python nên không cần gói bên thứ ba. Người dùng không cần tạo môi trường hoặc cài thư viện bằng Terminal.

## Cài plugin trong không gian làm việc

> **Ai làm bước này?** Người có quyền quản trị không gian làm việc trong ChatGPT. Các nhãn giao diện có thể hơi khác tùy phiên bản.

Repo GitHub đã có danh mục cài đặt ở thư mục gốc. Người quản trị làm theo các bước sau trong ChatGPT:

1. Mở **Admin → Plugins**.
2. Chọn **Add → Import marketplace**.
3. Trong ô **Source**, nhập `https://github.com/JocelynVN/odoo-to-sheet`.
4. Để trống ô **Path** và **Branch** để dùng nhánh mặc định của repo.
5. Chọn **Import marketplace** và đăng nhập GitHub nếu được yêu cầu.
6. Mở plugin **Odoo To Sheet** vừa nhập. Chọn **Available** để mọi người tự cài, hoặc **Installed** để tự cài cho nhóm người được chọn.
7. Đặt quyền chia sẻ plugin cho đúng nhóm trong không gian làm việc.

Sau khi quản trị viên hoàn tất, người dùng làm theo mục **Nếu bạn chỉ muốn sử dụng plugin** ở trên. Xem hướng dẫn chính thức về [quản lý và đồng bộ marketplace](https://learn.chatgpt.com/docs/enterprise/plugin-management) và [cài đặt, sử dụng, gỡ plugin](https://learn.chatgpt.com/docs/plugins).

## Kết nối Odoo lần đầu

Trong cuộc trò chuyện đã chọn plugin, gõ `/odoo2sheet-start` hoặc nhắn **Bắt đầu với Odoo To Sheet**. Chuẩn bị:

- Địa chỉ trang Odoo của công ty, ví dụ `https://congty.odoo.com`.
- Email dùng để đăng nhập Odoo.
- API key do Odoo cấp.
- Nếu muốn đổi, đường dẫn thư mục để lưu CSV. Mặc định là thư mục `odoo2sheet-output` trong thư mục cá nhân trên máy.

ChatGPT Desktop kiểm tra hồ sơ đã lưu và hỏi từng thông tin còn thiếu trong chat. Sau khi nhận auth, plugin tự tìm database; nếu chỉ có một, plugin tự lưu, còn nếu có nhiều thì hỏi bạn chọn bằng số. Nếu máy chủ không cho liệt kê, plugin sẽ hỏi tên database. Khi đăng nhập sai, plugin hỏi nhập lại email và API key. API key được nhập trong cuộc trò chuyện riêng, có thể còn trong lịch sử chat và được lưu trong file cấu hình cục bộ chưa mã hóa; plugin sẽ thông báo điều này trước khi hỏi key. Sau khi kết nối thành công, plugin hỏi bạn muốn dùng skill nào tiếp theo. Gõ `/odoo2sheet-help` để mở hộp lựa chọn các hướng dẫn phổ biến.

## Xuất báo cáo CSV

Gõ `/odoo2sheet-salereport` hoặc viết yêu cầu bằng lời, ví dụ:

> Lấy báo cáo bán hàng từ đầu tháng đến hôm nay, gồm ngày, số đơn, khách hàng, sản phẩm, số lượng và doanh thu.

Bạn có thể nêu khoảng thời gian, điều kiện lọc và cột ngay trong yêu cầu. Plugin hỏi trong chat về phần còn thiếu, dùng cấu hình đã lưu làm đề xuất để bạn xác nhận và chỉ gợi ý cột có thật trên Odoo; bạn không cần tự nhập tên trường kỹ thuật hay cú pháp domain. Trước khi xuất, plugin tóm tắt bộ lọc, cột và giới hạn dòng rồi chờ bạn xác nhận. Sau lần đầu dùng cấu hình mới, plugin hỏi bạn có muốn lưu để dùng lần sau không.

Sau khi xuất xong, ChatGPT Desktop sẽ báo số dòng và đường dẫn file. Mặc định file nằm trong `odoo2sheet-output` ở thư mục cá nhân của bạn. Tên file có tên báo cáo và thời điểm xuất; file cũ không bị ghi đè.

## Cập nhật phiên bản

Người quản trị marketplace GitHub có thể đồng bộ ngay khi muốn cập nhật:

1. Mở **Admin → Plugins → Marketplaces**.
2. Chọn marketplace đang cung cấp Odoo To Sheet.
3. Chọn **Sync now**.

Marketplace mới được kiểm tra thay đổi hằng ngày. Sau khi sync, quản trị viên cần xem trạng thái và báo cáo để biết plugin đã cập nhật thành công hay có lỗi. Người dùng thông thường không cần tải lại repo hoặc chạy lệnh cập nhật. Có thể nhắn `/odoo2sheet-upgrade`; nếu bạn không phải quản trị viên, plugin sẽ hướng dẫn liên hệ người quản lý để đồng bộ.

## Gỡ plugin hoặc xóa hồ sơ kết nối

- Để dọn dữ liệu local trước khi gỡ, dùng `/odoo2sheet-uninstall`. Plugin sẽ xem trước file cấu hình, CSV trong các thư mục output và `.odoo2shet-env`; bạn cần xác nhận đã sao lưu CSV và xác nhận xóa trong chat. Không có bước nào xóa dữ liệu trước khi bạn xác nhận.
- Với plugin cài riêng, mở tab **Plugins → Installed**, mở Odoo To Sheet và chọn **Uninstall plugin** nếu tùy chọn này có sẵn. Plugin workspace-installed hoặc plugin mặc định có thể không có nút gỡ; khi đó nhờ quản trị viên quản lý plugin trong **Admin → Plugins**. Không xóa cả marketplace chỉ để gỡ một plugin.

## Nếu không cài được

- Không thấy **Import marketplace**: bạn cần tài khoản quản trị không gian làm việc. Gửi trang GitHub này cho quản trị viên.
- Không thấy **Odoo To Sheet** sau khi cài: nhờ quản trị viên kiểm tra quyền **Available/Installed** và quyền chia sẻ.
- Đã chọn plugin nhưng `/odoo2sheet-start` báo không có công cụ: nhờ quản trị viên đồng bộ marketplace/cập nhật Odoo To Sheet lên phiên bản mới nhất, sau đó mở cuộc trò chuyện mới và chọn lại plugin. Không gửi thông tin đăng nhập cho đến khi plugin khả dụng.
- Không kết nối được Odoo: kiểm tra lại địa chỉ Odoo, email, API key và quyền truy cập báo cáo bán hàng. Không gửi API key cho bộ phận hỗ trợ.
- Nếu địa chỉ Odoo bắt đầu bằng `http://` thay vì `https://`, kết nối không mã hóa. Chỉ tiếp tục nếu bạn hiểu và chấp nhận rủi ro này.
