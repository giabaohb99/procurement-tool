---
title: "duoc-CR-755 — Kiêm nhiệm thành tab riêng, cho kiêm nhiệm ở công ty khác"
description: "Bảng kiêm nhiệm có công ty, chức vụ, ngày, quyết định; phạm vi quyền theo cặp (phòng, công ty); tab Kiêm nhiệm; nhãn ở phòng B"
status: in-progress
priority: P2
effort: 38h
branch: erp-v2
tags: [hr, employee, scope, permission, multi-company]
created: 2026-11-12
---

# duoc-CR-755 — Kiêm nhiệm thành tab riêng, cho kiêm nhiệm ở công ty khác
Trạng thái kế hoạch: **đang làm**

> **Mô hình cặp (phòng, công ty) đã thay bằng duoc-CR-756** (13/11/2026): hai loại dòng Phòng ban / Công ty độc lập — xem
> [`../261113-kiem-nhiem-phong-ban-cong-ty-doc-lap-duoc-cr-756/plan.md`](../261113-kiem-nhiem-phong-ban-cong-ty-doc-lap-duoc-cr-756/plan.md) và `01-ho-so-nhan-su.md` §7.18.

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 12/11/2026 | planner | Nháp | duoc-CR-755 (nền: CR-167, duoc-CR-342, bao-CR-709, duoc-CR-585) |

Người chủ chốt 12/11/2026: (1) công tắc **Tính vào phạm vi quyền** từng dòng, mở đúng CẶP (phòng, công ty), chỉ dòng còn hiệu
lực; (2) trường: công ty, phòng, chức vụ, từ ngày, đến ngày, số QĐ, ngày QĐ, tệp QĐ, ghi chú, công tắc — không phụ cấp;
(3) người gán phải sửa được hồ sơ (công ty chính) VÀ phạm vi ghi phủ cặp đích; giữ L1; (4) phòng B thấy người kiêm nhiệm có nhãn,
báo cáo chỉ đếm ở công ty + phòng CHÍNH; (5) tab riêng **Kiêm nhiệm**. Nghiên cứu ERPNext:
`plans/reports/researcher-261112-1420-erpnext-kiem-nhiem-multi-company.md` (ERPNext không có sẵn).

| # | Giai đoạn | Chủ | Phụ thuộc | Giờ | Trạng thái |
|---|---|---|---|---|---|
| 01 | [BE dữ liệu, migration, dịch vụ, API](phase-01-be-du-lieu-migration-api.md) | backend | merge `origin/erp-v2` | 8 | Chờ |
| 02 | [BE phạm vi quyền theo cặp + bài canh](phase-02-be-pham-vi-theo-cap.md) | backend | 01 | 8 | Chờ |
| 03 | [BE quá trình công tác, đổi pháp nhân, nhập Excel](phase-03-be-qua-trinh-doi-phap-nhan-nhap-excel.md) | backend | 01 | 6 | Xong |
| 04 | [FE tab Kiêm nhiệm trên hồ sơ](phase-04-fe-tab-kiem-nhiem.md) | giao-dien-v2 | 01 (API), 03 (tham số đổi pháp nhân) | 7 | Xong |
| 05 | [Hiển thị ở phòng B: danh sách, sơ đồ, /me, AI](phase-05-hien-thi-phong-b-so-do-me-ai.md) | fullstack | 02 (hàm phủ cặp, cờ `include_concurrent`), 03 | 6 | Chờ |
| 06 | [Tài liệu, HDSD, cẩm nang, RAG](phase-06-tai-lieu-hdsd-rag.md) | tai-lieu-kiem-thu | 04, 05 | 3 | Xong phần tài liệu, HDSD (local), cẩm nang (local); RAG + sổ do điều phối |

Thứ tự: **01 → (02 ∥ 03) → (04 ∥ 05) → 06**. Không deploy giữa 01 và 04 (01 gỡ `PUT /departments`, thẻ cũ chết tới khi 04 xong).

## Quyết định thiết kế dữ liệu — BẢNG MỚI `tab_employee_concurrent`
Chọn bảng mới, `tab_employee_department` chỉ còn dòng phòng CHÍNH (giữ để 12 nơi đọc `Employee.department_id` + tham chiếu
xóa phòng không đổi). Lý do bỏ phương án mở rộng bảng cũ:
- `set_departments` **xóa hết chèn lại** → id dòng đổi mỗi lần lưu → tệp QĐ (`FileLink.entity_id` = id dòng) mồ côi.
- UNIQUE(employee, department) chặn cùng phòng hai giai đoạn, và chặn cả trường hợp phổ biến: **phòng dùng chung**
  (`company_id = 0`, 26/27 phòng prod theo bao-CR-659) — cùng một id phòng ở công ty A (chính) và công ty B (kiêm nhiệm).
- Một bảng hai nghĩa (dòng chính không ngày, dòng kiêm nhiệm có ngày) bắt mọi nơi đọc phải nhớ lọc ngày + công tắc.
Dòng phụ cũ (`is_primary = 0`) chuyển sang bảng mới (công ty = công ty chính, ngày trống, tính phạm vi = bật) rồi xóa khỏi bảng cũ.

## Luật cốt lõi (áp mọi phase)
- **Hiệu lực** = `(from_date IS NULL OR from_date <= vn_today()) AND (to_date IS NULL OR to_date >= vn_today())`. Không tác vụ
  nền: lọc lúc dựng hồ sơ quyền; cache 60 giây nên dòng hết hạn lúc 0h còn tác dụng tối đa 60 giây. Nhãn Sắp tới / Đang hiệu
  lực / Đã hết là mã DẪN XUẤT (`ConcurrentStatus` IntEnum, không lưu cột).
- **Hồ sơ quyền**: dòng hiệu lực + bật công tắc, cùng công ty chính → gộp vào `dept_ids` (hành vi y CR-167); khác công ty →
  khóa mới `concurrent_pairs` = `[[phòng, công ty], ...]`. `company_id` giữ MỘT số (bậc company không phình).
- Các đường dùng `dept_ids` không ràng công ty (`dept_proc`, `_narrow_to_dept`, `_handler_match`) tự động không thấy cặp khác
  công ty; cặp khác công ty chỉ vào qua nhánh có `AND company == c`. Ngoại lệ chốt Q3: `subject_pairs` cộng THÊM phòng của
  `concurrent_pairs` (ACL không mang công ty).
- Đọc HỒ SƠ người kiêm nhiệm (Q1): nhánh `EXISTS` trên `tab_employee_concurrent`, chỉ hành động `read`, BẬT TƯỜNG MINH
  (`include_concurrent=True`) ở các đường đọc hồ sơ; báo cáo, sơ đồ (truy vấn gốc), xuất tệp, ghi giữ mặc định TẮT.
- Báo cáo nhân sự đọc `Employee.company_id/department_id` — không đổi, không đếm trùng.
- Chức vụ kiêm nhiệm **không** cấp vai trò hệ thống (duoc-CR-653 chỉ theo chức vụ chính).

## Rollback
Đảo thứ tự phase. `alembic downgrade` của migration `kn755a`: chép lại dòng hiệu lực cùng công ty chính về `tab_employee_department`
(`is_primary = 0`), bỏ bảng mới — dòng khác công ty + ngày + QĐ mất (báo trước, sao lưu bảng trước khi hạ). Tệp `FileLink`
entity `employee_concurrent` để lại (không xóa kho).

## Quyết định đã chốt (người chủ, 12/11/2026)
- **Q1 CÓ** — người có phạm vi `dept`/`company` phủ cặp (phòng, công ty) của dòng kiêm nhiệm còn hiệu lực + bật công tắc mở
  được HỒ SƠ ĐẦY ĐỦ (cả `get_scoped`), như người phòng mình. Nhạy cảm vẫn che theo `employee_sensitive`, lương chỉ chính chủ.
  Kế hoạch tự giới hạn: chỉ ĐỌC (sửa hồ sơ vẫn theo vị trí chính), danh sách `/hr/employees` không đổi (Q5) — phase 02, 05.
- **Q2 KHÔNG** — chức vụ kiêm nhiệm không tự cấp vai trò.
- **Q3 CÓ** — ACL theo phòng (văn bản, thư mục, báo cáo, skill AI qua `subject_match`) tính phòng của dòng kiêm nhiệm khác công
  ty còn hiệu lực + bật công tắc. Rủi ro chấp nhận: phòng dùng chung nhiều công ty → ACL cấp cho phòng X (ý cho công ty C) cũng
  khớp người kiêm nhiệm (X, B) — phase 02.
- **Q4** Đổi pháp nhân: kết thúc dòng ở công ty cũ (đến ngày = hôm qua), hộp hỏi để giữ; dòng công ty khác không đụng — phase 03.
- **Q5** Chỉ trang chi tiết phòng ban + sơ đồ tổ chức; `/hr/employees` lọc theo phòng không đổi — phase 05.
- **Q6** Bật công tắc mở cả hành động bậc phòng (duyệt, sửa) trên đúng cặp, theo vai trò sẵn có — phase 02.
