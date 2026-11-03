# YÊU CẦU CHỨC NĂNG — NHẬP KHẨU

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · CR chính trong tài liệu cũ: bao-CR-319, bao-CR-321, bao-CR-347, bao-CR-453, bao-CR-602 |

Tệp này là **mục lục chức năng**, mỗi dòng trỏ về tài liệu gốc chứa chi tiết. Nguồn: [10 Hồ sơ và tiến độ nhập
khẩu](10-danh-sach-tinh-nang.md) (bản 1.1, 12/09/2026, **tạm dừng**), [11 Chi phí thu mua](11-chi-phi-thu-mua.md) (bản 1.1,
22/09/2026) và [thu mua 13 Đơn mua hàng](../../thu-mua/chuc-nang/13-don-mua-hang.md) mục A, K — nơi giữ đặc tả hiện hành của
phần đã code.

## 1. Người dùng và vai trò

| Vai trò (mã vai trò) | Làm gì trong phân hệ |
|---|---|
| Nhân sự thu mua (phạm vi `proc`, `dept_proc`) | Lập đơn nhập khẩu, gõ chi phí, chốt tạm tính, quyết toán; tick hồ sơ nhập khẩu (theo đáp án H5 của tài liệu 10) |
| Quản lý thu mua (`pur_manager`, `pur_dept_manager`) | Như trên, cộng mở lại giai đoạn hoặc dòng chi phí đã chốt (bắt ghi lý do) |
| Admin, `pur_manager` | Quản danh mục Loại chi phí thu mua |
| Người lập YCTT | Tạo YCTT từ dòng chi phí đã sinh công nợ |

Nguồn: [11 mục 7](11-chi-phi-thu-mua.md), [10 mục 9](10-danh-sach-tinh-nang.md).

## 2. Danh sách chức năng

| Mã | Chức năng | Ai dùng | Màn / nơi dùng | Trạng thái | CR |
|---|---|---|---|---|---|
| CN-NK-01 | Đơn mua hàng loại nhập khẩu: `order_type`, đồng tiền, tỷ giá đầu đơn và từng dòng, số và ngày tờ khai, ETD — [thu mua 13 mục A.18..A.26, B.30..B.31](../../thu-mua/chuc-nang/13-don-mua-hang.md) | NSTM | Chi tiết ĐMH | chưa ghi | bao-CR-319, bao-CR-347 |
| CN-NK-02 | Điều khoản in trên đơn (số ngày kiểm hàng, số ngày đổi trả, hạn nhận hóa đơn) lấy mặc định từ NCC — [thu mua 13 mục A.23..A.25](../../thu-mua/chuc-nang/13-don-mua-hang.md), [thu mua 16 mục Nhà cung cấp](../../thu-mua/chuc-nang/16-danh-muc.md) | NSTM | Chi tiết ĐMH, bản in | chưa ghi | bao-CR-321 |
| CN-NK-03 | Chi phí thu mua ba giai đoạn (dự toán, tạm tính, quyết toán) trên **mọi loại đơn**, mỗi giai đoạn một tỷ giá, chốt và mở lại — [11 mục 5.1, 5.2](11-chi-phi-thu-mua.md), [thu mua 13 mục K.0, K.1](../../thu-mua/chuc-nang/13-don-mua-hang.md) | NSTM, QL thu mua | Khối *Chi phí thu mua* trên chi tiết ĐMH | Dev (tài liệu ghi code xong 22/09/2026, prod chưa lên lúc viết) | bao-CR-453 |
| CN-NK-04 | Phân bổ chi phí về dòng hàng theo năm cách (giá trị, khối lượng, số lượng, chỉ định mã, nhập tay), **chỉ để xem**, không vào giá kho — [11 mục 5.4](11-chi-phi-thu-mua.md), [thu mua 13 mục K.2](../../thu-mua/chuc-nang/13-don-mua-hang.md) | NSTM | Chi tiết ĐMH | Dev (cùng đợt bao-CR-453) | bao-CR-319, bao-CR-453 |
| CN-NK-05 | Công nợ cho từng dòng chi phí (sinh ở Quyết toán, trừ loại đánh dấu *không sinh*) và lập YCTT từ đó — [11 mục 5.3](11-chi-phi-thu-mua.md), [thu mua 13 mục K.4](../../thu-mua/chuc-nang/13-don-mua-hang.md), [thu mua 15 Luồng 3](../../thu-mua/chuc-nang/15-ton-kho-cong-no.md) | NSTM, người lập YCTT | Chi tiết ĐMH, Công nợ | Dev (cùng đợt bao-CR-453) | bao-CR-319, bao-CR-453 |
| CN-NK-06 | Giá vốn lô hàng nhập khẩu (báo cáo, tính lúc xem) — [thu mua 13 mục K.5](../../thu-mua/chuc-nang/13-don-mua-hang.md), [thu mua 17 tab Giá vốn nhập khẩu](../../thu-mua/chuc-nang/17-he-thong-bao-cao.md) | Quản lý | Báo cáo mua hàng, `/print/import-landed-cost` | chưa ghi | bao-CR-347, bao-CR-453 |
| CN-NK-07 | Danh mục Loại chi phí thu mua (15 mã mẫu, quản trị thêm bớt) — [11 mục 5.5](11-chi-phi-thu-mua.md), [thu mua 13 mục K.6](../../thu-mua/chuc-nang/13-don-mua-hang.md) | Admin, `pur_manager` | `/procurement/po-cost-types` | Dev (cùng đợt bao-CR-453) | bao-CR-453 |
| CN-NK-08 | Checklist hồ sơ nhập khẩu theo dòng hàng: danh mục chặng, khuôn hồ sơ, sinh checklist, tick, người phụ trách, hạn — [10 mục 6 nhóm A, B](10-danh-sach-tinh-nang.md) | NSTM | Tab *Hồ sơ nhập khẩu* trên ĐMH (dự kiến) | Chưa (tạm dừng 12/09/2026); một phần có qua Báo cáo thực hiện trên ĐMH | Chưa cấp; bao-CR-602 |
| CN-NK-09 | Tiến độ nhập khẩu tính theo ngày: số ngày trễ, ngày hàng về dự kiến, chặng chặn — [10 mục 6 nhóm C, mục 7.1](10-danh-sach-tinh-nang.md) | NSTM, quản lý | Chi tiết ĐMH | Chưa | Chưa cấp |
| CN-NK-10 | Màn Báo cáo tiến độ nhập khẩu, bốn ô số, bốn đồ thị, xuất Excel — [10 mục 6 nhóm D, mục 7](10-danh-sach-tinh-nang.md) | Quản lý | `/procurement/import-progress` (dự kiến) | Chưa | Chưa cấp |
| CN-NK-11 | Nhắc việc hồ sơ: chuông khi được giao, nhắc trước hạn, nhắc quá hạn — [10 mục 6 nhóm E](10-danh-sach-tinh-nang.md) | NSTM, trưởng phòng | Chuông, thư | Chưa (E01 dùng lại hệ thông báo sẵn có) | Chưa cấp |

## 3. Chi tiết từng chức năng

### CN-NK-01 — Đơn mua hàng nhập khẩu

- **Mục đích:** ghi đơn mua từ NCC nước ngoài bằng ngoại tệ, quy đổi về đồng theo tỷ giá, kèm thông tin tờ khai.
- **Luồng chính:** lập ĐMH, chọn loại đơn nhập khẩu, đồng tiền, tỷ giá; sau khi có tờ khai thì điền số, ngày tờ khai; in mẫu nhập khẩu (`/print/purchase-order-import/:id`).
- **Luật nghiệp vụ:** đi theo luật ĐMH (khóa sau duyệt CR-108); tỷ giá có ở đầu đơn và từng dòng. Chi tiết ở [thu mua 13 mục A.18..A.26](../../thu-mua/chuc-nang/13-don-mua-hang.md).
- **Dữ liệu:** `order_type`, `currency`, `exchange_rate`, `customs_decl_no`, `customs_decl_date`, `etd_date`.
- **Quyền:** như ĐMH, entity `purchase_order`.
- **Ngoại lệ / lỗi người dùng gặp:** chưa ghi.
- **Liên quan:** CN-NK-03, CN-NK-06; tra cứu giá hải quan (`customs/`).

### CN-NK-03 — Chi phí thu mua ba giai đoạn

- **Mục đích:** ghi mọi chi phí ngoài giá hàng (cước, thuế, phí cảng…) theo ba con số dự toán, tạm tính, quyết toán để so lệch và trả tiền đúng khoản.
- **Luồng chính:** gõ chi phí theo loại ở cột Dự toán → chốt Tạm tính → chốt Quyết toán (hoặc quyết toán riêng từng dòng) → công nợ sinh ở Quyết toán → lập YCTT; người có quyền duyệt mở lại được, bắt ghi lý do.
- **Luật nghiệp vụ:** bảy điểm đã chốt ở [11 mục 0](11-chi-phi-thu-mua.md); phí vận chuyển giữ chỗ cũ trên lần giao, khối chỉ hiện thêm một dòng chỉ xem; chi tiết vận hành ở [thu mua 13 mục K](../../thu-mua/chuc-nang/13-don-mua-hang.md).
- **Dữ liệu:** bảng `tab_po_cost` (đổi tên từ `tab_po_import_cost`), `tab_po_cost_type` — [11 mục 6.1, 6.2](11-chi-phi-thu-mua.md).
- **Quyền:** xem `purchase_order.read`; gõ, chốt `purchase_order.write`; mở lại `purchase_order.approve` kèm lý do; danh mục `purchase_cost_type.read/write` — [11 mục 7](11-chi-phi-thu-mua.md).
- **Ngoại lệ / lỗi người dùng gặp:** chưa ghi.
- **Liên quan:** CN-NK-04, CN-NK-05, CN-NK-07; bài HDSD *Chi phí thu mua trên đơn mua hàng*.

### CN-NK-08 — Checklist hồ sơ nhập khẩu

- **Mục đích:** trả lời trên màn hình lô hàng đang ở chặng nào, thiếu giấy tờ gì, ai đang giữ, khi nào hàng về ([10 mục 2](10-danh-sach-tinh-nang.md)).
- **Luồng chính (dự kiến):** khai danh mục chặng và khuôn hồ sơ → trên dòng hàng của đơn nhập khẩu chọn khuôn, hệ thống chép thành checklist → thu mua tick, gán người, đính kèm tệp → tiến độ tự tính theo ngày.
- **Luật nghiệp vụ:** sáu đáp án H1..H6 ở [10 mục 11](10-danh-sach-tinh-nang.md); bản 1 chỉ cảnh báo tiền quyết, không khóa; checklist chạy được trên đơn nháp; phải nới khóa sửa sau duyệt CR-108 cho checklist.
- **Dữ liệu:** mô hình tóm tắt ở [10 mục 8](10-danh-sach-tinh-nang.md).
- **Quyền:** dùng lại `purchase_order` (`read` xem, `write` tick và sửa danh mục) — [10 mục 9](10-danh-sach-tinh-nang.md).
- **Ngoại lệ / lỗi người dùng gặp:** chưa có (chưa làm).
- **Liên quan:** Báo cáo thực hiện trên ĐMH (bao-CR-602, [thu mua CN-TM-04](../../thu-mua/chuc-nang/01-yeu-cau-chuc-nang.md)) đã phủ B03, B06, B13, B21 và một phần B04; trước khi làm tiếp phải rà theo [10 mục 14](10-danh-sach-tinh-nang.md).

## 4. Luồng trạng thái chứng từ

Phân hệ không có chứng từ riêng. Giai đoạn chi phí đi theo thứ tự:

```
Dự toán → Tạm tính (chốt) → Quyết toán (chốt, sinh công nợ); mở lại cần quyền duyệt và lý do
```

Trạng thái dòng hồ sơ nhập khẩu (dự kiến, [10 mục 6 B05](10-danh-sach-tinh-nang.md)): Chưa bắt đầu · Đang làm · Chờ đối
tác · Hoàn thành · Không áp dụng.

## 5. Câu hỏi còn mở

| # | Câu hỏi | Ai trả lời | Hạn |
|---|---|---|---|
| 1 | Có khóa cột Dự toán ngay khi đơn được duyệt không | Khách / đại ca | chưa có |
| 2 | Lệch vượt bao nhiêu phần trăm thì cảnh báo lên chuông quản lý | Khách / đại ca | chưa có |
| 3 | Báo cáo so sánh có cần theo NCC dịch vụ không | Khách / đại ca | chưa có |
| 4 | Khi nào mở lại việc hồ sơ và tiến độ nhập khẩu (tạm dừng từ 12/09/2026), và rà bốn chỗ hỏi lại ở [10 mục 14](10-danh-sach-tinh-nang.md) | Đại ca | chưa có |

Câu 1 tới 3 lấy từ [11 mục 11](11-chi-phi-thu-mua.md).
