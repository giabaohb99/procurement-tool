# Phase 24 — A4 và A5 đọc kế hoạch theo kỳ (duoc-CR-690)

Thiết kế: `doc/erp/hrm/06-ke-hoach-nhan-su.md` §3 (kỳ hẹp thay kỳ rộng), §6 (so với thực tế). Chạy SAU phase 22.
Ưu tiên P1 · Chủ: BE-11 · Trạng thái: pending

## Luật chọn kế hoạch có hiệu lực cho một tháng
Với (pháp nhân, phòng, tháng m): lấy kế hoạch phủ tháng m có loại kỳ HẸP nhất (MONTH > QUARTER > HALF > YEAR). Theo pháp nhân và tháng: có kế hoạch
«Toàn pháp nhân» hiệu lực thì dùng nó, không thì cộng các kế hoạch phòng (giữ luật chống cộng đôi của CR-689). Hàm dùng chung
`modules/headcount_plan/effective.py`: `load_effective_monthly(db, user, prof, months, company_id, department_id, action)` →
{(company_id, department_id, position_id, month): {"headcount": n, "items": {code: amount}, "actual_source": …}} — gom SQL, số truy vấn cố định,
dùng `costing.compute_plan(...)["monthly"]`.

## A4 Định biên kế hoạch so với thực tế (khóa 25)
- Định biên kế hoạch = headcount của tháng cuối kỳ báo cáo. Thêm chiều «Xem theo» **Vị trí**.
- `/rows` khớp số như hiện tại (thiếu người theo vị trí).

## A5 Quỹ lương theo pháp nhân (khóa 21)
Thay 3 cột cũ bằng (chỉ khi xem được kế hoạch, và chỉ cộng pháp nhân người xem `can_see_payroll`):
- «Chi phí nhân sự kế hoạch» = Σ mọi khoản của các tháng trong kỳ báo cáo;
- «Kế hoạch phần so được» = Σ các khoản có `actual_source ≠ NONE`;
- «Thực tế phần so được» = từ HĐLĐ cộng theo đúng nguồn của các khoản đó, theo tháng trong kỳ (BASE / ALLOWANCE / % × lương đóng BHXH với trần của khoản);
- «Còn dư» = kế hoạch so được − thực tế so được; «% dùng».
Ghi chú (`notes`) liệt kê các khoản không có thực tế. Giữ dòng riêng cho pháp nhân/phòng có kế hoạch mà chưa có HĐ, giữ che nhóm nhỏ.

## Dọn
Migration riêng `hcplan03_...` DROP `planned_headcount`, `planned_payroll_monthly`. Sửa `payroll_report_plan.py`, `headcount_plan_report_*`,
bài kiểm `test_bao_cao_dinh_bien_ke_hoach_cr689.py`, `test_bao_cao_quy_luong_cr688.py` theo khuôn mới; bài đếm truy vấn còn xanh;
`test_phan_quyen_bao_cao_gac_duong.py` xanh. Giao diện A5 (`payroll-fund-report-page.tsx`) đổi nhãn cột nếu khóa chỉ số đổi.
