# Phase B duoc-CR-715 (Ngay cam nghi) — report
Migration lvblk715 (down lvacc715, hand-written idempotent, applied local). Head = lvblk715.

Backend new: leave/block_period_service.py, migrations/versions/lvblk715_*.py, test/backend/test_nghi_phep_ngay_cam_cr715.py (16 tests).
Backend edited: leave/catalog_model.py (LeaveBlockPeriod), leave/schema.py (Create/Update/Response + check_block_range), leave/catalog_controller.py (block_period_router, entity leave_type), leave/approval_bridge.py (_on_approved gate), leave/request_controller.py (_dump + estimate-days + estimate-periods -> block_conflicts), approval/entity_hooks.py (HookVeto), main.py, core/app_settings.py, core/config.py, setting/service.py (leave_block_exempt_roles).
Frontend new: config/leave-block-crud.tsx, pages/leave-block-{list,detail}-page.tsx, components/leave-block-warning-banner(+test).tsx, utils/leave-block-conflicts.ts.
Frontend edited: app-routes.ts, types/leave.ts, api/leave-api.ts, hooks/use-leave.ts, leave-section-tabs(+test), leave-request-form.tsx, leave-request-detail-page.tsx, routes.tsx, hr-settings-leave-shortcuts.tsx, app/router/module-visibility.test.ts.
Help: seed_help_nghi_phep.py + seed_help_nhan_su.py edited and reseeded (reindex_help_rag NOT run).

Gates: pytest -k filter 766 passed; tsc 0 errors; eslint src/modules/hr 0 errors (2 pre-existing warnings); vitest src/modules/hr + src/app/router 129 files / 1531 passed.

Deviations:
1. entity_hooks.fire SWALLOWS hook exceptions (writes finish_reason, instance still "approved", leave stuck Cho duyet). A plain 422 in _on_approved would not abort the engine path. Added HookVeto(HTTPException) in approval/entity_hooks.py; fire re-raises it, so action_service.approve aborts before commit and get_db rolls back. Test proves instance RUNNING, leave PENDING, balance pending kept, nothing consumed. Gate runs BEFORE consume_lines.
2. Single-period form uses GET /tools/estimate-days, not estimate-periods -> added block_conflicts to BOTH endpoints (+ hook typings).
3. Hidden nav item "Ngay cam nghi" (entity leave_type, manage) added so the routes are gated (nav gating fails open).
4. Extra: shortcut link on HR Settings leave tab; existing leave-section-tabs test "one tab" now uses holiday.write because leave_type.write yields 2 tabs.
5. Detail/create/update serializer: block_conflicts computed in request_controller._dump (single-order path), skipped for rejected/cancelled. List path untouched (no N+1).
6. Extra validation: year range 2000-2100 on block dates (input-limits rule).

Open questions: none blocking. HR Settings field renders via generic backend FIELDS (type roles) — verified by code path + existing form test, not by browser.

Status: DONE
