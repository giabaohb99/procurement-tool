# Nhiều loại nghỉ trong một đơn nghỉ phép

| | |
|---|---|
| Ngày | 07/09/2026 |
| Nhánh | `erp-v2` |
| Phân hệ | Nhân sự ▸ Nghỉ phép (`backend/app/modules/leave/` · `frontend-v2/src/modules/hr/`) |
| Tài liệu nền | `doc/tai-lieu-chuc-nang/17-nghi-phep.md` |

## 1. Việc phải làm

Một tờ đơn hiện gắn **đúng một** `leave_type_id`. Yêu cầu: một đơn khai được
**nhiều loại nghỉ** — *"nghỉ 07→10/09, trong đó 3 ngày phép năm + 1 ngày không lương"*.

## 2. Bốn điều đã chốt với người dùng (07/09/2026)

| Câu hỏi | Chốt |
|---|---|
| Hình dạng dòng | **Một khoảng ngày chung**, chia SỐ NGÀY theo loại. Dòng không có ngày riêng |
| Giấy GNP | **Một giấy cho cả đơn**; `metadata.leave_type` lấy loại chiếm nhiều ngày nhất, thêm ô `leave_lines` liệt kê đủ |
| `leave_type_id` đầu đơn | **Giữ**, thành cột DẪN XUẤT = loại nhiều ngày nhất. Bộ lọc + `entity_context` của luồng duyệt không phải sửa |
| Nghỉ theo giờ | **Chỉ 1 loại**. Chọn «Theo giờ» thì đơn khóa còn đúng một dòng |

## 3. Mô hình

Bảng mới `tab_leave_request_line` — `request_id · leave_type_id · days · sort_order`.

Hai cột đầu đơn trở thành **dẫn xuất, backend tự đặt, giao diện không gõ**:

```
total_days   = Σ line.days
leave_type_id = loại của dòng nhiều ngày nhất (hòa → dòng đầu)
```

Luật trên dòng:

1. Ít nhất 1 dòng, tối đa `MAX_LINES = 10`.
2. **Một loại không khai hai lần** — gộp vào một dòng.
3. Mỗi dòng `days > 0`. Ngoại lệ: đơn CHỈ CÓ MỘT dòng và `days = 0` thì máy tự
   tính từ khoảng ngày (giữ nguyên hành vi cũ).
4. Trần theo khoảng: `Σ days` không vượt số ngày dương lịch của khoảng
   (`(to − from).days + 1`). Trần này không bao giờ chặn nhầm ca hợp lệ — kể cả
   công ty chạy Chủ nhật — nhưng chặn được ca gõ 30 ngày trên khoảng 2 ngày.
5. `check_gender` và `check_max_days` xét **theo từng dòng**, theo loại của dòng đó.
6. Đơn theo giờ: đúng 1 dòng, `days` là phép chia, không cho gõ đè.

Sổ quỹ chạy **theo dòng** ở cả bốn nhịp — `reserve` · `consume` · `release` ·
`refund_used`. Không dòng nào bị bỏ sót là điều kiện sống còn của phân hệ.

## 4. Tương thích ngược

- API vẫn **nhận** `leave_type_id` + `total_days` như cũ khi không gửi `lines`
  (Trợ lý AI, bài kiểm, kịch bản seed chạy nguyên).
- API vẫn **trả** `leave_type_id` / `leave_type_name` (loại chính) nên danh sách,
  lịch nghỉ, bộ lọc, hộp việc duyệt không đổi hợp đồng.
- Migration backfill: mỗi đơn cũ sinh đúng một dòng `(leave_type_id, total_days)`.

## 5. Hạn chế đã biết — ghi ra để không ai tưởng là lỗi

Điều kiện rẽ nhánh của luồng duyệt đọc `leave_type_id`, tức **loại chính**. Đơn
3 ngày phép năm + 1 ngày không lương sẽ KHÔNG kích nhánh khai theo "không lương".
Không đưa danh sách loại vào `entity_context` vì `condition_service` chỉ so được
giá trị vô hướng — thêm một ô mà phép `in` không đọc nổi thì tệ hơn là không có.

## 6. Các bước

### Backend
- [x] `request_model.py` — bảng `LeaveRequestLine` + quan hệ `lines`
- [x] `schema.py` — `LeaveLineItem` vào `Create`/`Update`, `lines` ra `Response`
- [x] `request_service.py` — dựng dòng, sáu luật ở §3, bốn nhịp quỹ theo dòng
- [x] `approval_bridge.py` — `consume`/`release` theo dòng, GNP mang `leave_lines`
- [x] `request_serializer.py` — nạp dòng theo LÔ (không N+1), `line_count`
- [x] `request_controller.py` · `inbox_controller.py` — truyền map dòng
- [x] `catalog_controller.py` — chốt xóa loại nghỉ phải xét cả bảng dòng
- [x] `all_models.py` không phải sửa (dòng nằm trong `request_model`)
- [x] Migration `+ backfill`

### Frontend (`frontend-v2`)
- [x] `types/leave.ts` — `LeaveRequestLine`, `lines` trên `LeaveRequest`
- [x] `utils/leave-form-values.ts` — `lines` trong form, dựng payload
- [x] `components/leave-request-lines-editor.tsx` — bảng dòng loại nghỉ (mới)
- [x] `components/leave-request-form.tsx` — thay ô đơn lẻ bằng bảng dòng
- [x] `components/leave-request-summary.tsx` · `leave-decision-dialog.tsx` — hiện đủ dòng
- [x] `components/leave-request-columns.tsx` — cột loại nghỉ hiện «Phép năm +1»

### Kiểm tra
- [x] `test/backend/test_nghi_phep_nhieu_loai.py` — bài kiểm mới
- [x] Bộ kiểm nghỉ phép cũ còn xanh
- [x] `docker compose exec erp npm run check`
- [x] Cập nhật `doc/tai-lieu-chuc-nang/17-nghi-phep.md` + `change-log.md`
