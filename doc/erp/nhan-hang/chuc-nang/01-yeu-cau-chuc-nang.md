# YÊU CẦU CHỨC NĂNG — NHẬN HÀNG VÀ CHẤT LƯỢNG

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · chưa có CR làm mã riêng |

**Nguồn:** phân hệ chỉ có tài liệu **nghiên cứu** [00 Nhận hàng, kiểm chất lượng, trả hàng và chi phí nhập](../nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md).
CN-NH-01..04 là phần đã có mã nằm trong Đơn mua hàng (đặc tả ở [thu mua 13 mục C](../../thu-mua/chuc-nang/13-don-mua-hang.md));
CN-NH-05..18 là **chức năng dự kiến**, rút từ mục 6 và mục 7 của tài liệu nghiên cứu (mã việc N1.x, N2.x, N3.x), trạng thái
*Chưa*, chưa phải yêu cầu đã chốt.

## 1. Người dùng và vai trò

| Vai trò (mã vai trò) | Làm gì trong phân hệ |
|---|---|
| Nhân sự thu mua (quyền `purchase_order.write`) | Hiện nay: ghi số nhận trên lần giao của ĐMH |
| Thủ kho (dự kiến, chưa có vai trò) | Lập phiếu nhập khi xe tới, xác nhận số thực nhận, lập phiếu trả hàng |
| QC đầu vào (dự kiến) | Lập phiếu kiểm theo mẫu chỉ tiêu, kết luận chấp nhận hoặc từ chối |
| Kế toán | Chọn khoản nợ đã có (chỉ sinh theo số chấp nhận), đối chiếu hóa đơn NCC |

## 2. Danh sách chức năng

| Mã | Chức năng | Ai dùng | Màn / nơi dùng | Trạng thái | CR |
|---|---|---|---|---|---|
| CN-NH-01 | Lần giao nhiều đợt trên dòng ĐMH: số nhận, ngày nhận, kho nhận, hẹn giao, số ngày quy định, trễ cam kết — [thu mua 13 mục C](../../thu-mua/chuc-nang/13-don-mua-hang.md) | Thu mua | Chi tiết dòng ĐMH | chưa ghi · có mã | chưa ghi |
| CN-NH-02 | Đính kèm phiếu giao, biên bản trên lần giao — [nghiên cứu mục 4.2](../nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md) | Thu mua | Chi tiết dòng ĐMH | chưa ghi · có mã | chưa ghi |
| CN-NH-03 | Phiếu nhập kho sinh ngầm mỗi lần giao (`GRxxxxx`, không màn, không trạng thái) — [nghiên cứu mục 4.1](../nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md) | Hệ thống | Lưu ĐMH | chưa ghi · có mã một phần | chưa ghi |
| CN-NH-04 | Kết quả kiểm `qc_result` một ô chữ (*Đạt, Thiếu, Lỗi*) cho cả lần giao; *Lỗi* chỉ đổi trạng thái lần giao — [nghiên cứu mục 4.1, 4.2](../nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md) | Thu mua | Bảng lần giao (v2 chưa có ô) | chưa ghi · có mã một phần | chưa ghi |
| CN-NH-05 | Máy chủ chặn lưu số nhận khi ĐMH chưa duyệt (N1.1) | Hệ thống | Lưu ĐMH | Chưa | chưa có |
| CN-NH-06 | Kết quả kiểm thành bộ mã, thêm số chấp nhận, số từ chối trên lần giao, hiện trên bảng lần giao v2 (N1.2, N1.4) | Thu mua, QC | Bảng lần giao | Chưa | chưa có |
| CN-NH-07 | Tồn và công nợ tính theo số chấp nhận; lần giao *Không đạt* hoặc *Chưa kiểm* ở nhóm bắt buộc kiểm chưa sinh công nợ (N1.3; mục 6.5) | Hệ thống | Lưu ĐMH | Chưa | chưa có |
| CN-NH-08 | Dung sai nhận vượt theo nhóm hàng, ghi đè theo sản phẩm, chặn ở máy chủ (N1.5; mục 6.6) | Hệ thống, người duyệt ĐMH | Lưu ĐMH | Chưa | chưa có |
| CN-NH-09 | Nhật ký sửa số nhận, số chấp nhận (N1.6) | Kế toán, quản lý | Chi tiết ĐMH | Chưa | chưa có |
| CN-NH-10 | Báo cáo hàng về chưa có hóa đơn, cảnh báo ở YCTT khi chọn khoản chưa có số hóa đơn (N1.7) | Kế toán | Báo cáo, YCTT | Chưa | chưa có |
| CN-NH-11 | Phiếu nhập kho thật do thủ kho lập, lần giao chỉ còn là lịch dự kiến, đảo phiếu thay xóa (N2.3; mục 6.2) | Thủ kho | Màn phiếu nhập (dự kiến) | Chưa | chưa có |
| CN-NH-12 | Loại kho và kho hàng lỗi đi kèm, tồn dùng được loại trừ kho chờ kiểm, kho lỗi (N2.2; mục 6.3) | Thủ kho | Danh mục kho | Chưa | chưa có |
| CN-NH-13 | Mẫu kiểm theo nhóm hàng, phiếu kiểm có chỉ tiêu, cờ bắt buộc kiểm và mức chặn (N2.4; mục 6.4) | QC | Phiếu kiểm (dự kiến) | Chưa | chưa có |
| CN-NH-14 | Phiếu trả hàng NCC trỏ phiếu nhập gốc: trả để đổi, trả không đổi, trả hàng chưa sinh nợ (N2.5; mục 6.7) | Thủ kho, thu mua | Phiếu trả hàng (dự kiến) | Chưa | chưa có |
| CN-NH-15 | Khoản giảm nợ âm trong công nợ, cấn trừ trong YCTT, chuyển tiền treo NCC khi lô đã trả đủ (N2.6; mục 6.7) | Kế toán | Công nợ, YCTT | Chưa | chưa có |
| CN-NH-16 | Đẩy chi phí thu mua đã quyết toán vào giá kho bằng dòng sổ điều chỉnh giá trị (N2.7; mục 6.8) | Hệ thống, kế toán | Sổ kho | Chưa | chưa có |
| CN-NH-17 | Báo cáo nhận hàng theo kỳ, nhóm hàng, NCC, tỷ lệ từ chối; đưa vào chấm điểm NCC (N2.8); lô và hạn dùng trên dòng phiếu nhập (N2.9) | Quản lý | Báo cáo | Chưa | chưa có |
| CN-NH-18 | Nấc 3: hóa đơn NCC là chứng từ, công nợ sinh từ hóa đơn, đối chiếu bốn chiều, giấy báo nợ chính thức, chi phí về muộn (N3.1..N3.5) | Kế toán | chưa có | Chưa | chưa có |

## 3. Chi tiết từng chức năng

### CN-NH-06 và CN-NH-07 — Số chấp nhận, số từ chối; hàng lỗi không sinh nợ (dự kiến, nguồn nghiên cứu)

- **Mục đích:** chặn mất tiền khi hàng lỗi vẫn vào tồn và vẫn sinh công nợ đủ.
- **Luồng chính (đề xuất):** ghi số nhận → kiểm → chia số chấp nhận, số từ chối → tồn và công nợ chỉ tính số chấp nhận.
- **Luật nghiệp vụ (đề xuất):** công nợ hàng = số chấp nhận × giá, đặt làm luật cứng; lần giao chờ kiểm chưa sinh nợ — [mục 6.5](../nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md).
- **Dữ liệu (đề xuất):** `qc_result` thành `SMALLINT` (Chưa kiểm, Đạt, Đạt một phần, Không đạt) qua `status_catalog.py`; thêm `accepted_qty`, `rejected_qty` — [mục 7.1 N1.2](../nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md).
- **Quyền:** như ĐMH cho nấc 1.
- **Ngoại lệ / lỗi người dùng gặp:** chưa có.
- **Liên quan:** CN-NH-11, CN-NH-12; [thu mua CN-TM-13](../../thu-mua/chuc-nang/01-yeu-cau-chuc-nang.md).

### CN-NH-11 — Phiếu nhập kho do thủ kho lập (dự kiến, nguồn nghiên cứu)

- **Mục đích:** tách người đặt hàng khỏi người nhận hàng; kho có chứng từ của mình để đối chiếu.
- **Luồng chính (đề xuất):** thủ kho chọn lần giao khi xe tới → phiếu nhập *Nháp* (số thực nhận, số phiếu giao NCC, biển số xe) → kiểm (nếu nhóm bắt buộc) → *Đã ghi sổ*; sai thì *Đảo* rồi lập phiếu mới.
- **Luật nghiệp vụ (đề xuất):** một phiếu gom nhiều dòng cùng ĐMH; một lần giao được nhận bằng nhiều phiếu; số nhận trên lần giao thành số tổng hợp chỉ đọc — [mục 6.2](../nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md).
- **Dữ liệu (đề xuất):** nâng `tab_goods_receipt` thành chứng từ có đầu phiếu và dòng.
- **Quyền (đề xuất):** entity mới `goods_receipt` (lập, ghi sổ, đảo) tách khỏi `purchase_order.write`.
- **Ngoại lệ / lỗi người dùng gặp:** chưa có.
- **Liên quan:** cần sổ kho chỉ ghi thêm ([Kho CN-KHO-10](../../kho/chuc-nang/01-yeu-cau-chuc-nang.md)); lô ở [Lô, serial](../../lo-serial/chuc-nang/01-yeu-cau-chuc-nang.md) phải vào cùng lúc.

### CN-NH-14 — Trả hàng NCC (dự kiến, nguồn nghiên cứu)

- **Mục đích:** trả hàng mà không phải xóa lần giao (hiện xóa lần giao là xóa luôn phiếu nhập, dòng sổ kho, công nợ).
- **Luồng chính (đề xuất):** lập phiếu trả trỏ dòng phiếu nhập gốc → chọn trả để đổi, trả không đổi, hoặc trả hàng chưa sinh nợ → ghi sổ kho âm theo giá phiếu gốc → sinh khoản giảm nợ nếu đã có nợ.
- **Luật nghiệp vụ (đề xuất):** không trả quá số đã nhận còn lại; lô đã trả đủ tiền thì chuyển thành tiền treo NCC — [mục 6.7](../nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md).
- **Dữ liệu (đề xuất):** `tab_payable` thêm `source_type` mới (ví dụ `goods_return`) cho khoản âm.
- **Quyền:** chưa có.
- **Ngoại lệ / lỗi người dùng gặp:** chưa có.
- **Liên quan:** CN-NH-15; câu R-Q5, R-Q6.

## 4. Luồng trạng thái chứng từ

Hiện tại lần giao có trạng thái `pending`, `short`, `defect`, `received` (bộ mã B-06); phiếu nhập ngầm không có trạng thái.
Đề xuất cho phiếu nhập (mục 6.1, 6.2):

```
Nháp → (Chờ kiểm) → Đã ghi sổ → Đã đảo
```

## 5. Câu hỏi còn mở

Tám câu R-Q1..R-Q8 ở [nghiên cứu mục 6.11](../nghien-cuu/00-nghien-cuu-nhan-hang-chat-luong-erpnext.md) (QC đầu vào ở đâu, bộ
chỉ tiêu từng nhóm, phần nhận vượt có trả tiền, hàng kho lỗi có giá trị, trả hàng mặc định đổi hay không, lúc lập khoản
giảm nợ, khóa số nhận ở v1, có hướng ISO 9001), cùng các câu Đ3, K1, K3, K6 của [doc/plans/01](../../../plans/01-luong-chuan-mua-hang-kho-san-xuat.md).

| # | Câu hỏi | Ai trả lời | Hạn |
|---|---|---|---|
| 1 | R-Q1..R-Q8 | Đại ca, QC, kế toán, thủ kho | chưa có |
