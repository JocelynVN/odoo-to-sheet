---
name: odoo2sheet-help
description: Hướng dẫn sử dụng Odoo To Sheet bằng hội thoại HITL. Dùng khi người dùng gọi /odoo2sheet-help, hỏi plugin làm được gì, hoặc chưa biết nên bắt đầu từ đâu.
---

# Trợ giúp Odoo To Sheet

Luôn trả lời bằng tiếng Việt trừ khi người dùng yêu cầu ngôn ngữ khác. Dùng Human-in-the-loop (HITL) ngay trong hội thoại; không mở biểu mẫu UI và không tự chọn thay người dùng.

## Hỏi người dùng cần hướng dẫn gì

Nếu người dùng chưa nêu mục tiêu cụ thể, hãy đặt câu hỏi trực tiếp và đưa menu ngắn:

**Bạn muốn được hướng dẫn việc nào? Hãy trả lời bằng số hoặc mô tả theo cách của bạn.**

1. Kết nối Odoo lần đầu hoặc sửa lỗi đăng nhập.
2. Xuất báo cáo bán hàng thành CSV.
3. Chọn hồ sơ Odoo, đổi database hoặc thư mục lưu CSV.
4. Cập nhật plugin Odoo To Sheet.
5. Sao lưu, xóa dữ liệu cục bộ hoặc gỡ plugin.
6. Hướng dẫn khác, chẳng hạn tìm URL Odoo, tạo API key hoặc chọn database.

Chờ câu trả lời của người dùng trước khi chuyển sang skill khác, gọi tool hoặc thay đổi dữ liệu. Chấp nhận cả câu trả lời bằng số, tên lựa chọn hoặc yêu cầu tự do. Nếu họ đã nêu rõ việc cần làm, bỏ qua menu và hướng dẫn thẳng việc đó.

## Hướng dẫn theo lựa chọn

- **1. Kết nối hoặc sửa đăng nhập:** hướng dẫn dùng `/odoo2sheet-start`. Skill này kiểm tra hồ sơ, chỉ hỏi auth còn thiếu, tự tìm database và hỏi HITL nếu có nhiều database. Nếu đăng nhập sai, skill hỏi người dùng nhập lại email/API key.
- **2. Xuất báo cáo:** hướng dẫn dùng `/odoo2sheet-salereport`. Người dùng có thể nêu khoảng ngày, bộ lọc và cột trong cùng yêu cầu. Skill sẽ hỏi HITL phần còn thiếu, tóm tắt cấu hình CSV và chờ xác nhận trước khi xuất.
- **3. Chọn hồ sơ hoặc đổi cài đặt:** gọi `list_connections` trước. Nếu chưa có hồ sơ, hướng dẫn `/odoo2sheet-start`. Nếu có nhiều hồ sơ, hỏi người dùng chọn bằng số hoặc tên. Hỏi rõ họ muốn đổi database hay thư mục CSV trước khi thực hiện. Khi database/URL mới có thể xóa tùy chọn báo cáo đã lưu, giải thích tác động và chờ xác nhận HITL trước khi cập nhật.
- **4. Cập nhật plugin:** hướng dẫn dùng `/odoo2sheet-upgrade`. Nếu chưa biết họ dùng marketplace workspace hay bản cá nhân/local, hỏi chọn hoặc để họ mô tả cách cài trước khi đưa các bước tương ứng.
- **5. Sao lưu, xóa dữ liệu hoặc gỡ plugin:** hướng dẫn dùng `/odoo2sheet-uninstall`. Skill sẽ xem trước cấu hình, CSV và môi trường local; yêu cầu HITL xác nhận sao lưu và xác nhận dọn dữ liệu trước khi xóa.
- **6. Hướng dẫn khác:** hỏi người dùng muốn làm rõ nội dung nào nếu họ chưa nói cụ thể. Gợi ý một câu hỏi gần với nhu cầu của họ, ví dụ “Bạn đang cần tìm URL Odoo hay tạo API key?”. Không đoán câu trả lời thay người dùng.

## Quy tắc HITL

- Các lựa chọn luôn được trình bày thành câu hỏi trong chat, không tạo nút, biểu mẫu hay UI riêng.
- Mỗi lượt chỉ hỏi quyết định cần thiết tiếp theo. Người dùng có thể trả lời bằng số hoặc ngôn ngữ tự nhiên.
- Chờ người dùng trả lời trước khi gọi tool có thay đổi dữ liệu, chuyển skill, xuất CSV, lưu/xóa thiết lập hoặc bắt đầu dọn plugin.
- Không yêu cầu lại thông tin đã có trong cấu hình. Không hiển thị hoặc nhắc lại API key.
- MCP launcher kiểm tra và dùng lại `.odoo2shet-env` trước khi mở tool; nếu thiếu, nó cài thư viện còn thiếu theo `requirements.txt` vào đúng thư mục đó. Không yêu cầu người dùng tạo môi trường hoặc cài thư viện qua Terminal.
