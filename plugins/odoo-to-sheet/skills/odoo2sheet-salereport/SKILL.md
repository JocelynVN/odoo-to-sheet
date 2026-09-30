---
name: odoo2sheet-salereport
description: Xuất dữ liệu báo cáo bán hàng sale.report của Odoo thành CSV. Dùng khi người dùng yêu cầu báo cáo bán hàng hoặc gọi /odoo2sheet-salereport.
---

# Xuất sale.report sang CSV

Luôn trả lời bằng tiếng Việt, trừ khi người dùng yêu cầu rõ ràng ngôn ngữ khác. Không yêu cầu người dùng tự viết domain Odoo hoặc tự liệt kê tên trường kỹ thuật để dùng được luồng cơ bản.

Trước khi chạy tool, MCP launcher tự kiểm tra và dùng lại `.odoo2shet-env`; nếu thiếu dependency theo `requirements.txt`, launcher cài bổ sung vào đúng môi trường. Nếu tool báo runtime chưa sẵn sàng, dừng thao tác và hướng dẫn khởi động lại plugin; không yêu cầu người dùng tự tạo env hoặc cài thư viện qua Terminal.

## Cách hỏi theo HITL

- Tận dụng các bộ lọc, khoảng ngày, cột và giới hạn dòng mà người dùng đã nêu; không hỏi lại điều đã rõ trong yêu cầu.
- Hỏi trong hội thoại, mỗi lượt chỉ hỏi phần còn thiếu hoặc cần người dùng quyết định. Dùng câu ngắn và lựa chọn đánh số; không mở hoặc nhắc đến biểu mẫu UI.
- Bộ lọc và cột đã lưu là gợi ý, không phải sự đồng ý mặc định. Đưa chúng vào phần tóm tắt cuối để người dùng xác nhận hoặc sửa; không hỏi xác nhận riêng cho từng mục đã lưu. Yêu cầu hiện tại luôn được ưu tiên. Nếu người dùng nói xuất không lọc, dùng domain rỗng.
- Chỉ hỏi phần còn thiếu hoặc mơ hồ. Không yêu cầu lại hồ sơ, email hoặc key trong bước xuất báo cáo.
- Giữ lại nhãn và tên trường kỹ thuật Odoo khi cần đối chiếu, nhưng giải thích lựa chọn bằng tiếng Việt.

## Bước 1: chọn dịch vụ Odoo

1. Gọi `list_connections` trước mọi câu trả lời về hồ sơ. Không nói “chưa có hồ sơ” nếu kết quả có kết nối hoặc công cụ bị lỗi.
2. Nếu không có hồ sơ, hướng dẫn người dùng gọi `/odoo2sheet-start` rồi dừng trước khi truy vấn Odoo.
3. Nếu chỉ có một hồ sơ, dùng hồ sơ đó. Nếu có nhiều hồ sơ, hiển thị tên/URL và hỏi người dùng chọn bằng số hoặc tên. Không yêu cầu gửi thông tin đăng nhập.
4. Nếu hồ sơ thiếu URL, email, API key hoặc database theo các cờ trong `list_connections`, hướng dẫn người dùng gọi `/odoo2sheet-start` rồi dừng.
5. Gọi `check_connection`. Nếu xác thực thất bại, hướng dẫn người dùng gọi `/odoo2sheet-start` để nhập lại email/API key; nếu lỗi khác, giải thích đúng lỗi rồi dừng. Chỉ tiếp tục khi `connected=true`.
6. Gọi `describe_model` với `sale.report`. Dùng nhãn, tên kỹ thuật, kiểu, quan hệ và giá trị lựa chọn trả về cho mọi gợi ý sau đó. Nếu Odoo không cho truy cập `sale.report`, nói rõ và dừng; không thay bằng `sale.order` hoặc mô hình khác.
7. Gọi `get_report_preferences` cho hồ sơ đã chọn và `sale.report`.

## Bước 2: chọn bộ lọc

Nếu yêu cầu hiện tại nêu bộ lọc, dùng bộ lọc đó. Nếu người dùng nói xuất không lọc, dùng domain rỗng kể cả khi có bộ lọc đã lưu. Nếu bộ lọc chưa được nói rõ và có bộ lọc đã lưu, dùng nó làm đề xuất trong phần tóm tắt cuối. Nếu chưa có bộ lọc, hỏi người dùng muốn xuất không lọc hay chọn bộ lọc mới. Chỉ gợi ý bộ lọc ứng với trường thực sự có trong metadata `sale.report`, chẳng hạn:

- Khoảng ngày, dựa trên trường ngày phù hợp có trong metadata.
- Trạng thái đơn, dùng đúng các giá trị lựa chọn Odoo trả về.
- Khách hàng, nhân viên bán hàng, đội bán hàng, công ty, sản phẩm hoặc nhóm sản phẩm nếu có trường quan hệ tương ứng.

Khi cần người dùng chọn bộ lọc mới, hãy hỏi ngắn gọn về phần còn thiếu. Nếu có nhiều trường ngày, hỏi họ chọn trường nào trước khi hỏi khoảng ngày. Không tự thêm trạng thái, công ty hay mốc ngày. Với khoảng ngày bao gồm cả ngày cuối, dùng toán tử `>=` cho ngày bắt đầu và `<` cho ngày sau ngày kết thúc. Nếu tiêu chí vẫn mơ hồ, hỏi đúng phần chưa rõ.

Không yêu cầu người dùng nhập domain thô hoặc tự soạn cú pháp. Chỉ nhận domain thô khi họ chủ động yêu cầu thao tác nâng cao bằng domain Odoo.

## Bước 3: chọn các cột CSV

Nếu yêu cầu hiện tại nêu cột, dùng các cột đó. Nếu chưa nêu cột và có cột đã lưu, dùng chúng làm đề xuất trong phần tóm tắt cuối. Nếu chưa có cột đã lưu, trình bày danh sách cột khả dụng từ metadata để người dùng chọn một hay nhiều mục.

Chỉ đưa vào danh sách các trường hiện diện trong metadata. Có thể gợi ý ngày, số đơn, khách hàng, sản phẩm, nhân viên bán hàng, đội bán hàng, số lượng, doanh thu trước thuế, tổng tiền, chiết khấu hoặc biên lợi nhuận khi các trường đó thực sự tồn tại. Hiển thị nhãn dễ hiểu; thêm tên kỹ thuật trong ngoặc nếu giúp phân biệt. Người dùng chọn bằng số hoặc nhiều số, không cần tự gõ tên trường.

Ánh xạ lựa chọn sang tên trường kỹ thuật bằng `describe_model`, xử lý điểm mơ hồ trước khi xuất và chỉ xuất các trường đã chọn. Nếu cột đã lưu không còn tồn tại, báo bằng tiếng Việt và yêu cầu chọn cột mới qua danh sách metadata.

## Bước 4: xuất và lưu thiết lập

Trước khi gọi `export_csv`, tóm tắt trong chat: hồ sơ Odoo, bộ lọc theo ngôn ngữ thường, cột CSV, giới hạn dòng và thư mục lưu. Hỏi người dùng xác nhận xuất hay muốn chỉnh mục nào; chờ câu trả lời rồi mới tiếp tục. Nếu họ muốn chỉnh, chỉ hỏi về phần đó và trình bày lại tóm tắt mới trước khi xuất.

Sau khi người dùng xác nhận, gọi `export_csv` với model `sale.report`, các trường trực tiếp đã chọn, domain đã được người dùng duyệt và thứ tự/giới hạn dòng nếu họ yêu cầu. Mặc định tối đa 10.000 dòng; giới hạn cứng 50.000. Nếu kết quả báo `max_records_reached=true`, nói rõ đã chạm giới hạn và tệp có thể chỉ chứa một phần kết quả; đề nghị thu hẹp bộ lọc hoặc tăng giới hạn tối đa lên 50.000 dòng.

Sau khi xuất thành công, báo đường dẫn tệp, số dòng, model, bộ lọc và nhãn cột bằng tiếng Việt. CSV được lưu trong thư mục của hồ sơ đã chọn; hồ sơ mới mặc định dùng `~/odoo2sheet-output`, được tạo tự động khi cần. Tên mặc định `odoo2sheet-sale-report-YYYYMMDD-HHMMSS.csv`; nếu trùng tên, công cụ thêm số thứ tự, không ghi đè.

Sau khi xuất, nếu người dùng đã yêu cầu lưu cấu hình mới thì gọi `save_report_preferences`. Nếu chưa, hỏi có muốn lưu bộ lọc/cột mới cho lần sau không; chỉ gọi công cụ sau khi họ đồng ý. Không hỏi lưu lại nếu người dùng vừa dùng nguyên cấu hình đã lưu. Nếu họ yêu cầu chỉ dùng lần này, không lưu. Khi cần hỏi:

- **1. Lưu cho lần sau**: gọi `save_report_preferences`, thay thiết lập gần nhất cho hồ sơ/model này.
- **2. Chỉ dùng lần này**: không thay đổi thiết lập đã lưu.

Không dán các dòng dữ liệu bán hàng vào chat trừ khi người dùng yêu cầu xem. Truy cập Odoo chỉ đọc; plugin chỉ ghi CSV và tùy chọn cục bộ trên máy.
