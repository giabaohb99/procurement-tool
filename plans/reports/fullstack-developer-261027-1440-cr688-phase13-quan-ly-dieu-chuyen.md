# CR-688 phase 13 — A3 Cơ cấu quản lý (23) + D1 Điều chuyển & bổ nhiệm (24)

Test: 36 passed (18 + 18). Không commit.

## Files (employee/, mỗi tệp < 200 dòng)
- management_report_{controller,data,service}.py (A3)
- work_move_report_{controller,data,service}.py (D1)
- test/backend/test_bao_cao_co_cau_quan_ly_cr688.py, test_bao_cao_dieu_chuyen_cr688.py

## Quyết định
- A3: 3 loại hàng p/m/d (người · quản lý · người nghỉ). Quản lý ngoài tập đang xem KHÔNG sinh hàng m (không nở phạm vi), chỉ tra tên/tình trạng làm nhãn. Chiều `manager`: dòng của quản lý M có staff = số cấp dưới. `/summary` flat: không so sánh kỳ, trend [].
- A3 export dùng phạm vi `export` (apply_scope action). D1 cũng vậy.
- D1: lọc department/company theo hồ sơ HIỆN TẠI của người (ghi trong notes). Phòng đi = dòng NHÓM CHÍNH liền trước có khai phòng; không có + dòng chưa áp (trừ Tuyển dụng) → phòng hồ sơ hiện tại; còn lại «(Chưa rõ)». Snapshot kiêm nhiệm loại người đã nghỉ.
- Rows không có tệp QĐ; chỉ số quyết định.
- Số truy vấn cố định (test 5 vs 50 người, có kỳ so sánh ở D1).

## Cần lưu ý
- `avg_span`, `avg_months_to_appoint` khai kind="int" (không có kind số lẻ không đơn vị); FE `formatMoney` làm tròn 0 số lẻ → hiện 4 thay vì 4,2. Cần FE thêm kind (vd `number`) hoặc chấp nhận.
- /rows `people_moved` trả mọi dòng sự kiện trong kỳ (mỗi hàng một dòng, không gộp theo người).
- Không đụng test_phan_quyen_bao_cao_gac_duong.py (BE điều phối tự thêm 2 khóa nếu cần).

**Status:** DONE_WITH_CONCERNS
**Summary:** A3 + D1 xong đủ 3 đường mỗi báo cáo, 36 test xanh.
**Concerns/Blockers:** kind số lẻ cho 2 chỉ số trung bình (FE làm tròn); people_moved rows là theo dòng.
