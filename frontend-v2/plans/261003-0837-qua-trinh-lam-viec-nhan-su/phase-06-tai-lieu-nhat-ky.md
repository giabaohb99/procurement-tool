# Phase 06 — Tài liệu, luật, nhật ký task

**Ưu tiên:** P2 · **Effort:** 1h · **Trạng thái:** completed · **Phụ thuộc:** 03, 05

## Việc
1. **Số CR:** lấy số kế tiếp trong `doc/tai-lieu-ky-thuat/change-log.md` (`git fetch` trước — nhiều người cùng cấp số), dạng `duoc-CR-xxx`. Ghi một dòng change-log.
2. `doc/erp/hrm/01-ho-so-nhan-su.md`:
   - Bảng đầu: bản 1.5 — 03/10/2026.
   - §5.1 C3: tab thứ 6 «Quá trình công tác» (thay chữ «Sau này thêm … Lịch sử điều chuyển»).
   - §4 dòng kiêm nhiệm: «Phiếu V1-8 chưa làm; bản gọn (ghi tay theo người) đã có — §7.11».
   - **§7.11 mới**: bảng `tab_employee_work_history` (từ ngày = ngày hiệu lực), bộ mã 7 loại, bảng «loại nào áp gì», bốn chốt áp hồ sơ, chức danh kiêm nhiệm chỉ sống ở lịch sử, **Thôi việc áp qua đúng `update_employee` → khóa TK + thu hồi phiên, `resign_date` lấy từ dòng, ngày tương lai thì bấm Áp khi tới ngày**, quyền (không entity mới + chặn tự sửa trừ quản trị + ngoại lệ /me + **tệp người khác đòi `employee_sensitive.read`**), đường nâng V1-8 (`decision_id`).
   - §5.2 bảng phân quyền: dòng `employee_sensitive.read` thêm «tệp quyết định trong Quá trình công tác của người khác».
   - §7.10 «Còn treo»: không thêm dòng (4 câu đã chốt 03/10/2026).
3. `doc/erp/tham-khao-hrm/10-de-xuat-ap-dung.md` §0: V1-8 → **«Bản gọn đã làm»** — «lịch sử công tác theo người, HR ghi tay, tệp QĐ, hỏi rồi áp hồ sơ (duoc-CR-xxx). Còn: phiếu nhiều người, tờ trình, duyệt, “Thay thế cho”».
4. `.claude/rules/hr-employee-profile.md`: thêm mục ngắn «Quá trình công tác» — 4 bẫy: (a) áp hồ sơ chỉ đi `update_employee`/`set_extra_departments`, cấm ghi thẳng cột — kể cả Thôi việc, gọi thẳng `lock_linked_users` là lệch đường tab «Chung»; (d) tệp QĐ của người khác gác thêm `employee_sensitive.read` ở `work_history_access.check_file`, `file_count` vẫn lộ ra (chỉ số đếm) — cố ý; (b) `position_label` của lịch sử là nhãn CHỤP, cố ý không `propagate_rename` — không tính là đường ghi thứ ba vào `tab_employee.position`; (c) hộp thoại có `<form>` trong trang hồ sơ phải `stopPropagation` (portal vẫn nổi bọt). Thêm `test/backend/*qua_trinh*` vào `paths:`.
5. `doc/tai-lieu-ky-thuat/nhat-ky-task.md`: một mục, **câu tiếng Việt trọn vẹn**, việc trước — tên tệp/commit dồn xuống dòng `Mã nguồn:` / `Commit:` cuối; `- pic:` mặc định NSU209.
6. `frontend-v2/docs/` không đổi (không thêm primitive dùng chung).

## Todo
- [x] change-log + số CR (duoc-CR-585)
- [x] 01-ho-so-nhan-su.md (bản 1.5, C3, §4, §7.11, §5.2, §7.10)
- [x] 10-de-xuat-ap-dung.md §0
- [x] rule hr-employee-profile.md + paths
- [x] nhật ký task

## Thành công khi
Người đọc `01-ho-so-nhan-su.md` §7.11 trả lời được: dòng nào áp được, áp đi qua hàm nào, ai xem được tệp, nâng V1-8 thêm gì.

## Rủi ro tổng (cả plan)
| Rủi ro | K × A | Giảm thiểu |
|---|---|---|
| Áp hồ sơ sai người/sai phòng → đổi phạm vi dữ liệu người đó | Thấp × Cao | Tái dùng L1/L2/L3; hỏi trước khi áp; audit |
| Áp Thôi việc nhầm → khóa TK ngay | Thấp × Cao | Hộp xác nhận riêng nói rõ hệ quả; mở lại TK ở tab Tài khoản |
| Tệp QĐ lộ (có thể ghi lương) | Thấp × Cao | Riêng tư + vai trò + phạm vi + `employee_sensitive.read` + test |
| Deploy: bảng mới trên DB dùng chung v1/v2 | Thấp × Thấp | Chỉ thêm bảng; `frontend/` v1 không đọc |
| Nhiều người cùng sửa `query-keys.ts`, `main.py`, `file_registry.py` | TB × Thấp | `git fetch` trước push; sửa vài dòng, xung đột dễ gỡ |

## Kết quả
**Status:** DONE · **Hoàn tất:** 03/10/2026 · **Tài liệu:** 5 tệp cập nhật / mới

Triển khai phase 06 hoàn tất: change-log + duoc-CR-585, bản 01-ho-so-nhan-su.md nâng lên 1.5 (thêm §7.11, cập nhật §4/§5.2/§7.10), 10-de-xuat-ap-dung.md cập nhật V1-8 trạng thái, thêm mục Quá trình công tác vào rule hr-employee-profile.md, ghi nhật ký task. Các phase 01–05 (code) đã hoàn tất từ 03/10 chiều.
