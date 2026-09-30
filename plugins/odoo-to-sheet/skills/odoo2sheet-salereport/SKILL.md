---
name: odoo2sheet-salereport
description: Xuất dữ liệu sale.report của Odoo thành CSV với ít câu hỏi nhất. Dùng khi người dùng yêu cầu báo cáo bán hàng hoặc gọi /odoo2sheet-salereport.
---

# Xuất sale.report sang CSV

Luôn trả lời bằng tiếng Việt trừ khi người dùng yêu cầu ngôn ngữ khác. Không mở UI riêng. Không yêu cầu người dùng viết domain Odoo hoặc tên trường kỹ thuật.

## Nguyên tắc HITL

- Dùng toàn bộ thông tin đã có trong yêu cầu và cấu hình; không hỏi lại.
- Tự dùng hồ sơ duy nhất. Chỉ hỏi chọn hồ sơ khi có nhiều; khi đó gọi `request_user_input` nếu host cung cấp, không in menu chữ thay thế.
- Tự ánh xạ cách gọi thông thường sang metadata thật từ Odoo.
- Nếu thiếu nhiều quyết định, gom thành một câu hỏi. Ưu tiên đưa một cấu hình đề xuất hoàn chỉnh để người dùng chỉ cần trả lời **Xuất** hoặc nêu phần muốn sửa.
- Không hỏi xác nhận riêng từng bộ lọc/cột. Một lần xác nhận bản tóm tắt cuối là đủ.

## 1. Kiểm tra sẵn sàng

1. Gọi `get_runtime_status`, sau đó `list_connections`.
2. Nếu không có hồ sơ hoặc hồ sơ thiếu auth/database, thực hiện luồng `/odoo2sheet-start`; không yêu cầu người dùng gọi lại command.
3. Nếu có nhiều hồ sơ, hỏi chọn một lần bằng tên/URL. Nếu có một, dùng luôn.
4. Gọi `check_connection`; nếu lỗi auth, chuyển thẳng sang bước sửa auth của `/odoo2sheet-start`.
5. Gọi `describe_model` với `sale.report`. Nếu không có quyền, nói rõ và dừng; không tự đổi sang model khác.
6. Gọi `get_report_preferences` cho hồ sơ và `sale.report`.

## 2. Lập cấu hình đề xuất

Ưu tiên theo thứ tự:

1. Yêu cầu hiện tại của người dùng.
2. Bộ lọc/cột đã lưu còn hợp lệ.
3. Gợi ý mặc định từ metadata thật.

Quy tắc:

- Nếu người dùng nói không lọc, dùng domain rỗng.
- Nếu chưa có bộ lọc, đề xuất không lọc và giới hạn 10.000 dòng; người dùng có thể sửa trong bước xác nhận.
- Nếu chưa có cột, tự đề xuất một nhóm cột phổ biến thực sự tồn tại: ngày, số đơn, khách hàng, sản phẩm, số lượng, doanh thu và nhân viên bán hàng. Không đưa trường không có trong metadata.
- Nếu cách gọi của người dùng khớp nhiều trường, hỏi đúng một câu để phân biệt. Nếu nhiều trường ngày, hỏi chọn trường ngày cùng khoảng thời gian trong một lượt.
- Khoảng ngày bao gồm ngày cuối dùng `>=` ngày bắt đầu và `<` ngày kế tiếp sau ngày kết thúc.
- Chỉ nhận domain thô khi người dùng chủ động yêu cầu chế độ nâng cao.

## 3. Xác nhận và xuất

Tóm tắt trong một khối ngắn: hồ sơ, bộ lọc, cột CSV, giới hạn dòng và thư mục lưu. Nếu host hỗ trợ `request_user_input`, dùng câu hỏi này với lựa chọn **Xuất ngay** và **Sửa cấu hình**; nếu không thì hỏi trực tiếp: **“Xuất theo cấu hình này hay bạn muốn sửa mục nào?”**

- Nếu người dùng xác nhận, gọi `export_csv` ngay.
- Nếu họ sửa, chỉ cập nhật phần đó, trình bày lại bản tóm tắt mới và xin một lần xác nhận cuối.
- Mặc định tối đa 10.000 dòng, giới hạn cứng 50.000. Nếu chạm giới hạn, báo tệp có thể chưa đủ dữ liệu và gợi ý thu hẹp lọc hoặc tăng giới hạn.
- Sau khi xuất, báo đường dẫn, số dòng, model, bộ lọc và nhãn cột. Không dán dữ liệu vào chat nếu người dùng không yêu cầu.

## 4. Lưu cấu hình

- Nếu người dùng đã yêu cầu lưu cho lần sau, gọi `save_report_preferences` sau khi xuất thành công.
- Nếu cấu hình khác bản đã lưu và người dùng chưa nói, hỏi một câu: **“Lưu cấu hình này cho lần sau không?”**
- Không hỏi nếu họ dùng nguyên cấu hình đã lưu hoặc đã nói chỉ dùng lần này.

Plugin chỉ đọc dữ liệu nghiệp vụ Odoo; phần ghi chỉ gồm CSV và tùy chọn cục bộ.
