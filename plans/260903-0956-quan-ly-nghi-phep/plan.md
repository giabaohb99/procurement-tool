# Quản lý nghỉ phép — phân hệ Nhân sự (V1-6 + V1-7)

| | |
|---|---|
| Bản | 1.1 — 03/09/2026 (**ĐÃ LÀM XONG P-01…P-07**) |
| Nhánh | `erp-v2` |
| CR | **CR-259** — số cũ CR-258 đã bị đợt *Dự án* chiếm, đánh lại |
| Nguồn nghiệp vụ | `doc/erp/tham-khao-hrm/02-don-tu-va-duyet.md` (DT1, DT6) · `10-de-xuat-ap-dung.md` (V1-6, V1-7) |

---

## 0. Vì sao đợt này làm được

Doc xếp **V0-3 bộ máy duyệt dùng chung** đứng trước mọi thứ: *"Làm DT1 trước DT7 thì phải
viết luồng duyệt cứng cho nghỉ phép, rồi vứt đi lúc làm DT7."*

**V0-3 đã xong** — `backend/app/modules/approval/` là bộ máy generic (`flow.entity` là chuỗi
tự do, 7 kiểu chọn người duyệt, rẽ nhánh theo điều kiện, ủy quyền, SLA, CC). Cắm module mới
vào bằng `entity_hooks.register(...)`. Nên rào chắn đã dỡ.

## 1. Hiện trạng — đã có một nửa, ở phân hệ Văn thư

CR-159 làm *Giấy nghỉ phép* thành **loại văn bản `GNP`**, dữ liệu nằm trong
`tab_document.metadata` (JSON).

| Đã có | Ở đâu |
|---|---|
| Tờ đơn 8 ô | `document/type_metadata.py::_check_leave` |
| Bộ mã 7 loại nghỉ + 3 buổi | `core/leave_codes.py` → sinh sang `statuses.ts` |
| Luồng duyệt riêng cho GNP | `seed_luong_nghi_phep.py` |
| Form + màn chi tiết | `document/components/document-leave-fields.tsx` |
| Trợ lý AI soạn nháp | `assistant/tools/draft_tool.py` |

**Chưa có, và chính là phần doc gọi là đáng giá nhất:**

| Thiếu | Hệ quả |
|---|---|
| Quỹ phép năm | **Không hiện được _số phép còn lại_ trên form.** `type_metadata.py` ghi rõ là hoãn có chủ ý |
| Cấu hình loại đơn (V1-6) | 7 loại nghỉ là mã CỨNG. Đổi luật = sửa code + deploy |
| Bảng bậc thâm niên | Luật *5 năm +1 ngày* không khai được bằng dữ liệu |
| Lịch ngày lễ | `suggested_days()` cố ý không trừ T7/CN/lễ |
| `hire_date`, `gender` trên `tab_employee` | Không tính được thâm niên, không lọc loại nghỉ theo giới tính |
| Danh sách người bàn giao | Hiện chỉ **một** người (`handover_employee_id`) |
| Lịch nghỉ · báo cáo · thống kê | Dữ liệu trong ô JSON — không đánh chỉ mục, không gộp theo ngày được |

## 2. Quyết định đã chốt với chủ đầu tư (03/09/2026)

| # | Nội dung | Chốt |
|---|---|---|
| **QĐ-NP1** | Phạm vi | Đủ **V1-6 + V1-7**: cấu hình loại nghỉ + quỹ phép + đơn nghỉ + duyệt + Lịch nghỉ |
| **QĐ-NP2** | Ứng phép (nghỉ vượt quỹ, ghi nợ) | **KHÔNG làm.** Vượt quỹ thì chặn lúc nộp; muốn nghỉ tiếp thì chọn loại *Nghỉ không lương* |
| **QĐ-NP3** | Dữ liệu nền | Thêm **hết**: `tab_employee.hire_date`, `tab_employee.gender`, bảng `tab_holiday` |
| **QĐ-NP4** | Đơn vị nghỉ | Bản này: người dùng **chọn ngày + nhập tổng số ngày**. Cột `unit` khai sẵn 3 giá trị (ngày / nửa ngày / theo giờ) nhưng chỉ dùng giá trị *ngày*; khi có phân hệ **Lịch làm việc** thì migrate sang nửa ngày + theo giờ, KHÔNG phải đổi cấu trúc bảng |
| **QĐ-NP5** | Kiến trúc | **Module `leave` riêng** là nguồn sự thật. Đơn duyệt xong thì **sinh văn bản GNP** lưu văn thư — giữ nguyên giá trị hồ sơ và không bỏ phí CR-159 |

### QĐ-NP5 nói rõ hơn

Vì sao không mở rộng GNP tại chỗ: *Lịch nghỉ* và mọi báo cáo phải hỏi câu
"tuần tới ai nghỉ" và "người này năm nay dùng bao nhiêu ngày". Hỏi được câu đó trên cột
`DATE` có chỉ mục; quét `JSON_EXTRACT` trên `tab_document.metadata` thì vừa chậm vừa không
đánh chỉ mục được, và trừ quỹ phép sẽ dựa trên một ô không có ràng buộc kiểu.

Vì sao không bỏ GNP: văn bản GNP là **giấy tờ hồ sơ** — có số hiệu, có chữ ký, nằm trong sổ
văn bản. Đơn nghỉ phép là **chứng từ nghiệp vụ**. Hai thứ khác nhau, giữ cả hai và nối lại.

## 3. Kiến trúc đích

```
Nhân viên nộp đơn  →  tab_leave_request (Nháp)
        │                     │ gửi duyệt
        │                     ▼
        │            approval/instance_service.start("leave_request", …)
        │                     │  ← luồng khai bằng dữ liệu, vai tương đối
        │                     ▼  duyệt hết các bước
        │            leave/approval_bridge._on_approved
        │                     ├─ trừ quỹ:  tab_leave_balance.used_days
        │                     └─ sinh giấy: tab_document (loại GNP) ── vào sổ văn thư
        ▼
 số phép còn lại hiện NGAY trên form  ←  balance_service.remaining_days()
                                          = cấp phát (theo bậc thâm niên)
                                          + chuyển năm trước
                                          + điều chỉnh tay
                                          − đã dùng
```

## 4. Bảng dữ liệu mới

| Bảng | Vai trò | Ghi chú |
|---|---|---|
| `tab_leave_type` | **V1-6** — cấu hình loại nghỉ, ~15 cột (không phải 50) | Doc bảo bản 1 chỉ cần `tinhCong`, `theoCa`, hạn mức năm, bậc thâm niên |
| `tab_leave_type_seniority` | Bảng bậc phép theo thâm niên | `years_from`/`years_to`/`extra_days` — luật đổi thì sửa **dữ liệu**, không sửa mã |
| `tab_leave_balance` | Quỹ phép của một người trong một năm | `unique(employee_id, year, leave_type_id)` |
| `tab_leave_request` | **V1-7** — đơn nghỉ phép | Cột ngày là `DATE` có chỉ mục |
| `tab_leave_handover` | Người nhận bàn giao việc (nhiều người) | Doc DT1 `lsNhanVienBanGiao` |
| `tab_holiday` | Lịch ngày lễ | `company_id = 0` là áp cho mọi pháp nhân |

Sửa bảng cũ: `tab_employee` **thêm** `hire_date` (DATE, null) + `gender` (SMALLINT, 0 = chưa khai).
Đúng quy tắc 1 của bộ ERP — *chỉ thêm, không sửa*.

## 5. Các đợt

| Đợt | Nội dung | Nghiệm thu riêng được |
|---|---|---|
| [P-01](./phase-01-nen-du-lieu.md) ✅ | Bộ mã · 6 bảng mới · 2 cột `tab_employee` · migration · `all_models` | `alembic upgrade head` chạy sạch, bảng có đủ |
| [P-02](./phase-02-quyen-va-pham-vi.md) ✅ | 4 entity mới + khai `SCOPE_FIELDS` + seed vai trò | `test_pham_vi_khai_du_b07.py` xanh với số mới |
| [P-03](./phase-03-nghiep-vu-quy-phep.md) ✅ | `workday_service` (trừ T7/CN/lễ) · `balance_service` (thâm niên, còn lại) | Test đơn vị cho hai service |
| [P-04](./phase-04-don-nghi-phep-api.md) ✅ | Model → schema → service → controller của đơn nghỉ | Nộp/sửa/xóa/gửi duyệt qua API |
| [P-05](./phase-05-cam-vao-bo-may-duyet.md) ✅ | `approval_bridge` + trừ quỹ khi duyệt + sinh giấy GNP | Duyệt xong: quỹ giảm đúng, có văn bản GNP |
| [P-06](./phase-06-man-hinh-v2.md) ✅ | 7 màn ở `frontend-v2/src/modules/hr/` | `npm run check` xanh |
| [P-07](./phase-07-seed-va-tai-lieu.md) ✅ | Seed loại nghỉ + ngày lễ 2026 + luồng duyệt · tài liệu chức năng · gói tri thức Trợ lý AI | Đăng nhập thật nộp được đơn |

## 6. Ràng buộc bắt buộc, không được bỏ

1. **Số phép còn lại hiện ngay trên form lúc nộp.** Doc: *"chi tiết nhỏ, nhưng nó cắt phần
   lớn số đơn sai và phần lớn câu hỏi gửi về phòng Nhân sự"*. Đây là lý do tồn tại của cả đợt.
2. **Bậc thâm niên khai bằng dữ liệu**, không viết cứng số 5 vào mã nguồn.
3. **Cột trạng thái là `SMALLINT` + hằng số nguyên** (R2/QĐ-11), tiếng Việt chỉ ở tầng hiển
   thị. Khuôn mẫu: `vehicle_booking/model.py`. Không phải khuôn mã chuỗi của Thu mua (QĐ-9
   chỉ áp cho các cột ĐÃ có trong kế hoạch đó).
4. **Khai `SCOPE_FIELDS` cho đủ 4 entity mới.** Thiếu là `test_pham_vi_khai_du_b07.py` đỏ —
   cố ý, để lỗ hổng không quay lại lặng lẽ.
5. **Đọc một dòng theo id phải qua `get_scoped(...)`**, không `db.get(...)` — không thì gõ id
   vào URL là vượt rào bộ lọc danh sách.
6. **Ô chỉ xem cấm `<Input disabled>`** — dùng `shared/ui/read-only-value.tsx`.
7. **Bảng danh sách dùng `DataTable`**, đọc `docs/ui/table.md` trước.

## 7. Câu chưa có lời

| # | Câu | Ai quyết | Đang chặn |
|---|---|---|---|
| Q1 | Phép năm cấp **một lần đầu năm** hay **cộng dần theo tháng làm việc**? Bản này làm cấp một lần đầu năm, cấn theo thâm niên tính tại 01/01 | Phòng Nhân sự | P-03, đổi được sau vì nằm gọn trong `balance_service` |
| Q2 | Phép năm **chuyển sang năm sau** được không, hạn tới khi nào? Bản này khai cờ `carry_over` trên loại nghỉ, mặc định TẮT | Phòng Nhân sự | Không chặn — cờ đã có sẵn |
| Q3 | Ai được xem đơn nghỉ của người khác — trưởng phòng thấy cả phòng là chắc, còn phòng Nhân sự thấy toàn công ty thì cấp bằng phạm vi `company` hay entity riêng? Bản này dùng phạm vi `company` | Phòng Nhân sự | Không chặn |
| Q4 | Nhân viên cũ **chưa có `hire_date`** thì thâm niên tính từ đâu? Bản này coi như 0 năm và ghi cảnh báo lên màn Quỹ phép | Phòng Nhân sự | P-07, phải nhập bù trước khi chạy thật |
