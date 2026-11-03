# YÊU CẦU CHỨC NĂNG — KHO

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | đại ca và các agent |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · CR-001 (thiết kế lại danh mục kho) |

Tệp này là **mục lục chức năng**. Chức năng đã có mã (CN-KHO-01..07) đang được đặc tả trong tài liệu thu mua
[15 Tồn kho và Công nợ](../../thu-mua/chuc-nang/15-ton-kho-cong-no.md) và [16 Danh mục mục Kho](../../thu-mua/chuc-nang/16-danh-muc.md);
dòng dưới chỉ tóm tắt và trỏ về đó. Chức năng CN-KHO-08..17 là **dự kiến**, rút từ tài liệu **nghiên cứu**
[00 Kho lõi](../nghien-cuu/00-nghien-cuu-kho-erpnext.md) mục 6 (mã việc KHO-x.y) và [TDD thiết kế lại kho](../tai-lieu-ky-thuat/tdd-redesign-kho.md);
chưa phải yêu cầu đã chốt.

**Cách đọc cột Trạng thái:** *có mã* nghĩa là nghiên cứu kho lõi (soát `erp-v2` ngày 02/11/2026) xác nhận đã có mã, không
nói đã lên prod hay chưa.

## 1. Người dùng và vai trò

| Vai trò (mã vai trò) | Làm gì trong phân hệ |
|---|---|
| Người xem tồn (quyền `inventory.read`; mã vai trò: chưa ghi) | Xem tồn, sổ phát sinh theo phạm vi công ty |
| Người điều chỉnh (quyền `inventory.write`) | Điều chỉnh tồn tay qua popup |
| Nhân sự thu mua | Nhận hàng trên ĐMH, việc này tự ghi tồn |
| Thủ kho, trưởng kho, kế toán kho (đề xuất, chưa có vai trò) | Lập, duyệt phiếu kho, khóa sổ — [nghiên cứu kho lõi mục 5.7](../nghien-cuu/00-nghien-cuu-kho-erpnext.md) |

## 2. Danh sách chức năng

| Mã | Chức năng | Ai dùng | Màn / nơi dùng | Trạng thái | CR |
|---|---|---|---|---|---|
| CN-KHO-01 | Danh mục kho: mã, tên, địa chỉ, đang dùng; nhập, xuất CSV — [thu mua 16 mục Kho](../../thu-mua/chuc-nang/16-danh-muc.md) | Thu mua, quản trị | `/inventory/warehouses` | chưa ghi · có mã | chưa ghi |
| CN-KHO-02 | Tồn kho theo công ty, kho, mã hàng: số lượng, đơn giá bình quân, giá trị — [thu mua 15 mục A](../../thu-mua/chuc-nang/15-ton-kho-cong-no.md) | Người xem tồn | `/inventory/stock` | chưa ghi · có mã | chưa ghi |
| CN-KHO-03 | Điều chỉnh tồn tay (tăng hoặc giảm, có lý do) — [thu mua 15 mục B](../../thu-mua/chuc-nang/15-ton-kho-cong-no.md) | Người điều chỉnh | Popup trên màn Tồn kho | chưa ghi · có mã | chưa ghi |
| CN-KHO-04 | Ghi tồn tự động khi nhận hàng trên ĐMH, xóa khi lần giao bị xóa — [thu mua 15 mục C](../../thu-mua/chuc-nang/15-ton-kho-cong-no.md) | Hệ thống | Lưu ĐMH | chưa ghi · có mã | chưa ghi |
| CN-KHO-05 | Sổ phát sinh nhập, điều chỉnh (lọc kho, mã hàng, công ty) — [nghiên cứu kho lõi mục 3.1](../nghien-cuu/00-nghien-cuu-kho-erpnext.md) | Người xem tồn | `GET /api/inventory/moves` | chưa ghi · có mã một phần | chưa ghi |
| CN-KHO-06 | Tab *Đơn hàng về kho* trên chi tiết kho: dòng ĐMH sắp về, đã nhận về kho này — [thu mua 15 mục F](../../thu-mua/chuc-nang/15-ton-kho-cong-no.md) | Thủ kho, điều phối | Chi tiết kho | chưa ghi · có mã | chưa ghi |
| CN-KHO-07 | Tổng quan kho: tổng giá trị tồn, biểu đồ giá trị theo kho, tám mã tồn thấp nhất kèm nút tạo YCMH — [nghiên cứu kho lõi mục 3.1](../nghien-cuu/00-nghien-cuu-kho-erpnext.md) | Quản lý | `/inventory` | chưa ghi · có mã | chưa ghi |
| CN-KHO-08 | Danh mục kho có công ty sở hữu, loại kho (nội bộ, đối tác), cây kho (KHO-1.4, 1.5) — [TDD](../tai-lieu-ky-thuat/tdd-redesign-kho.md) | Quản trị | `/inventory/warehouses` | Chưa (TDD v0.1 chờ duyệt) | CR-001 |
| CN-KHO-09 | Vá nấc 1: ràng buộc duy nhất cho bảng tồn, điều chỉnh tay bắt lý do và chặn tồn âm, kiểm mã kho có trong danh mục, nhật ký sửa số nhận (KHO-1.1..1.3, 1.6) | Hệ thống | Chưa | Chưa | chưa có |
| CN-KHO-10 | Sổ kho chỉ ghi thêm, ngày ghi sổ, bình quân di động tại thời điểm ghi, khóa sổ, cài đặt kho (KHO-2.2..2.4) — [mục 5.4, 5.5](../nghien-cuu/00-nghien-cuu-kho-erpnext.md) | Kế toán kho | Màn cài đặt kho (dự kiến) | Chưa | chưa có |
| CN-KHO-11 | Phiếu kho chung *Nháp → Đã ghi sổ → Đã hủy*: nhập khác, xuất (KHO-2.5..2.7) — [mục 5.3, 5.6](../nghien-cuu/00-nghien-cuu-kho-erpnext.md) | Thủ kho, trưởng kho | Danh sách phiếu kho (dự kiến) | Chưa | chưa có |
| CN-KHO-12 | Chuyển kho một bước và hai bước qua kho đang chuyển (KHO-2.8) | Thủ kho | Phiếu kho | Chưa | chưa có |
| CN-KHO-13 | Kiểm kê (đếm mù, duyệt theo hạn mức) và số dư đầu kỳ (KHO-2.9, 2.12) | Thủ kho, hội đồng kiểm kê | Phiếu kho | Chưa | chưa có |
| CN-KHO-14 | Báo cáo số dư kho theo kỳ và sổ kho chi tiết, xuất Excel (KHO-2.13) | Kế toán kho, quản lý | Báo cáo | Chưa | chưa có |
| CN-KHO-15 | Tồn dự kiến (đang đặt, đang yêu cầu) và mức đặt hàng lại tự sinh YCMH nháp (KHO-2.14, 2.15) | Thu mua | Tổng quan kho | Chưa | chưa có |
| CN-KHO-16 | Chi phí thu mua vào giá kho bằng phiếu điều chỉnh giá trị (KHO-2.17) | Kế toán kho | Phiếu kho | Chưa | chưa có |
| CN-KHO-17 | Nấc 3: bảng kê nhập xuất theo mẫu MISA, đóng kỳ kho, tuổi tồn, xuất cho sản xuất, giữ chỗ, gửi gia công (KHO-3.1..3.8) | Kế toán kho, sản xuất | Nhiều màn | Chưa | chưa có |

Phiếu xuất theo mục đích và giao hàng có tài liệu riêng ở phân hệ [Xuất hàng](../../xuat-hang/chuc-nang/01-yeu-cau-chuc-nang.md);
phiếu nhập do thủ kho lập ở [Nhận hàng](../../nhan-hang/chuc-nang/01-yeu-cau-chuc-nang.md); lô và hạn dùng ở
[Lô, serial](../../lo-serial/chuc-nang/01-yeu-cau-chuc-nang.md).

## 3. Chi tiết từng chức năng

### CN-KHO-02 — Tồn kho

- **Mục đích:** biết từng kho của từng pháp nhân đang có bao nhiêu, giá trị bao nhiêu.
- **Luồng chính:** mở `/inventory/stock`, lọc theo kho, mã, nhóm hàng, còn hàng, hết hàng, tồn âm.
- **Luật nghiệp vụ:** mỗi lần có phát sinh, hệ thống cộng lại toàn bộ sổ của cặp *công ty, kho, mã*: `qty = Σ qty`, `value = Σ qty × đơn giá`, `avg_cost = value / qty` — [thu mua 15 mục D](../../thu-mua/chuc-nang/15-ton-kho-cong-no.md), [nghiên cứu mục 3.2](../nghien-cuu/00-nghien-cuu-kho-erpnext.md).
- **Dữ liệu:** `tab_inventory` (`company_id`, `warehouse_code`, `product_code`, `product_name`, `unit`, `qty`, `avg_cost`, `value`).
- **Quyền:** `inventory.read`; phạm vi chỉ chiều công ty.
- **Ngoại lệ / lỗi người dùng gặp:** chưa ghi.
- **Liên quan:** CN-KHO-03, CN-KHO-04; tab Tồn kho của Báo cáo mua hàng; thẻ tồn ở trang chủ.

### CN-KHO-03 — Điều chỉnh tồn tay

- **Mục đích:** sửa chênh lệch tồn khi chưa có phiếu kho.
- **Luồng chính:** bấm *Điều chỉnh tồn*, chọn công ty, kho, sản phẩm, số lượng tăng hoặc giảm, lý do → hệ thống thêm dòng sổ `ref_type = adjust` và tính lại tồn.
- **Luật nghiệp vụ:** đơn giá lấy theo người gọi nếu có, không thì lấy `avg_cost` hiện tại; không kiểm tồn âm, không có người duyệt — [thu mua 15 mục B, D](../../thu-mua/chuc-nang/15-ton-kho-cong-no.md).
- **Dữ liệu:** `company_id`, `warehouse_code`, `product_code`, `qty`, `note`.
- **Quyền:** `inventory.write`; `_writable_company` chặn ghi sang pháp nhân ngoài phạm vi.
- **Ngoại lệ / lỗi người dùng gặp:** chưa ghi.
- **Liên quan:** CN-KHO-09 (đề xuất bắt lý do, chặn tồn âm).

### CN-KHO-04 — Ghi tồn tự động khi nhận hàng

- **Mục đích:** tồn tăng ngay khi thu mua ghi số nhận trên lần giao của ĐMH.
- **Luồng chính:** lưu ĐMH có lần giao `received_qty > 0` → `apply_delivery` tạo hoặc ghi đè dòng sổ `ref_type = gr` theo `delivery_id` → tính lại tồn; đổi kho thì tính lại cả cặp cũ; lần giao về 0 hoặc bị xóa thì `remove_delivery` xóa dòng sổ.
- **Luật nghiệp vụ:** giá = đơn giá ĐMH × tỷ giá dòng — [thu mua 15 mục C](../../thu-mua/chuc-nang/15-ton-kho-cong-no.md), [nghiên cứu mục 3.2](../nghien-cuu/00-nghien-cuu-kho-erpnext.md).
- **Dữ liệu:** `tab_inventory_move`.
- **Quyền:** không cần quyền riêng, chạy trong dịch vụ ĐMH.
- **Ngoại lệ / lỗi người dùng gặp:** chưa ghi.
- **Liên quan:** [thu mua CN-TM-10](../../thu-mua/chuc-nang/01-yeu-cau-chuc-nang.md); đề xuất thay bằng phiếu nhập của thủ kho ở phân hệ Nhận hàng.

### CN-KHO-11 — Phiếu kho chung (dự kiến, nguồn nghiên cứu)

- **Mục đích:** mọi thay đổi tồn đi qua chứng từ có trạng thái, có người lập, người duyệt, thay cho điều chỉnh tay.
- **Luồng chính (đề xuất):** lập phiếu *Nháp* → (chờ duyệt nếu vượt hạn mức) → *Đã ghi sổ* → hủy bằng dòng đảo.
- **Luật nghiệp vụ (đề xuất):** bốn phiếu của nấc 2 (nhập khác, xuất, chuyển kho, kiểm kê) ở [mục 5.6](../nghien-cuu/00-nghien-cuu-kho-erpnext.md); luật khóa sổ, ghi lùi, tồn âm ở mục 5.5.
- **Dữ liệu (đề xuất):** `tab_stock_voucher` và dòng, `tab_stock_ledger` — mục 5.2.
- **Quyền (đề xuất):** entity mới `stock_voucher`, `stock_setting`, `inventory_value`; phạm vi theo kho — mục 5.7.
- **Ngoại lệ / lỗi người dùng gặp:** chưa có.
- **Liên quan:** CN-KHO-10, phân hệ Xuất hàng (XG1), Nhận hàng (N2.3).

## 4. Luồng trạng thái chứng từ

Hiện chưa có chứng từ kho; phiếu nhập ngầm `tab_goods_receipt` không có trạng thái. Đề xuất ở nghiên cứu mục 5.3:

```
Nháp → (Chờ duyệt) → Đã ghi sổ → Đã hủy → Sửa đổi
```

## 5. Câu hỏi còn mở

Chín câu Q1..Q9 ở [nghiên cứu kho lõi mục 7](../nghien-cuu/00-nghien-cuu-kho-erpnext.md) (phương pháp tính giá xuất, ngày cắt
chuyển sổ, có cho tồn âm, kho dùng chung nhiều pháp nhân, thủ kho từng kho, đơn giá số dư đầu kỳ, hạn mức duyệt, lô và hạn
dùng, ưu tiên kho hay công nợ). Không chép lại ở đây.

| # | Câu hỏi | Ai trả lời | Hạn |
|---|---|---|---|
| 1 | Duyệt TDD thiết kế lại danh mục kho bản v0.1 (CR-001) hay thay bằng việc KHO-1.4 của nghiên cứu | Agent 1 | chưa có |
| 2 | Q1..Q9 của nghiên cứu kho lõi | Đại ca, kế toán, trưởng kho | chưa có |
