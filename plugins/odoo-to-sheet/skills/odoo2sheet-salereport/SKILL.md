---
name: odoo2sheet-salereport
description: Xuất dữ liệu báo cáo bán hàng sale.report của Odoo thành CSV. Dùng khi người dùng yêu cầu báo cáo bán hàng hoặc gọi /odoo2sheet-salereport.
---

# Xuất sale.report sang CSV

Luôn trả lời bằng tiếng Việt, trừ khi người dùng yêu cầu rõ ràng ngôn ngữ khác. Không yêu cầu người dùng tự viết domain Odoo hoặc tự liệt kê tên trường kỹ thuật để dùng được luồng cơ bản.

## Quy tắc đặt câu hỏi

- Hỏi từng nội dung thành câu ngắn có nhãn riêng; không gộp nhiều yêu cầu vào một đoạn dài. Bộ lọc, cột và việc lưu thiết lập là các câu hỏi riêng.
- Nếu giao diện hỗ trợ câu hỏi có cấu trúc, lựa chọn nhanh hoặc chọn nhiều mục, hãy dùng chúng. Nếu không, đưa danh sách đánh số/ngắn gọn để người dùng chỉ cần trả lời số hoặc chữ; không giả vờ rằng giao diện đang hiện biểu mẫu.
- Khi cần thông tin bổ sung, chỉ hỏi trường còn thiếu. Không yêu cầu lại hồ sơ, email hoặc key trong bước xuất báo cáo.
- Giữ lại nhãn và tên trường kỹ thuật Odoo khi cần đối chiếu, nhưng giải thích lựa chọn bằng tiếng Việt.

## Bước 1: chọn dịch vụ Odoo

1. Gọi `list_connections` trước mọi câu trả lời về hồ sơ. Không nói “chưa có hồ sơ” nếu kết quả có kết nối hoặc công cụ bị lỗi.
2. Nếu không có hồ sơ, hướng dẫn người dùng gọi `/odoo2sheet-connect` rồi dừng trước khi truy vấn Odoo.
3. Nếu chỉ có một hồ sơ, dùng hồ sơ đó. Nếu có nhiều hồ sơ, hiển thị tên/URL và hỏi người dùng chọn bằng số hoặc tên. Không yêu cầu gửi thông tin đăng nhập.
4. Gọi `describe_model` với `sale.report`. Dùng nhãn, tên kỹ thuật, kiểu, quan hệ và giá trị lựa chọn trả về cho mọi gợi ý sau đó. Nếu Odoo không cho truy cập `sale.report`, nói rõ và dừng; không thay bằng `sale.order` hoặc mô hình khác.
   - Nếu lỗi nêu rõ hồ sơ thiếu database, hỏi riêng tên database bằng một câu hỏi tiếng Việt. Sau khi người dùng cung cấp, gọi `update_connection` để lưu database mà không yêu cầu API key; sau đó gọi lại `describe_model`.
   - Với lỗi khác, diễn giải lỗi bằng tiếng Việt, giữ nguyên các chi tiết kỹ thuật cần thiết.
5. Gọi `get_report_preferences` cho hồ sơ đã chọn và `sale.report`.

## Bước 2: chọn bộ lọc

Nếu có thiết lập đã lưu, tóm tắt bộ lọc bằng ngôn ngữ thường và hỏi một câu riêng với các lựa chọn:

- **1. Dùng lại bộ lọc đã lưu**
- **2. Xuất không lọc**
- **3. Chọn bộ lọc mới**

Nếu chưa có thiết lập đã lưu, hỏi người dùng muốn xuất không lọc hay chọn bộ lọc mới. Chỉ gợi ý bộ lọc ứng với trường thực sự có trong metadata `sale.report`, chẳng hạn:

- Khoảng ngày, dựa trên trường ngày phù hợp có trong metadata.
- Trạng thái đơn, dùng đúng các giá trị lựa chọn Odoo trả về.
- Khách hàng, nhân viên bán hàng, đội bán hàng, công ty, sản phẩm hoặc nhóm sản phẩm nếu có trường quan hệ tương ứng.

Khi người dùng chọn bộ lọc mới, hãy hướng dẫn bằng các câu hỏi riêng. Nếu có nhiều trường ngày, hỏi họ chọn trường nào trước khi hỏi khoảng ngày. Không tự thêm trạng thái, công ty hay mốc ngày. Với khoảng ngày bao gồm cả ngày cuối, dùng toán tử `>=` cho ngày bắt đầu và `<` cho ngày sau ngày kết thúc. Nếu tiêu chí vẫn mơ hồ, hỏi đúng phần chưa rõ.

Không yêu cầu người dùng nhập domain thô hoặc tự soạn cú pháp. Chỉ nhận domain thô khi họ chủ động yêu cầu thao tác nâng cao bằng domain Odoo.

## Bước 3: chọn các cột CSV

Hỏi riêng về cột, sau khi đã xác nhận bộ lọc:

- Nếu có cột đã lưu: **1. Dùng lại các cột đã lưu** hoặc **2. Chọn cột mới**.
- Nếu chưa có cột đã lưu: trình bày danh sách cột khả dụng từ metadata để người dùng chọn một hay nhiều mục.

Chỉ đưa vào danh sách các trường hiện diện trong metadata. Có thể gợi ý ngày, số đơn, khách hàng, sản phẩm, nhân viên bán hàng, đội bán hàng, số lượng, doanh thu trước thuế, tổng tiền, chiết khấu hoặc biên lợi nhuận khi các trường đó thực sự tồn tại. Hiển thị nhãn dễ hiểu; thêm tên kỹ thuật trong ngoặc nếu giúp phân biệt. Người dùng chọn bằng số hoặc nhiều số, không cần tự gõ tên trường.

Ánh xạ lựa chọn sang tên trường kỹ thuật bằng `describe_model`, xử lý điểm mơ hồ trước khi xuất và chỉ xuất các trường đã chọn. Nếu cột đã lưu không còn tồn tại, báo bằng tiếng Việt và yêu cầu chọn cột mới qua danh sách metadata.

## Bước 4: xuất và lưu thiết lập

Gọi `export_csv` với model `sale.report`, các trường trực tiếp đã chọn, domain đã được người dùng duyệt và thứ tự/giới hạn dòng nếu họ yêu cầu. Mặc định tối đa 10.000 dòng; giới hạn cứng 50.000.

Sau khi xuất thành công, báo đường dẫn tệp, số dòng, model, bộ lọc và nhãn cột bằng tiếng Việt. CSV được lưu trong thư mục của hồ sơ đã chọn; hồ sơ mới mặc định dùng `~/odoo2sheet-output`, được tạo tự động khi cần. Tên mặc định `odoo2sheet-sale-report-YYYYMMDD-HHMMSS.csv`; nếu trùng tên, công cụ thêm số thứ tự, không ghi đè.

Cuối cùng hỏi riêng người dùng có lưu bộ lọc và cột cho lần sau không:

- **1. Lưu cho lần sau**: gọi `save_report_preferences`, thay thiết lập gần nhất cho hồ sơ/model này.
- **2. Chỉ dùng lần này**: không thay đổi thiết lập đã lưu.

Không dán các dòng dữ liệu bán hàng vào chat trừ khi người dùng yêu cầu xem. Truy cập Odoo chỉ đọc; plugin chỉ ghi CSV và tùy chọn cục bộ trên máy.
