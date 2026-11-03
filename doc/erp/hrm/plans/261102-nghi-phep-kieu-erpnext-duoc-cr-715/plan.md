# duoc-CR-715 — Nghỉ phép kiểu ERPNext (hrms) vào phân hệ Nhân sự

Trạng thái kế hoạch: **xong** · CR liên quan: duoc-CR-715

Anh Được chọn (02/11/2026): cả 5 chức năng. Đối chiếu nguồn: `doc/erp/nghien-cuu/erpnext/04-hrms-chuc-nang-va-lien-ket.md` §4,
mã ERPNext ở `nexterp/hrms`. Luật nghỉ phép hiện có: `.claude/rules/hr-leave.md`, `doc/erp/hrm/02-nghi-phep.md`.

| # | Giai đoạn | Trạng thái |
|---|---|---|
| A | [Luật loại nghỉ + cách cấp quỹ](phase-01-luat-loai-nghi-va-cap-quy.md) — cấp theo tỷ lệ / cộng dần, quỹ theo cấp bậc / hình thức, nghỉ sau N ngày vào làm, ứng phép | Xong (migration `lvacc715`) |
| B | [Ngày cấm nghỉ](phase-02-ngay-cam-nghi.md) — cảnh báo lúc lập, chặn lúc duyệt | Xong (migration `lvblk715`, `HookVeto` ở `entity_hooks`) |
| C | [Phiếu xin nghỉ bù](phase-03-phieu-nghi-bu.md) — làm ngày lễ / ngày nghỉ, duyệt xong cộng quỹ | Xong (migration `lvcmp715`, khóa `leave_comp_request`) |

**Thứ tự bắt buộc A → B → C**: cả ba thêm migration (chuỗi `down_revision` nối nhau, head hiện tại `jobrun01`) và cùng
sửa `leave/catalog_model.py`, `balance_service.py`, `frontend-v2/src/modules/hr/routes.tsx`.

Luật chung cho cả ba giai đoạn:
- Mặc định của mọi cột / công tắc mới = hành vi HIỆN TẠI (bật tính năng mới là việc của quản trị).
- Số ngày phép còn lại chỉ tính ở `balance_service.remaining()`; mọi chốt đủ quỹ đi qua `check_enough*` — không thêm đường thứ hai.
- Bộ mã số mới (R2/QĐ-11): SMALLINT + `IntEnum` ở `leave/constants.py`, bản TS gõ tay ở `hr/types/leave.ts`.
- Cột `String(n)` phải có `max_length` ở schema (`.claude/rules/backend-input-limits.md`).
- Migration autogenerate phải gọt về đúng thay đổi của mình (repo trôi ~650 dòng mỗi lần).
- Không commit; mỗi giai đoạn chạy cổng: pytest các tệp liên quan, `npm run typecheck` (trên host), `npx eslint`, `npx vitest run src/modules/hr`.
- Bài HDSD: cập nhật `backend/scripts/seed_help_nghi_phep.py` cuối mỗi giai đoạn.
