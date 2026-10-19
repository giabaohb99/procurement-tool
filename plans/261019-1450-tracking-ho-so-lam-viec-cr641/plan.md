---
title: "duoc-CR-641 — Hồ sơ cách làm việc của từng người (tracking pha 1–3)"
description: "Gom ngày từ nhật ký sẵn có + thu sự kiện giao diện + nhãn kiểu làm việc theo tuần; chỉ admin xem qua ReportKey 14."
status: pending
priority: P2
effort: 44.5h
branch: erp-v2
tags: [tracking, usage-profile, report-access, celery, telemetry, backend, frontend-v2, privacy]
created: 2026-10-19
---

# duoc-CR-641 — Hồ sơ cách làm việc (pha 1, 2, 3 của duoc-CR-626)

Thiết kế gốc: `doc/tai-lieu-ky-thuat/tracking-nguoi-dung-ho-so-ca-nhan.md` (§2–6, 8, 9).
Nhật ký nguồn: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md`. Pha 4 (AI đọc hồ sơ) NGOÀI phạm vi,
nhưng snapshot dựng đúng khuôn §7 để cắm vào sau (phase 04).
Bảng định nghĩa chỉ số: [`metric-definitions.md`](metric-definitions.md).
Change-log: ĐẶT CHỖ `duoc-CR-641-tracking-ho-so-lam-viec` — chỉ ghi khi bắt tay làm (phase 08), plan này không sửa change-log.

## Chốt của chủ sản phẩm (không bàn lại)

Chỉ admin xem · không mở cho chính người đó / quản lý · không lưu từ khóa tìm kiếm · ngoài giờ theo Lịch làm việc
(+ lễ, trừ ngày nghỉ phép đã duyệt) · không lưu body, route không chứa id · sự kiện thô 90 ngày, số gom giữ lâu ·
so với người cùng vai trò, nhóm < 5 thì so pháp nhân · có công tắc bật/tắt thu thập.

## Luồng dữ liệu

```
FE v2 (core/telemetry) ──POST /api/telemetry/ui-events (lô ≤100, fetch keepalive, KHÔNG vào request_log)──► tab_ui_event (90 ngày)
tab_request_log · tab_login_session · tab_audit_log · tab_export_log · tab_ui_event
   + Lịch làm việc (resolver_many) + ngày lễ + đơn nghỉ đã duyệt
   └─ Celery 04:30 «usage.aggregate_daily» (hôm qua, ~14 truy vấn cố định) ─► tab_usage_daily (người × ngày, giữ lâu)
tab_usage_daily + audit/approval/notification/comment/… (cửa sổ 4 tuần)
   └─ Celery T2 05:15 «usage.build_weekly_snapshots» ─► tab_user_usage_snapshot (JSON số + mã, schema v1)
                                                     └► tab_user_usage_label (nhãn §4, có bằng chứng)
Admin ── /report/usage-profiles (+ /:userId) ── GET /api/usage-profiles/summary|/summary/export|/{user_id}|/cohorts
        gác KÉP: require("setting","read") + require_report(ReportKey.USAGE_PROFILE=14)
Celery 04:20 «usage.cleanup_ui_events» xóa lô 2.000 dòng > 90 ngày
```

## Các phase

| # | Phase | Effort | Phụ thuộc | Trạng thái |
|---|---|---|---|---|
| 01 | [Nền dữ liệu: model, mã số, migration, công tắc](phase-01-nen-du-lieu-migration-ma-so.md) | 3h | — | pending |
| 02 | [Gom ngày từ bảng sẵn có + sự kiện UI, backfill](phase-02-gom-ngay-tu-bang-san-co.md) | 7h | 01 | pending |
| 03 | [Thu sự kiện giao diện (backend), read_at, dọn 90 ngày](phase-03-thu-su-kien-giao-dien-backend.md) | 4h | 01 | pending |
| 04 | [Snapshot tuần + nhóm so sánh + nhận kiểu, đăng ký Celery](phase-04-snapshot-tuan-nhom-so-sanh-nhan-kieu.md) | 8h | 02, 03 | pending |
| 05 | [API đọc hồ sơ + ReportKey 14 + gác quyền](phase-05-api-doc-ho-so-gac-quyen.md) | 5h | 04 | pending |
| 06 | [FE bộ thu sự kiện (core/telemetry) + móc form/tìm kiếm](phase-06-fe-bo-thu-su-kien.md) | 6h | 03 (hợp đồng API) | pending |
| 07 | [FE màn admin: danh sách + hồ sơ từng người](phase-07-fe-man-ho-so-admin.md) | 9h | 05 | pending |
| 08 | [Tài liệu, thông báo nhân viên, triển khai, bật công tắc](phase-08-tai-lieu-trien-khai.md) | 2.5h | 01–07 | pending |

Song song được: 02 ∥ 03 ∥ 06 (khác tệp). ⚠️ 05 và 07 phải vào CÙNG một PR: thêm `ReportKey` 14 ở 05 làm đỏ
`report-catalog.test.ts` (FE) cho tới khi 07 khai mục danh mục.

## Sở hữu tệp chung (tránh đụng nhau)

`core/celery_app.py` → 04 · `main.py` → 03 (router telemetry) rồi 05 (router hồ sơ), tuần tự ·
`core/logging_policy.py`, `notification/controller.py`, `auth/controller.py` → 03 · `core/app_settings.py`,
`setting/service.py`, `core/code_sets.py`, `core/all_models.py` → 01 · `core/report_keys.py` → 05 ·
`frontend-v2/src/shared/constants/statuses.ts` (sinh tự động) → 01 rồi 05 · `report/config/*`, `report/routes.tsx`,
`app-routes.ts`, `query-keys.ts` → 07 · `core/telemetry/*`, `protected-route.tsx`, 6 trang form, 6 trang danh sách → 06.

## Tiêu chí xong (đo được)

1. Tắt công tắc: 0 dòng `tab_ui_event` sau 1 giờ dùng; bật: có PAGE_VIEW/PAGE_LEAVE trong ≤ 60 s, **0** dòng `tab_request_log` route `/api/telemetry%`.
2. `usage.aggregate_daily` 1 ngày prod-size (~10k dòng request_log) < 10 s; số truy vấn KHÔNG đổi theo số người (test).
3. `/summary` danh sách ≤ 5 truy vấn, hồ sơ 1 người ≤ 7 truy vấn, cố định (test 2 vs 15 người / 4 vs 12 tuần).
4. Người không phải admin: 403 ở cả 4 đường; menu không hiện; gõ thẳng `/report/usage-profiles/5` ra trang 403.
5. Snapshot chỉ chứa số/mã (test duyệt JSON: không chuỗi tự do ngoài khóa), có `schema_version`, `unmeasured`, ngữ cảnh nghỉ phép/bấm hộ.
6. Không bảng nào chứa từ khóa tìm kiếm, id trong route, body form (test + rà tay).

## Rollback

Tắt công tắc `usage_tracking_enabled` (tức thì, FE ngừng gửi, BE bỏ lô). Gỡ hẳn: revert PR + `alembic downgrade` migration
`usgprof01` (drop 4 bảng + cột `read_at` + 4 chỉ mục; không đụng dữ liệu nghiệp vụ). Dòng `tab_report_access` khóa 14
để nguyên vô hại (khóa không tái dùng).

## Câu hỏi còn mở → xem cuối `phase-08`.
