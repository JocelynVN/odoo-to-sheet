---
name: odoo2sheet-start
description: Chuẩn bị runtime và hoàn tất kết nối Odoo theo một luồng liên tục. Dùng khi người dùng gọi /odoo2sheet-start, kết nối lần đầu, hoặc muốn kiểm tra cấu hình.
---

# Bắt đầu với Odoo To Sheet

Luôn trả lời bằng tiếng Việt trừ khi người dùng yêu cầu ngôn ngữ khác. Thực hiện đúng thứ tự bên dưới, không nhảy bước và không mở UI riêng. Dùng HITL trực tiếp trong hội thoại khi thật sự cần người dùng chọn hoặc cung cấp dữ liệu.

## Cách dùng HITL gốc của host

- Khi cần người dùng **chọn** hồ sơ, database hoặc bước tiếp theo, phải gọi công cụ hỏi người dùng gốc `request_user_input` nếu host cung cấp. Mỗi lựa chọn có nhãn ngắn và một câu mô tả tác động.
- Không in một menu đánh số rồi kết thúc lượt nếu `request_user_input` đang khả dụng.
- URL, email và API key là dữ liệu tự do. Gom các trường còn thiếu vào một câu hỏi; dùng trường nhập tự do/bí mật của HITL nếu host hỗ trợ, nếu không thì hỏi trực tiếp trong chat một lần.
- Khi host không có `request_user_input`, đặt đúng một câu hỏi ngắn trong chat và chờ câu trả lời. Không dựng UI HTML hoặc gọi resource UI để thay thế.

## Nguyên tắc giảm nhập liệu

- Tự đọc mọi trạng thái có thể lấy bằng tool: hệ điều hành, vị trí runtime, hồ sơ, URL, database và thư mục output. Không hỏi lại dữ liệu đã có.
- Nếu thiếu nhiều trường auth, hỏi tất cả trường còn thiếu trong **một lượt**. Không chia URL, email và API key thành nhiều câu hỏi.
- Tự đặt tên hồ sơ mới: `odoo`, rồi `odoo-2`, `odoo-3`, ... Không hỏi tên hồ sơ nếu người dùng không yêu cầu.
- Chỉ hỏi chọn hồ sơ khi có nhiều hồ sơ. Chỉ hỏi chọn database khi Odoo trả nhiều database.
- Không yêu cầu người dùng xác nhận lại thao tác họ vừa yêu cầu. Vẫn xin xác nhận cho HTTP không mã hóa, thay thế/xóa dữ liệu hoặc xóa tùy chọn báo cáo.
- Không hiển thị hay nhắc lại API key.

## 1. Chuẩn bị môi trường chạy tool

1. Gọi `get_runtime_status` trước mọi tool khác.
2. Launcher đã tự phát hiện hệ điều hành và tự tạo hoặc dùng lại `.odoo2sheet-env` tại thư mục dữ liệu người dùng phù hợp với hệ điều hành. Không hỏi người dùng dùng OS nào hoặc muốn cài ở đâu.
3. Nếu `ready=true`, tiếp tục ngay. Nếu `environment.action` là `created`, `created_and_installed` hoặc `dependencies_updated`, báo ngắn gọn OS và đường dẫn đã chuẩn bị; không yêu cầu xác nhận.
4. Nếu tool không xuất hiện, chưa được phép thu thập auth. Hỏi người dùng đã chọn **Odoo To Sheet** cho cuộc trò chuyện này chưa. Nếu đã chọn mà tool vẫn thiếu, hướng dẫn đồng bộ plugin rồi mở cuộc trò chuyện mới.
5. Nếu launcher báo lỗi, nêu đúng OS, đường dẫn dự kiến và lỗi. Chỉ yêu cầu người dùng can thiệp khi lỗi cho thấy máy thiếu Python/venv hoặc không có quyền ghi; không yêu cầu họ lặp lại các bước đã thành công.

## 2. Kiểm tra auth đã lưu

1. Gọi `list_connections`.
2. Nếu có một hồ sơ, dùng hồ sơ đó. Nếu có nhiều hồ sơ, hỏi một câu HITL để chọn tên hồ sơ hoặc tạo kết nối mới. Nếu không có, tạo tên hồ sơ tự động.
3. Dựa vào `has_url`, `has_email`, `has_api_key`:
   - Đủ cả ba: không hỏi auth, sang bước database.
   - Thiếu trường nào: hỏi một lần chỉ các trường còn thiếu. Với kết nối mới thường hỏi URL Odoo, email và API key trong cùng một tin nhắn.
4. Trước khi nhận API key, nói ngắn gọn rằng key sẽ nằm trong lịch sử cuộc trò chuyện riêng và được lưu trong tệp cấu hình cục bộ chưa mã hóa. Không thu thập key trong cuộc trò chuyện nhóm/chia sẻ.
5. Nếu URL dùng HTTP, giải thích kết nối không mã hóa và chờ người dùng đồng ý trước khi dùng `allow_http=true`.
6. Với hồ sơ mới, gọi `save_connection` ngay sau khi đủ URL, email và API key, chưa cần database. Với hồ sơ hiện có, gọi `update_connection` chỉ với trường vừa bổ sung hoặc sửa.

## 3. Kiểm tra và tự lấy database

1. Gọi lại `list_connections` sau khi lưu auth để dùng trạng thái mới nhất.
2. Nếu `has_database=true`, không hỏi database và sang bước kiểm tra kết nối.
3. Nếu chưa có database, gọi `discover_databases` bằng `profile` đã lưu.
4. Xử lý kết quả:
   - Một database: tự gọi `update_connection` để lưu, không hỏi người dùng.
   - Nhiều database: hỏi một câu HITL với danh sách tên database; lưu đúng lựa chọn bằng `update_connection`.
   - Không thể liệt kê hoặc danh sách rỗng: hỏi tên database một lần. Không tự đoán.
5. Nếu thay database làm xóa tùy chọn báo cáo đã lưu, giải thích tác động và chỉ gọi lại với `confirm_clear_preferences=true` sau khi người dùng đồng ý.

## 4. Kiểm tra kết nối

1. Gọi `check_connection` sau khi hồ sơ đủ auth và database cần thiết.
2. Chỉ báo thành công khi `connected=true`.
3. Nếu `authentication_error=true`, hỏi người dùng nhập lại email và API key trong cùng một lượt; gọi `update_connection`, rồi kiểm tra lại. Không hỏi URL/database nếu lỗi không liên quan.
4. Với lỗi URL/network, hỏi đúng URL cần sửa hoặc yêu cầu kiểm tra máy chủ. Với lỗi database, hỏi database. Với HTTP 403, nói rõ Odoo từ chối quyền; không mặc định quy lỗi cho API key.

## 5. Gợi ý bước tiếp theo

Khi kết nối thành công, thông báo **Đã hoàn tất cấu hình kết nối Odoo**, nêu hồ sơ và database nhưng không nêu email/API key. Sau đó gọi `request_user_input` với đúng một câu và các lựa chọn:

1. Xuất báo cáo bán hàng thành CSV — `/odoo2sheet-salereport`.
2. Quản lý hồ sơ, database hoặc thư mục CSV — `/odoo2sheet-help`.
3. Cập nhật plugin — `/odoo2sheet-upgrade`.
4. Sao lưu, dọn dữ liệu hoặc gỡ plugin — `/odoo2sheet-uninstall`.
5. Hoàn tất.

Chờ lựa chọn rồi tiếp tục thẳng vào luồng tương ứng; không yêu cầu người dùng gọi lại slash command.
