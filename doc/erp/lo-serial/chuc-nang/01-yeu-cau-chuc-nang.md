# YÊU CẦU CHỨC NĂNG — LÔ, SERIAL VÀ HẠN DÙNG

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · chưa có CR làm mã |

**Nguồn:** phân hệ chỉ có tài liệu **nghiên cứu** [00 Lô, số serial, hạn dùng và truy xuất](../nghien-cuu/00-nghien-cuu-lo-serial-erpnext.md).
Mọi chức năng dưới đây là **dự kiến**, rút từ bảng fit-gap mục 6 (cột *DEGO cần*) và kế hoạch theo nấc mục 8 (L1..L4);
trạng thái đều là *Chưa*. Chức năng nghiên cứu ghi *Không* (serial, nhiều lô trên một dòng, giá theo lô) không đưa vào.

## 1. Người dùng và vai trò

| Vai trò (mã vai trò) | Làm gì trong phân hệ |
|---|---|
| Thủ kho (dự kiến) | Nhập số lô, ngày sản xuất, hạn dùng khi nhận; xác nhận lô gợi ý FEFO khi xuất; kiểm kê theo lô |
| QC, Lab (dự kiến) | Kết luận kiểm gắn vào lô, đổi trạng thái lô (dùng được, tạm giữ, khóa) |
| Nhà máy (dự kiến) | Sinh lô thành phẩm từ lệnh sản xuất theo mẫu số |
| Người quản danh mục (dự kiến) | Bật cờ theo dõi lô, hạn dùng theo phân loại; nhập số ngày sử dụng của thành phẩm |
| Kinh doanh | Thu hồi theo lô khi có sự cố sau sản xuất |

Nguồn: [nghiên cứu mục 7.4 bảng *Chi phí vận hành*](../nghien-cuu/00-nghien-cuu-lo-serial-erpnext.md).

## 2. Danh sách chức năng

| Mã | Chức năng | Ai dùng | Màn / nơi dùng | Trạng thái | CR |
|---|---|---|---|---|---|
| CN-LS-01 | Cờ theo dõi lô, cờ hạn dùng, số ngày sử dụng trên sản phẩm, mặc định theo phân loại (fit-gap 1, 2) | Người quản danh mục | Form sản phẩm, phân loại | Chưa | chưa có |
| CN-LS-02 | Danh mục lô `tab_stock_lot`: số lô, ngày sản xuất, hạn dùng, NCC, chứng từ gốc, trạng thái (fit-gap 3) | Thủ kho, QC | chưa có | Chưa | chưa có |
| CN-LS-03 | Đánh số lô tự động theo mẫu cho lô nội bộ, lô nhà máy (fit-gap 4) | Hệ thống | chưa có | Chưa | chưa có |
| CN-LS-04 | Ghi lô khi nhận hàng mua trên **phiếu nhập kho thật**, một dòng chứng từ một lô (fit-gap 5; L1) | Thủ kho | Phiếu nhập (phân hệ Nhận hàng) | Chưa | chưa có |
| CN-LS-05 | Tồn kho theo lô (`tab_inventory_lot`), tổng theo lô khớp tồn theo mã (fit-gap 6; L1) | Kho | Màn tồn | Chưa | chưa có |
| CN-LS-06 | QC kết luận theo lô, đổi trạng thái lô (fit-gap 9; L1) | QC, Lab | Phiếu kiểm | Chưa | chưa có |
| CN-LS-07 | Báo cáo lô sắp hết hạn, thẻ cảnh báo trên trang chủ; báo cáo nhập xuất tồn theo lô (fit-gap 10, 11; L1) | Kho, kinh doanh | Báo cáo, trang chủ | Chưa | chưa có |
| CN-LS-08 | Xuất kho chọn lô, gợi ý FEFO; phiếu xuất và chuyển kho mang lô; kiểm kê theo lô (fit-gap 7; L2) | Thủ kho | Phiếu xuất (phân hệ Xuất hàng) | Chưa | chưa có |
| CN-LS-09 | Chặn lô hết hạn và lô khóa (trừ xuất hủy), lấy danh sách lô hết hạn để lập phiếu hủy (fit-gap 8; L2) | Hệ thống, thủ kho | Phiếu xuất | Chưa | chưa có |
| CN-LS-10 | Lô thành phẩm sinh từ lệnh sản xuất; ghi lô NCC khi nhận thành phẩm gia công (fit-gap 12; L3) | Nhà máy | Lệnh sản xuất (chưa có) | Chưa | chưa có |
| CN-LS-11 | Ánh xạ lô nguyên liệu vào lô thành phẩm, truy xuất ngược (fit-gap 13, 14; L3) | QC, nhà máy | chưa có | Chưa | chưa có |
| CN-LS-12 | Truy xuất xuôi tới khách, danh sách thu hồi (fit-gap 14; L4) | Kinh doanh | chưa có | Chưa | chưa có |

Để sau theo nghiên cứu: phiếu soạn hàng theo lô, mẫu lưu theo lô. Không làm: serial, gói nhiều lô trên một dòng, giá
theo lô ([mục 8](../nghien-cuu/00-nghien-cuu-lo-serial-erpnext.md)).

## 3. Chi tiết từng chức năng

### CN-LS-04 và CN-LS-05 — Lô ở cửa nhập và tồn theo lô (dự kiến, nguồn nghiên cứu)

- **Mục đích:** biết từng lô đang ở kho nào, còn bao nhiêu, hạn khi nào, từ lúc nhận hàng.
- **Luồng chính (đề xuất):** thủ kho nhận hàng có mã theo lô → nhập số lô in trên bao bì, ngày sản xuất, hạn dùng (trống thì máy tính từ số ngày sử dụng) → ghi sổ kho kèm lô → tồn theo lô cập nhật.
- **Luật nghiệp vụ (đề xuất):** lô là chiều của tồn kho, không phải biến thể sản phẩm; một dòng chứng từ một lô (một lần giao hai lô thì tách hai dòng); không tính giá theo lô; hết hạn suy ra từ ngày, không lưu cột; chứng từ chép cả `lot_id` lẫn `lot_no` — [mục 7.4](../nghien-cuu/00-nghien-cuu-lo-serial-erpnext.md).
- **Dữ liệu (phác thảo, chờ Agent 1 duyệt):** cờ `track_lot`, `track_expiry`, `shelf_life_days` trên `tab_product` và `tab_item_group`; bảng `tab_stock_lot`; `lot_id`, `lot_no` trên `tab_inventory_move`; bảng `tab_inventory_lot`.
- **Quyền:** chưa có.
- **Ngoại lệ / lỗi người dùng gặp:** chưa có.
- **Liên quan:** phải làm **cùng lúc** với phiếu nhập kho thật ([Nhận hàng CN-NH-11](../../nhan-hang/chuc-nang/01-yeu-cau-chuc-nang.md)); làm trên phiếu nhập ngầm hiện tại là làm hai lần.

### CN-LS-08 và CN-LS-09 — Xuất theo FEFO, chặn lô hết hạn (dự kiến, nguồn nghiên cứu)

- **Mục đích:** lô hết hạn trước xuất trước; không để lô hết hạn hay lô khóa đi ra ngoài.
- **Luồng chính (đề xuất):** thủ kho lập phiếu xuất → máy gợi ý lô theo FEFO → thủ kho xác nhận hoặc đổi (xuất trái phải ghi lý do nếu Q-L5 chốt vậy).
- **Luật nghiệp vụ (đề xuất):** chặn lô hết hạn và lô khóa trừ xuất hủy; FEFO là gợi ý hay bắt buộc là câu Q-L5; lô hết hạn chặn hẳn hay cho xuất có duyệt là câu Q-L6.
- **Dữ liệu:** như CN-LS-04.
- **Quyền:** chưa có.
- **Ngoại lệ / lỗi người dùng gặp:** chưa có.
- **Liên quan:** cần phiếu xuất của [Xuất hàng CN-XH-01](../../xuat-hang/chuc-nang/01-yeu-cau-chuc-nang.md).

## 4. Luồng trạng thái chứng từ

Lô không phải chứng từ. Trạng thái lô do người đặt (đề xuất, lưu `SMALLINT` + `IntEnum`): *Dùng được*, *Tạm giữ chờ kiểm*,
*Khóa*. *Hết hạn*, *Sắp hết hạn* suy ra từ ngày theo khuôn `dossier/expiry.py`, không lưu cột.

## 5. Câu hỏi còn mở

Mười hai câu Q-L1..Q-L12 ở [nghiên cứu mục 9](../nghien-cuu/00-nghien-cuu-lo-serial-erpnext.md) (nguyên liệu rời có theo lô,
bao bì không theo lô, mẫu số lô nhà máy, cách tính hạn dùng, FEFO gợi ý hay bắt buộc, xử lý lô hết hạn, ngưỡng cảnh báo,
nguồn truy xuôi, cách kiểm kê đầu kỳ, nhiều lô trong một lần giao, kiểu cột ngày, kết quả Lab đổi trạng thái lô). Câu C5
(lô, hạn dùng, vị trí kho) của [doc/plans/00](../../../plans/00-ke-hoach-theo-module.md) chặn cả phân hệ.

| # | Câu hỏi | Ai trả lời | Hạn |
|---|---|---|---|
| 1 | Q-L1..Q-L12 | Theo cột *Hỏi ai* của nghiên cứu mục 9 | chưa có |
| 2 | C5: có theo dõi lô, hạn dùng không | Đại ca | chưa có |
