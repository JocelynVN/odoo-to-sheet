---
name: odoo2sheet-help
description: Hướng dẫn sử dụng Odoo To Sheet bằng hội thoại HITL và hộp lựa chọn tương tác. Dùng khi người dùng gọi /odoo2sheet-help, hỏi plugin làm được gì, hoặc chưa biết nên bắt đầu từ đâu.
---

# Trợ giúp Odoo To Sheet

Luôn trả lời bằng tiếng Việt trừ khi người dùng yêu cầu ngôn ngữ khác. Dùng HITL để người dùng quyết định bước tiếp theo; không tự chọn thay họ.

## Chọn nhu cầu cần hướng dẫn

- Nếu người dùng gọi `/odoo2sheet-help` mà chưa nói cụ thể cần gì, gọi `open_help_menu` để mở **hộp lựa chọn tương tác**. Chờ lựa chọn được gửi lại trong hội thoại rồi mới tiếp tục.
- Không thay hộp lựa chọn bằng danh sách số trong tin nhắn nếu `open_help_menu` khả dụng.
- Nếu `open_help_menu` không có trong phiên hoặc giao diện không hỗ trợ, hỏi trực tiếp trong chat với cùng các lựa chọn ngắn gọn; chấp nhận số, tên mục hoặc mô tả tự do.
- Nếu tool chỉ trả về chữ và người dùng không thấy hộp lựa chọn, chuyển sang hỏi trong chat; không khẳng định cửa sổ đã mở.
- Nếu người dùng đã nêu rõ việc cần làm, hoặc tin nhắn mới thể hiện lựa chọn vừa gửi từ hộp, bỏ qua hộp và tiếp tục đúng nhu cầu đó. Không mở menu lặp lại.
- Nếu người dùng chọn “Hướng dẫn khác” nhưng chưa nêu chủ đề, hỏi họ cần làm rõ việc gì, có thể gợi ý URL Odoo, API key hoặc chọn database.

Các mục trong hộp lựa chọn:

1. Kết nối Odoo lần đầu hoặc sửa lỗi đăng nhập.
2. Xuất báo cáo bán hàng thành CSV.
3. Chọn hồ sơ Odoo, đổi database hoặc thư mục lưu CSV.
4. Cập nhật plugin Odoo To Sheet.
5. Sao lưu, xóa dữ liệu cục bộ hoặc gỡ plugin.
6. Hướng dẫn khác.

## Tiếp tục theo lựa chọn

- **1. Kết nối hoặc sửa đăng nhập:** tiếp tục theo `/odoo2sheet-start`. Skill kiểm tra hồ sơ, chỉ hỏi thông tin xác thực còn thiếu, tự tìm database và hỏi HITL nếu có nhiều database. Nếu đăng nhập sai, hỏi người dùng nhập lại email/API key.
- **2. Xuất báo cáo:** tiếp tục theo `/odoo2sheet-salereport`. Hỏi HITL các bộ lọc/cột còn thiếu, tóm tắt cấu hình CSV và chờ xác nhận trước khi xuất.
- **3. Chọn hồ sơ hoặc đổi cài đặt:** gọi `list_connections` trước. Nếu chưa có hồ sơ, hướng dẫn `/odoo2sheet-start`. Nếu có nhiều hồ sơ, hỏi người dùng chọn bằng tên hoặc số. Làm rõ họ muốn đổi database hay thư mục CSV. Khi URL/database mới có thể xóa tùy chọn báo cáo đã lưu, giải thích tác động và chờ xác nhận HITL trước khi cập nhật.
- **4. Cập nhật plugin:** tiếp tục theo `/odoo2sheet-upgrade`. Nếu chưa biết họ dùng marketplace workspace hay bản cá nhân/local, hỏi chọn hoặc để họ mô tả cách cài trước khi đưa bước phù hợp.
- **5. Sao lưu, xóa dữ liệu hoặc gỡ plugin:** tiếp tục theo `/odoo2sheet-uninstall`. Skill xem trước cấu hình, CSV và môi trường local; yêu cầu HITL xác nhận sao lưu và xác nhận dọn dữ liệu trước khi xóa.

## Quy tắc HITL và công cụ

- Mỗi lượt chỉ hỏi quyết định cần thiết tiếp theo. Chờ người dùng trả lời trước khi chuyển skill, gọi tool có thay đổi dữ liệu, xuất CSV, lưu tùy chọn hoặc dọn plugin.
- Không yêu cầu lại thông tin đã có trong cấu hình. Không hiển thị hoặc nhắc lại API key.
- MCP launcher chuẩn bị môi trường Python `.odoo2shet-env` trước khi nạp tool: nếu đã có thì dùng lại, nếu chưa có thì tạo; chỉ cài các gói còn thiếu được khai báo trong `requirements.txt`. Runtime hiện dùng thư viện chuẩn Python nên không có gói bên thứ ba cần cài. Không yêu cầu người dùng tự tạo môi trường hoặc cài thư viện qua Terminal.
