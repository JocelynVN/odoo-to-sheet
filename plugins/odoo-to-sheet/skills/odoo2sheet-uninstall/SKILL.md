---
name: odoo2sheet-uninstall
description: Sao lưu và dọn dữ liệu cục bộ của Odoo To Sheet, xóa hồ sơ kết nối, hoặc hướng dẫn gỡ plugin. Dùng khi người dùng gọi /odoo2sheet-uninstall.
---

# Sao lưu, dọn dữ liệu và gỡ Odoo To Sheet

Luôn trả lời bằng tiếng Việt trừ khi người dùng yêu cầu ngôn ngữ khác. Trao đổi bằng HITL trong chat; không yêu cầu người dùng mở Terminal.

Các tool cleanup cũng chạy sau preflight của MCP launcher: môi trường `.odoo2shet-env` được kiểm tra và dùng lại trước khi gọi; dependency thiếu được cài bổ sung theo `requirements.txt`. Không yêu cầu người dùng tạo env hoặc cài thư viện thủ công.

## Xác định phạm vi

- Nếu người dùng chỉ muốn xóa **một hồ sơ kết nối cụ thể**, gọi `list_connections`, xác nhận đúng tên hồ sơ bằng HITL, rồi gọi `remove_connection` với `confirm=true`. Việc này chỉ xóa hồ sơ và tùy chọn báo cáo của hồ sơ đó; không xóa CSV hay `.odoo2shet-env`.
- Nếu người dùng muốn **gỡ Odoo To Sheet và dọn dữ liệu**, làm theo toàn bộ quy trình bên dưới. Không bắt đầu xóa khi chưa có xác nhận sao lưu và xác nhận dọn.
- Nếu yêu cầu chưa rõ là xóa một hồ sơ hay dọn toàn bộ, hỏi họ chọn một trong hai trước khi tiếp tục.

## Quy trình dọn toàn bộ bằng HITL

1. Gọi `preview_local_cleanup` trước. Đây chỉ là bước xem trước, không thay đổi dữ liệu.
2. Tóm tắt kết quả cho người dùng bằng đường dẫn cụ thể:
   - Tệp cấu hình Odoo To Sheet, các hồ sơ sẽ bị xóa và số nhóm tùy chọn báo cáo.
   - Nếu `other_keys` không rỗng, báo rằng tệp cấu hình còn khóa ngoài profiles/tùy chọn báo cáo; tool sẽ xóa phần Odoo To Sheet và giữ nguyên các khóa khác.
   - Từng thư mục output, số lượng và tổng dung lượng CSV sẽ bị xóa. Nêu rõ tên các tệp được trả về; nếu danh sách bị rút gọn, nói rõ còn bao nhiêu tệp chưa hiển thị.
   - Nếu một thư mục output bị đánh dấu `skipped`, nói rõ tool không thể quét/dọn thư mục đó an toàn nên kết quả sẽ không được báo là hoàn tất.
   - Đường dẫn `.odoo2shet-env` và liệu thư mục đó có tồn tại, có được nhận diện an toàn để xóa không.
   - Nêu rõ chỉ xóa các tệp `.csv` ngay trong thư mục được liệt kê; không xóa thư mục con hoặc tệp không phải CSV. Mọi CSV nằm trong các thư mục output đã liệt kê đều thuộc phạm vi, kể cả CSV người dùng đặt tên riêng.
3. Nếu có CSV, yêu cầu người dùng sao lưu chúng sang một thư mục khác nằm ngoài các thư mục output đó. Hỏi một câu HITL rõ ràng, ví dụ: **“Bạn đã sao lưu các CSV này và muốn tiếp tục dọn toàn bộ dữ liệu Odoo To Sheet chứ?”** Nếu không có CSV, nói rõ không có output cần sao lưu rồi vẫn hỏi họ xác nhận dọn cấu hình và môi trường.
4. Chỉ sau khi người dùng xác nhận đã sao lưu (hoặc xác nhận không có output cần sao lưu) **và** đồng ý xóa, gọi `clean_local_data` với `cleanup_id` mới nhất, `backup_confirmed=true`, `confirm_cleanup=true`. Không coi việc chỉ gọi skill là xác nhận xóa.
5. Nếu tool báo preview đã cũ, không có gì được xóa. Gọi `preview_local_cleanup` lại, trình bày phạm vi mới và hỏi xác nhận lại. Nếu kết quả dọn có lỗi, báo chính xác phần đã xóa và phần còn lại; không nói đã dọn sạch.
6. Chỉ khi tool xác nhận dọn thành công mới hướng dẫn bước gỡ plugin trong ứng dụng. Báo chính xác hồ sơ/tùy chọn đã xóa, số CSV đã xóa, trạng thái `.odoo2shet-env`, và liệu tệp cấu hình có bị xóa hay còn khóa ngoài Odoo To Sheet:
   - Với plugin cài riêng từ danh mục cá nhân, mở tab **Plugins → Installed**, mở Odoo To Sheet rồi chọn **Uninstall plugin** nếu tùy chọn này có sẵn. Workspace-installed hoặc plugin mặc định có thể không có nút gỡ.
   - Với plugin do workspace cung cấp, nhờ quản trị viên mở **Admin → Plugins** và quản lý Odoo To Sheet. Nếu cần đồng bộ hoặc quản lý marketplace, vào **Admin → Plugins → Marketplaces**. Không hướng dẫn xóa cả marketplace chỉ để gỡ riêng Odoo To Sheet; việc đó có thể xóa toàn bộ plugin nhập từ marketplace.
   - Nếu người dùng không phải quản trị viên, hướng dẫn họ gửi yêu cầu cho quản trị viên. Không tuyên bố plugin đã được gỡ từ workspace.
   - Nếu không thấy tùy chọn **Uninstall plugin**, nói rõ việc gỡ cần quản trị viên hoặc chủ marketplace xử lý theo nguồn cài. Không tuyên bố plugin đã được gỡ từ workspace.

## Kết thúc

Nêu rõ phần nào đã hoàn tất: hồ sơ, CSV, thư mục môi trường và trạng thái gỡ plugin. Không khẳng định đã gỡ plugin trong ChatGPT nếu người dùng hoặc quản trị viên chưa thực hiện bước trong ứng dụng. Không nhắc lại hoặc hiển thị thông tin xác thực.
