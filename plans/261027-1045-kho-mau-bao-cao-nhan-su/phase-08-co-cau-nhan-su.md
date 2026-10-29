# Phase 08 — A2 Cơ cấu nhân sự (mở rộng A1 «Biến động nhân sự»)

**Trạng thái:** pending · **Chủ:** BE-1 · **Phụ thuộc:** 06 · **Không khóa mới.**

## Chủ tệp
`backend/app/modules/employee/report_*.py` (A1) · test mới `test/backend/test_bao_cao_co_cau_cr687.py`.

## Việc
- Thêm 3 chiều «Xem theo» cho `/api/employees/summary`: `age_band` «Nhóm tuổi» (dưới 25 · 25–34 · 35–44 · 45–54 · 55 trở lên · chưa có ngày sinh; tuổi tính tại ngày sự kiện / ngày mốc, như thâm niên) · `education` «Trình độ» · `work_location` «Địa điểm làm việc» · `job_category` «Nhóm vị trí việc làm» (dùng `job_category_of` ở `employee/constants.py`).
- Đọc ngày sinh CHỈ để gom nhóm; không trả ra ngoài.
- **Che nhóm nhỏ:** khi `group_by=age_band`, nhóm có định biên cuối kỳ < 3 người → mọi giá trị số của nhóm đó thành `null` (giao diện hiện «—») và có dòng `notes` giải thích. Không áp cho người có `employee_sensitive.read`.
- `/summary/rows` với `group_by=age_band` + `group_key`: người thiếu `employee_sensitive.read` → 403 (danh sách theo nhóm tuổi lộ tuổi từng người).
- Số truy vấn giữ cố định.
