# Phase 07 — B2 Sổ quản lý lao động + B3 mẫu 01/PLI

**Trạng thái:** pending · **Chủ:** BE-3 · **Phụ thuộc:** 06
**Tài liệu:** `doc/erp/hrm/05-bao-cao-nhan-su.md` mục B2, B3 (đã kiểm luật 27/10/2026)

## Chủ tệp
Thư mục mới `backend/app/modules/labor_register/` (controller, service, rows, xlsx builder…) · `backend/app/main.py` (chỉ include router mới) · `backend/app/modules/assistant/tools/report_summary_tool.py` (mở 2 khóa) · `test/backend/test_phan_quyen_bao_cao_gac_duong.py` (thêm đường) · test mới `test/backend/test_bao_cao_so_lao_dong_cr687.py`, `test_bao_cao_mau_01_pli_cr687.py`.

## Chung
- Gác: `require('employee', read|export)` + `require_report(key)` + `apply_scope(Employee, "employee")`, VÀ trong service đòi thêm `employee_sensitive.read` và `labor_contract.read` (thiếu → 403 nói rõ thiếu quyền gì) — sổ và mẫu chứa CCCD, BHXH, ngày sinh, địa chỉ, lương.
- Tập người: nhân sự làm việc ở BẤT KỲ lúc nào trong kỳ (`hire_date ≤ cuối kỳ` và chưa nghỉ hoặc `resign_date ≥ đầu kỳ`; thiếu `hire_date` thì lấy ngày tạo hồ sơ, ghi notes). Lọc `company_id`, `department_id`.
- HĐ áp cho mỗi người = HĐ đã ký (SIGNED/TERMINATED) có hiệu lực tại cuối kỳ, không có thì HĐ gần nhất trước đó.
- Số truy vấn cố định (bài đếm 5 vs 50 người). Tệp < 200 dòng.
- `/summary` theo khuôn Haravan: KPI + Xem theo (company, department, job_category) + `meta.drilldown_metrics`; `trend = []`. `/summary/rows` trả danh sách theo hợp đồng `core/report_drilldown.py`.

## B2 — `/api/labor-register/summary` · khóa 19
- Chỉ số: `people` «Người trong sổ» · `working` «Đang làm cuối kỳ» · `left_in_period` «Nghỉ việc trong kỳ» · `missing_required` «Thiếu thông tin bắt buộc» (thiếu một trong: ngày sinh, CCCD, địa chỉ thường trú, trình độ, ngày vào làm, loại HĐ).
- Xuất `/summary/export`: Excel SỔ QUẢN LÝ LAO ĐỘNG, mỗi pháp nhân MỘT sheet (tên pháp nhân, MST, địa chỉ ở đầu sheet), mỗi người một dòng. Cột: STT · Mã NV · Họ tên · Giới tính · Ngày sinh · Quốc tịch (trống) · Nơi cư trú · Số CCCD · Trình độ chuyên môn · Bậc kỹ năng nghề (trống) · Vị trí việc làm (chức vụ) · Loại HĐLĐ · Ngày bắt đầu làm việc · Số BHXH · Tiền lương (HĐ) · Nâng lương (các mức lương HĐ trước → nay, «dd/mm/yyyy: số») · Ngày nghỉ có lương trong năm · Ngày nghỉ không lương trong năm (từ Nghỉ phép, chia theo kỳ như CR-686) · Giờ làm thêm (trống) · Đào tạo (trống) · Kỷ luật (trống) · Tai nạn LĐ / bệnh nghề nghiệp (trống) · Ngày chấm dứt HĐ · Lý do.

## B3 — `/api/labor-usage-report/summary` · khóa 20
- Chỉ số: `people` «Tổng lao động» · `female` «Nữ» · `job_manager`, `job_high`, `job_mid`, `job_other` (4 nhóm vị trí việc làm, tự suy `job_category_of`) · `ct_indefinite`, `ct_fixed`, `ct_other` (loại HĐ: không xác định / xác định thời hạn / khác gồm thử việc, khoán, cộng tác viên, chưa có HĐ).
- Xuất `/summary/export`: Excel đúng Mẫu số 01/PLI, mỗi pháp nhân một sheet:
  - Đầu: tên pháp nhân · «CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM / Độc lập - Tự do - Hạnh phúc» · «BÁO CÁO TÌNH HÌNH SỬ DỤNG LAO ĐỘNG» · «Kính gửi: Sở Nội vụ …» · mục 1 thông tin chung (tên, địa chỉ, MST; điện thoại/fax/email/website/ngành nghề để trống).
  - Bảng 27 cột, tiêu đề 3 tầng có gộp ô đúng mẫu, dòng đánh số 1…27, dòng Tổng, khối ký «ĐẠI DIỆN DOANH NGHIỆP, CƠ QUAN, TỔ CHỨC (Chữ ký, dấu)», chú thích (2) vị trí việc làm.
  - Cột: 2 Họ tên · 3 Mã số BHXH · 4 Ngày sinh · 5 Giới tính · 6 Số CCCD · 7 Chức vụ, nơi làm việc · 8–11 đánh «x» theo nhóm vị trí · 12 Mức lương (HĐ) · 13–15 phụ cấp chức vụ / thâm niên VK / thâm niên nghề (trống) · 16 Phụ cấp lương (ô phụ cấp của HĐ) · 17 Các khoản bổ sung (trống) · 18–19 nặng nhọc (trống) · 20 ngày bắt đầu HĐ không xác định thời hạn · 21–22 bắt đầu / kết thúc HĐ xác định thời hạn · 23–24 bắt đầu / kết thúc HĐ khác · 25–26 BHXH (trống) · 27 Ghi chú (nghỉ việc ngày … nếu nghỉ trong kỳ).
- Cột trống ghi rõ ở `notes` để Nhân sự điền tay.

## Thành công khi
Bài kiểm: tập người theo kỳ, phạm vi + chỉ thu hẹp, 403 thiếu quyền nhạy cảm / HĐLĐ / chưa giao báo cáo (cả `/rows`, `/export`), suy nhóm vị trí, chọn HĐ, mở được tệp Excel và soi đúng ô tiêu đề gộp + cột 1…27, số truy vấn cố định. `-k "cr687 or gac_duong or assistant_report_summary"` xanh.
