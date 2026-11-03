# YÊU CẦU CHỨC NĂNG — XUẤT KHO VÀ GIAO HÀNG

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · chưa có CR làm mã |

**Nguồn:** phân hệ chỉ có tài liệu **nghiên cứu** [00 Xuất kho, giao hàng và kết nối bán hàng](../nghien-cuu/00-nghien-cuu-xuat-giao-hang-erpnext.md).
Mọi chức năng dưới đây là **dự kiến**, rút từ kế hoạch theo nấc ở mục 7 (mã XG1..XG9) và đề xuất ở mục 6; trạng thái đều
là *Chưa*. Phần đang có và dùng tạm (điều chỉnh tồn âm, Đặt xe giao hàng) nằm ở phân hệ khác, ghi ở cuối mục 2.

## 1. Người dùng và vai trò

| Vai trò (mã vai trò) | Làm gì trong phân hệ |
|---|---|
| Thủ kho (dự kiến, chưa có vai trò) | Lập phiếu xuất, phiếu chuyển kho từ đề nghị đã duyệt; xác nhận số thực phát |
| Người có nhu cầu (dự kiến) | Lập đề nghị lĩnh vật tư, đề nghị chuyển kho |
| Trưởng phòng, trưởng kho (dự kiến) | Duyệt đề nghị, duyệt xuất hủy theo hạn mức (câu X3) |
| Hành chính điều xe | Điều phối chuyến giao trên Đặt xe (đã có ở phân hệ Đặt xe) |
| Kinh doanh (dự kiến, chỉ khi X1 = có) | Đơn bán, phiếu giao hàng bán |

## 2. Danh sách chức năng

| Mã | Chức năng | Ai dùng | Màn / nơi dùng | Trạng thái | CR |
|---|---|---|---|---|---|
| CN-XH-01 | Phiếu kho chung loại xuất dùng nội bộ, xuất hủy, chuyển kho một bước; dòng có mục đích chi phí và bộ phận; *Nháp → Đã ghi sổ → Đã đảo*; chặn tồn âm (XG1) | Thủ kho | Phiếu kho (dự kiến) | Chưa | chưa có |
| CN-XH-02 | Đề nghị lĩnh vật tư (xuất dùng, chuyển kho) qua bộ máy duyệt chung; thủ kho lập phiếu từ đề nghị; theo dõi đã phát, chặn phát vượt (XG2) | Người có nhu cầu, thủ kho | Đề nghị lĩnh (dự kiến) | Chưa | chưa có |
| CN-XH-03 | Chuyển kho hai bước qua kho đang chuyển, kho đến xác nhận số thực nhận (XG3) | Thủ kho hai đầu | Phiếu kho | Chưa | chưa có |
| CN-XH-04 | Nối Đặt xe: phiếu xuất, phiếu chuyển gắn phiếu đặt xe giao hàng, điểm dừng trỏ chứng từ, tài xế xác nhận từng điểm kèm ảnh biên bản; đặt xe không tự trừ kho (XG4; mục 6.2) | Thủ kho, hành chính, tài xế | Phiếu kho, Đặt xe | Chưa | chưa có |
| CN-XH-05 | Xuất cho lệnh sản xuất theo định mức, xuất vượt có lý do và duyệt, nhập trả vật tư thừa, giữ chỗ vật tư (XG5) | Thủ kho, sản xuất | Phiếu kho | Chưa | chưa có |
| CN-XH-06 | Giao hàng bán bản 1: khách hàng tối thiểu, đơn bán, phiếu giao trừ kho, giao nhiều lần, đóng phần còn lại, trả hàng bán (XG6) | Kinh doanh, thủ kho | Phân hệ Bán hàng (vỏ) | Chưa (chờ câu X1) | chưa có |
| CN-XH-07 | Giữ hàng cho đơn, phiếu soạn hàng theo kho, đóng gói (XG7) | Thủ kho | chưa có | Chưa | chưa có |
| CN-XH-08 | Báo cáo hàng đã giao chưa lập hóa đơn, xu hướng giao hàng, đầu nối phiếu xuất, phiếu giao sang MISA (XG8) | Kế toán | Báo cáo | Chưa | chưa có |
| CN-XH-09 | Gửi qua hãng vận chuyển: kiện, mã vận đơn, tình trạng, cước thành công nợ (XG9) | Kinh doanh, hành chính | chưa có | Chưa (chờ câu X9) | chưa có |
| CN-XH-10 | In phiếu xuất kho, phiếu giao theo mẫu (fit-gap C11) | Thủ kho | Trang in | Chưa | chưa có |

**Đang có ở phân hệ khác, dùng tạm:** điều chỉnh tồn âm ([Kho CN-KHO-03](../../kho/chuc-nang/01-yeu-cau-chuc-nang.md), không
chứng từ, không mục đích); Đặt xe giao hàng (`vehicle_booking`, `TYPE_DELIVERY`) có xe, tài xế, nhiều điểm dừng, duyệt, báo
cáo — [nghiên cứu mục 4](../nghien-cuu/00-nghien-cuu-xuat-giao-hang-erpnext.md).

## 3. Chi tiết từng chức năng

### CN-XH-01 — Phiếu kho chung chiều ra (dự kiến, nguồn nghiên cứu)

- **Mục đích:** mọi lần lấy hàng ra có chứng từ, có mục đích, có người chịu trách nhiệm, thay cho điều chỉnh âm.
- **Luồng chính (đề xuất):** thủ kho lập phiếu *Nháp* (loại xuất dùng, xuất hủy, chuyển kho) → ghi sổ → sai thì đảo.
- **Luật nghiệp vụ (đề xuất):** chặn tồn âm; giá xuất theo cách tính giá của kho lõi; dòng bắt buộc mục đích chi phí và bộ phận (danh sách chờ câu X6). Phải làm **sau kho lõi** (sổ chỉ thêm, ngày ghi sổ, bình quân di động) — [nghiên cứu mục 1, 7](../nghien-cuu/00-nghien-cuu-xuat-giao-hang-erpnext.md).
- **Dữ liệu:** chưa có thiết kế bảng riêng; đi chung khung phiếu kho của [Kho CN-KHO-11](../../kho/chuc-nang/01-yeu-cau-chuc-nang.md).
- **Quyền:** chưa có.
- **Ngoại lệ / lỗi người dùng gặp:** chưa có.
- **Liên quan:** CN-XH-02, CN-XH-03; kế hoạch `TM-GN-4`, `SX2-1` đã ghi chỗ hở này.

### CN-XH-02 — Đề nghị lĩnh vật tư (dự kiến, nguồn nghiên cứu)

- **Mục đích:** người có nhu cầu xin lấy vật tư qua luồng duyệt, thủ kho phát theo đề nghị đã duyệt.
- **Luồng chính (đề xuất):** lập đề nghị → duyệt qua `approval/` → thủ kho lập phiếu xuất hoặc chuyển từ đề nghị → theo dõi đã phát bao nhiêu.
- **Luật nghiệp vụ (đề xuất):** chặn phát vượt số đề nghị; có cần duyệt và hạn mức nào là câu X3.
- **Dữ liệu:** chưa có.
- **Quyền:** chưa có.
- **Ngoại lệ / lỗi người dùng gặp:** chưa có.
- **Liên quan:** CN-XH-01; bộ máy duyệt chung.

### CN-XH-04 — Nối Đặt xe giao hàng (dự kiến, nguồn nghiên cứu)

- **Mục đích:** dùng phiếu đặt xe làm chuyến giao cho hàng xuất, chuyển giữa các nhà máy.
- **Luồng chính (đề xuất):** phiếu xuất hoặc chuyển kho gắn vào phiếu đặt xe giao hàng; mỗi điểm dừng trỏ một chứng từ; tài xế xác nhận từng điểm kèm ảnh biên bản.
- **Luật nghiệp vụ (đề xuất):** *nối chứ không gộp*; đặt xe không bao giờ tự trừ kho; thêm cột vào phiếu đặt xe phải giữ ràng buộc đồng bộ app đặt xe cũ (`legacy_datxe/`) — [nghiên cứu mục 4, 6.2](../nghien-cuu/00-nghien-cuu-xuat-giao-hang-erpnext.md).
- **Dữ liệu:** chưa có.
- **Quyền:** chưa có.
- **Ngoại lệ / lỗi người dùng gặp:** chưa có.
- **Liên quan:** phân hệ Đặt xe; câu X10.

## 4. Luồng trạng thái chứng từ

Đề xuất (nghiên cứu mục 7, XG1):

```
Nháp → Đã ghi sổ → Đã đảo
```

## 5. Câu hỏi còn mở

Mười hai câu X1..X12 ở [nghiên cứu mục 8](../nghien-cuu/00-nghien-cuu-xuat-giao-hang-erpnext.md): có bán hàng qua ERP
không (X1, hạn 30/11/2026 theo tài liệu), ai lập phiếu xuất (X2), duyệt và hạn mức (X3), sổ kho chính thức ở ERP hay MISA
(X4), cách tính giá xuất của MISA (X5), danh sách mục đích chi phí (X6), cấp vật tư sản xuất (X7), lô và hạn dùng (X8),
hãng vận chuyển (X9), duyệt chuyến giao (X10), hàng gửi đi bán (X11), phần mềm hóa đơn bán (X12).

| # | Câu hỏi | Ai trả lời | Hạn |
|---|---|---|---|
| 1 | X1..X3 | Ban lãnh đạo | X1: 30/11/2026; còn lại chưa có |
| 2 | X4..X6, X11, X12 | Kế toán | chưa có |
