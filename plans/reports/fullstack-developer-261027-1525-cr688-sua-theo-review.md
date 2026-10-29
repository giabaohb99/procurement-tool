# CR-688 sua theo code review

Status: DONE. Test: 251 passed (-k "cr688 or co_cau or che_nhom or bao_cao_nhan_su or bien_dong or gac_duong or assistant_report_summary or bao_cao_cache"). Chua commit.

1. report_small_group: tra `SmallGroupResult(changed, unsafe_sides)` (bool-compatible); vong thu cap chi chay o ky co nhom 1-2 nguoi that; khong cuu duoc -> `drop_unsafe_breakdown` (groups=[], breakdown rong, ghi chu "Khong du nguoi..."). Ap cho A2 (report_headcount_privacy) va A5. A5 /rows: group_key khong nam trong nhom hien -> 403.
2. A5 dedupe theo (employee_id, company_id); note "hai phap nhan"; NOTE_SMALL viet lai.
3. H1: thieu hire_date -> created_at (to_local_date) + note dem; include_on_leave=0 can leave_request.read (403); dung can_read_sensitive; chunk 900; hire_estimated tren BenefitRow. Truy van nhan su 2 (co/khong hire_date).
4. A3: metric `manager_resigned` (+ drilldown, cot); khong tinh la da gan, khong cong cap duoi, nhom "(Chua gan)"; nhan quan ly chi con ten.
5. D1: phong di chua ap -> "(Chua ro)" neu co dong nhom chinh da ap muon hon; cot `months` chi o avg_months_to_appoint, so (float).
6. Go /api/payroll-fund/summary khoi REPORT_SUMMARY_PATHS; docstring "13 bao cao" sua (chi docstring dau tep).
7. `as_of_filtered`, `not_resigned_cond` cong khai o report_headcount_events (giu alias ten cu); A3/D1 nhap ten cong khai.

Tests moi: test_che_nhom_nho_cr688, quy_luong (3), co_cau_cr687 (3), phuc_loi (2), co_cau_quan_ly (2), dieu_chuyen (1) + sua months.

Ngoai danh sach file: sua report_headcount_events.py (muc 7 - home module).
Chua giai quyet: mo ta tool `report_summary_tool.py` dong ~246 van ghi "13 bao cao" (chuoi hien cho AI, khong phai docstring).
