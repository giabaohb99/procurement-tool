# CR-688 Phase 12 — H1 Phúc lợi & sự kiện (BENEFIT_AUDIENCE=22)
Files (all new, <200 lines): employee/benefit_report_{controller,inputs,data,service,export}.py; test/backend/test_bao_cao_phuc_loi_cr688.py.
Tests: 31 passed (loc, ngay dip, dang nghi, dem con, ngan sach 2 muc, 403 nhay cam, 422, pham vi, gac khoa 3 duong, xlsx, query count 5 vs 50).
Decisions: managers/staff dem theo DON VI (con khi child_max_age) nen budget = managers*mq + staff*nv; /rows chi ho tro metric `people`; group_by mac dinh company, `none` = khong nhom; HD loai tru xet HD ky/con hieu luc tai ngay dip; nguoi nghi khong ghi resign_date khong tinh; nguoi chua co hire_date khong tinh; seniority = thang vao lam trung thang cua ngay dip va so nam tron thuoc danh sach; exclude_contract_types="" = khong loai ai.
Export dung scope `export`; ten dip (occasion_label) ≤100 ky tu, chan cong thuc qua text_cell.
Unresolved: none.
