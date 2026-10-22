---
title: "D0 ghi nhận thao tác + D1 năng lực theo loại việc"
description: "Bấm chức năng, mở rộng form, báo cáo theo chức năng, nhóm chỉ số Dùng AI; thời gian trọn vòng, làm lại, task có loại việc/giờ/kết quả, tải đang ôm — số liệu cho AI chia việc"
status: pending
priority: P1
effort: 12.5d
branch: erp-v2
tags: [usage-profile, telemetry, capability, work, report, ai]
created: 2026-10-20
---

# D0 + D1 — ghi nhận thao tác & năng lực theo loại việc

Nguồn yêu cầu: lời đại ca 20/10 (D0 4–6 ngày, D1 1–1,5 tuần) + `doc/erp/tai-lieu-ai/22-ai-ke-hoach-phan-viec.md` §5, §7.
Nền: duoc-CR-641 (`usage_profile/`, `core/telemetry/`), CR-649/650 (Bộ chỉ số). CR số: lead cấp, chưa gán.

## Nguyên tắc chung
- R2: mọi mã mới = `SMALLINT` + `IntEnum` đăng ký `status_catalog`/`code_sets`, TS sinh bằng `gen_status_ts.py`.
- Không bao giờ lưu chữ người dùng gõ. Sự kiện chỉ mang mã số + route mẫu.
- API báo cáo: số truy vấn cố định, SQL gom, index gom một migration mỗi phase, test đếm truy vấn.
- Migration viết tay, nối từ **head tại thời điểm triển khai** (hiện `usgprof01`, CR-653 đang thêm migration chức vụ).
- Máy tính số, AI viết chữ: D1 cung cấp hàm dịch vụ; công cụ MCP/agent-gw là việc của Agent 4 (A1).

## Phases

| # | Phase | Ước | Phụ thuộc | Status |
|---|---|---|---|---|
| 01 | [D0a Sự kiện Bấm chức năng](phase-01-d0a-su-kien-bam-chuc-nang.md) | 1,5d | — | implemented (CR-654) |
| 02 | [D0b Mở rộng theo dõi form (7 form)](phase-02-d0b-mo-rong-theo-doi-form.md) | 1d | 01 (cùng tệp mã) | implemented (CR-654) |
| 03 | [D0c Báo cáo theo chức năng (ReportKey 15)](phase-03-d0c-bao-cao-theo-chuc-nang.md) | 1,5d | 01, 02, CR-651 đã gộp | implemented (CR-655) |
| 04 | [D0d Nhóm chỉ số 3.8 Dùng AI](phase-04-d0d-nhom-chi-so-dung-ai.md) | 1d + 0,5d sau A0 | A0 (Agent 4), CR-651 | implemented (CR-655) |
| 05 | [D1b Task Dự án: loại việc, giờ, kết quả](phase-05-d1b-task-loai-viec-gio-ket-qua.md) | 2d | — (song song D0) | implemented (CR-656) |
| 06 | [D1a Thời gian trọn vòng + làm lại](phase-06-d1a-thoi-gian-tron-vong-lam-lai.md) | 2,5d | 05 | implemented (CR-656) |
| 07 | [D1c Tải đang ôm tính tức thì](phase-07-d1c-tai-dang-om-tuc-thi.md) | 1d | 05, 06 (index) | implemented (CR-656) |
| 08 | [D1d Báo cáo năng lực (ReportKey 16) + hợp đồng cho AI](phase-08-d1d-bao-cao-nang-luc-hop-dong-ai.md) | 1,5d | 06, 07 | implemented (CR-657) |

Tổng: D0 ≈ 5–5,5d · D1 ≈ 7d. Hai luồng D0 (01→02→03→04) và D1 (05→06→07→08) chạy song song được.

## Luồng dữ liệu (tóm)
```
FE bấm nút ─trackUiAction(code)─► telemetry queue ─► POST /api/telemetry/ui-events ─► tab_ui_event(action_key)
tab_ui_event + tab_request_log ─(celery 04:45)─► tab_feature_usage_daily ─► /api/feature-usage/summary (RK15)
A0: agent_hub ─cổng B─► tab_ai_usage_daily ┐
tab_assistant_change (đã có) ──────────────┴─► snapshot tuần (3.8) ─► Hồ sơ cách làm việc (RK14)
tab_change_log/audit/approval/work_task ─(celery 05:00, gia tăng)─► tab_work_cycle ─► capability_service
bảng nguồn sống (approval_task, work_task, PR/PO, delegation, leave) ─► workload_service (tức thì)
capability_service + workload_service ─► /api/work-capability/* (RK16) + hàm cho A1 (Agent 4)
```

## Tệp nóng dùng chung (chỉ một phase sửa tại một thời điểm; phase sau rebase + sinh lại)
`core/report_keys.py` (03, 08) · `core/code_sets.py` · `shared/constants/statuses.ts` (sinh) · `core/all_models.py` ·
`app/main.py` · `core/celery_app.py` · `report-catalog-system.ts` · `modules/report/routes.tsx` · `app-routes.ts` · nav báo cáo.

## Vùng đang có agent khác — KHÔNG sửa cho tới khi họ gộp
- CR-651 (biểu đồ): `backend/app/modules/usage_profile/metric_*`, `frontend-v2/src/modules/report/**` → phase 03, 04 chờ.
- CR-652 (/me + labor_contract): không giao.
- CR-653 (job_position + role grants + migration): chỉ ảnh hưởng head migration.

## Rollback
Mỗi phase có migration `downgrade` riêng + cờ `usage_tracking_enabled` (D0) — tắt cờ là dừng thu; bảng mới không có FK
từ bảng nghiệp vụ nên gỡ không lan. Cột mới trên `tab_work_task` đều nullable/có mặc định.

## Câu hỏi mở
Xem [open-questions.md](open-questions.md) — 14 câu, mỗi câu có mặc định đề xuất; plan đi theo mặc định.
