---
title: "Hồ sơ nhân sự — tab Quá trình công tác / Quyết định bổ nhiệm (bản gọn V1-8)"
description: "Lịch sử công tác theo từng người, HR ghi tay, đính kèm tệp QĐ, hỏi rồi mới áp vào hồ sơ; xem ở /hr/employees/:id và /me."
status: completed
priority: P2
effort: 19h
branch: erp-v2
tags: [hrm, employee, work-history, attachment, frontend-v2, backend]
created: 2026-10-03
---

# Quá trình công tác (bản gọn của V1-8)

Chốt với đại ca 03/10/2026: lịch sử THEO NGƯỜI, HR ghi tay từng dòng; không phiếu nhiều người,
không duyệt, không tờ trình. Lưu dòng đã tới ngày hiệu lực → giao diện HỎI rồi mới áp vào hồ sơ
(một giao dịch). Tệp QĐ đính kèm thẳng vào dòng. `/me` chỉ đọc của chính mình.

## Quyết định đã chốt 03/10/2026

| # | Câu hỏi | Chốt |
|---|---|---|
| Q1 | Ngày hiệu lực vs Từ ngày | **GỘP**: `from_date` = ngày hiệu lực; `decision_date` (ngày ký QĐ) giữ riêng |
| Q2 | Dòng «Thôi việc» có áp hồ sơ? | **CÓ** — đã tới ngày thì hỏi «Chuyển hồ sơ sang nghỉ việc?» (hộp xác nhận RIÊNG, nói rõ khóa tài khoản + đăng xuất mọi thiết bị); đồng ý → đi đúng `update_employee` (nhánh `has_left_company` → `lock_linked_users`), cùng giao dịch với ghi dòng; `resign_date` = `from_date` của dòng |
| Q3 | HR tự ghi/sửa quá trình của mình | **CHẶN**, trừ quản trị hệ thống (`is_system_admin`) |
| Q4 | Mở tệp QĐ của người khác | **Cần thêm `employee_sensitive.read`** (ngoài `employee.read` + phạm vi). Chính chủ luôn mở được tệp của mình. Dòng lịch sử (không tệp) vẫn hiện với `employee.read`; FE ẩn nút xem/tải nhưng vẫn báo «có N tệp đính kèm» |

## Quyết định kiến trúc

| # | Quyết định | Lý do |
|---|---|---|
| A1 | Bảng mới `tab_employee_work_history`, FK mềm `employee_id` | Khuôn `tab_employee_department`; V1-8 sau chỉ THÊM `decision_id` |
| A2 | **KHÔNG entity quyền mới** — `employee.read/write` + `get_scoped(Employee)`; tệp thêm `employee_sensitive.read` (khóa ĐÃ CÓ) | CR-157, D-018, §5.4 `01-ho-so-nhan-su.md` |
| A3 | `event_type` SMALLINT + `WorkEventType(IntEnum)` ở `core/hr_work_history_codes.py` → `gen_status_ts` | R2/QĐ-11 |
| A4 | Áp hồ sơ CHỈ qua `service.update_employee` (chính + thôi việc) / `set_extra_departments` (kiêm nhiệm) | Không mở đường ghi thứ ba; tái dùng L1/L2/L3, sync_label, khóa TK khi nghỉ việc, xóa cache quyền |
| A5 | Áp hồ sơ idempotent; chỉ `applied_at/applied_by` | KISS |
| A6 | Tệp QĐ: entity đính kèm `employee_work_history` (cha `employee`, RIÊNG TƯ) + `work_history_access.check_file` ở đầu `_check` | Ngoại lệ chính chủ + gác `employee_sensitive.read` một chỗ |
| A7 | Không migration dữ liệu; danh sách rỗng → hộp Thêm điền sẵn từ hồ sơ | Không bịa lịch sử |
| A8 | Không tác vụ nền; dòng tương lai → HR bấm «Áp vào hồ sơ» khi tới ngày | Đại ca chốt |
| A9 | Cờ `can_edit`, `can_open_files` do BACKEND tính, trả kèm danh sách | FE không chép luật tự-sửa/quản trị/nhạy cảm |

## Phase

| # | Phase | Effort | Phụ thuộc | Trạng thái |
|---|---|---|---|---|
| 01 | [Backend: model, bộ mã, migration](phase-01-backend-model-bo-ma-migration.md) | 2h | — | completed |
| 02 | [Backend: API, áp hồ sơ, đính kèm, /me](phase-02-backend-api-ap-ho-so-dinh-kem.md) | 5h | 01 | completed |
| 03 | [Backend: bài kiểm](phase-03-backend-bai-kiem.md) | 3.5h | 02 | completed |
| 04 | [Frontend: tab Quá trình công tác ở hồ sơ](phase-04-frontend-tab-qua-trinh-cong-tac.md) | 5.5h | 01 + hợp đồng API ở 02 | completed (chưa bấm tay qua trình duyệt) |
| 05 | [Frontend: thẻ ở Trang cá nhân /me](phase-05-frontend-trang-ca-nhan.md) | 2h | 04 | completed (chưa bấm tay qua trình duyệt) |
| 06 | [Tài liệu, luật, nhật ký task](phase-06-tai-lieu-nhat-ky.md) | 1h | 03, 05 | completed |

Song song: **02 ∥ 04** (sau 01). 03 sau 02. 05 sau 04. Không hai phase song song nào chung tệp.

## Luồng dữ liệu

```
HR ── POST/PATCH /api/employees/{eid}/work-history {…, apply_to_profile, close_open_main}
   └─ require(employee.write) → get_scoped(Employee, write) → chặn tự sửa (trừ quản trị) → validate
      → ghi dòng (flush) → [apply: update_employee | set_extra_departments] → 1 commit → audit
Tệp QĐ ── /api/attachments (entity=employee_work_history) → _check → check_file
      (chính chủ đọc: qua · người khác: employee.read + phạm vi + employee_sensitive.read)
/me ── GET /api/employees/me/work-history (id từ phiên)
```

## Cổng hoàn thành
- pytest các tệp mới + `test_pham_vi_dinh_kem_b08.py` + `test_ho_so_nhan_su_dot1.py` xanh.
- typecheck 0 lỗi, lint 0 lỗi, vitest theo tên tệp mới xanh.
- Bấm tay: Bổ nhiệm hôm nay → hỏi → chip chức vụ đổi; Thôi việc hôm nay → hộp xác nhận riêng → tài khoản bị khóa; /me mở được tệp của mình.
- `gen_status_ts` «đã khớp»; migration lên/xuống sạch.

Câu hỏi treo: hết (xem phase-06).
