---
title: "duoc-CR-756 — Kiêm nhiệm phòng ban và công ty độc lập"
description: "Sửa mô hình CR-755: dòng loại Phòng ban (phòng của công ty hiện tại) và dòng loại Công ty (công ty khác, không phòng); phạm vi công ty kiêm nhiệm theo bậc vai trò"
status: in-progress
priority: P1
effort: 23h
branch: erp-v2
tags: [hr, employee, scope, permission, multi-company]
created: 2026-11-13
---

# duoc-CR-756 — Kiêm nhiệm phòng ban và công ty độc lập
Trạng thái kế hoạch: **xong**

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 13/11/2026 | planner | Nháp | duoc-CR-756 (sửa duoc-CR-755; nền CR-167, bao-CR-709, duoc-CR-585) |

Người chủ chốt 13/11/2026: CR-755 sai mô hình (cặp công ty → phòng chọn theo tầng). Đúng: *"anh A kiêm nhiệm phòng ban A
và công ty B; phòng ban thuộc công ty hiện tại"*. Hai loại dòng; công ty B tính như công ty của họ THEO BẬC vai trò.
CR-755 đã commit trên `erp-v2`, CHƯA lên dev/prod — `kn755a` + `kn756a` sẽ chạy cùng lượt deploy.

| # | Giai đoạn | Chủ | Phụ thuộc | Giờ | Trạng thái |
|---|---|---|---|---|---|
| 01 | [BE dữ liệu, API tab, luồng ghi, L2](phase-01-be-du-lieu-luong-ghi-l2.md) | backend A | merge `origin/erp-v2` | 8 | Xong |
| 02 | [BE phạm vi đọc, chủ thể, hiển thị, /me, AI](phase-02-be-pham-vi-doc-hien-thi.md) | backend B | 01 bước 1-3 (mã loại, model, migration) | 6 | Xong |
| 03 | [FE tab Kiêm nhiệm, đổi pháp nhân, trang công ty, sơ đồ, phạm vi](phase-03-fe-tab-hien-thi.md) | giao-dien-v2 | 01 bước 1 (`statuses.ts` sinh lại) + hợp đồng dưới | 6 | Xong |
| 04 | [Tài liệu, HDSD, cẩm nang, luật, RAG](phase-04-tai-lieu-hdsd-rag.md) | tai-lieu-kiem-thu | 01, 02, 03 xong | 3 | Xong |

Thứ tự: **01 (bước 1-3) → (01 còn lại ∥ 02 ∥ 03) → 04 → rà mã → cổng kiểm → commit một lượt**. Không deploy dev giữa chừng.

## Quyết định dữ liệu (chi tiết phase 01)
- Cột mới `kind` SMALLINT NOT NULL mặc định 1 trên `tab_employee_concurrent`, bộ mã `ConcurrentKind` (1 Phòng ban, 2 Công ty).
- Loại **Phòng ban**: `company_id` = công ty CHÍNH lúc ghi (lưu thật, không để 0) — giữ nguyên lọc cứng `company_id == công ty cũ`
  khi đổi pháp nhân, chỉ mục (phòng, công ty) của trang phòng ban, câu mô tả. Loại **Công ty**: `department_id = 0`.
- Migration MỚI `kn756a` chồng `kn755a` (không sửa `kn755a`). Dòng khác công ty chính → loại 2, bỏ phòng (mất phòng — chấp nhận,
  chỉ có trên DB local). Dòng phòng phụ cũ chép sang ở `kn755a` đều cùng công ty → loại 1, dev/prod không mất gì.

## Luật cốt lõi (áp mọi phase)
- Hồ sơ quyền: `dept_ids` = phòng chính + phòng loại 1 (hiệu lực + bật công tắc); khóa MỚI `concurrent_companies` = công ty loại 2
  (hiệu lực + bật, khác công ty chính). BỎ `concurrent_pairs`. `company_id` vẫn MỘT số. Vẫn MỘT truy vấn đọc dòng.
- Bậc `company` → `công ty IN (chính, *concurrent_companies)`; bậc `dept` → `công ty IN (...) AND phòng IN dept_ids`;
  `dept_proc` / `_narrow_to_dept` / handler ĐMH / `holds_handling_dept` vốn KHÔNG ràng công ty (bao-CR-434) nên không cộng gì;
  `own` (kể cả nhánh `own` rơi về `company` của entity không có cột chủ) và `all` giữ nguyên. Áp cho MỌI hành động (như Q6 cũ).
- Q1 đọc hồ sơ người kiêm nhiệm: dòng loại 1 ngồi ở (phòng dòng, công ty chính); dòng loại 2 ngồi ở (mỗi phòng của người đó, B).
- Q3 `subject_match`: cộng chủ thể CÔNG TY B; bỏ việc cộng phòng của cặp khác công ty.
- Q4 đổi pháp nhân A→C: dòng loại 1 (ở A) và dòng loại 2 trùng C đều kết thúc; hộp hỏi chỉ còn MỘT câu "giữ kiêm nhiệm ở công
  ty cũ A" → tạo một dòng loại 2 (A). Chức vụ kiêm nhiệm không cấp vai trò; báo cáo quân số không đếm trùng.
- L1 không tự sửa của mình. L2: dòng loại 1 → người gán phủ (phòng, công ty chính của hồ sơ); dòng loại 2 → người gán có grant
  `employee.write` bậc `all`, hoặc bậc `company` với B thuộc (công ty chính ∪ công ty kiêm nhiệm) của chính họ.

## Hợp đồng API (bản đủ ở phase 01 mục Architecture)
- `ConcurrentOut` + `kind` (1|2), `kind_label`; loại 2 có `department_id = 0`, `department_name = ""`.
- `POST /api/employees/{eid}/concurrents`: `kind` bắt buộc; loại 1 gửi `department_id`, KHÔNG gửi `company_id` (máy chủ điền);
  loại 2 gửi `company_id` (khác công ty chính), KHÔNG gửi `department_id`. `PATCH`: không đổi `kind` (422).
- `GET /api/employee-concurrents?department_id=&company_id=&kind=&include_ended=` — cần ít nhất một trong hai id; item + `kind`.
- `PATCH /api/employees/{id}`: bỏ `keep_concurrent_ids`; thêm `keep_old_company_concurrent: bool`.
- `/api/auth/me` `concurrents[]`, `/api/org-chart` `concurrents[]` + `kind`, `kind_label`.

## Rollback
Revert commit CR-756 (mã) rồi `alembic downgrade kn755a`: bỏ cột `kind` + chỉ mục; dòng loại 2 ở lại với `department_id = 0`
(mã CR-755 bỏ qua phòng 0 ở hồ sơ quyền nên không mở quyền nào); phòng đã bỏ không dựng lại được. Chưa lên dev/prod nên
rollback chỉ tác động DB local.

## Câu hỏi mở (mặc định đề xuất, làm theo mặc định nếu không ai chốt khác)
1. Hồ sơ chưa gắn pháp nhân chính khai kiêm nhiệm? → **chặn 400 cả hai loại** ("gắn pháp nhân chính trước").
2. `folder_access_service.company_reach` (tạo văn bản / thư mục cho công ty nào) có cộng công ty kiêm nhiệm? → **có**, cho grant
   bậc `company` / `dept` / `dept_proc`; `own` / `assigned` / `proc` không.
3. Bài diễn đàn đối tượng **Công ty** có hiện cho người kiêm nhiệm công ty B? → **không đổi** ở CR này (không nằm trong Q3).
4. Người gán có công ty kiêm nhiệm B (bậc company) gán tiếp loại 2 (B) cho người khác được? → **được** (B là công ty của họ).
5. Hộp **giữ ở công ty cũ** và tick **giữ phòng cũ** khi đổi cả pháp nhân lẫn phòng → **gộp thành một dòng loại 2 (A)**, qua L2.
