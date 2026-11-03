# Giai đoạn A — Luật loại nghỉ + cách cấp quỹ

## Bối cảnh
`balance_service.ensure_balance` cấp `allocated_days = annual_quota_days` ĐỦ CẢ NĂM cho mọi người, kể cả người vào làm
tháng 11 — trái Điều 113 khoản 2 BLLĐ 2019 (chưa đủ 12 tháng thì theo tỷ lệ tháng làm việc). ERPNext có: cấp theo tỷ lệ
ngày vào làm (Leave Policy Assignment), cộng dần theo tháng (earned leave), **applicable after N working days**, **allow
negative**, Leave Policy theo nhóm.

## Quyết định thiết kế
1. `tab_leave_type.accrual_mode` SMALLINT NOT NULL default 1 — `LeaveAccrualMode`:
   - `1 FULL_YEAR` — đủ đầu năm (như cũ).
   - `2 PRORATA_HIRE` — người VÀO LÀM TRONG NĂM được `quota × số tháng làm / 12`; vào làm ngày 1–15 tính cả tháng đó, từ
     16 tính từ tháng sau; làm tròn tới 0.5 ngày (round half up). Vào trước năm đó → đủ quota. Chưa có `hire_date` → đủ.
   - `3 MONTHLY` — cộng dần: số dùng được tới hôm nay = `allocated_days × số tháng đã tới (tính cả tháng hiện tại) / số
     tháng của kỳ` (kỳ = từ tháng vào làm nếu vào trong năm, không thì 12 tháng); làm tròn xuống 0.5. `allocated_days` lưu
     CẢ NĂM (đã tỷ lệ như mode 2) để báo cáo đọc đúng; phần chưa tới tháng trừ ở `remaining()`. Năm đã qua → đủ.
   - Thâm niên (`seniority_days`), phần mang sang, điều chỉnh tay: KHÔNG tỷ lệ, KHÔNG cộng dần.
2. Quỹ theo nhóm: bảng `tab_leave_type_quota(id, leave_type_id, basis SMALLINT, basis_value SMALLINT, quota_days FLOAT,
   audit)`, UNIQUE(leave_type_id, basis, basis_value). `basis`: `1 EMPLOYMENT_TYPE`, `2 JOB_LEVEL` (bộ mã ở
   `employee/constants.py`). Thứ tự áp lúc cấp: khớp hình thức nhân viên → khớp cấp bậc → `annual_quota_days`. Đường API
   thay-cả-danh-sách `PUT /api/leave-types/{id}/quotas` + `GET` (gác `leave_type.write` / `read`), trần 50 dòng.
3. `tab_leave_type.applicable_after_days` INT NOT NULL default 0 (0–3650): ngày bắt đầu của khoảng sớm nhất có dòng loại
   đó < `hire_date + N` → 422 **Loại nghỉ X chỉ dùng được sau N ngày vào làm (từ dd/mm/yyyy)**. Kiểm ở lập / sửa (khi ngày
   hoặc dòng loại đổi) / gửi duyệt. Không có `hire_date` → không chặn.
4. `tab_leave_type.max_negative_days` FLOAT NOT NULL default 0 (0–30): `check_enough*` cho còn lại xuống tới `-N`
   (ứng phép). Loại không tính quỹ (`counts_balance=False`) không bị ảnh hưởng.
5. Quỹ ĐÃ CẤP không tính lại khi đổi mode / quota (luật hiện có ở `balance_controller.allocate`), TRỪ mode 3 vì phần
   **chưa tới tháng** tính động ở `remaining()` — lời giải thích trên form phải nói rõ điều này.

## Tệp
Backend: `leave/catalog_model.py`, `leave/constants.py`, `leave/schema.py`, `leave/balance_service.py` (ensure_balance,
remaining, check_enough*), `leave/request_service.py` (gọi chốt N ngày), `leave/catalog_controller.py` (đường quota +
serializer), migration mới, `test/backend/test_nghi_phep_cap_quy_cr715.py`.
Frontend: `hr/types/leave.ts`, `hr/api/*leave-type*`, `hr/pages/leave-type-detail-page.tsx` (+ ô mới, bảng quota),
vitest kèm. Bài HDSD loại nghỉ.

## Xong khi
- Bài kiểm: vào làm 10/03 → 12 × 10/12 = 10; vào 20/03 → 9.5 (từ tháng 4 → 9 tháng = 9); mode 3 tháng 5 → 5/12 quota;
  quota theo hình thức thắng cấp bậc; N ngày chặn đúng biên; ứng phép cho xuống -N không hơn; mặc định = hành vi cũ
  (bộ bài nghỉ phép cũ xanh nguyên).
