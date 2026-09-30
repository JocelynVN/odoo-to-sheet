---
name: odoo2sheet-help
description: Hướng dẫn sử dụng Odoo To Sheet bằng câu hỏi HITL trực tiếp. Dùng khi người dùng gọi /odoo2sheet-help, hỏi plugin làm được gì, hoặc chưa biết nên bắt đầu từ đâu.
---

# Trợ giúp Odoo To Sheet

Luôn trả lời bằng tiếng Việt trừ khi người dùng yêu cầu ngôn ngữ khác. Không mở UI HTML, biểu mẫu hoặc thẻ lựa chọn riêng. Với câu hỏi có lựa chọn, phải gọi công cụ HITL gốc `request_user_input` nếu host cung cấp. Chỉ đặt câu hỏi trực tiếp trong chat khi host không có công cụ này hoặc cần nhận dữ liệu tự do mà công cụ không hỗ trợ.

## Giảm số lần người dùng phải trả lời

- Nếu người dùng đã nêu rõ mục tiêu, đi thẳng vào hướng dẫn tương ứng, không hiện menu.
- Nếu chưa rõ mục tiêu, gọi `request_user_input` đúng một lần với các lựa chọn sau:
  1. Kết nối Odoo hoặc sửa lỗi đăng nhập.
  2. Xuất báo cáo bán hàng thành CSV.
  3. Đổi hồ sơ, database hoặc thư mục lưu CSV.
  4. Cập nhật plugin.
  5. Sao lưu, dọn dữ liệu hoặc gỡ plugin.
  6. Nội dung khác.
- Chấp nhận số, tên mục hoặc mô tả tự nhiên. Sau khi người dùng chọn, tiếp tục luôn; không yêu cầu họ gọi slash command khác.
- Không thay lời gọi `request_user_input` bằng một menu đánh số trong câu trả lời khi công cụ đang khả dụng.
- Mỗi câu hỏi chỉ yêu cầu dữ liệu mà tool không thể tự lấy. Nếu thiếu nhiều giá trị liên quan, gom chúng trong một lượt.

## Tiếp tục theo lựa chọn

- **Kết nối hoặc sửa đăng nhập:** thực hiện toàn bộ luồng của `/odoo2sheet-start`.
- **Xuất báo cáo:** thực hiện luồng `/odoo2sheet-salereport`.
- **Đổi hồ sơ/database/thư mục CSV:** gọi `list_connections`. Tự dùng hồ sơ duy nhất; chỉ hỏi chọn khi có nhiều. Sau đó hỏi một lần người dùng muốn đổi mục nào và giá trị mới. Nếu đổi URL/database làm xóa tùy chọn báo cáo, giải thích và xin xác nhận trước khi cập nhật.
- **Cập nhật plugin:** thực hiện luồng `/odoo2sheet-upgrade`.
- **Sao lưu/dọn/gỡ:** thực hiện luồng `/odoo2sheet-uninstall`.
- **Nội dung khác:** nếu người dùng chưa mô tả, hỏi một câu mở ngắn; có thể gợi ý URL Odoo, API key hoặc database.

Không hiển thị hoặc nhắc lại API key. Không hỏi lại hệ điều hành, vị trí runtime, hồ sơ hoặc database nếu tool đã trả về.
