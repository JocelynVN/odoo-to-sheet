---
name: odoo2sheet-start
description: Bắt đầu hoặc hoàn tất cấu hình Odoo To Sheet. Dùng khi người dùng gọi /odoo2sheet-start, kết nối Odoo lần đầu, hoặc muốn kiểm tra và hoàn tất cấu hình.
---

# Bắt đầu với Odoo To Sheet

Luôn trả lời bằng tiếng Việt trừ khi người dùng yêu cầu ngôn ngữ khác. Thực hiện toàn bộ bằng hội thoại HITL; không mở hoặc nhắc đến UI. Hỏi ngắn gọn đúng phần còn thiếu, dùng lựa chọn đánh số khi cần người dùng chọn. Không yêu cầu người dùng nhập lại thông tin đã có trong cấu hình, trừ khi kiểm tra xác thực báo thông tin đăng nhập sai.

Trước khi chạy tool, MCP launcher tự kiểm tra và dùng lại `.odoo2shet-env`; nếu thiếu dependency theo `requirements.txt`, launcher cài bổ sung vào đúng môi trường. Nếu tool báo runtime chưa sẵn sàng, dừng thao tác và hướng dẫn người dùng khởi động lại plugin; không yêu cầu họ tạo env hoặc cài thư viện qua Terminal.

Nếu các tool Odoo To Sheet không xuất hiện trong phiên hiện tại, không yêu cầu người dùng nhập auth và không lặp lại skill. Hỏi họ đã chọn **Odoo To Sheet** cho cuộc trò chuyện này chưa. Nếu đã chọn mà tool vẫn không xuất hiện, hướng dẫn quản trị viên đồng bộ/cập nhật plugin lên phiên bản mới nhất rồi mở cuộc trò chuyện mới. Chỉ tiếp tục khi tool đã khả dụng; không nói rằng chưa có hồ sơ nếu chưa gọi được `list_connections`.

## 1. Kiểm tra hồ sơ và auth

1. Gọi `list_connections` trước. Dựa vào `has_url`, `has_email`, `has_api_key` và `has_database`; các cờ này không tiết lộ giá trị email hoặc API key.
2. Nếu có nhiều hồ sơ, hỏi người dùng chọn hồ sơ bằng tên hoặc số, hoặc chọn tạo kết nối mới. Nếu chỉ có một hồ sơ, dùng hồ sơ đó, trừ khi người dùng yêu cầu kết nối mới. Nếu cần tạo mới, đặt tên tự động: dùng `odoo` nếu còn trống, nếu không thì lần lượt `odoo-2`, `odoo-3`, ...; không hỏi tên hồ sơ.
3. Thu thập URL Odoo, email và API key còn thiếu. Có thể hỏi URL và email cùng một lượt, rồi hỏi API key sau khi thông báo key sẽ nằm trong lịch sử cuộc trò chuyện riêng và được lưu trong file cấu hình cục bộ chưa mã hóa. Không thu thập key trong cuộc trò chuyện nhóm/chia sẻ. Không hiển thị hay nhắc lại key trong câu trả lời.
4. Ưu tiên HTTPS. Nếu URL dùng HTTP, giải thích kết nối không mã hóa và hỏi người dùng có muốn tiếp tục không; chỉ dùng `allow_http=true` sau khi họ đồng ý.
5. Với hồ sơ hiện có, cập nhật các trường auth vừa thu thập bằng `update_connection` trước khi kiểm tra database hoặc kết nối. Chỉ truyền các trường còn thiếu hoặc vừa được sửa; không đọc hay gửi lại giá trị auth đã lưu.

## 2. Tự lấy database

1. Nếu hồ sơ đã có database, bỏ qua bước này.
2. Nếu chưa có hồ sơ đã lưu, gọi `discover_databases` bằng URL và API key người dùng vừa cung cấp. Nếu hồ sơ đã tồn tại và auth đã đủ, gọi bằng `profile`.
3. Xử lý kết quả:
   - Có đúng một database: tự lưu tên đó vào hồ sơ bằng `save_connection` (hồ sơ mới) hoặc `update_connection` (hồ sơ hiện có); không hỏi người dùng chọn.
   - Có từ hai database trở lên: trình bày danh sách đánh số, hỏi người dùng chọn, rồi lưu lựa chọn vào hồ sơ.
   - Nếu `available=false` và lỗi nêu xác thực thất bại/HTTP 401, báo auth chưa hợp lệ, hỏi người dùng nhập lại email/API key, cập nhật hồ sơ hiện có nếu có, rồi gọi lại `discover_databases`.
   - Với lỗi liệt kê khác hoặc danh sách rỗng, giải thích ngắn gọn và hỏi tên database. Nếu người dùng không biết, không tự đoán; có thể thử kết nối không có database chỉ khi phiên bản/cấu hình Odoo hỗ trợ JSON-2 không cần chọn database. Nếu không xác định được khả năng đó, tiếp tục hỏi tên database.
4. Nếu đổi URL hoặc database khiến tùy chọn báo cáo đã lưu bị xóa, công cụ sẽ yêu cầu xác nhận riêng. Hãy cho người dùng biết rõ tác động và chỉ gọi lại `update_connection` với `confirm_clear_preferences=true` sau khi họ đồng ý.

## 3. Kiểm tra kết nối và xử lý lỗi

1. Khi hồ sơ đã có URL, email, API key và database cần thiết, gọi `check_connection`. Không dùng `describe_model sale.report` để thay cho kiểm tra auth, vì quyền với model bán hàng là bước riêng.
2. Nếu `connected=true`, báo cấu hình kết nối đã hoàn tất, nêu tên hồ sơ và database; không hiển thị email hoặc API key.
3. Nếu `authentication_error=true` hoặc thông báo nêu xác thực thất bại/HTTP 401, giải thích rằng đăng nhập chưa thành công và hỏi người dùng nhập lại email và API key. Cập nhật hồ sơ bằng `update_connection`, rồi gọi lại `check_connection`. Lặp lại nếu họ cung cấp thông tin mới mà vẫn lỗi.
4. Nếu lỗi không phải xác thực, diễn giải đúng lỗi thực tế. Với URL/network, hỏi sửa URL hoặc kiểm tra máy chủ. Với database, hỏi kiểm tra/chọn database. Với HTTP 403 hoặc quyền truy cập, nói rõ Odoo từ chối quyền; không yêu cầu thay key trừ khi lỗi cho thấy auth sai.
5. Không tuyên bố kết nối thành công nếu `check_connection` chưa trả `connected=true`.

## 4. Gợi ý bước tiếp theo bằng HITL

Sau khi kết nối thành công, thông báo **Đã hoàn tất cấu hình kết nối Odoo** và hỏi người dùng muốn làm gì tiếp theo. Chỉ đưa ra các lựa chọn phù hợp với skill đang có:

1. Xuất báo cáo bán hàng `sale.report` thành CSV — `/odoo2sheet-salereport`.
2. Hỏi cách dùng hoặc chọn tác vụ — `/odoo2sheet-help`.
3. Cập nhật plugin — `/odoo2sheet-upgrade`.
4. Xóa hồ sơ kết nối hoặc xem hướng dẫn gỡ plugin — `/odoo2sheet-uninstall`.
5. Hoàn tất ở đây.

Chờ người dùng chọn rồi mới chuyển sang skill tương ứng. Không tự xuất báo cáo sau khi kết nối.
