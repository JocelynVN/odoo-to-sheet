---
name: odoo2sheet-upgrade
description: Hướng dẫn kiểm tra nguồn cài và cập nhật Odoo To Sheet an toàn. Dùng khi người dùng gọi /odoo2sheet-upgrade hoặc hỏi cách cập nhật plugin.
---

# Cập nhật Odoo To Sheet

Luôn trả lời bằng tiếng Việt trừ khi người dùng yêu cầu ngôn ngữ khác. Hướng dẫn theo cách cài plugin và quyền của người dùng; không khẳng định cập nhật thành công khi chưa có kết quả xác nhận.

## 1. Xác định nguồn cài đặt

Nếu chưa biết nguồn, hỏi người dùng bằng HITL:

**Odoo To Sheet được cài theo cách nào?**

1. Quản trị viên workspace nhập GitHub marketplace để nhiều người cùng dùng.
2. Tôi tự cài hoặc quản lý marketplace cá nhân/local.
3. Tôi không chắc; hãy giúp tôi nhận biết.

Chờ người dùng chọn trước khi đưa hướng dẫn phụ thuộc vào quyền truy cập. Nếu họ không chắc, giải thích: plugin do tổ chức cung cấp chung thường thuộc lựa chọn 1; plugin được cài từ danh mục cá nhân, thư mục repo hoặc marketplace do chính họ quản lý thường thuộc lựa chọn 2. Nếu vẫn chưa rõ, hỏi họ xem ai đã cài plugin hoặc plugin nằm trong workspace chung hay nguồn cá nhân.

## 2. GitHub marketplace dùng chung trong workspace

Marketplace workspace được quản trị viên quản lý. Người dùng thường không thể tự đồng bộ bản dùng chung.

### Nếu người dùng không phải quản trị viên

1. Nói rằng họ cần nhờ quản trị viên workspace đồng bộ marketplace **Odoo To Sheet**.
2. Có thể đưa câu nhắn mẫu: “Bạn vui lòng đồng bộ GitHub marketplace Odoo To Sheet và kiểm tra báo cáo đồng bộ giúp mình được không?”
3. Không yêu cầu người dùng tải source, thay đổi thiết lập workspace hoặc chạy lệnh Terminal.

### Nếu người dùng là quản trị viên workspace

1. Mở **Admin → Plugins → Marketplaces**.
2. Chọn marketplace đang cung cấp Odoo To Sheet; xác nhận đúng repository và Path trước khi đồng bộ.
3. Chọn **Sync now** để yêu cầu đồng bộ ngay thay vì chờ lịch đồng bộ tự động hằng ngày.
4. Chờ hoàn tất rồi mở trạng thái và báo cáo đồng bộ. Chỉ báo thành công khi kết quả xác nhận bản cập nhật đã được xử lý và không có lỗi liên quan đến plugin.
5. Nếu kết quả **Completed — N errors**, giải thích lượt đồng bộ đã chạy nhưng một số plugin gặp lỗi. Đọc báo cáo, nêu lỗi tương ứng với Odoo To Sheet và nhờ người quản lý source sửa rồi đồng bộ lại. Bản mới không hợp lệ có thể khiến ChatGPT giữ phiên bản hoạt động gần nhất.
6. Nếu lỗi quyền GitHub, người quản trị đã nhập marketplace ban đầu cần kiểm tra quyền đọc repository và kết nối GitHub của họ. Nếu thay chủ sở hữu, quản trị viên mới phải nhập cùng nguồn, đường dẫn và ref để các lần sync sau dùng quyền GitHub của người đó.
7. Sau khi trạng thái đồng bộ thành công, mở cuộc trò chuyện mới và kiểm tra skill/tác vụ vừa được cập nhật. Nếu chưa thấy thay đổi, chờ vài phút rồi làm mới ứng dụng và kiểm tra lại báo cáo sync; không nói đã cập nhật chỉ dựa trên việc đã bấm nút.

Không hướng dẫn xóa marketplace để xử lý lỗi sync hoặc để cập nhật một plugin. Xóa marketplace sẽ xóa toàn bộ plugin đã nhập từ marketplace đó; xóa riêng một entry trong source không nhất thiết xóa bản đã nhập trong workspace.

## 3. Plugin cá nhân hoặc source local do người dùng quản lý

1. Hỏi người dùng họ đang dùng marketplace cá nhân dựa trên GitHub hay thư mục plugin local nếu điều đó chưa rõ.
2. Yêu cầu chủ source đưa phiên bản mới vào đúng repository/thư mục mà marketplace đang trỏ tới. Nếu marketplace được ghim vào tag hoặc commit cố định, chủ source cần chuyển sang branch hoặc ref mới theo chính sách của họ trước khi mong đợi nhận commit mới.
3. Với thư mục plugin local, cập nhật nội dung ở đúng thư mục source rồi khởi động lại ChatGPT Desktop để ứng dụng nạp lại tệp. Không yêu cầu Terminal; người dùng có thể cập nhật source bằng công cụ họ vẫn dùng để quản lý dự án.
4. Mở lại Plugins Directory, xác nhận plugin hiện diện trong đúng nguồn, rồi thử skill vừa thay đổi trong cuộc trò chuyện mới.
5. Nếu plugin không xuất hiện hoặc vẫn là bản cũ, hỏi người dùng cho biết nguồn local/personal marketplace và bước nào đã hoàn tất; hướng dẫn kiểm tra đúng đường dẫn source và khởi động lại ứng dụng lần nữa.

## 4. Dữ liệu cục bộ và thư viện tool

- Hồ sơ kết nối và tùy chọn báo cáo nằm trong tệp cấu hình Odoo To Sheet cục bộ; CSV nằm ở các thư mục output của người dùng. Quy trình sync plugin không nhắm tới các vị trí này, nhưng không cam kết với một bản triển khai đã tùy biến.
- MCP launcher của plugin tự kiểm tra và dùng lại `.odoo2shet-env`; thư viện còn thiếu theo `requirements.txt` sẽ được cài bổ sung vào đúng môi trường đó khi MCP server khởi chạy. Không yêu cầu người dùng tự tạo env hoặc cài thư viện qua Terminal.

## Nguồn tham khảo

- [Quản lý và đồng bộ plugin marketplace từ GitHub](https://learn.chatgpt.com/docs/enterprise/plugin-management)
- [Tài liệu plugin local và nạp lại source](https://developers.openai.com/plugins/build/plugins)
