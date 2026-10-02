---
title: "Phân quyền xem TỪNG báo cáo (phân hệ Báo cáo)"
description: "Gác kép: quyền phân hệ gốc + được gán báo cáo; chưa gán = đóng; cấu hình ở tab Báo cáo của Phân quyền tài khoản."
status: pending
priority: P2
effort: 18h
branch: erp-v2
tags: [report, rbac, permission, backend, frontend-v2]
created: 2026-10-02
---

# Phân quyền xem từng báo cáo

**Đính chính số liệu:** danh mục có **13 báo cáo** (Thu mua 5 · Nhân sự 3 · Hành chính 2 · Văn bản 2 · Công việc 1), entity `report` dùng cho 2 báo cáo → **26 đường** `/summary` + `/summary/export`, không phải 12/24.

## Quyết định thiết kế chính
- Khóa báo cáo = **`SMALLINT` + `IntEnum ReportKey`** (luật R2/QĐ-11), khai DUY NHẤT ở `backend/app/core/report_keys.py` (thuần stdlib), đăng ký bộ mã `report_key` → `gen_status_ts.py` sinh `REPORT_KEY` vào `statuses.ts`; test FE bắt khóa catalog khớp 1-1.
- Bảng `tab_report_access` cùng hình dạng `tab_doc_folder_access` → dùng lại `core/subject_match.py` (4 chủ thể, CẤM thắng, thu hồi = `revoked_at`).
- Gác backend: `dependencies=[Depends(require_report(ReportKey.X))]` trên decorator — KHÔNG đụng `require(entity, …)`/`apply_scope` có sẵn → gác kép, gán không mở rộng dữ liệu.
- FE nhận khóa được xem qua trường **`report_keys` trong `/api/auth/me`** (cùng lối `is_driver` → `useNavContext`), thay cho `GET /api/report-access/me` — lý do ở phase 02.
- Không thêm entity mới: cấu hình gác `role.read`/`role.write`.
- Mặc định admin: migration chèn 13 dòng CHO PHÉP cho vai trò `admin`; seed `ensure_report_access_defaults` (seed + seed_prod) chỉ chèn cho khóa **chưa từng có dòng nào** (kể cả dòng đã thu hồi) → báo cáo mới tự có admin, không ghi đè chỉnh sửa.
- Đã kiểm: KHÔNG trang phân hệ gốc nào (v1 `frontend/` lẫn v2 ngoài `modules/report`) gọi 26 đường này → gác không làm vỡ trang gốc.

## Phase

| # | Phase | Effort | Phụ thuộc | Trạng thái |
|---|---|---|---|---|
| 01 | [Backend nền: khóa, bảng, migration, seed, sinh TS](phase-01-backend-report-key-model-migration-seed.md) | 3h | — | done |
| 02 | [Backend gác 26 đường + `/auth/me` + API cấu hình](phase-02-backend-guard-and-config-api.md) | 3h | 01 | done |
| 03 | [Backend test mới + sửa test HTTP cũ](phase-03-backend-tests.md) | 3h | 02 | done |
| 04 | [FE nâng ô chọn chủ thể lên `src/shared/`](phase-04-frontend-lift-subject-picker-to-shared.md) | 2h | — (song song 01-03) | done |
| 05 | [FE gác menu/route/Tổng quan theo `report_keys`](phase-05-frontend-report-gating.md) | 2.5h | 01 (statuses.ts), hợp đồng 02 | pending |
| 06 | [FE tab «Báo cáo» ở Phân quyền tài khoản](phase-06-frontend-report-access-tab.md) | 3h | 02, 04 | done |
| 07 | [Tài liệu, nhật ký task, deploy](phase-07-docs-journal-deploy.md) | 1.5h | 01-06 | done |

## Đồ thị phụ thuộc
```
01 ─► 02 ─► 03 ─┐
 │     └──────► 06 ─► 07
 └──► 05 ──────────►┘
04 ───────────► 06
```
Song song được: {04} với {01→02→03}; {05} sau 01. Sở hữu tệp: mỗi phase liệt kê tệp riêng, không phase song song nào chạm cùng tệp (xem từng phase).

## Ma trận test (chạy THEO THƯ MỤC/TỆP, không quét cả cây)
- Backend: `test_phan_quyen_bao_cao_*.py` (mới) + `test_bao_cao_*.py` + `test_pham_vi_luat_bat_bien.py` + test thư mục văn bản (vì nâng `subject_names`) + `test_status_catalog_b01.py`.
- FE: `typecheck` + `lint` cả cây; `vitest run src/modules/report src/app/router src/core/authorization src/modules/system src/modules/document src/shared/access-subject`.
- Thủ công: đăng nhập admin / tài khoản thường trên local (:8083) — menu, gõ URL, Tổng quan, xuất Excel, cấp/cấm/thu hồi.

## Rủi ro hàng đầu
- **Prod sau deploy chỉ admin thấy báo cáo** (đúng chốt «chưa gán = đóng») → đại ca chuẩn bị danh sách gán TRƯỚC, gán ngay sau deploy (phase 07).
- Test HTTP cũ của 26 đường sẽ ăn 403 → phase 03 thêm fixture gán.
- `auth/me` lưu cũ ở trình duyệt thiếu `report_keys` → đóng (an toàn) tới khi nạp lại.

## Rollback
Revert commit FE + BE là đủ trở về hành vi cũ (gác nằm hết trong code). Bảng `tab_report_access` để nguyên (vô hại, giữ cấu hình); chỉ `alembic downgrade -1` khi cần dọn hẳn.

## Câu hỏi còn treo
Xem cuối [phase-07](phase-07-docs-journal-deploy.md#câu-hỏi-còn-treo).
