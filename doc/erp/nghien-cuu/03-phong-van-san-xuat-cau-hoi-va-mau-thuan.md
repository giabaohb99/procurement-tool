# PHỎNG VẤN SẢN XUẤT: CÂU HỎI, CÂU TRẢ LỜI VÀ MÂU THUẪN CẦN CHỐT

| | |
|---|---|
| Phiên bản | **1.0** — 24/10/2026 |
| Người lập | A5 Nghiên cứu nghiệp vụ |
| Nguồn | Dự án *Khảo sát hiện trạng Quản lý sản xuất (19/10/2026)* trên ứng dụng khảo sát Make It Clear (MIC), Phòng Sản xuất |
| Ảnh chụp dữ liệu | 24/10/2026 08:59 giờ Việt Nam. Khảo sát còn mở, còn 9 vòng chưa nộp |
| Dùng để | Gửi Phòng Sản xuất đọc lại, chốt các chỗ mâu thuẫn ở Phần A, sửa câu trả lời nào ghi chưa đúng |
| Bản Excel | [`03-mau-thuan-san-xuat.xlsx`](./03-mau-thuan-san-xuat.xlsx): sheet *Mâu thuẫn* để điền trả lời, sheet *Câu hỏi* cùng dữ liệu Phần C |
| Đọc kèm | [`02-phan-tich-khao-sat-hien-trang-san-xuat.md`](./02-phan-tich-khao-sat-hien-trang-san-xuat.md) |

> Có 3 điểm nhạy cảm về chứng từ và thuế với NCC gia công. Không ghi trong tài liệu này, trao đổi riêng.

## Cách đọc

- **Câu hỏi** ở đây là các ô thông tin MIC thu thập cho từng bước, ví dụ *Ai chịu trách nhiệm cuối*, *Bắt đầu khi nào*. Trang quản trị MIC không trả về nguyên văn câu hỏi đã hỏi từng người, chỉ trả về câu trả lời đã ghi vào từng ô. Mỗi câu trả lời ghi rõ ai nói, vòng nào, câu nào.
- **V2 · C4** nghĩa là vòng 2, câu 4 của người đó.
- **as-is (thực tế)**: người trả lời nói rõ hiện trạng. **giả thuyết**: MIC suy ra từ câu trả lời, chưa được xác nhận; dòng ghi *Suy diễn (AI)* là loại này. **to-be (đã chốt)**: giá trị đã được người quản trị khảo sát chốt.
- **Độ tin** cao / vừa / thấp do MIC chấm.
- Mã **M01…M13** là mâu thuẫn MIC đã đánh dấu, đang chờ phân xử. Mã **L01…L12** là chỗ lệch A5 đọc chéo tìm thêm, MIC chưa đánh dấu. Dưới mỗi câu trả lời có liên quan sẽ ghi mã đó.
- Ngoài 13 mục chờ phân xử, MIC còn một mâu thuẫn đã chốt ngày 22/10 (người giữ vị trí Trưởng phòng), ghi ở mục 8 Phần C.

---

## Phần A. Mâu thuẫn cần Phòng Sản xuất chốt

Mục M01 đến M13 chép đúng nguyên văn màn *Mâu thuẫn & quyết định* trên MIC: tiêu đề, đường dẫn, nhãn, nguồn, trích dẫn và nhận định của AI. Phần *Câu cần chốt*, *Người chốt đề nghị* và *Ghi chú của A5* do A5 thêm. Mục L01 đến L12 do A5 tìm thêm, MIC chưa đánh dấu.

| Mã | Tiêu đề | Trạng thái | Người chốt đề nghị |
|---|---|---|---|
| M01 | Thẩm quyền quyết định cuối cùng khi đơn hàng vướng mắc điều kiện triển khai: Trưởng phòng Sản xuất vs Phòng Kinh doanh | Chờ phân xử | Trưởng phòng Sản xuất, Giám đốc (hỏi ý Phòng Kinh doanh) |
| M02 | Thẩm quyền quyết định cuối cùng khi đơn hàng vướng mắc điều kiện triển khai: Trưởng phòng Sản xuất vs Phòng Kinh doanh | Chờ phân xử | Trưởng phòng Sản xuất, Giám đốc (hỏi ý Phòng Kinh doanh) |
| M03 | Ai chịu trách nhiệm cuối: hai nguồn nói khác nhau | Chờ phân xử | Trưởng phòng Sản xuất, Giám đốc (hỏi ý Phòng Kinh doanh) |
| M04 | Người có thẩm quyền quyết định cuối cùng khi tồn kho VTBB không đủ: Trưởng phòng Sản xuất vs Phòng Kinh doanh | Chờ phân xử | Trưởng phòng Sản xuất, Giám đốc (hỏi ý Phòng Kinh doanh) |
| M05 | Ai chịu trách nhiệm cuối: hai nguồn nói khác nhau | Chờ phân xử | Trưởng phòng Sản xuất, Giám đốc (hỏi ý Phòng Kinh doanh) |
| M06 | Thẩm quyền quyết định khi đơn hàng chưa đáp ứng điều kiện triển khai: Trưởng phòng Sản xuất vs Phối hợp giữa Phòng Kinh doanh và Quản lý | Chờ phân xử | Trưởng phòng Sản xuất, Giám đốc (hỏi ý Phòng Kinh doanh) |
| M07 | Ai chịu trách nhiệm cuối: hai nguồn nói khác nhau | Chờ phân xử | Trưởng phòng Sản xuất, Giám đốc (hỏi ý Phòng Kinh doanh) |
| M08 | Đầu mối nhận Phiếu yêu cầu điều chuyển nguyên liệu để làm việc với NCC GC: Điều phối thành phẩm vs Quản lý dữ liệu | Chờ phân xử | Trưởng nhóm Điều phối |
| M09 | Người có thẩm quyền quyết định khi điều kiện đơn hàng không đạt: Phòng Kinh doanh vs Quản lý sản xuất | Chờ phân xử | Trưởng phòng Sản xuất, Giám đốc (hỏi ý Phòng Kinh doanh) |
| M10 | Ai chịu trách nhiệm cuối: hai nguồn nói khác nhau | Chờ phân xử | Trưởng phòng Sản xuất, Giám đốc (hỏi ý Phòng Kinh doanh) |
| M11 | Người có thẩm quyền quyết định khi điều kiện đơn hàng không đạt: Phòng Kinh doanh vs Quản lý sản xuất | Chờ phân xử | Trưởng phòng Sản xuất, Giám đốc (hỏi ý Phòng Kinh doanh) |
| M12 | Thẩm quyền phê duyệt chi phí phát sinh ngoài ngân sách: Trưởng phòng cho rằng không cần duyệt vs Giám đốc quy định phải trình Giám đốc công ty thành viên phê duyệt | Chờ phân xử | Giám đốc, Trưởng phòng Sản xuất, Phòng Tài chính Kế toán |
| M13 | Việc nào phải xin duyệt, ai duyệt, ngưỡng nào: hai nguồn nói khác nhau | Đã hỏi lại hai bên | Trưởng phòng Sản xuất |
| L01 | Bao lâu một lần (số đơn) | A5 tìm thêm, chưa có trên MIC | Trưởng nhóm Điều phối, Chuyên viên Điều phối sản xuất |
| L02 | Việc nào phải xin duyệt, ai duyệt, ngưỡng nào | A5 tìm thêm, chưa có trên MIC | Giám đốc, Phòng Tài chính Kế toán |
| L03 | Phiếu điều chuyển nguyên liệu gửi cho ai | A5 tìm thêm, chưa có trên MIC | Chuyên viên Điều phối nguyên liệu/bán thành phẩm |
| L04 | Ai chịu trách nhiệm cuối | A5 tìm thêm, chưa có trên MIC | Trưởng phòng Sản xuất |
| L05 | Ai quyết phương án khi hàng lỗi | A5 tìm thêm, chưa có trên MIC | Trưởng phòng Sản xuất |
| L06 | Các bước theo thứ tự | A5 tìm thêm, chưa có trên MIC | Trưởng phòng Sản xuất |
| L07 | Ai ký hợp đồng NCC GC mới | A5 tìm thêm, chưa có trên MIC | Giám đốc |
| L08 | Toàn trình mất bao lâu | A5 tìm thêm, chưa có trên MIC | Trưởng nhóm Điều phối |
| L09 | Số trạng thái theo dõi đơn | A5 tìm thêm, chưa có trên MIC | Trưởng nhóm Điều phối |
| L10 | Ai kiểm chất lượng thành phẩm khi nhận | A5 tìm thêm, chưa có trên MIC | Trưởng nhóm Điều phối, Kho, Lab |
| L11 | Ai đang giữ vị trí Chuyên viên Pháp lý - Xử lý sự cố | A5 tìm thêm, chưa có trên MIC | Trưởng phòng Sản xuất |
| L12 | Tuyến báo cáo của Chuyên viên Điều phối NL/BTP | A5 tìm thêm, chưa có trên MIC | Trưởng phòng Sản xuất |

**Cụm lớn nhất:** M01 đến M07 và M09 đến M11 (10 mục) cùng hỏi một câu: khi đơn hàng không đủ điều kiện triển khai thì ai quyết cuối. Chốt một lần là đóng được cả 10 mục.

### Các mâu thuẫn trên MIC

#### M01. Thẩm quyền quyết định cuối cùng khi đơn hàng vướng mắc điều kiện triển khai: Trưởng phòng Sản xuất vs Phòng Kinh doanh

`Quản lý đơn hàng sản xuất gia công tại nhà cung cấp › Bước 3 · Kiểm tra điều kiện triển khai đơn hàng › Ai chịu trách nhiệm cuối`

Trạng thái: **Chờ phân xử**

| giả thuyết | as-is · thực tế |
|---|---|
| Suy diễn (AI) · Chuyên viên Điều phối vật tư bao bì · V4 · C1 | Trưởng nhóm Quản lý dữ liệu · V6 · C1 |
| “Trưởng phòng sản xuất (khi các phương án kiểm tra tồn kho luân chuyển nội bộ, thương lượng Kinh doanh dời ngày và trao đổi Thu mua mua hàng không giải quyết được)” | “Phòng Kinh doanh là đơn vị xem xét và quyết định việc tiếp tục triển khai hoặc tạm dừng đơn hàng khi kiểm tra điều kiện có vướng mắc; Điều phối thành phẩm phối hợp kiểm tra và thông báo” |
| Chuyên viên Điều phối vật tư bao bì, vòng 4 | Trưởng nhóm Quản lý dữ liệu, vòng 6 |

**Nhận định của AI**

> Chuyên viên Điều phối VTBB làm rõ khi các phương án nội bộ, dời ngày và mua thêm không giải quyết được sẽ trình Trưởng phòng sản xuất quyết định cuối cùng, trong khi Trưởng nhóm Quản lý dữ liệu khẳng định Phòng Kinh doanh xem xét và quyết định việc tiếp tục triển khai hoặc tạm dừng đơn hàng.
>
> Phát hiện ngày 23/10/2026

- **Câu cần chốt:** Khi đơn hàng không đủ điều kiện triển khai, ai quyết cuối cho đi tiếp hay dừng? Đề xuất chia theo loại vướng mắc: pháp lý và cung ứng nội bộ do Trưởng phòng quyết; dời ngày giao hoặc hủy đơn với khách do Phòng Kinh doanh quyết; hai bên không thống nhất thì Giám đốc. Xác nhận hoặc sửa.
- **Người chốt đề nghị:** Trưởng phòng Sản xuất, Giám đốc (hỏi ý Phòng Kinh doanh)
- **Trả lời của Sản xuất:** ............................................................
- **Ghi chú của A5:** Nguồn A là giả thuyết MIC suy ra từ câu trả lời, chưa được người trả lời xác nhận (độ tin thấp). Nguồn B là as-is, độ tin cao. Theo nguồn A, thiếu VTBB thì lần lượt luân chuyển nội bộ, xin KD dời ngày, nhờ Thu mua mua thêm; không xong mới trình Trưởng phòng.

#### M02. Thẩm quyền quyết định cuối cùng khi đơn hàng vướng mắc điều kiện triển khai: Trưởng phòng Sản xuất vs Phòng Kinh doanh

`Quản lý đơn hàng sản xuất gia công tại nhà cung cấp › Bước 3 · Kiểm tra điều kiện triển khai đơn hàng › Ai chịu trách nhiệm cuối`

Trạng thái: **Chờ phân xử**

| as-is · thực tế | as-is · thực tế |
|---|---|
| Chị Ngân · V3 · C4 | Trưởng nhóm Quản lý dữ liệu · V6 · C1 |
| “Trưởng phòng (Quản lý sản xuất) chịu trách nhiệm cuối quyết định duyệt cho đơn hàng triển khai (kể cả trường hợp duyệt trước bổ sung sau)” | “Phòng Kinh doanh là đơn vị xem xét và quyết định việc tiếp tục triển khai hoặc tạm dừng đơn hàng khi kiểm tra điều kiện có vướng mắc; Điều phối thành phẩm phối hợp kiểm tra và thông báo” |
| Trưởng phòng, vòng 3 | Trưởng nhóm Quản lý dữ liệu, vòng 6 |

**Nhận định của AI**

> Chị Ngân khẳng định Trưởng phòng chịu trách nhiệm cuối duyệt triển khai hoặc hoãn đơn hàng (kể cả duyệt trước bổ sung sau), trong khi Trưởng nhóm Quản lý dữ liệu khẳng định Phòng Kinh doanh là đơn vị xem xét và quyết định việc tiếp tục triển khai hoặc tạm dừng đơn hàng.
>
> Phát hiện ngày 23/10/2026

- **Câu cần chốt:** Khi đơn hàng không đủ điều kiện triển khai, ai quyết cuối cho đi tiếp hay dừng? Đề xuất chia theo loại vướng mắc: pháp lý và cung ứng nội bộ do Trưởng phòng quyết; dời ngày giao hoặc hủy đơn với khách do Phòng Kinh doanh quyết; hai bên không thống nhất thì Giám đốc. Xác nhận hoặc sửa.
- **Người chốt đề nghị:** Trưởng phòng Sản xuất, Giám đốc (hỏi ý Phòng Kinh doanh)
- **Trả lời của Sản xuất:** ............................................................
- **Ghi chú của A5:** Cả hai là as-is. Trưởng phòng nói Trưởng phòng quyết cuối, kể cả duyệt trước bổ sung sau. Trưởng nhóm QLDL nói KD quyết.

#### M03. Ai chịu trách nhiệm cuối: hai nguồn nói khác nhau

`Quản lý đơn hàng sản xuất gia công tại nhà cung cấp › Bước 3 · Kiểm tra điều kiện triển khai đơn hàng › Ai chịu trách nhiệm cuối`

Trạng thái: **Chờ phân xử**

| as-is · thực tế | as-is · thực tế |
|---|---|
| Trưởng nhóm Điều phối · V2 · C4 | Trưởng nhóm Quản lý dữ liệu · V6 · C1 |
| “Quản lý sản xuất là người quyết định cuối cùng (cho duyệt trước bổ sung sau hoặc tạm ngưng đơn) dựa trên dữ liệu kiểm tra từ các nhóm nội bộ; Trưởng nhóm Điều phối cập nhật tiến độ lại cho Kinh doanh” | “Phòng Kinh doanh là đơn vị xem xét và quyết định việc tiếp tục triển khai hoặc tạm dừng đơn hàng khi kiểm tra điều kiện có vướng mắc; Điều phối thành phẩm phối hợp kiểm tra và thông báo” |
| Trưởng nhóm Điều phối, vòng 2 | Trưởng nhóm Quản lý dữ liệu, vòng 6 |

**Nhận định của AI**

> "Quản lý sản xuất là người quyết định cuối cùng (cho duyệt trước bổ sung sau hoặc tạm ngưng đơn) dựa trên dữ liệu kiểm tra từ các nhóm nội bộ; Trưởng nhóm Điều phối cập nhật tiến độ lại cho Kinh doanh" (Trưởng nhóm Điều phối · V2 · C4) khác "Phòng Kinh doanh là đơn vị xem xét và quyết định việc tiếp tục triển khai hoặc tạm dừng đơn hàng khi kiểm tra điều kiện có vướng mắc; Điều phối thành phẩm phối hợp kiểm tra và thông báo" (Trưởng nhóm Quản lý dữ liệu · V6 · C1).
>
> Phát hiện ngày 23/10/2026

- **Câu cần chốt:** Khi đơn hàng không đủ điều kiện triển khai, ai quyết cuối cho đi tiếp hay dừng? Đề xuất chia theo loại vướng mắc: pháp lý và cung ứng nội bộ do Trưởng phòng quyết; dời ngày giao hoặc hủy đơn với khách do Phòng Kinh doanh quyết; hai bên không thống nhất thì Giám đốc. Xác nhận hoặc sửa.
- **Người chốt đề nghị:** Trưởng phòng Sản xuất, Giám đốc (hỏi ý Phòng Kinh doanh)
- **Trả lời của Sản xuất:** ............................................................
- **Ghi chú của A5:** Cả hai là as-is, độ tin cao. Hai trưởng nhóm nói hai người quyết khác nhau. Theo danh sách vị trí trên MIC, Trưởng nhóm Điều phối đang do Trưởng phòng kiêm nhiệm.

#### M04. Người có thẩm quyền quyết định cuối cùng khi tồn kho VTBB không đủ: Trưởng phòng Sản xuất vs Phòng Kinh doanh

`Quản lý đơn hàng sản xuất gia công tại nhà cung cấp › Bước 3 · Kiểm tra điều kiện triển khai đơn hàng › Ai chịu trách nhiệm cuối`

Trạng thái: **Chờ phân xử**

| as-is · thực tế | as-is · thực tế |
|---|---|
| Chị Ngân · V3 · C4 | Chuyên viên Điều phối vật tư bao bì · V3 · C3 |
| “Trưởng phòng (Quản lý sản xuất) chịu trách nhiệm cuối quyết định duyệt cho đơn hàng triển khai (kể cả trường hợp duyệt trước bổ sung sau)” | “Trưởng phòng sản xuất hoặc Phòng Kinh doanh quyết định cuối cùng về việc duyệt tiếp hay dừng đơn khi tồn kho VTBB không đủ hoặc không kịp tiến độ đơn hàng” |
| Trưởng phòng, vòng 3 | Chuyên viên Điều phối vật tư bao bì, vòng 3 |

**Nhận định của AI**

> Chuyên viên Điều phối VTBB cho biết khi thiếu VTBB thì thẩm quyền thuộc Trưởng phòng sản xuất / Kinh doanh, chưa phân định rạch ròi vai trò quyết định cuối cùng giữa hai bên trong trường hợp có bất đồng ý kiến.
>
> Phát hiện ngày 23/10/2026

- **Câu cần chốt:** Khi đơn hàng không đủ điều kiện triển khai, ai quyết cuối cho đi tiếp hay dừng? Đề xuất chia theo loại vướng mắc: pháp lý và cung ứng nội bộ do Trưởng phòng quyết; dời ngày giao hoặc hủy đơn với khách do Phòng Kinh doanh quyết; hai bên không thống nhất thì Giám đốc. Xác nhận hoặc sửa.
- **Người chốt đề nghị:** Trưởng phòng Sản xuất, Giám đốc (hỏi ý Phòng Kinh doanh)
- **Trả lời của Sản xuất:** ............................................................
- **Ghi chú của A5:** Chuyên viên VTBB nói Trưởng phòng hoặc KD, chưa phân định khi hai bên bất đồng.

#### M05. Ai chịu trách nhiệm cuối: hai nguồn nói khác nhau

`Quản lý đơn hàng sản xuất gia công tại nhà cung cấp › Bước 3 · Kiểm tra điều kiện triển khai đơn hàng › Ai chịu trách nhiệm cuối`

Trạng thái: **Chờ phân xử**

| as-is · thực tế | as-is · thực tế |
|---|---|
| Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V2 · C2 | Chuyên viên Điều phối vật tư bao bì · V3 · C3 |
| “Phòng Kinh doanh xem xét và quyết định phương án duyệt hoặc hoãn đơn hàng khi NL/BTP không đủ hoặc không kịp tiến độ” | “Trưởng phòng sản xuất hoặc Phòng Kinh doanh quyết định cuối cùng về việc duyệt tiếp hay dừng đơn khi tồn kho VTBB không đủ hoặc không kịp tiến độ đơn hàng” |
| Chuyên viên Điều phối nguyên liệu/bán thành phẩm, vòng 2 | Chuyên viên Điều phối vật tư bao bì, vòng 3 |

**Nhận định của AI**

> "Phòng Kinh doanh xem xét và quyết định phương án duyệt hoặc hoãn đơn hàng khi NL/BTP không đủ hoặc không kịp tiến độ" (Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V2 · C2) khác "Trưởng phòng sản xuất hoặc Phòng Kinh doanh quyết định cuối cùng về việc duyệt tiếp hay dừng đơn khi tồn kho VTBB không đủ hoặc không kịp tiến độ đơn hàng" (Chuyên viên Điều phối vật tư bao bì · V3 · C3).
>
> Phát hiện ngày 23/10/2026

- **Câu cần chốt:** Khi đơn hàng không đủ điều kiện triển khai, ai quyết cuối cho đi tiếp hay dừng? Đề xuất chia theo loại vướng mắc: pháp lý và cung ứng nội bộ do Trưởng phòng quyết; dời ngày giao hoặc hủy đơn với khách do Phòng Kinh doanh quyết; hai bên không thống nhất thì Giám đốc. Xác nhận hoặc sửa.
- **Người chốt đề nghị:** Trưởng phòng Sản xuất, Giám đốc (hỏi ý Phòng Kinh doanh)
- **Trả lời của Sản xuất:** ............................................................
- **Ghi chú của A5:** Chuyên viên NL/BTP nói KD quyết khi thiếu NL/BTP. Chuyên viên VTBB nói Trưởng phòng hoặc KD khi thiếu VTBB.

#### M06. Thẩm quyền quyết định khi đơn hàng chưa đáp ứng điều kiện triển khai: Trưởng phòng Sản xuất vs Phối hợp giữa Phòng Kinh doanh và Quản lý

`Quản lý đơn hàng sản xuất gia công tại nhà cung cấp › Bước 3 · Kiểm tra điều kiện triển khai đơn hàng › Ai chịu trách nhiệm cuối`

Trạng thái: **Chờ phân xử**

| as-is · thực tế | as-is · thực tế |
|---|---|
| Chị Ngân · V3 · C4 | Trưởng nhóm Quản lý dữ liệu · V3 · C1 |
| “Trưởng phòng (Quản lý sản xuất) chịu trách nhiệm cuối quyết định duyệt cho đơn hàng triển khai (kể cả trường hợp duyệt trước bổ sung sau)” | “Nhân sự phụ trách thông báo trực tiếp cho Phòng Kinh doanh và Quản lý để xem xét, quyết định tiếp tục triển khai hoặc tạm dừng đơn hàng khi điều kiện triển khai chưa đáp ứng” |
| Trưởng phòng, vòng 3 | Trưởng nhóm Quản lý dữ liệu, vòng 3 |

**Nhận định của AI**

> Trưởng phòng Ngân khẳng định Trưởng phòng là người chịu trách nhiệm cuối quyết định duyệt cho đơn hàng triển khai hoặc bổ sung sau, trong khi Trưởng nhóm Quản lý dữ liệu cho rằng nhân sự thông báo cho cả Phòng Kinh doanh và Quản lý cùng xem xét, quyết định.
>
> Phát hiện ngày 23/10/2026

- **Câu cần chốt:** Khi đơn hàng không đủ điều kiện triển khai, ai quyết cuối cho đi tiếp hay dừng? Đề xuất chia theo loại vướng mắc: pháp lý và cung ứng nội bộ do Trưởng phòng quyết; dời ngày giao hoặc hủy đơn với khách do Phòng Kinh doanh quyết; hai bên không thống nhất thì Giám đốc. Xác nhận hoặc sửa.
- **Người chốt đề nghị:** Trưởng phòng Sản xuất, Giám đốc (hỏi ý Phòng Kinh doanh)
- **Trả lời của Sản xuất:** ............................................................
- **Ghi chú của A5:** Trưởng phòng nói mình quyết. Trưởng nhóm QLDL (vòng 3) nói báo cả KD và Quản lý cùng xem xét.

#### M07. Ai chịu trách nhiệm cuối: hai nguồn nói khác nhau

`Quản lý đơn hàng sản xuất gia công tại nhà cung cấp › Bước 3 · Kiểm tra điều kiện triển khai đơn hàng › Ai chịu trách nhiệm cuối`

Trạng thái: **Chờ phân xử**

| as-is · thực tế | as-is · thực tế |
|---|---|
| Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V2 · C2 | Trưởng nhóm Quản lý dữ liệu · V3 · C1 |
| “Phòng Kinh doanh xem xét và quyết định phương án duyệt hoặc hoãn đơn hàng khi NL/BTP không đủ hoặc không kịp tiến độ” | “Nhân sự phụ trách thông báo trực tiếp cho Phòng Kinh doanh và Quản lý để xem xét, quyết định tiếp tục triển khai hoặc tạm dừng đơn hàng khi điều kiện triển khai chưa đáp ứng” |
| Chuyên viên Điều phối nguyên liệu/bán thành phẩm, vòng 2 | Trưởng nhóm Quản lý dữ liệu, vòng 3 |

**Nhận định của AI**

> "Phòng Kinh doanh xem xét và quyết định phương án duyệt hoặc hoãn đơn hàng khi NL/BTP không đủ hoặc không kịp tiến độ" (Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V2 · C2) khác "Nhân sự phụ trách thông báo trực tiếp cho Phòng Kinh doanh và Quản lý để xem xét, quyết định tiếp tục triển khai hoặc tạm dừng đơn hàng khi điều kiện triển khai chưa đáp ứng" (Trưởng nhóm Quản lý dữ liệu · V3 · C1).
>
> Phát hiện ngày 23/10/2026

- **Câu cần chốt:** Khi đơn hàng không đủ điều kiện triển khai, ai quyết cuối cho đi tiếp hay dừng? Đề xuất chia theo loại vướng mắc: pháp lý và cung ứng nội bộ do Trưởng phòng quyết; dời ngày giao hoặc hủy đơn với khách do Phòng Kinh doanh quyết; hai bên không thống nhất thì Giám đốc. Xác nhận hoặc sửa.
- **Người chốt đề nghị:** Trưởng phòng Sản xuất, Giám đốc (hỏi ý Phòng Kinh doanh)
- **Trả lời của Sản xuất:** ............................................................
- **Ghi chú của A5:** KD quyết, so với KD và Quản lý cùng quyết.

#### M08. Đầu mối nhận Phiếu yêu cầu điều chuyển nguyên liệu để làm việc với NCC GC: Điều phối thành phẩm vs Quản lý dữ liệu

`Quản lý đơn hàng sản xuất gia công tại nhà cung cấp › Bước 4 · Chuẩn bị nguồn lực và hoàn thiện điều kiện đặt hàng › Làm ra gì, giao cho ai, qua kênh nào`

Trạng thái: **Chờ phân xử**

| as-is · thực tế | as-is · thực tế |
|---|---|
| Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V2 · C5 | Trưởng nhóm Điều phối · V4 · C1 |
| “Phiếu yêu cầu điều chuyển nguyên liệu được lập và gửi cho Điều phối thành phẩm để gửi tiếp cho NCC GC phối hợp xuất và điều chuyển” | “Chuyên viên Quản lý hồ sơ sản xuất và Dữ liệu NCC GC làm đầu mối giao dịch với NCC GC về việc điều chuyển nguyên liệu” |
| Chuyên viên Điều phối nguyên liệu/bán thành phẩm, vòng 2 | Trưởng nhóm Điều phối, vòng 4 |

**Nhận định của AI**

> Chuyên viên NL/BTP nêu Phiếu điều chuyển gửi cho Điều phối thành phẩm để gửi tiếp NCC GC, trong khi Trưởng nhóm Điều phối khẳng định Điều phối thành phẩm chỉ nhận thông tin đủ hàng và việc giao dịch với NCC GC phải do Quản lý dữ liệu thực hiện.
>
> Phát hiện ngày 23/10/2026

- **Câu cần chốt:** Phiếu yêu cầu điều chuyển nguyên liệu gửi cho ai, và ai là đầu mối làm việc với NCC GC về điều chuyển: Điều phối thành phẩm hay Chuyên viên Quản lý hồ sơ SX và Dữ liệu NCC GC?
- **Người chốt đề nghị:** Trưởng nhóm Điều phối
- **Trả lời của Sản xuất:** ............................................................
- **Ghi chú của A5:** Thêm nguồn thứ ba: Chuyên viên Điều phối sản xuất V3 C2 nói mình nhận phiếu điều chuyển để làm việc với NCC GC.

#### M09. Người có thẩm quyền quyết định khi điều kiện đơn hàng không đạt: Phòng Kinh doanh vs Quản lý sản xuất

`Quản lý đơn hàng sản xuất gia công tại nhà cung cấp › Bước 3 · Kiểm tra điều kiện triển khai đơn hàng › Ai chịu trách nhiệm cuối`

Trạng thái: **Chờ phân xử**

| as-is · thực tế | as-is · thực tế |
|---|---|
| Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V2 · C2 | Chuyên viên Pháp lý - Xử lý sự cố · V3 · C1 |
| “Phòng Kinh doanh xem xét và quyết định phương án duyệt hoặc hoãn đơn hàng khi NL/BTP không đủ hoặc không kịp tiến độ” | “Quản lý sản xuất là người quyết định cuối cùng việc duyệt cho đơn hàng triển khai hay không khi hồ sơ pháp lý chưa đạt hoặc chưa đủ” |
| Chuyên viên Điều phối nguyên liệu/bán thành phẩm, vòng 2 | Chuyên viên Pháp lý - Xử lý sự cố, vòng 3 |

**Nhận định của AI**

> Chuyên viên Điều phối NL/BTP (r_6) nêu Phòng Kinh doanh quyết định duyệt hoặc hoãn đơn, trong khi Chuyên viên Pháp lý - Xử lý sự cố (r_8) xác nhận Quản lý sản xuất là người quyết định cho đi đơn hàng hay dừng lại.
>
> Phát hiện ngày 23/10/2026

- **Câu cần chốt:** Khi đơn hàng không đủ điều kiện triển khai, ai quyết cuối cho đi tiếp hay dừng? Đề xuất chia theo loại vướng mắc: pháp lý và cung ứng nội bộ do Trưởng phòng quyết; dời ngày giao hoặc hủy đơn với khách do Phòng Kinh doanh quyết; hai bên không thống nhất thì Giám đốc. Xác nhận hoặc sửa.
- **Người chốt đề nghị:** Trưởng phòng Sản xuất, Giám đốc (hỏi ý Phòng Kinh doanh)
- **Trả lời của Sản xuất:** ............................................................
- **Ghi chú của A5:** KD quyết khi thiếu NL/BTP, so với Quản lý sản xuất quyết khi hồ sơ pháp lý chưa đạt. Hai câu có thể nói về hai loại vướng mắc khác nhau.

#### M10. Ai chịu trách nhiệm cuối: hai nguồn nói khác nhau

`Quản lý đơn hàng sản xuất gia công tại nhà cung cấp › Bước 3 · Kiểm tra điều kiện triển khai đơn hàng › Ai chịu trách nhiệm cuối`

Trạng thái: **Chờ phân xử**

| as-is · thực tế | as-is · thực tế |
|---|---|
| Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V2 · C2 | Chị Ngân · V3 · C4 |
| “Phòng Kinh doanh xem xét và quyết định phương án duyệt hoặc hoãn đơn hàng khi NL/BTP không đủ hoặc không kịp tiến độ” | “Trưởng phòng (Quản lý sản xuất) chịu trách nhiệm cuối quyết định duyệt cho đơn hàng triển khai (kể cả trường hợp duyệt trước bổ sung sau)” |
| Chuyên viên Điều phối nguyên liệu/bán thành phẩm, vòng 2 | Trưởng phòng, vòng 3 |

**Nhận định của AI**

> "Phòng Kinh doanh xem xét và quyết định phương án duyệt hoặc hoãn đơn hàng khi NL/BTP không đủ hoặc không kịp tiến độ" (Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V2 · C2) khác "Trưởng phòng (Quản lý sản xuất) chịu trách nhiệm cuối quyết định duyệt cho đơn hàng triển khai (kể cả trường hợp duyệt trước bổ sung sau)" (Chị Ngân · V3 · C4).
>
> Phát hiện ngày 23/10/2026

- **Câu cần chốt:** Khi đơn hàng không đủ điều kiện triển khai, ai quyết cuối cho đi tiếp hay dừng? Đề xuất chia theo loại vướng mắc: pháp lý và cung ứng nội bộ do Trưởng phòng quyết; dời ngày giao hoặc hủy đơn với khách do Phòng Kinh doanh quyết; hai bên không thống nhất thì Giám đốc. Xác nhận hoặc sửa.
- **Người chốt đề nghị:** Trưởng phòng Sản xuất, Giám đốc (hỏi ý Phòng Kinh doanh)
- **Trả lời của Sản xuất:** ............................................................
- **Ghi chú của A5:** KD quyết, so với Trưởng phòng quyết.

#### M11. Người có thẩm quyền quyết định khi điều kiện đơn hàng không đạt: Phòng Kinh doanh vs Quản lý sản xuất

`Quản lý đơn hàng sản xuất gia công tại nhà cung cấp › Bước 3 · Kiểm tra điều kiện triển khai đơn hàng › Ai chịu trách nhiệm cuối`

Trạng thái: **Chờ phân xử**

| as-is · thực tế | as-is · thực tế |
|---|---|
| Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V2 · C2 | Trưởng nhóm Điều phối · V2 · C4 |
| “Phòng Kinh doanh xem xét và quyết định phương án duyệt hoặc hoãn đơn hàng khi NL/BTP không đủ hoặc không kịp tiến độ” | “Quản lý sản xuất là người quyết định cuối cùng (cho duyệt trước bổ sung sau hoặc tạm ngưng đơn) dựa trên dữ liệu kiểm tra từ các nhóm nội bộ; Trưởng nhóm Điều phối cập nhật tiến độ lại cho Kinh doanh” |
| Chuyên viên Điều phối nguyên liệu/bán thành phẩm, vòng 2 | Trưởng nhóm Điều phối, vòng 2 |

**Nhận định của AI**

> Chuyên viên Điều phối NL/BTP (sv_114) cho rằng Phòng Kinh doanh quyết định duyệt hoặc hoãn đơn khi thiếu nguyên liệu; trong khi Trưởng nhóm Điều phối (a_47) nêu Quản lý sản xuất là người quyết định cuối cùng (cho duyệt trước bổ sung sau hoặc tạm ngưng đơn).
>
> Phát hiện ngày 22/10/2026

- **Câu cần chốt:** Khi đơn hàng không đủ điều kiện triển khai, ai quyết cuối cho đi tiếp hay dừng? Đề xuất chia theo loại vướng mắc: pháp lý và cung ứng nội bộ do Trưởng phòng quyết; dời ngày giao hoặc hủy đơn với khách do Phòng Kinh doanh quyết; hai bên không thống nhất thì Giám đốc. Xác nhận hoặc sửa.
- **Người chốt đề nghị:** Trưởng phòng Sản xuất, Giám đốc (hỏi ý Phòng Kinh doanh)
- **Trả lời của Sản xuất:** ............................................................
- **Ghi chú của A5:** KD quyết, so với Quản lý sản xuất quyết (Trưởng nhóm Điều phối chỉ báo lại tiến độ cho KD).

#### M12. Thẩm quyền phê duyệt chi phí phát sinh ngoài ngân sách: Trưởng phòng cho rằng không cần duyệt vs Giám đốc quy định phải trình Giám đốc công ty thành viên phê duyệt

`Việc nào phải xin duyệt, ai duyệt, ngưỡng nào`

Trạng thái: **Chờ phân xử**

| as-is · thực tế | as-is · thực tế |
|---|---|
| Chị Ngân · V2 · C2 | Giám đốc · V1 · C1 |
| “Không áp dụng phê duyệt chi phí hoặc vượt ngân sách dự toán đơn hàng do công ty hiện không có quỹ chi phí và ngân sách dự toán” | “Chi phí phát sinh ngoài ngân sách sản xuất phải trình Giám đốc phụ trách và ghi kèm tên công ty tương ứng để phê duyệt (áp dụng cho 12 công ty thuộc Group)” |
| Trưởng phòng, vòng 2 | Giám đốc, vòng 1 |

**Nhận định của AI**

> Chị Ngân (Trưởng phòng) cho biết công ty không có ngân sách dự toán nên không cần phê duyệt chi phí phát sinh; trong khi Giám đốc khẳng định các chi phí ngoài ngân sách đều phải trình Giám đốc phụ trách công ty tương ứng phê duyệt.
>
> Phát hiện ngày 22/10/2026

- **Câu cần chốt:** Chi phí phát sinh của một đơn gia công hiện có phải xin duyệt không, ai duyệt, ngưỡng bao nhiêu?
- **Người chốt đề nghị:** Giám đốc, Trưởng phòng Sản xuất, Phòng Tài chính Kế toán
- **Trả lời của Sản xuất:** ............................................................
- **Ghi chú của A5:** Trưởng phòng nói không có ngân sách dự toán nên không duyệt chi phí phát sinh. Giám đốc nói chi phí ngoài ngân sách phải trình Giám đốc phụ trách công ty tương ứng. Có thể hai câu nói về hai việc: không có ngân sách theo đơn hàng, nhưng chi phí phát sinh vẫn phải xin duyệt. Xem thêm L02.

#### M13. Việc nào phải xin duyệt, ai duyệt, ngưỡng nào: hai nguồn nói khác nhau

`Việc nào phải xin duyệt, ai duyệt, ngưỡng nào`

Trạng thái: **Đã hỏi lại hai bên**

| as-is · thực tế | as-is · thực tế |
|---|---|
| QUY TRÌNH SẢN XUẤT 09.07.2026 (2).xlsx · sheet 1. QT LÀM VIỆC VỚI NCC MỚI | Chị Ngân · V2 · C2 |
| “Duyệt hợp đồng NCC GC mới lần lượt qua Pháp lý -> P. TCKT -> Giám đốc ký duyệt” | “Không áp dụng phê duyệt chi phí hoặc vượt ngân sách dự toán đơn hàng do công ty hiện không có quỹ chi phí và ngân sách dự toán” |
|  | Trưởng phòng, vòng 2 |

**Nhận định của AI**

> "Duyệt hợp đồng NCC GC mới lần lượt qua Pháp lý -> P. TCKT -> Giám đốc ký duyệt" (QUY TRÌNH SẢN XUẤT 09.07.2026 (2).xlsx · sheet 1. QT LÀM VIỆC VỚI NCC MỚI) khác "Không áp dụng phê duyệt chi phí hoặc vượt ngân sách dự toán đơn hàng do công ty hiện không có quỹ chi phí và ngân sách dự toán" (Chị Ngân · V2 · C2).
>
> Phát hiện ngày 21/10/2026

- **Câu cần chốt:** Xác nhận đây là hai việc khác nhau: duyệt hợp đồng NCC mới đi theo tệp quy trình; duyệt chi phí theo câu trả lời ở M12.
- **Người chốt đề nghị:** Trưởng phòng Sản xuất
- **Trả lời của Sản xuất:** ............................................................
- **Ghi chú của A5:** Trạng thái trên MIC: đã hỏi lại. Hai câu nói về hai việc khác nhau (duyệt hợp đồng NCC mới và duyệt chi phí), nên nhiều khả năng không mâu thuẫn thật. Điểm thật cần chốt nằm ở L07.

### Các chỗ lệch A5 tìm thêm

#### L01. Bao lâu một lần (số đơn)

`Quản lý đơn hàng SX gia công · Tiếp nhận / Kiểm tra điều kiện › Bao lâu một lần (số đơn)`

Trạng thái: **A5 tìm thêm, chưa có trên MIC**

| as-is · thực tế | as-is · thực tế |
|---|---|
| Chuyên viên Điều phối sản xuất · V2 · C1 | Trưởng nhóm Điều phối · V4 · C2 |
| “Tiếp nhận khoảng 10 đến 15 đơn hàng một ngày từ Phòng Kinh doanh (bao gồm cả các đơn hàng dự trù trước)” | “Trung bình khoảng 15 đơn/tuần cho 3 loại: đơn đặt hàng thành phẩm (chiếm tỷ trọng lớn), đơn đặt hàng bán thành phẩm, và đơn xử lý lại do phát sinh sự cố” |
| Chuyên viên Điều phối sản xuất, vòng 2 | Trưởng nhóm Điều phối, vòng 4 |

**Nhận định của A5**

> Lệch khoảng 5 lần. Giả thuyết: hai nhóm đếm hai thứ khác nhau, một bên đếm mọi yêu cầu KD gửi vào (gồm đơn dự trù), một bên đếm đơn thật sự đi duyệt giá và gửi NCC.
>
> Phát hiện ngày 24/10/2026

- **Câu cần chốt:** Mỗi ngày nhận bao nhiêu yêu cầu từ KD, và mỗi tuần có bao nhiêu đơn thật sự gửi NCC GC?
- **Người chốt đề nghị:** Trưởng nhóm Điều phối, Chuyên viên Điều phối sản xuất
- **Trả lời của Sản xuất:** ............................................................
- **Ghi chú của A5:** Chuyên viên VTBB V3 C1 cũng nói 10 đến 15 đơn mỗi ngày. Chuyên viên Giá vốn V2 C1 cũng nói khoảng 15 đơn mỗi tuần.

#### L02. Việc nào phải xin duyệt, ai duyệt, ngưỡng nào

`Tổng quan phòng · Duyệt và ngưỡng › Việc nào phải xin duyệt, ai duyệt, ngưỡng nào`

Trạng thái: **A5 tìm thêm, chưa có trên MIC**

| as-is · thực tế | as-is · thực tế |
|---|---|
| Chị Ngân · V2 · C2 | Bản sao của QUY TRINH THANH TOAN V1- 7.11.2025.xlsx · sheet Form DE XUAT MUA HANG |
| “Không áp dụng phê duyệt chi phí hoặc vượt ngân sách dự toán đơn hàng do công ty hiện không có quỹ chi phí và ngân sách dự toán” | “Duyệt chi phí mua sắm: Trưởng bộ phận duyệt tối đa 3 triệu/lần (hạn mức 10 triệu/tháng); Quản lý thương hiệu duyệt tối đa 5 triệu/lần; vượt mức do Giám đốc điều hành duyệt” |
| Trưởng phòng, vòng 2 |  |

**Nhận định của A5**

> Ba nguồn, ba kiểu. MIC chỉ so cặp Trưởng phòng và Giám đốc (M12), chưa so với tệp có hạn mức. Còn một chỗ lệch nhỏ: Giám đốc phụ trách và Giám đốc điều hành có phải một người không.
>
> Phát hiện ngày 24/10/2026

- **Câu cần chốt:** Hạn mức 3 triệu và 5 triệu trong tệp quy trình thanh toán có đang áp cho chi phí của phòng Sản xuất không? Giám đốc phụ trách và Giám đốc điều hành có phải một người?
- **Người chốt đề nghị:** Giám đốc, Phòng Tài chính Kế toán
- **Trả lời của Sản xuất:** ............................................................
- **Ghi chú của A5:** Giám đốc V1 C1 lại nói chi phí ngoài ngân sách phải trình Giám đốc phụ trách (xem M12).

#### L03. Phiếu điều chuyển nguyên liệu gửi cho ai

`Quản lý đơn hàng SX gia công · Chuẩn bị nguồn lực › Phiếu điều chuyển nguyên liệu gửi cho ai`

Trạng thái: **A5 tìm thêm, chưa có trên MIC**

| as-is · thực tế | as-is · thực tế |
|---|---|
| Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V1 · C2 | Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V2 · C5 |
| “Phiếu yêu cầu phối trộn hoặc điều chuyển nguyên liệu do Chuyên viên NL/BTP lập khi phát sinh nhu cầu phối trộn BTP hoặc điều chuyển NL, gửi Kinh doanh, Kho và Nhà gia công” | “Bộ phận Sản xuất không gửi trực tiếp Phiếu điều chuyển nguyên liệu cho Kho, mà Điều phối NL/BTP lập gửi cho Điều phối thành phẩm để Điều phối thành phẩm yêu cầu NCC GC phối hợp xuất điều chuyển” |
| Chuyên viên Điều phối nguyên liệu/bán thành phẩm, vòng 1 | Chuyên viên Điều phối nguyên liệu/bán thành phẩm, vòng 2 |

**Nhận định của A5**

> Cùng một người nói hai ý ở hai vòng. Giả thuyết: phiếu phối trộn gửi Kho, phiếu điều chuyển thì không.
>
> Phát hiện ngày 24/10/2026

- **Câu cần chốt:** Phiếu phối trộn và phiếu điều chuyển nguyên liệu có gửi thẳng cho Kho không? Nếu khác nhau thì mỗi loại gửi ai?
- **Người chốt đề nghị:** Chuyên viên Điều phối nguyên liệu/bán thành phẩm
- **Trả lời của Sản xuất:** ............................................................

#### L04. Ai chịu trách nhiệm cuối

`Quản lý đơn hàng SX gia công · Tiếp nhận và kiểm tra yêu cầu đặt hàng › Ai chịu trách nhiệm cuối`

Trạng thái: **A5 tìm thêm, chưa có trên MIC**

| as-is · thực tế | as-is · thực tế |
|---|---|
| Trưởng nhóm Điều phối · V2 · C3 | Chị Ngân · V3 · C3 |
| “Điều phối thành phẩm chịu trách nhiệm đảm bảo tính đầy đủ của thông tin, Phòng Kinh doanh chịu trách nhiệm đảm bảo tính chính xác của đơn đặt hàng” | “Chuyên viên Điều phối sản xuất chịu trách nhiệm cuối nếu đơn hàng bị sót thông tin hoặc sai quy cách” |
| Trưởng nhóm Điều phối, vòng 2 | Trưởng phòng, vòng 3 |

**Nhận định của A5**

> Nếu Điều phối thành phẩm và Chuyên viên Điều phối sản xuất là một vị trí thì chỉ lệch ở phần trách nhiệm của KD. Hai tên gọi đang dùng lẫn.
>
> Phát hiện ngày 24/10/2026

- **Câu cần chốt:** Điều phối thành phẩm và Chuyên viên Điều phối sản xuất có phải một vị trí? Đơn sai quy cách do KD ghi sai thì ai chịu?
- **Người chốt đề nghị:** Trưởng phòng Sản xuất
- **Trả lời của Sản xuất:** ............................................................

#### L05. Ai quyết phương án khi hàng lỗi

`Quản lý đơn hàng SX gia công · Nhận hàng và xử lý sai lệch / Xử lý sự cố › Ai quyết phương án khi hàng lỗi`

Trạng thái: **A5 tìm thêm, chưa có trên MIC**

| as-is · thực tế | as-is · thực tế |
|---|---|
| Trưởng nhóm Điều phối · V4 · C4 | Chuyên viên Pháp lý - Xử lý sự cố · V5 · C3 |
| “Trưởng nhóm Điều phối quyết định phương án xử lý cuối cùng sau khi tổng hợp ý kiến từ NCC GC, các bộ phận liên quan và Kinh doanh” | “Trưởng nhóm Quản lý dữ liệu phê duyệt phương án trong thẩm quyền; nếu phát sinh ngoài quy trình, vượt thẩm quyền hoặc có rủi ro thì Trưởng phòng (Quản lý sản xuất) quyết định” |
| Trưởng nhóm Điều phối, vòng 4 | Chuyên viên Pháp lý - Xử lý sự cố, vòng 5 |

**Nhận định của A5**

> Hai trưởng nhóm khác nhau cùng được nói là người quyết. Giả thuyết: Trưởng nhóm Điều phối quyết khi lỗi phát hiện lúc nhận hàng tại NCC, Trưởng nhóm QLDL quyết khi đã thành sự cố.
>
> Phát hiện ngày 24/10/2026

- **Câu cần chốt:** Hàng nhận về bị lỗi: ai quyết phương án cuối? Có tách theo lúc phát hiện (tại NCC hay đã về kho) không?
- **Người chốt đề nghị:** Trưởng phòng Sản xuất
- **Trả lời của Sản xuất:** ............................................................

#### L06. Các bước theo thứ tự

`Quản lý đơn hàng SX gia công · Mức quy trình › Các bước theo thứ tự`

Trạng thái: **A5 tìm thêm, chưa có trên MIC**

| as-is · thực tế | as-is · thực tế |
|---|---|
| Chị Ngân · V1 · C4 | QUY TRÌNH SẢN XUẤT 09.07.2026 (1).xlsx · sheet 4. QT QL ĐƠN HÀNG SX GC |
| “Quy trình quan trọng nhất là Quản lý đơn hàng sản xuất gia công tại nhà cung cấp (NCC GC) gồm 6 bước từ tiếp nhận đơn đến hoàn thiện chứng từ thanh lý.” | “Gồm 7 bước: 1. Tiếp nhận và xử lý dữ liệu -> 2. Kiểm tra thông tin -> 3. Gửi đơn đặt hàng NCC GC & cập nhật tiến độ -> 4. Nhập kho & nhận hóa đơn từ NCC GC -> 5. Theo dõi nhận hàng từ NCC GC -> 6. Kiểm tra mẫu gửi Lab -> 7. Lập chứng từ cấu thành, đối chiếu, thanh toán.” |
| Trưởng phòng, vòng 1 |  |

**Nhận định của A5**

> Số bước và tên bước khác nhau giữa câu trả lời và tệp quy trình. MIC đang dựng theo 6 bước.
>
> Phát hiện ngày 24/10/2026

- **Câu cần chốt:** Bản quy trình chuẩn hiện hành là bản nào: 6 bước hay 7 bước?
- **Người chốt đề nghị:** Trưởng phòng Sản xuất
- **Trả lời của Sản xuất:** ............................................................

#### L07. Ai ký hợp đồng NCC GC mới

`Làm việc với NCC GC mới · Soạn hợp đồng / Hoàn thiện › Ai ký hợp đồng NCC GC mới`

Trạng thái: **A5 tìm thêm, chưa có trên MIC**

| as-is · thực tế | as-is · thực tế |
|---|---|
| QUY TRÌNH SẢN XUẤT 09.07.2026 (2).xlsx · sheet 1. QT LÀM VIỆC VỚI NCC MỚI | Giám đốc · V2 · C2 |
| “Duyệt hợp đồng NCC GC mới lần lượt qua Pháp lý -> P. TCKT -> Giám đốc ký duyệt” | “Hợp đồng và bảng giá với NCC mới bắt buộc phải trình Đại diện pháp luật của Công ty ký duyệt” |
|  | Giám đốc, vòng 2 |

**Nhận định của A5**

> Tập đoàn có 12 công ty. Giám đốc ký, Giám đốc phụ trách và Đại diện pháp luật có thể là những người khác nhau ở từng công ty.
>
> Phát hiện ngày 24/10/2026

- **Câu cần chốt:** Với từng công ty, ai duyệt kết quả chọn NCC mới và ai ký hợp đồng?
- **Người chốt đề nghị:** Giám đốc
- **Trả lời của Sản xuất:** ............................................................
- **Ghi chú của A5:** Giám đốc V1 C2 nói thêm: kết quả chọn NCC mới do Giám đốc phụ trách công ty tương ứng duyệt bằng văn bản.

#### L08. Toàn trình mất bao lâu

`Quản lý đơn hàng SX gia công · Mức quy trình › Toàn trình mất bao lâu`

Trạng thái: **A5 tìm thêm, chưa có trên MIC**

| as-is · thực tế | as-is · thực tế |
|---|---|
| Bản sao của ĐIỀU PHỒI THÀNH PHẨM (NHÁP).xlsx · sheet Data số ngày cập nhật cho KD | QUY TRÌNH SẢN XUẤT 09.07.2026 (1).xlsx · sheet 17. TT NCC GC |
| “Thời gian sản xuất 1 đơn hàng tại NCC Hà Long: Cấu thành BTP và VTBB nội bộ là 15 ngày; BTP khách hàng và VTBB nội bộ là 10 ngày; BTP khách hàng và VTBB NCC là 7 ngày” | “Nhà cung cấp gia công Hà Long (gia công thuốc BVTV, có app theo dõi tiến độ, đơn tối thiểu 10 thùng, thời gian 5-14 ngày)” |

**Nhận định của A5**

> Hai bảng cùng nói về một NCC nhưng khác số.
>
> Phát hiện ngày 24/10/2026

- **Câu cần chốt:** KD đang hứa ngày giao theo bảng nào? Bảng nào là bảng đúng?
- **Người chốt đề nghị:** Trưởng nhóm Điều phối
- **Trả lời của Sản xuất:** ............................................................

#### L09. Số trạng thái theo dõi đơn

`Công cụ, tài liệu › Số trạng thái theo dõi đơn`

Trạng thái: **A5 tìm thêm, chưa có trên MIC**

| as-is · thực tế | as-is · thực tế |
|---|---|
| Bản sao của ĐIỀU PHỒI THÀNH PHẨM (NHÁP).xlsx · sheet họp07.10 | Bản sao của ĐIỀU PHỒI THÀNH PHẨM (NHÁP).xlsx · sheet NHẬP-XUẤT TP |
| “File Excel ĐIỀU PHỒI THÀNH PHẨM dùng quản lý và cập nhật tiến độ đơn hàng sản xuất qua 6 trạng thái điều phối” | “Quy trình điều phối theo dõi 7 trạng thái nhập xuất; hàng sản xuất dư nếu được chấp nhận thì nhập kho TP, nếu Kinh doanh chưa nhận hàng thì chuyển sang quy trình Xử lý sự cố” |

**Nhận định của A5**

> Hai sheet trong cùng một tệp. Có thể là hai bộ trạng thái khác nhau (điều phối và nhập xuất).
>
> Phát hiện ngày 24/10/2026

- **Câu cần chốt:** Đây là một bộ trạng thái hay hai bộ? Liệt kê tên từng trạng thái.
- **Người chốt đề nghị:** Trưởng nhóm Điều phối
- **Trả lời của Sản xuất:** ............................................................

#### L10. Ai kiểm chất lượng thành phẩm khi nhận

`Quản lý đơn hàng SX gia công · Nhận hàng › Ai kiểm chất lượng thành phẩm khi nhận`

Trạng thái: **A5 tìm thêm, chưa có trên MIC**

| as-is · thực tế | as-is · thực tế |
|---|---|
| Trưởng nhóm Điều phối · V2 · C7 | Bản sao của ĐIỀU PHỒI THÀNH PHẨM (NHÁP).xlsx · sheet Kết quả KCS Kho Dr.Xanh |
| “Kiểm tra mẫu thành phẩm tại Lab nội bộ khi nhận hàng từ NCC GC chỉ kiểm tra ngoại dạng, màu sắc, trọng lượng; chỉ kiểm tra hàm lượng hoạt chất hoặc chỉ tiêu chuyên môn sâu khi có yêu cầu hoặc phát sinh sự cố” | “Biểu mẫu Kết quả KCS Kho Dr.Xanh dùng theo dõi quy cách ngoại quan, phụ kiện và chứng từ khi nhận thành phẩm từ NCC gia công.” |
| Trưởng nhóm Điều phối, vòng 2 |  |

**Nhận định của A5**

> Có thể cả Lab và Kho cùng kiểm, mỗi bên một phần. Cần biết kết quả của bên nào thì hàng mới được nhập kho dùng được.
>
> Phát hiện ngày 24/10/2026

- **Câu cần chốt:** Khi nhận thành phẩm, Kho kiểm gì, Lab kiểm gì? Kết quả của bên nào quyết định hàng được nhập kho?
- **Người chốt đề nghị:** Trưởng nhóm Điều phối, Kho, Lab
- **Trả lời của Sản xuất:** ............................................................

#### L11. Ai đang giữ vị trí Chuyên viên Pháp lý - Xử lý sự cố

`Bộ máy › Ai đang giữ vị trí Chuyên viên Pháp lý - Xử lý sự cố`

Trạng thái: **A5 tìm thêm, chưa có trên MIC**

| as-is · thực tế | dữ liệu MIC |
|---|---|
| Ảnh sơ đồ tổ chức · tr. 1 | Danh sách vị trí trên MIC |
| “Chuyên viên Pháp lý - Xử lý sự cố báo cáo Trưởng nhóm Quản lý dữ liệu (Trần Ngọc Huỳnh lead, Nguyễn Ngọc Bảo Thi)” | Chuyên viên Pháp lý - Xử lý sự cố: Trần Ngọc Huỳnh kiêm nhiệm và một nhân viên tên Thơ. |

**Nhận định của A5**

> Mới phát hiện khi đọc lại ngày 24/10. Tên nhân viên thứ hai khác nhau. Nếu Trưởng nhóm QLDL đang kiêm vị trí này thì hai vai trả lời khác nhau ở câu ai quyết cuối (M09 so với M02).
>
> Phát hiện ngày 24/10/2026

- **Câu cần chốt:** Ai đang giữ vị trí Chuyên viên Pháp lý - Xử lý sự cố? Người trả lời khảo sát ở vai này là ai?
- **Người chốt đề nghị:** Trưởng phòng Sản xuất
- **Trả lời của Sản xuất:** ............................................................

#### L12. Tuyến báo cáo của Chuyên viên Điều phối NL/BTP

`Bộ máy › Tuyến báo cáo của Chuyên viên Điều phối NL/BTP`

Trạng thái: **A5 tìm thêm, chưa có trên MIC**

| as-is · thực tế | as-is · thực tế |
|---|---|
| Ảnh sơ đồ tổ chức · tr. 1 | Lỗ hổng trên MIC (mức cao) |
| “Chuyên viên Điều phối NL/BTP báo cáo Trưởng nhóm Điều phối (Đào Thị Thúy Oanh)” | Chuyên viên Điều phối NL/BTP phản hồi chưa xác định rõ Trưởng nhóm Điều phối có phải quản lý trực tiếp hay không. |

**Nhận định của A5**

> Có thể do kiêm nhiệm hai vị trí, và Trưởng nhóm Điều phối đang do Trưởng phòng kiêm nhiệm.
>
> Phát hiện ngày 24/10/2026

- **Câu cần chốt:** Chuyên viên Điều phối NL/BTP báo cáo trực tiếp cho ai? Nhân sự có tên ở hai nhóm có kiêm nhiệm không?
- **Người chốt đề nghị:** Trưởng phòng Sản xuất
- **Trả lời của Sản xuất:** ............................................................
- **Ghi chú của A5:** Theo ảnh sơ đồ tổ chức, cùng một nhân sự có tên ở cả nhóm Điều phối sản xuất và nhóm Điều phối NL/BTP.

---

## Phần B. Bộ máy theo dữ liệu MIC

| Vị trí | Người đang giữ | Báo cáo cho |
|---|---|---|
| Trưởng phòng (Quản lý sản xuất) | Phạm Khánh Ngân. Dự kiến bàn giao cho Lê Thị Ngọc Mi chậm nhất 31/12/2026 (đã chốt trên MIC) | Giám đốc |
| Trưởng nhóm Điều phối | Trưởng phòng kiêm nhiệm (trợ lý sản xuất kiêm nhiệm). Sắp bố trí một nhân sự riêng | Trưởng phòng |
| Trưởng nhóm Quản lý dữ liệu | Trần Ngọc Huỳnh | Trưởng phòng |
| Chuyên viên Điều phối sản xuất (Điều phối thành phẩm) | Nguyễn Thị Phương Thảo, Lê Mỹ Ngọc, Đào Thị Thúy Oanh | Trưởng nhóm Điều phối |
| Chuyên viên Điều phối vật tư bao bì | Mai Thị Yến Ly (nhóm trưởng), Bùi Thị Diễm Tiên, Phạm Phú An | Trưởng nhóm Điều phối |
| Chuyên viên Điều phối nguyên liệu / bán thành phẩm | Đào Thị Thúy Oanh | Trưởng nhóm Điều phối (chưa chắc, xem L12) |
| Chuyên viên Pháp lý - Xử lý sự cố | Trần Ngọc Huỳnh kiêm nhiệm, cùng một nhân viên (tên chưa thống nhất, xem L11) | Trưởng nhóm Quản lý dữ liệu |
| Chuyên viên Giá vốn và Xử lý dữ liệu | Huỳnh Thị Kim Hương | Trưởng nhóm Quản lý dữ liệu |
| Chuyên viên Quản lý hồ sơ sản xuất và Dữ liệu NCC GC | Lê Thị Trúc Thơ, Hồ Thị Diệu Liên, Trần Phước Hoàng Khang | Trưởng nhóm Quản lý dữ liệu |
| Giám đốc | Giám đốc phụ trách theo từng công ty thành viên (12 công ty) |  |
| Kế toán sản xuất | Chưa ghi tên | Phòng Kế toán |
| Bộ phận Lab | Chưa ghi tên. MIC gợi ý thêm vào khảo sát, chưa mời |  |

Người trả lời khảo sát được MIC ghi theo vị trí, trừ Trưởng phòng ghi là *Chị Ngân*. Vị trí có nhiều người thì MIC không ghi ai trong số đó đã trả lời.

---

## Phần C. Danh sách câu hỏi và câu trả lời của từng người

Đánh số theo *mục.bước.câu*. Bước 0 là phần chung của mục hoặc của quy trình.

### 1. Tổng quan phòng Sản xuất

**1.0.1. Phòng tồn tại để mang lại kết quả gì**

- Trưởng phòng (Chị Ngân) · V1 · C1 · _as-is (thực tế), độ tin cao_: Đảm bảo sản phẩm sản xuất hoàn thành đúng chất lượng, đủ sản lượng theo kế hoạch đơn hàng, kiểm soát chi phí, định mức hao hụt nguyên vật liệu và điều phối tiến độ giao hàng cho công ty.

**1.0.2. Phòng có những ai, vị trí nào, ai báo cáo cho ai**

- Tài liệu: SƠ ĐỒ SX & MTCV.xlsx · sheet 2. TNĐP · _as-is (thực tế), độ tin cao_: Trưởng nhóm Điều phối báo cáo Quản lý sản xuất, quản lý các Chuyên viên Điều phối
- Tài liệu: SƠ ĐỒ SX & MTCV.xlsx · sheet 3. TN QLDL · _as-is (thực tế), độ tin cao_: Trưởng nhóm Quản lý dữ liệu (Trần Ngọc Huỳnh lead) báo cáo Quản lý sản xuất
- Tài liệu: Ảnh sơ đồ tổ chức · tr. 1 · _as-is (thực tế), độ tin cao_: Chuyên viên Điều phối sản xuất báo cáo Trưởng nhóm Điều phối (gồm Nguyễn Thị Phương Thảo, Lê Mỹ Ngọc, Đào Thị Thúy Oanh)
- Tài liệu: Ảnh sơ đồ tổ chức · tr. 1 · _as-is (thực tế), độ tin cao_: Chuyên viên Điều phối VTBB báo cáo Trưởng nhóm Điều phối (Mai Thị Yến Ly lead, Bùi Thị Diễm Tiên, Phạm Phú An)
- Tài liệu: Ảnh sơ đồ tổ chức · tr. 1 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L12**: Chuyên viên Điều phối NL/BTP báo cáo Trưởng nhóm Điều phối (Đào Thị Thúy Oanh)
- Tài liệu: Ảnh sơ đồ tổ chức · tr. 1 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L11**: Chuyên viên Pháp lý - Xử lý sự cố báo cáo Trưởng nhóm Quản lý dữ liệu (Trần Ngọc Huỳnh lead, Nguyễn Ngọc Bảo Thi)
- Tài liệu: Ảnh sơ đồ tổ chức · tr. 1 · _as-is (thực tế), độ tin cao_: Chuyên viên Giá vốn và Xử lý dữ liệu báo cáo Trưởng nhóm Quản lý dữ liệu (Huỳnh Thị Kim Hương)
- Tài liệu: Ảnh sơ đồ tổ chức · tr. 1 · _as-is (thực tế), độ tin cao_: Chuyên viên Quản lý hồ sơ SX & Dữ liệu NCC GC báo cáo Trưởng nhóm Quản lý dữ liệu (Trần Ngọc Huỳnh lead, Lê Thị Trúc Thơ, Hồ Thị Diệu Liên, Trần Phước Hoàng Khang)

**1.0.3. Một hai quy trình quan trọng nhất, kể lần gần nhất**

- Trưởng phòng (Chị Ngân) · V1 · C4 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L06**: Quy trình quan trọng nhất là Quản lý đơn hàng sản xuất gia công tại nhà cung cấp (NCC GC) gồm 6 bước từ tiếp nhận đơn đến hoàn thiện chứng từ thanh lý.

**1.0.4. Nhận việc từ đâu, giao kết quả cho ai**

- Trưởng phòng (Chị Ngân) · V1 · C5 · _as-is (thực tế), độ tin cao_: Phòng nhận yêu cầu đặt hàng thành phẩm, dự trù mua hàng từ Kinh doanh qua Google Drive và Zalo
- Trưởng phòng (Chị Ngân) · V1 · C4 · _as-is (thực tế), độ tin cao_: Phòng gửi đơn đặt hàng gia công, mẫu thiết kế, vật tư cho Nhà cung cấp gia công và nhận lại thành phẩm, hóa đơn, biên bản đối chiếu
- Tài liệu: 4. XUẤT NHẬP TỒN - VTBB.xlsx · sheet MỤC LỤC · _as-is (thực tế), độ tin cao_: Bộ phận Sản xuất tiếp nhận kết quả mua hàng từ Bộ phận Thu mua để lấy thông tin phục vụ nhận hàng VTBB.

**1.0.5. Công cụ đang dùng**

- Trưởng phòng (Chị Ngân) · V1 · C6 · _as-is (thực tế), độ tin cao_: Google Drive / Google Sheets dùng quản lý dữ liệu, đơn hàng, tiến độ, tồn kho, giá vốn và sự cố
- Trưởng phòng (Chị Ngân) · V1 · C6 · _as-is (thực tế), độ tin cao_: Zalo dùng trao đổi, phối hợp tiến độ và xử lý phát sinh với KD, Thu mua, Kho, Lab, NCC GC qua hơn 50 nhóm chat
- Trưởng phòng (Chị Ngân) · V1 · C6 · _as-is (thực tế), độ tin cao_: MISA dùng phối hợp xuất kho, quản lý hóa đơn và đối chiếu kế toán
- Chuyên viên Điều phối vật tư bao bì · V1 · C1 · _as-is (thực tế), độ tin vừa_: Google Sheets theo dõi xuất nhập tồn và cân đối nhu cầu vật tư bao bì

**1.0.6. Việc nào phải xin duyệt, ai duyệt, ngưỡng nào**

- Tài liệu: QUY TRÌNH SẢN XUẤT 09.07.2026 (2).xlsx · sheet 1. QT LÀM VIỆC VỚI NCC MỚI · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: M13, L07**: Duyệt hợp đồng NCC GC mới lần lượt qua Pháp lý -> P. TCKT -> Giám đốc ký duyệt
- Tài liệu: Bản sao của QUY TRINH THANH TOAN V1- 7.11.2025.xlsx · sheet Form DE XUAT MUA HANG · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L02**: Duyệt chi phí mua sắm: Trưởng bộ phận duyệt tối đa 3 triệu/lần (hạn mức 10 triệu/tháng); Quản lý thương hiệu duyệt tối đa 5 triệu/lần; vượt mức do Giám đốc điều hành duyệt
- Trưởng phòng (Chị Ngân) · V2 · C2 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: M12, M13, L02**: Không áp dụng phê duyệt chi phí hoặc vượt ngân sách dự toán đơn hàng do công ty hiện không có quỹ chi phí và ngân sách dự toán
- Tài liệu: Bản sao của ĐIỀU PHỒI THÀNH PHẨM (NHÁP).xlsx · sheet DUYỆT ĐƠN HÀNG · _as-is (thực tế), độ tin cao_: Duyệt đơn hàng nội bộ đủ điều kiện triển khai qua 7 bộ phận: NL/BTP, VTBB, Giá vốn, Pháp lý, Sự cố, QLDL và Quản lý sản xuất
- Tài liệu: Bản sao của ĐIỀU PHỒI THÀNH PHẨM (NHÁP).xlsx · sheet MỤC LỤC · _as-is (thực tế), độ tin cao_: Quyết định tặng quà Nhà cung cấp gia công do Quản lý sản xuất phê duyệt cuối cùng trên cơ sở tổng hợp đánh giá từ QLDL và theo dõi của ĐP TP.
- Tài liệu: NỘI DUNG HỌP 25.09.26.xlsx · sheet NỘI DUNG HỌP 25.09.26 · _as-is (thực tế), độ tin cao_: Đơn đặt hàng sản xuất gia công bắt buộc phải ký duyệt (bảng giá không thay thế được); tên hợp đồng được phép ghi hợp đồng nguyên tắc
- Giám đốc · V1 · C1 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: M12, L02**: Chi phí phát sinh ngoài ngân sách sản xuất phải trình Giám đốc phụ trách và ghi kèm tên công ty tương ứng để phê duyệt (áp dụng cho 12 công ty thuộc Group)
- Trưởng phòng (Chị Ngân) · V3 · C1 · _giả thuyết, độ tin thấp_ · *Suy diễn (AI)*: Trưởng phòng (Quản lý sản xuất) phê duyệt đơn hàng thành phẩm, đơn hàng bán thành phẩm, duyệt giá và các sự cố phát sinh ngoài quy trình

**1.0.7. Theo dõi kết quả bằng gì, báo cáo cho ai, bao lâu một lần**

- Trưởng phòng (Chị Ngân) · V1 · C8 · _as-is (thực tế), độ tin cao_: Báo cáo tiến độ đơn hàng thành phẩm gửi Kinh doanh và Kế toán liên tục khi phát sinh hoặc định kỳ hàng tuần, hàng tháng qua Google Drive và Zalo
- Tài liệu: Bản sao của ĐIỀU PHỒI THÀNH PHẨM (NHÁP).xlsx · sheet MỤC LỤC · _as-is (thực tế), độ tin cao_: Báo cáo tồn kho hàng ngày gửi cho bộ phận Kho lấy từ báo cáo tồn kho và kiểm tra hóa đơn của sheet Nhập xuất TP
- Tài liệu: 4. XUẤT NHẬP TỒN - VTBB.xlsx · sheet HƯỚNG DẪN · _as-is (thực tế), độ tin cao_: Báo cáo cảnh báo ngưỡng tồn kho VTBB theo dõi ngày giao dịch cuối, cảnh báo tồn âm, tồn dưới mức an toàn Min hoặc dưới MOQ gửi Chuyên viên VTBB và Quản lý.

**1.0.8. Chỗ hay tắc, hay sai, hay làm lại, hay phụ thuộc một người**

- Trưởng phòng (Chị Ngân) · V1 · C9 · _as-is (thực tế), độ tin cao_: Công việc nào cũng bị chậm và sai; hiện công việc nào có một người thực hiện thì không có người biết làm thay thế
- Tài liệu: QUY TRÌNH SẢN XUẤT 09.07.2026 (1).xlsx · sheet TIẾN ĐỘ DRIVE · _as-is (thực tế), độ tin cao_: Hệ thống Google Drive phụ thuộc vào Data 1, nếu thay đổi Data 1 thì tất cả các Drive phải chạy lại toàn bộ.
- Trưởng phòng (Chị Ngân) · V2 · C3 · _as-is (thực tế), độ tin cao_: Kinh doanh không có kế hoạch sản xuất theo tháng, quý gây bị động cho bộ phận; phát sinh sự cố từ phía Nhà cung cấp gia công
- Tài liệu: HỌP KẾ HOẠCH BÀN GIAO SX - 15.10.2026.xlsx · sheet NỘI DUNG HỌP 15.10.26 · _as-is (thực tế), độ tin cao_: Phát sinh sự cố hàng hóa phải trả lại Nhà cung cấp do lỗi từ cả phía công ty (Dego) lẫn nhà cung cấp
- Tài liệu: 4. XUẤT NHẬP TỒN - VTBB.xlsx · sheet MỤC LỤC · _as-is (thực tế), độ tin cao_: Lịch sử đối chiếu tồn kho với NCC gia công được lưu trữ nhưng chưa có quy trình theo dõi xử lý sau đối chiếu và chưa xác định phiếu in
- Tài liệu: 3. XUẤT NHẬP TỒN NL, BTP.xlsx · sheet QUY TẮC · _as-is (thực tế), độ tin cao_: Sản phẩm đóng tối ưu thể tích tại NCC Thu Loan chốt 435ml/450ml nhưng thực tế NCC đang đóng 450ml dẫn đến chênh lệch đang phải tính vào chi phí Kinh doanh
- Tài liệu: NỘI DUNG HỌP 25.09.26.xlsx · sheet BÁO CÁO HIỆN TRẠNG CHỨNG TỪ VỚI · _as-is (thực tế), độ tin cao_: Biên bản giao nhận với hầu hết nhà cung cấp gia công chưa đúng pháp nhân nhận hóa đơn; đối chiếu tồn kho chưa được tách riêng theo từng công ty
- Tài liệu: NỘI DUNG HỌP 25.09.26.xlsx · sheet Trang tính1 · _as-is (thực tế), độ tin cao_: Kế toán yêu cầu hợp đồng thành phẩm kèm giá và số lượng khi đặt BTP của NCC GC, trong khi Kinh doanh chưa xác định hoặc thay đổi quy cách thành phẩm sau khi ký
- Chuyên viên Pháp lý - Xử lý sự cố · V2 · C3 · _as-is (thực tế), độ tin cao_: Ký kết hợp đồng gia công gặp vướng mắc do điều khoản thỏa thuận chưa thống nhất, NCC GC không chấp nhận đưa vào hợp đồng trong khi Kế toán bắt buộc phải có đầy đủ chứng từ.

**1.0.9. Đầu việc chính theo ngày, tuần, tháng**

- Tài liệu: QUY TRÌNH SẢN XUẤT 09.07.2026 (1).xlsx · sheet TIẾN ĐỘ DRIVE · _as-is (thực tế), độ tin cao_: Kinh doanh lập dự trù mua hàng vào ngày 15 hằng tháng cho NL, BTP và VTBB gửi Bộ phận Sản xuất

### 2. Quy trình Quản lý đơn hàng sản xuất gia công tại NCC

#### Bước 0. Mức quy trình

**2.0.1. Bắt đầu khi nào, do đâu**

- Trưởng phòng (Chị Ngân) · V1 · C4 · _as-is (thực tế), độ tin cao_: Kinh doanh gửi yêu cầu đặt hàng thành phẩm qua Drive và thông báo nhóm Zalo Dự trù hàng hóa.

**2.0.2. Kết quả cuối, kết thúc khi nào**

- Trưởng phòng (Chị Ngân) · V1 · C4 · _as-is (thực tế), độ tin cao_: Hồ sơ sản xuất hoàn thiện, công nợ và số lượng đối chiếu xong với NCC GC, cập nhật trạng thái hoàn thành đơn hàng.

**2.0.3. Các bước theo thứ tự**

- Tài liệu: QUY TRÌNH SẢN XUẤT 09.07.2026 (1).xlsx · sheet 4. QT QL ĐƠN HÀNG SX GC · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L06**: Gồm 7 bước: 1. Tiếp nhận và xử lý dữ liệu -> 2. Kiểm tra thông tin -> 3. Gửi đơn đặt hàng NCC GC & cập nhật tiến độ -> 4. Nhập kho & nhận hóa đơn từ NCC GC -> 5. Theo dõi nhận hàng từ NCC GC -> 6. Kiểm tra mẫu gửi Lab -> 7. Lập chứng từ cấu thành, đối chiếu, thanh toán.

**2.0.4. Nhánh, trường hợp khác**

- Tài liệu: QUY TRÌNH SẢN XUẤT 09.07.2026 (1).xlsx · sheet 4. QT QL ĐƠN HÀNG SX GC · _as-is (thực tế), độ tin cao_: Hủy đơn đặt hàng NCC GC: (1) Chưa gửi đơn NCC: dừng quy trình, xử lý tồn kho và ghi nhận chi phí; (2) Đã gửi đơn NCC: thỏa thuận hủy, nếu NCC không nhận hủy thì chờ KD xác nhận hoặc chuyển sang Quy trình xử lý sự cố.
- Tài liệu: Bản sao của ĐIỀU PHỒI THÀNH PHẨM (NHÁP).xlsx · sheet NHẬP-XUẤT TP · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L09**: Quy trình điều phối theo dõi 7 trạng thái nhập xuất; hàng sản xuất dư nếu được chấp nhận thì nhập kho TP, nếu Kinh doanh chưa nhận hàng thì chuyển sang quy trình Xử lý sự cố

**2.0.5. Chỗ hay tắc, sai, làm lại trong quy trình**

- Tài liệu: 3. XUẤT NHẬP TỒN NL, BTP.xlsx · sheet QUY TẮC · _as-is (thực tế), độ tin cao_: NCC Basel chưa nắm thông tin thay đổi công thức và màu của dòng sản phẩm V1 - V4, tiềm ẩn rủi ro đóng sai quy cách nếu không được thông báo trước khi phát sinh đơn hàng
- Tài liệu: Bản sao của ĐIỀU PHỒI THÀNH PHẨM (NHÁP).xlsx · sheet MỤC LỤC · _as-is (thực tế), độ tin cao_: Quy trình duyệt đơn hàng xử lý lại đối với hàng sự cố chưa được thống nhất, chưa rõ xem xét gộp chung với đơn hàng điều phối hay thực hiện theo quy trình riêng.

**2.0.6. Toàn trình mất bao lâu**

- Tài liệu: Bản sao của ĐIỀU PHỒI THÀNH PHẨM (NHÁP).xlsx · sheet Data số ngày cập nhật cho KD · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L08**: Thời gian sản xuất 1 đơn hàng tại NCC Hà Long: Cấu thành BTP và VTBB nội bộ là 15 ngày; BTP khách hàng và VTBB nội bộ là 10 ngày; BTP khách hàng và VTBB NCC là 7 ngày
- Trưởng nhóm Điều phối · V2 · C5 · _as-is (thực tế), độ tin vừa_: Thời gian quy định cung ứng vật tư và nguyên liệu sản xuất: Can/xô 5-7 ngày; Túi flexo 12-15 ngày; Túi trục 21 ngày; Thùng carton 15-20 ngày; NL trong nước 10-14 ngày; NL nhập khẩu 59 ngày (đường bay 41 ngày), điều chỉnh khi NCC có quy định mới

#### Bước 1. Tiếp nhận và kiểm tra yêu cầu đặt hàng

**2.1.1. Bắt đầu khi nào**

- Trưởng phòng (Chị Ngân) · V1 · C4 · _as-is (thực tế), độ tin cao_: Kinh doanh gửi yêu cầu đặt hàng thành phẩm, cung cấp thông tin sản phẩm, số lượng, thời gian cần hàng

**2.1.2. Ai làm**

- Tài liệu: QUY TRÌNH SẢN XUẤT 09.07.2026 (2).xlsx · sheet 4. QT QL ĐƠN HÀNG SX GC · _as-is (thực tế), độ tin cao_: Chuyên viên Điều phối sản xuất

**2.1.3. Nhận gì, từ ai, qua kênh nào**

- Tài liệu: QUY TRÌNH SẢN XUẤT 09.07.2026 (2).xlsx · sheet 4. QT QL ĐƠN HÀNG SX GC · _as-is (thực tế), độ tin cao_: Thông tin đơn hàng thành phẩm từ Kinh doanh qua Drive Yêu cầu đặt hàng TP và Zalo Dự trù hàng hóa

**2.1.4. Làm ra gì, giao cho ai, qua kênh nào**

- Tài liệu: QUY TRÌNH SẢN XUẤT 09.07.2026 (2).xlsx · sheet 4. QT QL ĐƠN HÀNG SX GC · _as-is (thực tế), độ tin cao_: Thông tin đơn hàng và bảng định mức được sao chép vào Drive SX-ĐIỀU PHỒI THÀNH PHẨM để chuyển tiếp cho các bộ phận kiểm tra và lập duyệt giá

**2.1.5. Công cụ dùng ở bước này**

- Chuyên viên Điều phối sản xuất · V1 · C1 · _as-is (thực tế), độ tin cao_: Drive làm việc điều phối (Google Sheets, sheet duyệt đơn hàng)

**2.1.6. Ai chịu trách nhiệm cuối**

- Trưởng nhóm Điều phối · V2 · C3 · _as-is (thực tế), độ tin vừa_ · **mâu thuẫn: L04**: Điều phối thành phẩm chịu trách nhiệm đảm bảo tính đầy đủ của thông tin, Phòng Kinh doanh chịu trách nhiệm đảm bảo tính chính xác của đơn đặt hàng
- Trưởng phòng (Chị Ngân) · V3 · C3 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L04**: Chuyên viên Điều phối sản xuất chịu trách nhiệm cuối nếu đơn hàng bị sót thông tin hoặc sai quy cách

**2.1.7. Bao lâu một lần**

- Chuyên viên Điều phối sản xuất · V2 · C1 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L01**: Tiếp nhận khoảng 10 đến 15 đơn hàng một ngày từ Phòng Kinh doanh (bao gồm cả các đơn hàng dự trù trước)

#### Bước 2. Kiểm tra điều kiện triển khai đơn hàng

**2.2.1. Làm gì trong bước, tra cứu gì**

- Tài liệu: QUY TRÌNH SẢN XUẤT 09.07.2026 (1).xlsx · sheet 5. QT PHÁP LÝ SẢN XUẤT · _as-is (thực tế), độ tin cao_: Kiểm tra 5 điều kiện pháp lý đơn hàng: đơn vị sở hữu (GĐK thuốc/QĐ lưu hành phân bón, hợp quy), đơn vị cấu thành (ủy quyền/thỏa thuận), điều kiện sản xuất (giấy phép đủ điều kiện SX, hợp đồng gia công), điều kiện mua bán, và dòng hóa đơn phù hợp.
- Chuyên viên Điều phối vật tư bao bì · V4 · C1 · _as-is (thực tế), độ tin cao_: Khi tồn kho VTBB không đủ hoặc bị trễ: kiểm tra tồn kho luân chuyển nội bộ, thương lượng Kinh doanh dời ngày, trao đổi Thu mua mua hàng; nếu vẫn chưa giải quyết được thì trình báo Trưởng phòng sản xuất quyết định

**2.2.2. Có phải xin duyệt không, ai duyệt, ngưỡng nào**

- Tài liệu: Bản sao của ĐIỀU PHỒI THÀNH PHẨM (NHÁP).xlsx · sheet DUYỆT ĐƠN HÀNG · _as-is (thực tế), độ tin cao_: Đơn hàng phải được duyệt đủ điều kiện nội bộ bởi 7 bộ phận trước khi gửi NCC: NL/BTP, VTBB, Giá vốn, Pháp lý, Sự cố, QLDL và QLSX duyệt

**2.2.3. Ai làm**

- Chuyên viên Điều phối vật tư bao bì · V1 · C2 · _as-is (thực tế), độ tin vừa_: Chuyên viên Điều phối vật tư bao bì
- Trưởng phòng (Chị Ngân) · V3 · C4 · _giả thuyết, độ tin cao_: Chuyên viên Pháp lý - Xử lý sự cố kiểm tra các điều kiện pháp lý của đơn hàng
- Chuyên viên Pháp lý - Xử lý sự cố · V3 · C1 · _as-is (thực tế), độ tin cao_: Chuyên viên pháp lý ghi nhận cụ thể các giấy tờ pháp lý chưa đạt hoặc chưa đủ, lập phương án tham mưu và đánh giá rủi ro cần chấp nhận
- Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V4 · C2 · _as-is (thực tế), độ tin cao_: Chuyên viên Điều phối nguyên liệu/bán thành phẩm kiểm tra tồn kho và điều kiện nguyên liệu/bán thành phẩm (NL/BTP)

**2.2.4. Nhận gì, từ ai, qua kênh nào**

- Chuyên viên Điều phối vật tư bao bì · V1 · C2 · _as-is (thực tế), độ tin vừa_: Tra cứu số lượng tồn kho VTBB trên Google Drive để kiểm tra khả năng đáp ứng đơn hàng
- Tài liệu: 4. XUẤT NHẬP TỒN - VTBB.xlsx · sheet MỤC LỤC · _as-is (thực tế), độ tin cao_: Dữ liệu đơn đặt hàng thành phẩm lấy tự động từ sheet Điều phối Thành phẩm để phục vụ kiểm tra và duyệt điều kiện tồn kho VTBB.
- Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V2 · C1 · _as-is (thực tế), độ tin vừa_: Đơn hàng từ Phòng Kinh doanh gửi qua Drive điều phối thành phẩm để kiểm tra điều kiện NL/BTP
- Chuyên viên Điều phối vật tư bao bì · V3 · C2 · _as-is (thực tế), độ tin cao_: Hình Mockup đơn hàng từ Bộ phận Thiết kế để phục vụ việc kiểm tra và phê duyệt vật tư bao bì

**2.2.5. Làm ra gì, giao cho ai, qua kênh nào**

- Chuyên viên Điều phối vật tư bao bì · V1 · C2 · _as-is (thực tế), độ tin vừa_: Kết quả xác nhận điều kiện tồn kho VTBB cho đơn hàng phản hồi qua Drive
- Chuyên viên Điều phối vật tư bao bì · V2 · C3 · _as-is (thực tế), độ tin cao_: Kết quả xác nhận điều kiện VTBB được cập nhật tại mục DUYỆT VẬT TƯ BAO BÌ TRẢ VỀ Điều phối thuộc sheet Điều Phối trên Drive làm việc
- Chuyên viên Điều phối vật tư bao bì · V6 · C3 · _as-is (thực tế), độ tin cao_: Phiếu đề nghị mua hàng hóa dịch vụ gửi Bộ phận Thu mua theo quy định của PTCKT khi tồn kho VTBB không đủ hoặc bị trễ tiến độ đơn hàng.

**2.2.6. Công cụ dùng ở bước này**

- Chuyên viên Điều phối vật tư bao bì · V1 · C2 · _as-is (thực tế), độ tin vừa_: Google Drive / Google Sheets tra cứu tồn kho VTBB và phản hồi điều kiện đơn hàng
- Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V2 · C1 · _as-is (thực tế), độ tin vừa_: Google Drive dùng để kiểm tra thông tin và điều kiện NL/BTP
- Chuyên viên Điều phối vật tư bao bì · V2 · C2 · _as-is (thực tế), độ tin cao_: Drive làm việc kiểm tra tồn kho và duyệt VTBB (Google Sheets)

**2.2.7. Bắt đầu khi nào**

- Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V2 · C1 · _as-is (thực tế), độ tin vừa_: Nhận yêu cầu đơn hàng từ Phòng Kinh doanh trên Drive điều phối thành phẩm để kiểm tra điều kiện NL/BTP
- Chuyên viên Điều phối vật tư bao bì · V2 · C2 · _as-is (thực tế), độ tin cao_: Nhận thông tin đơn hàng từ Phòng Kinh doanh thông qua Drive Điều phối thành phẩm hoặc trực tiếp từ cấp quản lý

**2.2.8. Ai chịu trách nhiệm cuối**

- Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V2 · C2 · _as-is (thực tế), độ tin vừa_ · **mâu thuẫn: M05, M07, M09, M10, M11**: Phòng Kinh doanh xem xét và quyết định phương án duyệt hoặc hoãn đơn hàng khi NL/BTP không đủ hoặc không kịp tiến độ
- Trưởng nhóm Điều phối · V2 · C4 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: M03, M11**: Quản lý sản xuất là người quyết định cuối cùng (cho duyệt trước bổ sung sau hoặc tạm ngưng đơn) dựa trên dữ liệu kiểm tra từ các nhóm nội bộ; Trưởng nhóm Điều phối cập nhật tiến độ lại cho Kinh doanh
- Trưởng phòng (Chị Ngân) · V3 · C4 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: M02, M04, M06, M10**: Trưởng phòng (Quản lý sản xuất) chịu trách nhiệm cuối quyết định duyệt cho đơn hàng triển khai (kể cả trường hợp duyệt trước bổ sung sau)
- Chuyên viên Pháp lý - Xử lý sự cố · V3 · C1 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: M09**: Quản lý sản xuất là người quyết định cuối cùng việc duyệt cho đơn hàng triển khai hay không khi hồ sơ pháp lý chưa đạt hoặc chưa đủ
- Trưởng nhóm Quản lý dữ liệu · V3 · C1 · _as-is (thực tế), độ tin vừa_ · **mâu thuẫn: M06, M07**: Nhân sự phụ trách thông báo trực tiếp cho Phòng Kinh doanh và Quản lý để xem xét, quyết định tiếp tục triển khai hoặc tạm dừng đơn hàng khi điều kiện triển khai chưa đáp ứng
- Chuyên viên Điều phối vật tư bao bì · V3 · C3 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: M04, M05**: Trưởng phòng sản xuất hoặc Phòng Kinh doanh quyết định cuối cùng về việc duyệt tiếp hay dừng đơn khi tồn kho VTBB không đủ hoặc không kịp tiến độ đơn hàng
- Trưởng nhóm Quản lý dữ liệu · V6 · C1 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: M01, M02, M03**: Phòng Kinh doanh là đơn vị xem xét và quyết định việc tiếp tục triển khai hoặc tạm dừng đơn hàng khi kiểm tra điều kiện có vướng mắc; Điều phối thành phẩm phối hợp kiểm tra và thông báo
- Chuyên viên Điều phối vật tư bao bì · V4 · C1 · _giả thuyết, độ tin thấp_ · *Suy diễn (AI)* · **mâu thuẫn: M01**: Trưởng phòng sản xuất (khi các phương án kiểm tra tồn kho luân chuyển nội bộ, thương lượng Kinh doanh dời ngày và trao đổi Thu mua mua hàng không giải quyết được)

**2.2.9. Chỗ tắc, sai, làm lại, phụ thuộc một người ở bước này**

- Chuyên viên Pháp lý - Xử lý sự cố · V2 · C3 · _as-is (thực tế), độ tin cao_: Khâu kiểm tra pháp lý đơn hàng bị chậm do các điều khoản thỏa thuận với NCC GC chưa thống nhất không đưa vào hợp đồng, trong khi Kế toán yêu cầu phải thể hiện đầy đủ trên chứng từ.

**2.2.10. Ai được hỏi ý, ai được báo**

- Trưởng phòng (Chị Ngân) · V3 · C4 · _giả thuyết, độ tin cao_: Trưởng nhóm Quản lý dữ liệu kiểm tra cuối và tham mưu về điều kiện pháp lý đơn hàng

**2.2.11. Bao lâu một lần**

- Trưởng nhóm Điều phối · V4 · C2 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L01**: Trung bình khoảng 15 đơn/tuần cho 3 loại: đơn đặt hàng thành phẩm (chiếm tỷ trọng lớn), đơn đặt hàng bán thành phẩm, và đơn xử lý lại do phát sinh sự cố
- Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V3 · C1 · _as-is (thực tế), độ tin cao_: Kiểm tra điều kiện NL/BTP khi phát sinh đơn hàng từ Phòng Kinh doanh trên Drive điều phối thành phẩm, tùy theo số lượng đơn hàng và yêu cầu tiến độ thực tế, không cố định số đơn mỗi ngày
- Chuyên viên Điều phối vật tư bao bì · V3 · C1 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L01**: Kiểm tra điều kiện tồn kho VTBB thực hiện hằng ngày do đơn hàng phát sinh liên tục trong ngày (10–15 đơn/ngày) và tra cứu đột xuất để báo cáo theo yêu cầu cấp trên

**2.2.12. Mất bao lâu**

- Chuyên viên Điều phối vật tư bao bì · V3 · C2 · _as-is (thực tế), độ tin cao_: Mất 30 phút đến 1 giờ để kiểm tra tồn kho VTBB; thời gian duyệt và trả kết quả duyệt VTBB mất 1 buổi đến 1 ngày do phụ thuộc tiến độ gửi hình Mockup đơn hàng từ Bộ phận Thiết kế

#### Bước 3. Chuẩn bị nguồn lực và hoàn thiện điều kiện đặt hàng

**2.3.1. Ai chịu trách nhiệm cuối**

- Tài liệu: QUY TRÌNH SẢN XUẤT 09.07.2026 (2).xlsx · sheet 4. QT QL ĐƠN HÀNG SX GC · _as-is (thực tế), độ tin cao_: Quản lý sản xuất

**2.3.2. Có phải xin duyệt không, ai duyệt, ngưỡng nào**

- Tài liệu: QUY TRÌNH SẢN XUẤT 09.07.2026 (2).xlsx · sheet 4. QT QL ĐƠN HÀNG SX GC · _as-is (thực tế), độ tin cao_: Quản lý sản xuất ký duyệt Phiếu duyệt giá gồm 3 mức giá trước khi gửi đơn NCC GC

**2.3.3. Ai làm**

- Tài liệu: QUY TRÌNH SẢN XUẤT 09.07.2026 (1).xlsx · sheet 4. QT QL ĐƠN HÀNG SX GC · _as-is (thực tế), độ tin cao_: Chuyên viên Giá vốn và Xử lý dữ liệu
- Trưởng nhóm Điều phối · V4 · C1 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: M08**: Chuyên viên Quản lý hồ sơ sản xuất và Dữ liệu NCC GC làm đầu mối giao dịch với NCC GC về việc điều chuyển nguyên liệu

**2.3.4. Làm ra gì, giao cho ai, qua kênh nào**

- Tài liệu: QUY TRÌNH SẢN XUẤT 09.07.2026 (1).xlsx · sheet 4. QT QL ĐƠN HÀNG SX GC · _as-is (thực tế), độ tin cao_: Phiếu duyệt giá gồm 3 mức giá trình QLSX duyệt và cập nhật giá vốn đã duyệt vào Drive Điều phối thành phẩm
- Chuyên viên Giá vốn và Xử lý dữ liệu · V1 · C2 · _as-is (thực tế), độ tin cao_: Dữ liệu chi phí đơn hàng và cập nhật giá NL/BTP/VTBB cung cấp cho Phòng Kinh doanh
- Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V1 · C2 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L03**: Phiếu yêu cầu phối trộn hoặc điều chuyển nguyên liệu gửi Phòng Kinh doanh, Bộ phận Kho và Nhà gia công để phối hợp thực hiện
- Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V2 · C5 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: M08, L03**: Phiếu yêu cầu điều chuyển nguyên liệu được lập và gửi cho Điều phối thành phẩm để gửi tiếp cho NCC GC phối hợp xuất và điều chuyển

**2.3.5. Nhận gì, từ ai, qua kênh nào**

- Tài liệu: QUY TRÌNH SẢN XUẤT 09.07.2026 (1).xlsx · sheet 4. QT QL ĐƠN HÀNG SX GC · _as-is (thực tế), độ tin cao_: Đơn hàng và bảng định mức TP từ Điều phối thành phẩm

**2.3.6. Làm gì trong bước, tra cứu gì**

- Chuyên viên Giá vốn và Xử lý dữ liệu · V1 · C1 · _as-is (thực tế), độ tin cao_: 8 bước lập Phiếu duyệt giá: 1. Kiểm tra đơn hàng từ KD; 2. Kiểm tra định mức BDM/BOM; 3. Kiểm tra chính sách NCC; 4. Cập nhật báo giá mới nhất NL/BTP/VTBB; 5. Tính toán chi phí; 6. Tổng hợp kiểm tra tính hợp lý giá thành; 7. Lập Phiếu duyệt giá trình duyệt; 8. Cập nhật kết quả gửi KD và các bộ phận liên quan.

**2.3.7. Bắt đầu khi nào**

- Chuyên viên Giá vốn và Xử lý dữ liệu · V1 · C1 · _as-is (thực tế), độ tin cao_: Nhận thông tin đơn hàng cần duyệt giá từ Phòng Kinh doanh và thông tin định mức thành phẩm

**2.3.8. Công cụ dùng ở bước này**

- Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V1 · C2 · _as-is (thực tế), độ tin cao_: Google Drive dùng cập nhật và theo dõi dữ liệu phối trộn BTP và điều chuyển nguyên liệu

**2.3.9. Bao lâu một lần**

- Chuyên viên Giá vốn và Xử lý dữ liệu · V2 · C1 · _as-is (thực tế), độ tin vừa_ · **mâu thuẫn: L01**: Trung bình khoảng 15 đơn hàng/tuần, tùy theo tình hình sản xuất và số lượng đơn hàng gia công phát sinh từng thời điểm

**2.3.10. Chỗ tắc, sai, làm lại, phụ thuộc một người ở bước này**

- Chuyên viên Giá vốn và Xử lý dữ liệu · V3 · C3 · _as-is (thực tế), độ tin cao_: Thường phải chờ NCC GC xác nhận giá, điều kiện áp dụng hoặc tính toán lại khi giá và thông tin đơn hàng thay đổi

**2.3.11. Mất bao lâu**

- Chuyên viên Giá vốn và Xử lý dữ liệu · V4 · C1 · _as-is (thực tế), độ tin cao_: Mất khoảng 15–30 phút cho mỗi Phiếu duyệt giá khi đủ thông tin; thời gian kéo dài hơn nếu cần xác minh hoặc cập nhật lại dữ liệu giá NCC GC

#### Bước 4. Gửi đơn đặt hàng và theo dõi tiến độ sản xuất

**2.4.1. Mất bao lâu**

- Tài liệu: QUY TRÌNH SẢN XUẤT 09.07.2026 (1).xlsx · sheet 4. QT QL ĐƠN HÀNG SX GC · _as-is (thực tế), độ tin cao_: Chậm nhất 3 ngày sau khi nhận đơn phải cập nhật tiến độ xử lý; kiểm tra tiến độ với NCC sau 2 ngày làm việc kể từ ngày gửi đơn

**2.4.2. Chỗ tắc, sai, làm lại, phụ thuộc một người ở bước này**

- Tài liệu: NỘI DUNG HỌP 25.09.26.xlsx · sheet Chi tiết vướng mắt từng NCC · _as-is (thực tế), độ tin cao_: Gửi đơn đặt hàng có đơn giá vướng bảo mật thông tin khi điều phối gửi; nhiều nhà cung cấp từ chối ký đơn đặt hàng vì đã có hóa đơn hoặc hợp đồng

**2.4.3. Ai làm**

- Chuyên viên Điều phối sản xuất · V1 · C2 · _as-is (thực tế), độ tin cao_: Chuyên viên Điều phối sản xuất
- Trưởng phòng (Chị Ngân) · V4 · C1 · _giả thuyết, độ tin cao_: Chuyên viên Điều phối sản xuất phụ trách gửi đơn đặt hàng và theo dõi tiến độ đơn hàng thành phẩm và đơn xử lý lại
- Trưởng phòng (Chị Ngân) · V4 · C1 · _giả thuyết, độ tin vừa_: Chuyên viên Điều phối nguyên liệu/bán thành phẩm phụ trách gửi đơn đặt hàng và theo dõi tiến độ đơn hàng bán thành phẩm

**2.4.4. Làm gì trong bước, tra cứu gì**

- Chuyên viên Điều phối sản xuất · V1 · C2 · _as-is (thực tế), độ tin cao_: Cập nhật và theo dõi trên Drive làm việc điều phối qua các sheet: ĐIỀU PHỒI (còn cấu thành), DUYỆT ĐƠN HÀNG, GỬI ĐƠN NCC (kèm công thức NL và link VTBB từ drive)

**2.4.5. Công cụ dùng ở bước này**

- Chuyên viên Điều phối sản xuất · V1 · C2 · _as-is (thực tế), độ tin cao_: Drive làm việc điều phối (Google Sheets các sheet: ĐIỀU PHỒI, DUYỆT ĐƠN HÀNG, GỬI ĐƠN NCC)

**2.4.6. Nhận gì, từ ai, qua kênh nào**

- Trưởng nhóm Điều phối · V4 · C1 · _as-is (thực tế), độ tin vừa_: Thông tin xác nhận đủ điều kiện NL/BTP cho đơn hàng và ngày có đủ nguyên liệu để triển khai đơn
- Chuyên viên Điều phối sản xuất · V3 · C2 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: M08**: Tiếp nhận Phiếu yêu cầu điều chuyển nguyên liệu từ Điều phối NL/BTP để làm căn cứ làm việc với NCC GC

**2.4.7. Ai chịu trách nhiệm cuối**

- Trưởng phòng (Chị Ngân) · V4 · C1 · _giả thuyết, độ tin vừa_: Trưởng nhóm Điều phối quản lý chung và chịu trách nhiệm tiến độ gửi đơn đặt hàng và theo dõi sản xuất
- Trưởng nhóm Điều phối · V5 · C2 · _giả thuyết, độ tin thấp_ · *Suy diễn (AI)*: Trưởng nhóm Điều phối là cấp trên tiếp nhận báo cáo và chịu trách nhiệm khi có phát sinh trong việc gửi đơn đặt hàng và theo dõi tiến độ

**2.4.8. Làm ra gì, giao cho ai, qua kênh nào**

- Chuyên viên Điều phối sản xuất · V2 · C2 · _as-is (thực tế), độ tin cao_: Báo cáo gửi kho được lập hằng ngày vào 16h chiều trên Drive làm việc điều phối gửi cho Bộ phận Kho để thông báo lịch và thông tin giao nhận hàng

#### Bước 5. Theo dõi kết quả sản xuất, tiếp nhận hàng và xử lý sai lệch

**2.5.1. Chỗ tắc, sai, làm lại, phụ thuộc một người ở bước này**

- Tài liệu: Bản sao của ĐIỀU PHỒI THÀNH PHẨM (NHÁP).xlsx · sheet MỤC LỤC · _as-is (thực tế), độ tin cao_: Chưa quy định rõ số ngày tối đa kể từ khi nhận hàng để Điều phối thành phẩm làm việc với NCC GC khi phát sinh lỗi sản phẩm sau kiểm tra KCS tại kho.
- Trưởng nhóm Điều phối · V5 · C1 · _as-is (thực tế), độ tin cao_: Quy trình xử lý sự cố hàng hóa chưa có quy định cụ thể về thời hạn cho từng công đoạn xử lý và khiếu nại với nhà cung cấp

**2.5.2. Làm ra gì, giao cho ai, qua kênh nào**

- Chuyên viên Điều phối sản xuất · V1 · C3 · _as-is (thực tế), độ tin cao_: Báo cáo gửi kho, danh sách nhận hàng, phiếu nhập kho TP và phiếu xuất bán hàng gửi Bộ phận Kho

**2.5.3. Làm gì trong bước, tra cứu gì**

- Trưởng nhóm Điều phối · V2 · C7 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L10**: Kiểm tra mẫu thành phẩm tại Lab nội bộ khi nhận hàng từ NCC GC chỉ kiểm tra ngoại dạng, màu sắc, trọng lượng; chỉ kiểm tra hàm lượng hoạt chất hoặc chỉ tiêu chuyên môn sâu khi có yêu cầu hoặc phát sinh sự cố
- Trưởng nhóm Điều phối · V5 · C3 · _as-is (thực tế), độ tin cao_: Khi có hàng tại NCC GC, Điều phối báo Kho cân đối chuyến nhận; sau đó Điều phối chốt lịch, số lượng, chủng loại và thông tin xe, tài xế với NCC GC

**2.5.4. Ai làm**

- Trưởng nhóm Điều phối · V4 · C3 · _giả thuyết, độ tin thấp_ · *Suy diễn (AI)*: Chuyên viên Pháp lý - Xử lý sự cố tiếp nhận và theo dõi tiến độ xử lý khi phát hiện lỗi hoặc sự cố liên quan đến hàng hóa thành phẩm
- Trưởng nhóm Điều phối · V5 · C3 · _as-is (thực tế), độ tin cao_: Chuyên viên Điều phối sản xuất tiếp nhận thông tin từ Kho, chốt lịch, số lượng, loại và thông tin xe - tài xế nhận với NCC GC

**2.5.5. Ai chịu trách nhiệm cuối**

- Trưởng nhóm Điều phối · V4 · C4 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L05**: Trưởng nhóm Điều phối quyết định phương án xử lý cuối cùng sau khi tổng hợp ý kiến từ NCC GC, các bộ phận liên quan và Kinh doanh

**2.5.6. Nhận gì, từ ai, qua kênh nào**

- Chuyên viên Điều phối sản xuất · V2 · C2 · _as-is (thực tế), độ tin cao_: Kết quả số lượng nhận hàng thực tế cập nhật trên Drive và các chứng từ giao nhận gửi qua Zalo từ Bộ phận Kho
- Trưởng nhóm Điều phối · V5 · C4 · _as-is (thực tế), độ tin cao_: Kết quả giao nhận (đúng hàng, lượng, ngày, chứng từ) hoặc phản ánh phát sinh lỗi khi nhận hàng tại NCC GC từ Bộ phận Kho

**2.5.7. Mất bao lâu**

- Trưởng nhóm Điều phối · V5 · C1 · _as-is (thực tế), độ tin cao_: Chưa có quy định thời hạn cụ thể cho các công đoạn xử lý sự cố hàng hóa; tiếp nhận và bám sát xử lý hằng ngày

**2.5.8. Xong bước này thì tới bước nào, rẽ nhánh khi nào**

- Trưởng nhóm Điều phối · V5 · C4 · _as-is (thực tế), độ tin cao_: Khi hàng về kho phát sinh lỗi thì chuyển sang Quy trình xử lý sự cố; nếu hàng còn tại NCC GC thì báo Điều phối TP xem xét xử lý nhanh hoặc đưa vào quy trình xử lý sự cố

**2.5.9. Bắt đầu khi nào**

- Chuyên viên Điều phối sản xuất · V3 · C3 · _as-is (thực tế), độ tin cao_: Bắt đầu theo dõi và đối chiếu từ lúc đơn hàng được Kinh doanh lên đơn hoặc có các yêu cầu xử lý lại

#### Bước 6. Hoàn thiện chứng từ, đối chiếu và kết thúc đơn hàng

**2.6.1. Làm ra gì, giao cho ai, qua kênh nào**

- Chuyên viên Giá vốn và Xử lý dữ liệu · V1 · C3 · _as-is (thực tế), độ tin cao_: Dữ liệu giá NL/BTP/VTBB thực tế phát sinh sau sản xuất bàn giao cho Phòng Kế toán
- Kế toán sản xuất · V1 · C1 · _as-is (thực tế), độ tin vừa_: Bộ chứng từ quyết toán đơn hàng gia công gồm 11 loại chứng từ bàn giao cho Phòng Kế toán dưới dạng hồ sơ bản cứng có chữ ký sống hoặc chữ ký số.

**2.6.2. Làm gì trong bước, tra cứu gì**

- Tài liệu: 4. XUẤT NHẬP TỒN - VTBB.xlsx · sheet HƯỚNG DẪN · _as-is (thực tế), độ tin cao_: Quy trình đối chiếu số liệu xuất nhập tồn VTBB với NCC GC: nhập số liệu NCC gửi, hệ thống tự động tính chênh lệch giao nhận và chênh lệch tồn cuối kỳ để kết luận Khớp hoặc Lệch.
- Trưởng nhóm Quản lý dữ liệu · V2 · C2 · _as-is (thực tế), độ tin cao_: Phân công mỗi nhân sự trong nhóm phụ trách các nhà cung cấp gia công cụ thể để trực tiếp thu thập chứng từ, đối chiếu số liệu và lập hồ sơ hoàn tất đơn hàng của NCC đó

**2.6.3. Chỗ tắc, sai, làm lại, phụ thuộc một người ở bước này**

- Trưởng nhóm Quản lý dữ liệu · V1 · C3 · _as-is (thực tế), độ tin cao_: Dữ liệu MISA kế toán bị sai hoặc cập nhật chậm; chứng từ không đúng phải chỉnh sửa nhiều lần và có sai lệch giữa số liệu nội bộ với thuế
- Tài liệu: NỘI DUNG HỌP 25.09.26.xlsx · sheet Chi tiết vướng mắt từng NCC · _as-is (thực tế), độ tin cao_: Nhiều NCC phàn nàn và từ chối ký Giấy đề nghị thanh toán do thủ tục phức tạp, khiến việc hoàn tất hồ sơ và thanh toán cho NCC bị chậm

**2.6.4. Công cụ dùng ở bước này**

- Chuyên viên Quản lý hồ sơ sản xuất và Dữ liệu NCC GC · V1 · C3 · _giả thuyết, độ tin thấp_ · *Suy diễn (AI)*: Sử dụng các công cụ làm việc tương tự vị trí Quản lý dữ liệu

**2.6.5. Nhận gì, từ ai, qua kênh nào**

- Kế toán sản xuất · V1 · C1 · _as-is (thực tế), độ tin vừa_: Bộ chứng từ quyết toán đơn hàng gia công gồm 11 loại chứng từ (Giấy đề nghị thanh toán, Giấy đề nghị thanh toán của NCC, Phiếu mua hàng hóa, Hóa đơn, Hợp đồng có giá, Hợp đồng không giá, Đơn đặt hàng, Giấy nhập kho, Giấy xuất kho/Phiếu giao hàng, Bảng xác nhận công nợ, Phiếu đề xuất mua) tiếp nhận dưới dạng hồ sơ bản cứng có chữ ký sống hoặc chữ ký số.

**2.6.6. Ai chịu trách nhiệm cuối**

- Trưởng nhóm Quản lý dữ liệu · V2 · C3 · _as-is (thực tế), độ tin cao_: Trưởng nhóm Quản lý dữ liệu
- Trưởng phòng (Chị Ngân) · V3 · C5 · _as-is (thực tế), độ tin cao_: Trưởng nhóm Quản lý dữ liệu kiểm tra cuối và chịu trách nhiệm khi khai báo công nợ và hoàn thiện chứng từ

**2.6.7. Bắt đầu khi nào**

- Trưởng nhóm Quản lý dữ liệu · V2 · C4 · _as-is (thực tế), độ tin cao_: Căn cứ vào điều khoản thanh toán trên hợp đồng của từng nhà cung cấp gia công để xác định thời điểm đối chiếu công nợ và lập hồ sơ thanh toán

**2.6.8. Ai làm**

- Trưởng phòng (Chị Ngân) · V3 · C5 · _giả thuyết, độ tin cao_: Chuyên viên Quản lý hồ sơ sản xuất và Dữ liệu NCC GC phụ trách lập biên bản đối chiếu, quản lý hợp đồng và phụ lục với NCC GC
- Trưởng nhóm Quản lý dữ liệu · V3 · C6 · _as-is (thực tế), độ tin cao_: Chuyên viên Quản lý hồ sơ sản xuất và Dữ liệu NCC GC phụ trách các NCC GC được phân công, chịu trách nhiệm theo dõi dữ liệu, đối chiếu công nợ, thu thập chứng từ và hoàn thiện hồ sơ đơn hàng gia công của NCC GC đó
- Chuyên viên Quản lý hồ sơ sản xuất và Dữ liệu NCC GC · V2 · C4 · _giả thuyết, độ tin thấp_ · *Suy diễn (AI)*: Chuyên viên Quản lý hồ sơ sản xuất và Dữ liệu NCC GC (Quản lý dữ liệu) thực hiện hoàn thiện chứng từ, đối chiếu và kết thúc đơn hàng

**2.6.9. Bao lâu một lần**

- Trưởng nhóm Quản lý dữ liệu · V3 · C4 · _as-is (thực tế), độ tin vừa_: Thực hiện theo thời hạn công nợ trong hợp đồng của từng NCC GC; số lượng đơn hàng mỗi tuần tùy thuộc vào tình hình phát sinh thực tế

**2.6.10. Có phải xin duyệt không, ai duyệt, ngưỡng nào**

- Trưởng nhóm Quản lý dữ liệu · V3 · C5 · _as-is (thực tế), độ tin vừa_: Bộ hồ sơ sau khi ký duyệt được chuyển sang Phòng Kế toán theo quy trình; việc trình Trưởng phòng Quản lý sản xuất hoặc cấp khác duyệt lại tùy thuộc vào quy định phê duyệt hiện hành

### 3. Quy trình Làm việc với NCC GC mới

#### Bước 0. Mức quy trình

**3.0.1. Bắt đầu khi nào, do đâu**

- Tài liệu: QUY TRÌNH SẢN XUẤT 09.07.2026 (1).xlsx · sheet 1. QT LÀM VIỆC VỚI NCC MỚI · _as-is (thực tế), độ tin cao_: Nhu cầu sản xuất với NCC GC hiện tại không còn phù hợp (năng lực, chất lượng, giá...) cần tìm NCC GC thay thế, hoặc phát sinh sản phẩm mới NCC hiện tại không sản xuất được.

**3.0.2. Các bước theo thứ tự**

- Tài liệu: QUY TRÌNH SẢN XUẤT 09.07.2026 (1).xlsx · sheet 1. QT LÀM VIỆC VỚI NCC MỚI · _as-is (thực tế), độ tin cao_: Gồm 7 bước: 1. Tiếp nhận yêu cầu -> 2. Tìm NCC -> 3. So sánh, đánh giá sơ bộ -> 4. Liên hệ NCC, thỏa thuận & check pháp lý -> 5. Lấy mẫu và kiểm tra mẫu -> 6. Soạn thảo Hợp đồng, bảng giá -> 7. Hoàn thiện quy trình làm việc NCC mới.

**3.0.3. Kết quả cuối, kết thúc khi nào**

- Giám đốc · V1 · C2 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L07**: Kết quả tìm kiếm và đánh giá NCC mới được Giám đốc phụ trách công ty tương ứng phê duyệt bằng văn bản trước khi đưa vào sản xuất
- Trưởng phòng (Chị Ngân) · V3 · C2 · _as-is (thực tế), độ tin cao_: Quy trình làm việc với NCC GC mới được thống nhất; Team QLDL lưu chính sách/hợp đồng/phụ lục, Team Pháp lý lưu hồ sơ pháp lý, các Team Điều phối cập nhật chính sách làm việc và thông tin liên hệ

**3.0.4. Vị trí chủ trì quy trình**

- Trưởng phòng (Chị Ngân) · V4 · C3 · _as-is (thực tế), độ tin cao_: Trưởng phòng (Quản lý sản xuất) chịu trách nhiệm chủ trì tìm kiếm và phân bổ công việc cho các nhân sự liên quan

#### Bước 5. Lấy mẫu và kiểm tra mẫu tại Lab

**3.5.1. Ai làm**

- Trưởng phòng (Chị Ngân) · V4 · C5 · _giả thuyết, độ tin vừa_: Chuyên viên Điều phối nguyên liệu/bán thành phẩm phụ trách lấy mẫu sản phẩm thử nghiệm từ NCC mới gửi Lab kiểm tra

**3.5.2. Ai chịu trách nhiệm cuối**

- Trưởng phòng (Chị Ngân) · V4 · C5 · _giả thuyết, độ tin vừa_: Bộ phận Lab chịu trách nhiệm chuyên môn đánh giá và kết luận mẫu sản phẩm thử nghiệm đạt yêu cầu

#### Bước 6. Soạn thảo Hợp đồng và bảng giá

**3.6.1. Ai làm**

- Trưởng phòng (Chị Ngân) · V4 · C4 · _giả thuyết, độ tin vừa_: Chuyên viên Quản lý hồ sơ sản xuất và Dữ liệu NCC GC (team Quản lý dữ liệu) trực tiếp soạn thảo hợp đồng và bảng giá với NCC mới

**3.6.2. Có phải xin duyệt không, ai duyệt, ngưỡng nào**

- Giám đốc · V2 · C2 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L07**: Hợp đồng và bảng giá với NCC mới bắt buộc phải trình Đại diện pháp luật của Công ty ký duyệt

**3.6.3. Ai chịu trách nhiệm cuối**

- Trưởng nhóm Quản lý dữ liệu · V4 · C1 · _giả thuyết, độ tin vừa_: Chuyên viên Quản lý hồ sơ sản xuất và Dữ liệu NCC GC (nhân sự phụ trách NCC) chịu trách nhiệm kiểm tra tính chính xác của điều khoản hợp đồng và đơn giá trước khi trình cấp có thẩm quyền xem xét, phê duyệt

#### Bước 7. Hoàn thiện quy trình làm việc NCC GC mới

**3.7.1. Có phải xin duyệt không, ai duyệt, ngưỡng nào**

- Giám đốc · V2 · C3 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L07**: Trưởng phòng (Quản lý sản xuất) là người quyết định quy trình làm việc với NCC GC mới sau khi tham mưu ý kiến từ Kinh doanh; Hợp đồng trình Đại diện pháp luật ký

**3.7.2. Ai chịu trách nhiệm cuối**

- Giám đốc · V2 · C3 · _as-is (thực tế), độ tin cao_: Trưởng phòng (Quản lý sản xuất) chịu trách nhiệm quyết định quy trình làm việc với NCC GC mới sau khi tham mưu ý kiến từ Kinh doanh

**3.7.3. Ai được hỏi ý, ai được báo**

- Giám đốc · V2 · C3 · _as-is (thực tế), độ tin cao_: Phòng Kinh doanh được hỏi ý kiến tham mưu trước khi Trưởng phòng quyết định quy trình làm việc NCC GC mới

**3.7.4. Ai làm**

- Trưởng nhóm Quản lý dữ liệu · V5 · C1 · _giả thuyết, độ tin vừa_: Chuyên viên Quản lý hồ sơ sản xuất và Dữ liệu NCC GC (nhân sự phụ trách NCC gia công mới) trực tiếp tổng hợp, soạn thảo nội dung quy trình làm việc và phối hợp với các bên liên quan

**3.7.5. Bắt đầu khi nào**

- Trưởng nhóm Quản lý dữ liệu · V6 · C2 · _as-is (thực tế), độ tin vừa_: Bắt đầu sau khi hoàn tất việc thống nhất thông tin hợp tác với NCC gia công mới (giá, điều kiện gia công và các chính sách liên quan)

**3.7.6. Công cụ dùng ở bước này**

- Trưởng nhóm Quản lý dữ liệu · V6 · C3 · _as-is (thực tế), độ tin vừa_: Word và Excel dùng để soạn thảo quy trình làm việc với nhà cung cấp gia công mới
- Trưởng nhóm Quản lý dữ liệu · V6 · C3 · _as-is (thực tế), độ tin vừa_: Google Drive và máy tính dùng để lưu trữ quy trình làm việc với NCC GC mới
- Trưởng nhóm Quản lý dữ liệu · V6 · C3 · _as-is (thực tế), độ tin vừa_: Nhóm Zalo và Email dùng trao đổi, thống nhất nội dung quy trình trước khi trình duyệt

**3.7.7. Bao lâu một lần**

- Trưởng nhóm Quản lý dữ liệu · V6 · C4 · _as-is (thực tế), độ tin vừa_: Tần suất phát sinh không cố định, phụ thuộc nhu cầu thực tế và phát sinh đột xuất

### 4. Quy trình Xử lý sự cố trong sản xuất

#### Bước 0. Mức quy trình

**4.0.1. Các bước theo thứ tự**

- Chuyên viên Pháp lý - Xử lý sự cố · V3 · C2 · _giả thuyết, độ tin thấp_ · *Suy diễn (AI)*: Quy trình xử lý sự cố trong sản xuất gồm 5 bước: 1. Xác định nguyên nhân -> 2. Tìm phương án phù hợp -> 3. Chuẩn bị thủ tục và phối hợp liên quan -> 4. Theo dõi tiến độ xử lý -> 5. Cập nhật và lưu trữ

**4.0.2. Bắt đầu khi nào, do đâu**

- Trưởng nhóm Điều phối · V4 · C3 · _as-is (thực tế), độ tin cao_: Bộ phận phát hiện lỗi hoặc sự cố liên quan đến hàng hóa thành phẩm thông báo về bộ phận xử lý sự cố để tiếp nhận và theo dõi tiến độ xử lý

**4.0.3. Kết quả cuối, kết thúc khi nào**

- Chuyên viên Pháp lý - Xử lý sự cố · V5 · C1 · _as-is (thực tế), độ tin cao_: Kết quả xử lý sự cố gồm 4 phương án: (1) Chấp nhận hàng không cần xử lý lại; (2) Gửi yêu cầu xử lý lại với NCC GC; (3) Hủy, cấn trừ công nợ hoặc hạch toán chi phí; (4) Tạm thời chờ ý kiến từ bộ phận liên quan.

#### Bước 1. Xác định nguyên nhân

**4.1.1. Ai làm**

- Chuyên viên Pháp lý - Xử lý sự cố · V5 · C2 · _as-is (thực tế), độ tin cao_: Chuyên viên Xử lý sự cố (Chuyên viên Pháp lý - Xử lý sự cố) phụ trách tổng hợp đủ thông tin để xác định nguyên nhân lỗi

**4.1.2. Làm gì trong bước, tra cứu gì**

- Chuyên viên Pháp lý - Xử lý sự cố · V5 · C2 · _as-is (thực tế), độ tin cao_: Tùy theo phân loại sự cố, kiểm tra bằng mắt thường, gửi mẫu sang Lab kiểm tra hoặc tra cứu lại dữ liệu và chứng từ để tổng hợp đủ thông tin xác định nguyên nhân lỗi

**4.1.3. Ai chịu trách nhiệm cuối**

- Chuyên viên Pháp lý - Xử lý sự cố · V6 · C1 · _as-is (thực tế), độ tin cao_: Thẩm quyền kết luận nguyên nhân tùy thuộc vào tính chất sự cố và ý kiến từ các bộ phận chuyên môn liên quan (Lab, Kinh doanh, NCC GC...); Trưởng nhóm Quản lý dữ liệu là cấp quản lý kiểm tra công việc của chuyên viên

#### Bước 2. Tìm phương án phù hợp

**4.2.1. Ai chịu trách nhiệm cuối**

- Chuyên viên Pháp lý - Xử lý sự cố · V5 · C3 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L05**: Trưởng nhóm Quản lý dữ liệu phê duyệt phương án trong thẩm quyền; nếu phát sinh ngoài quy trình, vượt thẩm quyền hoặc có rủi ro thì Trưởng phòng (Quản lý sản xuất) quyết định

**4.2.2. Có phải xin duyệt không, ai duyệt, ngưỡng nào**

- Chuyên viên Pháp lý - Xử lý sự cố · V5 · C3 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L05**: Phương án xử lý sự cố do Trưởng nhóm Quản lý dữ liệu phê duyệt; trường hợp phát sinh ngoài quy trình, vượt thẩm quyền hoặc có rủi ro phải trình Trưởng phòng (Quản lý sản xuất) phê duyệt

**4.2.3. Ai được hỏi ý, ai được báo**

- Chuyên viên Pháp lý - Xử lý sự cố · V5 · C3 · _as-is (thực tế), độ tin cao_: Phòng Kinh doanh tham mưu ý kiến trong quá trình phê duyệt phương án xử lý sự cố trên cơ sở thống nhất chung

**4.2.4. Ai làm**

- Chuyên viên Pháp lý - Xử lý sự cố · V6 · C2 · _as-is (thực tế), độ tin cao_: Trưởng nhóm Quản lý dữ liệu phụ trách xây dựng phương án xử lý sự cố dựa vào kinh nghiệm và tình hình mới, cung cấp công cụ và hướng dẫn chuyên viên thực hiện
- Chuyên viên Pháp lý - Xử lý sự cố · V6 · C2 · _as-is (thực tế), độ tin cao_: Chuyên viên xử lý sự cố (Chuyên viên Pháp lý - Xử lý sự cố) trực tiếp thực hiện tìm phương án theo hướng dẫn và công cụ của Trưởng nhóm Quản lý dữ liệu

#### Bước 3. Chuẩn bị thủ tục và công việc phối hợp liên quan

**4.3.1. Ai làm**

- Chuyên viên Pháp lý - Xử lý sự cố · V6 · C3 · _as-is (thực tế), độ tin cao_: Chuyên viên xử lý sự cố (Chuyên viên Pháp lý - Xử lý sự cố) là người điều phối, chủ động phối hợp với các bộ phận để tổng hợp và chuẩn bị đầy đủ thủ tục, giấy tờ

**4.3.2. Ai được hỏi ý, ai được báo**

- Chuyên viên Pháp lý - Xử lý sự cố · V6 · C3 · _as-is (thực tế), độ tin cao_: Phối hợp với Điều phối NL/BTP khi xuất/chuyển/nhập NL/BTP, Điều phối VTBB khi xuất/chuyển/nhập VTBB, và Chuyên viên QLDL về thủ tục, giấy tờ, công nợ với NCC GC

#### Bước 4. Theo dõi tiến độ xử lý

**4.4.1. Ai làm**

- Chuyên viên Pháp lý - Xử lý sự cố · V6 · C1 · _as-is (thực tế), độ tin cao_: Chuyên viên xử lý sự cố (Chuyên viên Pháp lý - Xử lý sự cố) chịu trách nhiệm bám tiến độ đến cùng kể từ khi tiếp nhận yêu cầu xử lý sự cố

#### Bước 5. Cập nhật và lưu trữ

**4.5.1. Ai làm**

- Chuyên viên Pháp lý - Xử lý sự cố · V6 · C4 · _as-is (thực tế), độ tin cao_: Chuyên viên xử lý sự cố (Chuyên viên Pháp lý - Xử lý sự cố) phụ trách bám tiến độ, cập nhật kết quả và lưu trữ hồ sơ liên quan

### 5. Đối tác bên ngoài và phòng ban liên quan

**5.0.1. Bên ngoài công ty có qua lại**

- Tài liệu: QUY TRÌNH SẢN XUẤT 09.07.2026 (1).xlsx · sheet 17. TT NCC GC · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L08**: Nhà cung cấp gia công Hà Long (gia công thuốc BVTV, có app theo dõi tiến độ, đơn tối thiểu 10 thùng, thời gian 5-14 ngày)
- Tài liệu: QUY TRÌNH SẢN XUẤT 09.07.2026 (1).xlsx · sheet 17. TT NCC GC · _as-is (thực tế), độ tin cao_: Nhà cung cấp gia công Yamato (gia công thuốc BVTV, thời gian 3-5 ngày, đơn dưới 500kg chờ ghép đơn lâu, không đóng túi nhỏ 10g-15g)
- Tài liệu: QUY TRÌNH SẢN XUẤT 09.07.2026 (1).xlsx · sheet 17. TT NCC GC · _as-is (thực tế), độ tin cao_: Nhà cung cấp gia công An Nông (gia công thuốc BVTV, MOQ 30 thùng, phải duyệt mẫu VTBB trước khi mang sang)
- Tài liệu: QUY TRÌNH SẢN XUẤT 09.07.2026 (1).xlsx · sheet 10. QT QL DVVC · _as-is (thực tế), độ tin cao_: Dịch vụ vận chuyển Grab (vận chuyển mẫu thành phẩm cho Lab R&D và chuyển hàng nội bộ)
- Tài liệu: 4. XUẤT NHẬP TỒN - VTBB.xlsx · sheet DATA 1 · _as-is (thực tế), độ tin cao_: Nhà cung cấp gia công Basel (KCN Hải Sơn, có chi phí lưu kho 5.000đ/ngày/thùng)
- Trưởng nhóm Điều phối · V2 · C6 · _as-is (thực tế), độ tin vừa_: Nhà cung cấp gia công Hà Long áp dụng chính sách tính phí lưu kho 86.400đ/tháng/pallet/1,1m2 (theo dõi điều chỉnh khi NCC có thông báo mới)
- Trưởng phòng (Chị Ngân) · V4 · C6 · _as-is (thực tế), độ tin cao_: Trung tâm kiểm nghiệm bên ngoài được thuê để thực hiện kiểm nghiệm chuyên sâu đối với mẫu sản phẩm khi Lab không đủ thiết bị công nghệ

**5.0.2. Phòng ban khác trong công ty có qua lại**

- Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V2 · C5 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L03**: Bộ phận Sản xuất không gửi trực tiếp Phiếu điều chuyển nguyên liệu cho Kho, mà Điều phối NL/BTP lập gửi cho Điều phối thành phẩm để Điều phối thành phẩm yêu cầu NCC GC phối hợp xuất điều chuyển
- Kế toán sản xuất · V1 · C1 · _as-is (thực tế), độ tin vừa_: Phòng Kế toán tiếp nhận bộ chứng từ quyết toán đơn hàng gia công gồm 11 loại chứng từ từ Bộ phận Sản xuất dưới dạng hồ sơ bản cứng có chữ ký sống hoặc chữ ký số.
- Chuyên viên Điều phối sản xuất · V1 · C3 · _as-is (thực tế), độ tin cao_: Bộ phận Lab tiếp nhận mẫu thành phẩm kiểm tra theo quy trình riêng của Lab
- Chuyên viên Pháp lý - Xử lý sự cố · V2 · C1 · _as-is (thực tế), độ tin cao_: Phối hợp với Bộ phận Pháp lý ở công ty để cảnh báo và cập nhật mới các giấy tờ pháp lý sản xuất, mua bán và sản phẩm khi sắp hết hạn.
- Trưởng phòng (Chị Ngân) · V3 · C6 · _as-is (thực tế), độ tin cao_: Nhận yêu cầu khảo sát, đặt mua/sản xuất/gia công từ Phòng Kinh doanh và bàn giao kết quả khảo sát, sản xuất gia công tương ứng
- Trưởng phòng (Chị Ngân) · V3 · C6 · _as-is (thực tế), độ tin cao_: Gửi yêu cầu kiểm tra, đánh giá mẫu/sản phẩm sang Bộ phận Lab và tiếp nhận kết quả kiểm nghiệm (Lab làm đầu mối với các Trung tâm kiểm nghiệm bên ngoài)
- Trưởng phòng (Chị Ngân) · V3 · C6 · _as-is (thực tế), độ tin cao_: Tiếp nhận yêu cầu chứng từ từ Phòng Kế toán và cung cấp bộ chứng từ theo biểu mẫu cho từng nghiệp vụ mua hàng, nhập kho, thanh toán, đối chiếu
- Trưởng phòng (Chị Ngân) · V3 · C6 · _as-is (thực tế), độ tin cao_: Phối hợp với Bộ phận Kho tiếp nhận thông báo hàng lỗi; truyền đạt thông tin giao nhận cho NCC GC để Kho thực hiện nhận hàng
- Chuyên viên Điều phối vật tư bao bì · V3 · C2 · _as-is (thực tế), độ tin cao_: Bộ phận Sản xuất tiếp nhận hình Mockup đơn hàng từ Bộ phận Thiết kế để kiểm tra và duyệt vật tư bao bì cho đơn hàng
- Chuyên viên Điều phối vật tư bao bì · V4 · C1 · _giả thuyết, độ tin thấp_ · *Suy diễn (AI)*: Phòng Kinh doanh: phối hợp thương lượng dời ngày giao hàng với Chuyên viên Điều phối VTBB khi tồn kho vật tư bao bì bị thiếu hụt hoặc chậm trễ
- Chuyên viên Điều phối vật tư bao bì · V6 · C1 · _as-is (thực tế), độ tin cao_: Bộ phận Thu mua tiếp nhận Phiếu đề nghị mua hàng hóa dịch vụ từ Chuyên viên Điều phối VTBB khi tồn kho vật tư bao bì không đủ hoặc bị trễ tiến độ đơn hàng theo quy định của PTCKT.

### 6. Công cụ, tài liệu, biểu mẫu

**6.0.1. Danh mục công cụ, dùng ở đầu việc nào, ai dùng, ai giữ bản gốc**

- Tài liệu: 4. XUẤT NHẬP TỒN - VTBB.xlsx · sheet HƯỚNG DẪN · _as-is (thực tế), độ tin cao_: File Excel XUẤT NHẬP TỒN - VTBB quản lý nhập xuất tồn kho VTBB, khai báo định mức an toàn Min/MOQ và đối chiếu số liệu NCC gia công
- Tài liệu: Bản sao của ĐIỀU PHỒI THÀNH PHẨM (NHÁP).xlsx · sheet họp07.10 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L09**: File Excel ĐIỀU PHỒI THÀNH PHẨM dùng quản lý và cập nhật tiến độ đơn hàng sản xuất qua 6 trạng thái điều phối
- Chuyên viên Điều phối vật tư bao bì · V1 · C1 · _as-is (thực tế), độ tin vừa_: Bảng tính Google Sheets theo dõi tồn kho và cân đối VTBB dùng trong kiểm tra điều kiện đơn hàng
- Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V2 · C4 · _as-is (thực tế), độ tin cao_: Google Drive dùng quản lý dữ liệu, theo dõi đơn hàng trên Drive điều phối thành phẩm, cập nhật số liệu điều chuyển NL, phối trộn BTP, theo dõi và cập nhật bảng giá, chính sách NCC
- Chuyên viên Điều phối vật tư bao bì · V2 · C2 · _as-is (thực tế), độ tin cao_: Drive làm việc theo dõi tồn kho và duyệt VTBB (Google Sheets) dùng để tra cứu tồn kho và trả kết quả duyệt cho Điều phối thành phẩm
- Chuyên viên Pháp lý - Xử lý sự cố · V4 · C3 · _as-is (thực tế), độ tin cao_: File Google Sheets quy trình sản xuất (Sheet 11 Quy trình xử lý sự cố)
- Chuyên viên Điều phối sản xuất · V3 · C5 · _as-is (thực tế), độ tin cao_: Drive làm việc điều phối (Google Sheets) dùng để tiếp nhận đơn hàng, duyệt đơn, gửi đơn NCC, cập nhật báo cáo gửi kho và tiếp nhận kết quả giao nhận từ Bộ phận Kho

**6.0.2. Danh mục tài liệu, biểu mẫu, báo cáo, ai lập, ai dùng**

- Tài liệu: Bản sao của ĐIỀU PHỒI THÀNH PHẨM (NHÁP).xlsx · sheet P.NHẬP KHO TP · _as-is (thực tế), độ tin cao_: Giấy đề nghị nhập kho thành phẩm do Nhân viên điều phối lập khi tiếp nhận hàng từ NCC GC, có chữ ký của NL, VTBB, Kế toán và Trưởng bộ phận
- Tài liệu: Bản sao của ĐIỀU PHỒI THÀNH PHẨM (NHÁP).xlsx · sheet P.XUẤT BÁN HÀNG · _as-is (thực tế), độ tin cao_: Phiếu đề nghị xuất kho bán hàng do Kế hoạch sản xuất lập khi xuất bán hàng hóa từ kho
- Tài liệu: Bản sao của ĐIỀU PHỒI THÀNH PHẨM (NHÁP).xlsx · sheet DS NHẬN HÀNG · _as-is (thực tế), độ tin cao_: Phiếu giao nhận hàng tại nhà cung cấp dành cho tài xế nhận hàng tại kho NCC GC
- Tài liệu: Bản sao của ĐIỀU PHỒI THÀNH PHẨM (NHÁP).xlsx · sheet Kết quả KCS Kho Dr.Xanh · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L10**: Biểu mẫu Kết quả KCS Kho Dr.Xanh dùng theo dõi quy cách ngoại quan, phụ kiện và chứng từ khi nhận thành phẩm từ NCC gia công.
- Tài liệu: Bản sao của ĐIỀU PHỒI THÀNH PHẨM (NHÁP).xlsx · sheet GỬI ĐƠN NCC · _as-is (thực tế), độ tin cao_: Đơn đặt hàng sản xuất gia công gửi NCC (Mã PO) thể hiện mã hàng, công thức, màu BTP, quy cách và số lượng thành phẩm.
- Tài liệu: 4. XUẤT NHẬP TỒN - VTBB.xlsx · sheet MỤC LỤC · _as-is (thực tế), độ tin cao_: Phiếu đề nghị chuyển kho dùng khi luân chuyển vật tư bao bì giữa các kho hoặc nhà cung cấp gia công.
- Tài liệu: 4. XUẤT NHẬP TỒN - VTBB.xlsx · sheet MỤC LỤC · _as-is (thực tế), độ tin cao_: Phiếu ký duyệt BĐM dùng khi phê duyệt bảng định mức vật tư bao bì cấu thành sản phẩm.
- Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V1 · C2 · _as-is (thực tế), độ tin cao_ · **mâu thuẫn: L03**: Phiếu yêu cầu phối trộn hoặc điều chuyển nguyên liệu do Chuyên viên NL/BTP lập khi phát sinh nhu cầu phối trộn BTP hoặc điều chuyển NL, gửi Kinh doanh, Kho và Nhà gia công
- Tài liệu: NỘI DUNG HỌP 25.09.26.xlsx · sheet Chi tiết vướng mắt từng NCC · _as-is (thực tế), độ tin cao_: Giấy đề nghị thanh toán gửi NCC ký xác nhận để hoàn thiện bộ hồ sơ thanh toán công nợ và phí gia công
- Tài liệu: NỘI DUNG HỌP 25.09.26.xlsx · sheet Chi tiết vướng mắt từng NCC · _as-is (thực tế), độ tin cao_: Hồ sơ pháp lý và hợp đồng NCC gia công do Sản xuất lưu bản gốc và Kế toán lưu bản scan
- Kế toán sản xuất · V1 · C1 · _giả thuyết, độ tin thấp_ · *Suy diễn (AI)*: Bảng xác nhận công nợ là chứng từ bắt buộc trong bộ hồ sơ quyết toán đơn hàng gia công gửi Phòng Kế toán dưới dạng bản cứng.
- Kế toán sản xuất · V1 · C1 · _giả thuyết, độ tin thấp_ · *Suy diễn (AI)*: Giấy đề nghị thanh toán của NCC là chứng từ do nhà cung cấp lập trong bộ hồ sơ quyết toán chuyển Phòng Kế toán.
- Chuyên viên Pháp lý - Xử lý sự cố · V4 · C1 · _as-is (thực tế), độ tin cao_: File Google Sheets Sơ đồ và mô tả công việc các vị trí lưu trữ sơ đồ tổ chức và MTCV phòng ban
- Chuyên viên Pháp lý - Xử lý sự cố · V4 · C3 · _as-is (thực tế), độ tin cao_: Tài liệu Quy trình xử lý sự cố trong sản xuất quy định chi tiết tại Sheet 11 file Google Sheets quy trình sản xuất
- Kế toán sản xuất · V3 · C2 · _giả thuyết, độ tin thấp_ · *Suy diễn (AI)*: Bảng xác nhận công nợ là chứng từ bắt buộc trong bộ hồ sơ quyết toán đơn hàng gia công gửi Phòng Kế toán dưới dạng bản cứng (do Chuyên viên Quản lý dữ liệu phụ trách lập và hoàn thiện)
- Chuyên viên Điều phối sản xuất · V2 · C2 · _as-is (thực tế), độ tin cao_: Báo cáo gửi kho được lập hằng ngày vào 16h chiều trên Drive làm việc điều phối; Bộ phận Kho tự xem Drive và cập nhật kết quả nhận hàng cùng chứng từ gửi qua Zalo để Điều phối kiểm tra số lượng thực tế
- Chuyên viên Điều phối vật tư bao bì · V6 · C2 · _as-is (thực tế), độ tin cao_: Phiếu đề nghị mua hàng hóa dịch vụ do Chuyên viên Điều phối VTBB lập theo quy định của PTCKT gửi Bộ phận Thu mua khi tồn kho VTBB không đủ hoặc bị trễ tiến độ đơn hàng.

### 7. Nhật ký công việc

**7.0.1. Việc làm hằng ngày**

- Chuyên viên Điều phối nguyên liệu/bán thành phẩm · V4 · C2 · _as-is (thực tế), độ tin cao_: Chuyên viên Điều phối NL/BTP thực hiện hằng ngày: kiểm tra tồn kho và điều kiện NL/BTP; điều phối nguyên liệu các kho/NCC; theo dõi tiến độ phối BTP và SXGC; theo dõi hao hụt thừa thiếu; báo cáo tồn kho đáp ứng đơn hàng; tiếp nhận yêu cầu phối mẫu và kiểm tra chất lượng mẫu phối

### 8. Quyết định đã chốt trên MIC

**8.0.1. Ai đang giữ vị trí này**

- Tài liệu: Quyết định của người quản trị khảo sát ngày 22/10 · _to-be (đã chốt), độ tin cao_: Ghi nhận as-is: Phạm Khánh Ngân (dự kiến bàn giao quy trình cải tiến hoặc công việc hiện tại cho Ms Lê Thị Ngọc Mi chậm nhất vào ngày 31/12/2026)

### Các quy trình đã có tên, chưa có câu trả lời

- Khai báo sản xuất
- Khảo sát và tính giá vốn
- Thanh toán và tạm ứng
- Đặt dịch vụ vận chuyển (Grab)
- Xử lý sự cố sau sản xuất
- Quản lý vật tư bao bì

Sáu quy trình này dự kiến hỏi ở pha 2 của khảo sát.

---

*Hết tài liệu. 108 câu hỏi, 222 câu trả lời đã ghi vào ô, 25 mục mâu thuẫn. Số liệu chụp lúc 24/10/2026 08:59.*
