---
name: odoo2sheet-uninstall
description: Xóa hồ sơ kết nối Odoo đã lưu hoặc hướng dẫn gỡ Odoo To Sheet. Dùng khi người dùng gọi /odoo2sheet-uninstall.
---

# Xóa dữ liệu Odoo To Sheet hoặc gỡ plugin

Luôn trả lời bằng tiếng Việt, trừ khi người dùng yêu cầu ngôn ngữ khác.

Hồ sơ Odoo lưu trên máy và plugin là hai phần riêng. Xóa hồ sơ sẽ xóa email/API key đã lưu cùng tùy chọn báo cáo; các CSV đã xuất vẫn được giữ nguyên.

1. Gọi `list_connections` và cho biết đường dẫn cấu hình cục bộ, thường là `~/.config/odoo2sheet/config.json`.
2. Hỏi một lựa chọn rõ ràng:
   - **1. Giữ các hồ sơ kết nối** để dùng lại Odoo To Sheet.
   - **2. Xóa các hồ sơ kết nối và tùy chọn báo cáo khỏi máy này**.
3. Chỉ khi người dùng chọn xóa, gọi `remove_connection` cho từng hồ sơ trong danh sách với `confirm=true`. Không xóa CSV đã xuất.
4. Hướng dẫn gỡ plugin trong GPT Desktop:
   - Nếu người dùng quản lý workspace: mở **Workspace settings → Plugins**, tìm **Odoo To Sheet**, rồi tắt hoặc xóa plugin.
   - Nếu không quản lý workspace: nhờ quản trị viên workspace tắt hoặc xóa plugin.
5. Báo rõ hồ sơ nào được giữ/xóa; nhắc rằng CSV vẫn nằm trong thư mục đầu ra; cho biết quản trị viên có cần gỡ plugin khỏi workspace hay không.

Không yêu cầu người dùng mở Terminal hoặc chạy lệnh dòng lệnh. Không nói plugin đã được gỡ khỏi workspace; chỉ quản trị viên mới có thể gỡ trong ứng dụng.
