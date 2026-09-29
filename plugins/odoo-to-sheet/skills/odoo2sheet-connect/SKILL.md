---
name: odoo2sheet-connect
description: Kết nối hoặc chọn hồ sơ Odoo đã lưu cho Odoo To Sheet. Dùng khi người dùng gọi /odoo2sheet-connect hoặc yêu cầu kết nối, cấu hình Odoo.
---

# Kết nối Odoo To Sheet

Luôn trả lời bằng tiếng Việt, trừ khi người dùng yêu cầu rõ ràng ngôn ngữ khác. Không khẳng định chưa có hồ sơ trước khi gọi `list_connections` và kiểm tra kết quả.

Hồ sơ kết nối và tùy chọn báo cáo được lưu cục bộ tại `~/.config/odoo2sheet/config.json` (đường dẫn theo thư mục người dùng trên máy). Plugin giới hạn quyền đọc tệp trên macOS/Linux. Tệp không được mã hóa. Không bao giờ hiển thị, nhắc lại, tóm tắt, hoặc ghi API key vào tên tệp, log hay kết quả công cụ.

## Cách hỏi thông tin

- Trong luồng dự phòng bằng hội thoại, hỏi bằng câu ngắn, gắn nhãn rõ cho từng mục. Mỗi lượt chỉ hỏi **một trường**; không gom nhiều trường vào một đoạn yêu cầu và không bắt người dùng tự soạn một tin nhắn chứa toàn bộ thông tin.
- Nếu giao diện có bộ điều khiển nhập liệu hoặc lựa chọn có cấu trúc, dùng nó cho từng câu hỏi. Nếu không có, hỏi từng trường riêng trong hội thoại; không nói rằng một ô nhập hoặc biểu mẫu đang được hiển thị khi giao diện không cung cấp nó.
- Với lựa chọn đóng, đưa ra các phương án có số hoặc chữ để người dùng chỉ cần chọn.
- Trước khi hỏi API key, báo rõ key sẽ được lưu trong tệp cục bộ chưa mã hóa (dù quyền truy cập tệp bị giới hạn). Hỏi người dùng có muốn tiếp tục rồi mới xin key. Không nhắc lại giá trị key sau khi nhận.
- Bỏ qua thư mục CSV nếu người dùng không chọn; mặc định là `~/odoo2sheet-output`.

## Quy trình kết nối

1. Gọi `list_connections` trước. Dựa đúng vào danh sách trả về:
   - Nếu không có hồ sơ, mở biểu mẫu ở bước 2; chỉ hỏi từng trường theo thứ tự đó nếu giao diện không hiển thị biểu mẫu.
   - Nếu chỉ có một hồ sơ và người dùng không yêu cầu thêm dịch vụ mới, chọn hồ sơ đó; không xin lại key.
   - Nếu có nhiều hồ sơ, hiển thị tên hồ sơ, URL và thư mục CSV rồi hỏi người dùng chọn một hồ sơ hay thêm kết nối mới. Dùng tên hoặc số thứ tự; không yêu cầu viết lại thông tin kết nối.
2. Khi thêm kết nối, gọi `open_connection_form` để hiển thị biểu mẫu có nhãn riêng cho các trường. Biểu mẫu dùng ô mật khẩu cho API key, báo rõ việc lưu key chưa mã hóa và có xác nhận riêng cho HTTP không mã hóa. Khi biểu mẫu đã được hiển thị, không hỏi người dùng gõ lại những trường trong đó. Nếu máy khách không hỗ trợ/hiển thị MCP Apps UI, lần lượt hỏi từng trường còn thiếu, mỗi lần một trường:
   1. Tên hồ sơ ngắn, ví dụ `cong-ty-prod`.
   2. URL Odoo.
   3. Tên cơ sở dữ liệu nếu biết. Trường này bắt buộc với XML-RPC (thường dùng trên Odoo 18 trở xuống) và thường không bắt buộc với JSON-2 của Odoo 19.
   4. Email đăng nhập.
   5. Sau cảnh báo bảo mật ở trên, API key Odoo.
   6. Thư mục CSV chỉ hỏi khi người dùng muốn đổi khỏi mặc định.
3. Nếu tên hồ sơ đã tồn tại, hỏi người dùng muốn thay thế hồ sơ đó hay chọn tên khác. Không ghi đè âm thầm.
4. Ưu tiên URL HTTPS. Nếu người dùng đưa URL HTTP, giải thích thông tin đăng nhập sẽ đi qua kết nối không mã hóa và chờ họ xác nhận trước khi gọi `save_connection` với `allow_http=true`.
5. Với luồng hỏi bằng hội thoại, gọi `save_connection` sau khi đã có thông tin bắt buộc và xác nhận cần thiết. Biểu mẫu MCP Apps tự lưu hồ sơ và kiểm tra `sale.report`; khi người dùng báo biểu mẫu đã lưu thành công, không lưu lại lần nữa. Công cụ lưu hồ sơ cục bộ bằng thay thế tệp nguyên tử, giới hạn quyền trên macOS/Linux và không trả API key về.
6. Sau khi lưu, gọi `describe_model` với `sale.report` để xác nhận có thể truy cập báo cáo, trừ khi kết quả từ biểu mẫu đã xác nhận việc này.
   - Nếu hồ sơ đã lưu thiếu tên cơ sở dữ liệu và công cụ trả đúng lỗi này, hỏi riêng tên cơ sở dữ liệu rồi gọi `update_connection` với tên hồ sơ và database. Không xin lại API key. Sau đó gọi lại `describe_model`.
   - Nếu người dùng muốn đổi một database đã có sang tên khác, gọi `get_report_preferences`. Nếu có bộ lọc/cột đã lưu, báo rõ chúng sẽ bị xóa và hỏi xác nhận trước khi gọi `update_connection` với `confirm_clear_preferences=true`.
   - Nếu xác thực, URL, database, mô-đun bán hàng hoặc quyền Odoo có lỗi, giải thích bằng tiếng Việt dựa trên lỗi thật. Giữ hồ sơ đã lưu và không xin key lần nữa, trừ khi người dùng chủ động chọn thay thế hồ sơ.
7. Xác nhận tên hồ sơ, URL Odoo, database nếu có, thư mục CSV và đường dẫn tệp cấu hình. Không hiển thị API key.

Thư mục CSV mặc định cho hồ sơ mới là `~/odoo2sheet-output`, tự được tạo ở lần xuất đầu tiên. Hồ sơ cũ giữ nguyên thư mục đã cấu hình. Đổi thư mục không di chuyển hoặc xóa các CSV đã xuất.

Hồ sơ chỉ nằm trên máy này, không được chia sẻ qua marketplace của plugin.
