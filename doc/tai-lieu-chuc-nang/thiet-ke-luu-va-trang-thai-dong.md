# Thiết kế: Nút "Lưu" vs Tự động lưu + Trạng thái dòng theo từng module

> Tài liệu quyết định (design decision) cho: khi nào hiện nút **Lưu**, khi nào **tự động lưu**;
> và mô hình trạng thái dòng của từng module: YCKS (`SurveyRequestLine.line_status`),
> YCMH (`PurchaseRequestItem.line_status`), ĐMH (`POItem.progress_status`).

## 1. Vấn đề

Người dùng thấy **không đồng bộ**: ở màn Yêu cầu mua hàng khi phiếu *đã duyệt*, sửa trạng thái dòng thì
**tự lưu ngay, không có nút Lưu**; trong khi các chỗ khác lại có nút Lưu. Cần chốt quy tắc chung.

## 2. Nguyên tắc (đã chốt)

Phân biệt **2 loại thao tác** theo bản chất, KHÔNG gom về một kiểu:

| Loại | Cơ chế | Áp dụng ở |
|---|---|---|
| **Sửa theo LÔ** (nhiều trường/nhiều dòng, lưu 1 lần) | Nút **Lưu** (bấm mới ghi) | Mọi màn khi **Nháp / Bị trả lại**; **ĐMH khi đã duyệt** (nhập nhiều lần giao + SL nhận + đính kèm) |
| **Cập nhật 1 TRƯỜNG vận hành** | **Auto-save + toast** ngay khi đổi | Trạng thái dòng YCKS; trạng thái dòng / NSTM phụ trách trên YCMH khi đã duyệt |

**Lý do:** nhập liệu nhận hàng trên ĐMH (nhiều lần giao, chứng từ đính kèm) là thao tác theo lô — bắt
buộc phải có nút Lưu. Ngược lại, đổi 1 ô trạng thái là hành động đơn lẻ, auto-save cho nhanh & liền mạch.

### Kết luận đề xuất "bỏ nút Lưu ở trạng thái khác Nháp trên ĐMH"
**KHÔNG bỏ.** ĐMH sau duyệt là nơi nhập dữ liệu nhận hàng theo lô → cần nút Lưu. Chỉ **ghi chú rõ
"tự động lưu"** cạnh các ô auto-save (trạng thái dòng, NSTM) để người dùng không tưởng là lỗi.

## 3. Áp dụng từng màn

- **ĐMH (`PurchaseOrderDetail`)**
  - Nút **Lưu/Tạo**: giữ ở Nháp và ở Đã duyệt/Đang giao/Đã nhận (cho phần lần giao). Làm **to hơn** cho dễ thấy.
  - **Trạng thái tiến độ dòng (`progress_status`)**: tự động tiến theo dữ liệu — không có dropdown chọn tay cho các bước tuần tự; hiển thị cả trong **popup chi tiết dòng**.
  - Bỏ nút **Nhân bản** trong chi tiết (đã chuyển ra danh sách).
  - **NSPT phụ trách**: chỉ admin/người có quyền duyệt được gán; KHÔNG auto-gán từ YCMH.
- **YCMH (`PurchaseRequestDetail`) & YCKS (`SurveyRequestDetail`)**
  - Nháp/Bị trả lại: nút **Lưu** (như hiện tại).
  - Đã duyệt: cập nhật trạng thái dòng / NSTM = **auto-save + toast**; thêm **ghi chú nhỏ "· tự động lưu"** cạnh ô.

## 4. Trạng thái dòng Yêu cầu khảo sát (`SurveyRequestLine.line_status`)

File: `backend/app/modules/survey_request/model.py`, `service.py`.

Đây là trạng thái do **người yêu cầu / phòng ban yêu cầu** cập nhật sau khi xem kết quả khảo sát.
Mục đích: xác nhận chấp thuận kết quả hay yêu cầu làm lại — KHÔNG phản ánh tiến độ đặt hàng.

Hằng số trong code: `LINE_STATUSES = ("", "can_khao_sat_lai", "hoan_thanh")` (service.py).

| Giá trị (DB) | Nhãn hiển thị | Mô tả |
|---|---|---|
| `""` | Chưa xác định | Giá trị mặc định — chưa có ý kiến của người yêu cầu |
| `"can_khao_sat_lai"` | Cần khảo sát lại | Kết quả chưa phù hợp, yêu cầu NSTM khảo sát lại |
| `"hoan_thanh"` | Hoàn thành | Đã chọn phương án, người yêu cầu chốt dòng xong |

**Quy tắc chuyển trạng thái (hàm `set_line_status`):**
- Chuyển sang `"hoan_thanh"`: bắt buộc dòng phải có ít nhất 1 option với `is_chosen = True`.
- Chuyển sang `"can_khao_sat_lai"`: tự động bỏ chọn (`is_chosen = False`) mọi option của dòng;
  nếu phiếu YCKS đang ở `"survey_done"` thì hạ về `"processing"`.
- Khi người YC bấm chọn 1 option (choose_option): nếu dòng đang ở `"can_khao_sat_lai"` thì tự gỡ về `""`.
- Khi NSTM chốt hoàn thành khảo sát (complete_sr) với dòng có option mới: nếu dòng đang ở `"can_khao_sat_lai"` thì tự gỡ về `""`.

**Đồng bộ cờ `is_completed`:** `is_completed = (line_status == "hoan_thanh")` — ghi luôn khi `set_line_status`.

**Ai cập nhật:** người yêu cầu / phòng ban yêu cầu qua endpoint `PATCH /{sid}/lines/{line_id}/line-status`.

## 5. Máy trạng thái tiến độ dòng ĐMH (`POItem.progress_status`)

File: `backend/app/modules/purchase_order/model.py`, `service.py`.

Tiến trạng thái là **HOÀN TOÀN TỰ ĐỘNG** (`apply_auto_progress` sau mỗi lần lưu ĐMH) theo điều kiện
cộng dồn. Người dùng **KHÔNG** đặt tay các bước tuần tự; chỉ có thể bấm **Tạm ngưng** / **Hủy đơn** /
**Tiếp tục** (ngoại lệ, bắt buộc nhập lý do).

### 5.1 Luồng tuần tự (PROGRESS_ORDER)

Hằng số: `PROGRESS_ORDER = ["Chưa đặt hàng", "Đã đặt hàng", "Đã nhận hàng", "Chưa gửi ĐMH cho KT", "Đã gửi ĐMH cho KT", "Hoàn thành"]`

| Bước (index) | Trạng thái | Điều kiện đủ để đạt bước này (cộng dồn từ bước 1) | Màu (tham khảo) |
|---|---|---|---|
| 0 | Chưa đặt hàng | (khởi tạo, không cần điều kiện) | xám |
| 1 | Đã đặt hàng | phiếu ĐMH có **Mã Misa** (`po.misa_code != ""`) | xanh dương |
| 2 | Đã nhận hàng | **SL nhận > 0** (`item.qty_received > 0`) | teal |
| 3 | Chưa gửi ĐMH cho KT | có **Số hóa đơn** (`item.invoice_no != ""`) | tím nhạt |
| 4 | Đã gửi ĐMH cho KT | có **Ngày giao chứng từ cho KT** (`item.document_delivery_date != ""`) | tím |
| 5 | Hoàn thành | **đã thanh toán dòng** (`is_line_paid = True`) — **điểm cuối, khóa** | xanh lá |

Điều kiện **CỘNG DỒN**: để tiến lên bước N, tất cả điều kiện từ bước 1 đến N đều phải thỏa.
Hàm `validate_progress` và `highest_satisfied_step` trong service.py kiểm tra theo logic này.

### 5.2 Trạng thái ngoại lệ (PROGRESS_EXCEPTIONS)

Hằng số: `PROGRESS_EXCEPTIONS = ["Tạm ngưng", "Hủy đơn"]`

| Trạng thái | Cách vào | Cách ra |
|---|---|---|
| Tạm ngưng | Bấm tay qua `set_item_progress`, bắt buộc nhập lý do; lưu trạng thái cũ vào `status_before_pause` | Bấm **Tiếp tục** (target `"__resume__"`) → khôi phục `status_before_pause` hoặc "Chưa đặt hàng" |
| Hủy đơn | Bấm tay qua `set_item_progress`, bắt buộc nhập lý do — **điểm cuối, không ra được** | (không thể thoát) |

### 5.3 Cơ chế tự tiến (`apply_auto_progress`)

Sau mỗi lần lưu ĐMH (`update_po`), hệ thống gọi `apply_auto_progress`:
1. Duyệt mọi dòng `POItem` của ĐMH.
2. Bỏ qua dòng đang ở "Hoàn thành", "Hủy đơn", "Tạm ngưng".
3. Tính `highest_satisfied_step` = bước cao nhất liên tục thỏa điều kiện (dừng ở bước hụt đầu tiên).
4. Nếu bước cao nhất > bước hiện tại → nâng `progress_status`, ghi audit.
5. Nếu có dòng nào đổi → commit + gọi `_sync_pr` để đồng bộ ngược về YCMH.

Cơ chế là **forward-only** (chỉ TIẾN), không hạ cấp tự động.

### 5.4 Khóa dòng ở điểm cuối

Dòng có `progress_status in ("Hoàn thành", "Hủy đơn")`:
- `_save_items` kiểm tra trước khi cập nhật — bỏ qua, không sửa.
- `set_item_progress` từ chối thao tác và trả lỗi.

### 5.5 Lưu ý: `POItem.line_status` khác với `progress_status`

`POItem` có thêm cột `line_status` (khác `progress_status`) phản ánh **tiến độ giao hàng thực tế**,
được tính lại tự động trong `recompute_effects`:

| Giá trị | Điều kiện |
|---|---|
| `"Chưa giao"` | `qty_received == 0` |
| `"Đang giao"` | `0 < qty_received < qty_order` |
| `"Đủ"` | `qty_received >= qty_order` |

Cột này không đồng bộ sang YCMH; chỉ dùng nội bộ ĐMH để hiển thị tình trạng giao từng dòng.

## 6. Trạng thái dòng YCMH (`PurchaseRequestItem.line_status`)

File: `backend/app/modules/purchase_request/model.py`, `service.py`.

Đây là trạng thái **rút gọn 5 mức**, chủ yếu được **đồng bộ tự động từ ĐMH**. Không khớp 1-1 với
`progress_status` của ĐMH (6 bước tuần tự + 2 ngoại lệ).

Hằng số: `LINE_STATUS = ["Chưa đặt hàng", "Đã đặt hàng", "Đã nhận hàng", "Hoàn thành", "Hủy đơn"]` (service.py).

| Giá trị | Mô tả | Nguồn |
|---|---|---|
| `"Chưa đặt hàng"` | Chưa có ĐMH đã đặt nào liên kết (mặc định) | Sync hoặc khởi tạo |
| `"Đã đặt hàng"` | Ít nhất 1 ĐMH liên kết đã đặt, chưa nhận hàng | Sync từ ĐMH |
| `"Đã nhận hàng"` | Đã có SL nhận > 0 (kể cả khi chưa gửi/đã gửi KT) | Sync từ ĐMH |
| `"Hoàn thành"` | Mọi dòng ĐMH liên kết đã đặt đều ở "Hoàn thành" | Sync từ ĐMH |
| `"Hủy đơn"` | Toàn bộ dòng ĐMH liên kết đều Hủy, hoặc đặt thủ công | Sync từ ĐMH / tay |

**Lưu ý rút gọn (CR-007 #3):** hai bước chứng từ kế toán của ĐMH ("Chưa gửi ĐMH cho KT" và "Đã gửi
ĐMH cho KT") được **GỘP** vào "Đã nhận hàng" phía YCMH. "Tạm ngưng" của ĐMH **không có** tương đương
bên YCMH (khi sync dùng `status_before_pause` thay thế).

**Ai cập nhật:**
- Chủ yếu: hàm `sync_from_purchase_orders` gọi tự động sau mỗi thay đổi trên ĐMH.
- Thủ công (hạn chế): `update_item_status` cho phép NSTM cập nhật dòng được giao; `return_pr` reset
  toàn bộ về "Chưa đặt hàng" khi trả lại phiếu.

## 7. Đồng bộ ĐMH -> YCMH (`sync_from_purchase_orders`)

File: `backend/app/modules/purchase_request/service.py`.

### 7.1 Khi nào chạy

- Lưu ĐMH (`update_po`) → `_sync_pr(db, po.pr_code)`.
- Đổi trạng thái phiếu ĐMH (`set_status`) → `_sync_pr`.
- Tự tiến trạng thái dòng ĐMH có đổi (`apply_auto_progress`) → `_sync_pr`.
- Đổi trạng thái dòng thủ công (`set_item_progress`) → `_sync_pr`.

### 7.2 ĐMH nào được tính

Chỉ tính ĐMH có `status NOT IN ("draft", "submitted", "cancelled", "rejected")`,
tức từ trạng thái "Đã duyệt" (approved) trở đi.

### 7.3 Quy tắc tính trạng thái dòng YCMH

Khớp theo `product_code`. Với mỗi sản phẩm, duyệt qua tất cả dòng ĐMH liên kết:
- Dòng `"Hủy đơn"`: ghi nhận vào `has_cancel`, **bỏ qua** khỏi tính SL và tiến độ.
- Dòng `"Tạm ngưng"`: thay bằng `status_before_pause` (hoặc "Đã đặt hàng" nếu trống) để tính tiến độ.
- Dòng `"Chưa đặt hàng"` (index < 1): **bỏ qua hoàn toàn** — không kéo tiến độ YCMH xuống.
- Các dòng còn lại: tích lũy tổng `qty_order` và `qty_received`; lấy mức tiến độ **thấp nhất** (min index theo `_PROGRESS_ORDER`).

Kết quả đặt vào `PurchaseRequestItem.line_status`:
- Không có dòng đủ điều kiện và có `has_cancel` → `"Hủy đơn"`.
- Không có dòng đủ điều kiện và không `has_cancel` → `"Chưa đặt hàng"`.
- Min index >= index của "Hoàn thành" → `"Hoàn thành"`.
- `qty_received > 0` → `"Đã nhận hàng"`.
- Còn lại → `"Đã đặt hàng"`.

**Ngoại lệ:** Nếu dòng YCMH đang ở `"Hủy đơn"` do **đặt thủ công** (không từ sync), hàm
`sync_from_purchase_orders` **giữ nguyên**, không ghi đè.

### 7.4 Đồng bộ SL

`qty_ordered` và `qty_received` của mỗi dòng YCMH được cập nhật bằng tổng SL đặt/nhận theo
`product_code` từ tất cả dòng ĐMH đủ điều kiện (bỏ dòng Hủy, gộp SL từ mọi lần giao).

### 7.5 Suy lại trạng thái phiếu YCMH (`recompute_status`)

Chạy sau khi sync xong, chỉ khi phiếu đang ở "approved" / "processing" / "completed":
- Mọi dòng active (không Hủy) đều "Hoàn thành" → phiếu `"completed"`.
- Có dòng không ở "Chưa đặt hàng" / "Hủy đơn" → phiếu `"processing"`.
- Còn lại → phiếu `"approved"`.

Dòng `"Hủy đơn"` **không cản** việc hoàn thành phiếu: 1 dòng hủy + các dòng còn lại đều Hoàn thành
= phiếu vẫn `"completed"`.
