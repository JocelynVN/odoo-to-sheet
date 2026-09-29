# Cài Odoo To Sheet vào GPT Desktop

Hướng dẫn này dành cho người dùng và người quản lý GPT Desktop. Người dùng cuối không cần dùng Terminal hoặc biết lập trình. Plugin chỉ hoạt động trong GPT Desktop, không dùng trong GPT trên web hoặc điện thoại.

## Nếu bạn chỉ muốn sử dụng plugin

Người quản lý không gian làm việc cần cài plugin một lần trước. Khi họ báo đã cài:

1. Mở GPT Desktop và tạo cuộc trò chuyện mới.
2. Chọn **Odoo To Sheet** trong menu `+` → **More**. Nếu GPT Desktop hỏi xác nhận cài đặt, chọn **Install plugin**.
3. Nếu không thấy plugin, nhờ người quản lý kiểm tra rằng plugin đã được bật cho tài khoản của bạn.
4. Gõ `/odoo2sheet-connect` hoặc nhắn **Kết nối Odoo** để bắt đầu.

Tài khoản cá nhân không có mục **Workspace settings → Plugins** cần nhờ người quản lý cài plugin giúp. Chỉ tải repo trên GitHub về máy thì plugin chưa tự xuất hiện trong GPT Desktop.

## Cài plugin trong không gian làm việc

> **Ai làm bước này?** Người có quyền quản trị không gian làm việc trong ChatGPT. Các nhãn giao diện có thể hơi khác tùy phiên bản.

Repo GitHub đã có danh mục cài đặt ở thư mục gốc. Người quản trị làm theo các bước sau trong ChatGPT:

1. Mở **Workspace settings → Plugins**.
2. Chọn **Add → Import marketplace**.
3. Trong ô **Source**, nhập `https://github.com/JocelynVN/odoo-to-sheet`.
4. Để trống ô **Path** và **Branch** để dùng nhánh mặc định của repo.
5. Chọn **Import marketplace** và đăng nhập GitHub nếu được yêu cầu.
6. Mở plugin **Odoo To Sheet** vừa nhập. Chọn **Available** để mọi người tự cài, hoặc **Installed** để tự cài cho nhóm người được chọn.
7. Đặt quyền chia sẻ plugin cho đúng nhóm trong không gian làm việc.

Sau khi quản trị viên hoàn tất, người dùng làm theo mục **Nếu bạn chỉ muốn sử dụng plugin** ở trên. Hướng dẫn chính thức về [nhập marketplace từ GitHub](https://help.openai.com/en/articles/20001504-importing-and-syncing-plugin-marketplaces-from-github) và [sử dụng plugin trong ChatGPT](https://help.openai.com/en/articles/20001256-plugins-in-chatgpt-and-codex).

## Kết nối Odoo lần đầu

Trong cuộc trò chuyện đã chọn plugin, gõ `/odoo2sheet-connect` hoặc nhắn **Kết nối Odoo**. Chuẩn bị:

- Địa chỉ trang Odoo của công ty, ví dụ `https://congty.odoo.com`.
- Email dùng để đăng nhập Odoo.
- API key do Odoo cấp.
- Tên cơ sở dữ liệu nếu Odoo yêu cầu.
- Tên dễ nhớ cho hồ sơ, ví dụ `cong-ty`.
- Nếu muốn, đường dẫn thư mục để lưu CSV. Mặc định là thư mục `odoo2sheet-output` trong thư mục cá nhân trên máy.

GPT Desktop sẽ hỏi lần lượt và kiểm tra kết nối. API key được lưu trên máy để dùng lần sau; file cấu hình là văn bản chưa mã hóa. Chỉ kết nối trong cuộc trò chuyện riêng và không gửi file cấu hình cho người khác.

## Xuất báo cáo CSV

Gõ `/odoo2sheet-salereport` hoặc viết yêu cầu bằng lời, ví dụ:

> Lấy báo cáo bán hàng từ đầu tháng đến hôm nay, gồm ngày, số đơn, khách hàng, sản phẩm, số lượng và doanh thu.

Plugin sẽ hỏi:

1. Dùng lại bộ lọc đã lưu hay chọn bộ lọc mới.
2. Dùng lại các cột đã lưu hay chọn cột mới.
3. Có lưu lựa chọn mới để dùng lần sau không.

Chọn một phương án trong danh sách hoặc mô tả điều bạn muốn lọc/lấy. Plugin chỉ gợi ý cột có thật trên dịch vụ Odoo đang kết nối.

Sau khi xuất xong, GPT Desktop sẽ báo số dòng và đường dẫn file. Mặc định file nằm trong `odoo2sheet-output` ở thư mục cá nhân của bạn. Tên file có tên báo cáo và thời điểm xuất; file cũ không bị ghi đè.

## Cập nhật phiên bản

Người quản trị marketplace GitHub có thể đồng bộ ngay khi muốn cập nhật:

1. Mở **Workspace settings → Plugins**.
2. Mở mục **Marketplaces** và chọn marketplace **Odoo To Sheet**.
3. Chọn **Sync now**.

ChatGPT cũng tự kiểm tra thay đổi hằng ngày. Người dùng thông thường không cần tải lại repo hoặc chạy lệnh cập nhật. Có thể nhắn `/odoo2sheet-upgrade`; nếu bạn không phải quản trị viên, plugin sẽ hướng dẫn liên hệ người quản lý để đồng bộ.

## Gỡ plugin hoặc xóa hồ sơ kết nối

- Để xóa hồ sơ Odoo lưu trên máy, dùng `/odoo2sheet-uninstall` và chọn giữ hay xóa các hồ sơ. File CSV đã xuất vẫn được giữ lại.
- Để tắt plugin cho không gian làm việc, người quản trị vào **Workspace settings → Plugins**, mở **Odoo To Sheet** và chọn tắt hoặc đổi quyền sử dụng. Việc tắt plugin không tự xóa hồ sơ Odoo trên từng máy.

## Nếu không cài được

- Không thấy **Import marketplace**: bạn cần tài khoản quản trị không gian làm việc. Gửi trang GitHub này cho quản trị viên.
- Không thấy **Odoo To Sheet** sau khi cài: nhờ quản trị viên kiểm tra quyền **Available/Installed** và quyền chia sẻ.
- Không kết nối được Odoo: kiểm tra lại địa chỉ Odoo, email, API key và quyền truy cập báo cáo bán hàng. Không gửi API key cho bộ phận hỗ trợ.
- Nếu địa chỉ Odoo bắt đầu bằng `http://` thay vì `https://`, kết nối không mã hóa. Chỉ tiếp tục nếu bạn hiểu và chấp nhận rủi ro này.
