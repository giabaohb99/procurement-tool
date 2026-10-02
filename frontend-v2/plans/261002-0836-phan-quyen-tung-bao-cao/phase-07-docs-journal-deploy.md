# Phase 07 — Tài liệu, nhật ký task, deploy

**Ưu tiên:** P2 · **Effort:** 1.5h · **Trạng thái:** done · **Phụ thuộc:** 01-06

## Context
- `doc/phan-quyen/Thiet_Ke_Phan_Quyen.md`, `doc/tai-lieu-ky-thuat/change-log.md`, `doc/tai-lieu-ky-thuat/nhat-ky-task.md` (đọc luật viết mô tả ở đầu tệp), `doc/tai-lieu-ky-thuat/quy-trinh-nhanh-va-deploy.md`
- `CLAUDE.md` mục «Two-axis permission system»

## Việc
1. `Thiet_Ke_Phan_Quyen.md`: mục mới «Lớp gác thứ ba: quyền xem từng báo cáo» — gác kép, chưa gán = đóng, 4 chủ thể, cấm thắng, thu hồi đánh dấu, mặc định admin + luật seed không ghi đè, khóa số bất biến.
2. `change-log.md`: một dòng quyết định (D-xxx) — khóa `SMALLINT` theo R2, `report_keys` đi qua `/auth/me`, báo cáo mới phải thêm `ReportKey` + `key` catalog + `require_report` ở 2 đường.
3. `CLAUDE.md`: 1–2 câu dưới mục phân quyền trỏ tới tài liệu trên (luật «thêm báo cáo mới» — để người sau không quên gác).
4. `nhat-ky-task.md`: một mục, câu tiếng Việt trọn vẹn, việc trước tên tệp sau; dòng cuối `Mã nguồn:` / `Commit:`; `- pic: NSU209`.
5. Commit tách theo phase (conventional, không nhắc AI): `feat(bao-cao): …` BE nền / BE gác / FE picker (refactor) / FE gác / FE tab; `docs: …`.

## Kế hoạch deploy
- Trước deploy: chạy `npm run check` (full — đúng luật «chỉ trước deploy») + bộ backend của phase 03; `gen_status_ts --check`.
- Đại ca chốt **danh sách gán** (báo cáo → phòng/vai trò) TRƯỚC giờ deploy.
- Dev/UAT trước, rồi prod (`-f docker-compose.production.yml`, theo `quy-trinh-nhanh-va-deploy.md`); merge `erp-v2` → `main` theo §A.2 nếu đi chiều ngược.
- Sau deploy, kiểm: `SELECT COUNT(*) FROM tab_report_access` = 13 (dòng admin); `alembic_version` lên head mới; admin đăng nhập lại thấy 13 báo cáo.
- **Thông báo nội bộ:** «Từ hôm nay báo cáo phải được giao mới xem được; chỉ Quản trị hệ thống thấy sẵn. Ai cần, báo admin gán. Đăng xuất/đăng nhập lại nếu chưa thấy.»
- Đại ca gán ngay trên tab «Báo cáo» (prod) theo danh sách đã chốt.
- `thumua.degoholding.vn` (v1) không gọi 26 đường này → không ảnh hưởng (đã grep).

## Rollback
| Mức | Cách | Hệ quả |
|---|---|---|
| Nhanh | Revert commit BE gác (phase 02) + FE gác (05), deploy lại | Báo cáo mở lại như cũ theo entity; bảng + cấu hình giữ nguyên để bật lại |
| Toàn bộ | Revert mọi commit + `alembic downgrade -1` | Mất cấu hình gán (cân nhắc sao lưu bảng trước) |
Phase 04 (nâng picker) revert độc lập được.

## Todo
- [x] 3 tài liệu + CLAUDE.md (Thiet_Ke_Phan_Quyen.md §4b + change-log.md CR-555 + CLAUDE.md)
- [x] nhật ký task (duoc-CR-555 ở nhat-ky-task.md)
- [ ] danh sách gán được chốt (đại ca chốt trước deploy)
- [ ] deploy dev → prod + thông báo (không thực hiện ở phase này)

## Deploy notes — rủi ro & mitigations
- **Prod sau deploy chỉ admin thấy 13 báo cáo** (đúng chốt "chưa gán = đóng"). **Mitigations:** đại ca chuẩn bị danh sách gán (báo cáo → phòng/vai trò/người) TRƯỚC giờ deploy; gán ngay sau deploy trên tab Báo cáo bằng giao diện (không tự động, admin gán tay).
- **Cache `report_keys` chỉ được nạp lúc đăng nhập.** Người dùng đã đăng nhập trước deploy sẽ **không nhận** `report_keys` (vẫn thấy 403). **Mitigation:** thông báo nội bộ yêu cầu đăng xuất/đăng nhập lại sau deploy, hoặc admin chủ động kiểm tra.
- **Backend migration tạo 13 dòng admin; seed `ensure_report_access_defaults` không ghi đè.** Nếu seed chạy 2 lần thì idempotent (kiểm qua: `git stash` trước khi chạy migration, nếu migration + seed sạch thì ổn). **Kiểm sau deploy:** `SELECT COUNT(*) FROM tab_report_access` phải = 13 (chỉ admin).
- **`alembic_version` lên migration mới** (`rptacc01_phan_quyen_tung_bao_cao`). Kiểm `HEAD` đúng không trước deploy prod.

## Tiêu chí xong
Tài liệu có luật «thêm báo cáo mới»; nhật ký đồng bộ được lên phân hệ Dự án; prod: admin thấy 13, người được gán thấy đúng phần mình.

## Câu hỏi còn treo
1. Đồng ý thay `GET /api/report-access/me` bằng trường `report_keys` trong `/api/auth/me` không (lý do ở phase 02)? Nếu vẫn cần đường riêng thì thêm 5 dòng, gọi lại `viewable_keys`.
2. Có cần MỞ ngày hiệu lực (`valid_from/valid_to`) trên giao diện ngay không? Plan giữ cột (để dùng lại `still_live_condition`) nhưng UI chưa hiện.
3. Seed LOCAL (`seed.py`, có tài khoản demo) có gán thêm báo cáo cho vai trò demo (TESTREQ, DEMO_MANAGER_PURCHASE…) để e2e/kiểm tay đỡ phải gán không, hay giữ giống prod (chỉ admin)?
4. Danh sách gán ban đầu trên prod (báo cáo nào → phòng/vai trò nào) — đại ca chốt trước deploy.
5. Có cần chặn người giữ `role.write` (không phải admin) tự gán báo cáo cho chính mình/vai trò mình như luật L1 của ma trận quyền không? Plan KHÔNG chặn vì gác kép không mở rộng dữ liệu.
6. Có muốn hiện cả lịch sử dòng đã thu hồi trong hộp thoại không? Plan chỉ hiện dòng còn hiệu lực (lịch sử vẫn ở DB + nhật ký thao tác).
