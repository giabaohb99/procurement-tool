# Phase C2 (frontend) duoc-CR-715 — Phiếu xin nghỉ bù — report

Built strictly on `phase-c1-backend.md`. No backend / doc / rules / change-log / nhat-ky touched. Not committed.

## Files

New (frontend-v2/src/modules/hr):
- types/leave-comp.ts (+ .test.ts) — status enum/labels, `LeaveCompRequest`, `getLeaveCompActions` (pure: which buttons by status + approval_instance_id + perms)
- api/leave-comp-api.ts — list, to-approve, get, create, update, remove, submit, approve, reject, cancel
- hooks/use-leave-comp.ts — queries + `useSaveLeaveCompRequest`, `useDeleteLeaveCompRequest`, `useLeaveCompAction`; every mutation invalidates `queryKeys.hr.all` (covers leave-balances) + `approval.all`
- utils/leave-comp-form-values.ts (+ .test.ts), utils/format-comp-days.ts (+ .test.ts)
- components/leave-comp-request-form.tsx (+ .test.tsx), leave-comp-request-summary.tsx, leave-comp-approval-timeline.tsx, leave-comp-decision-actions.tsx
- pages/leave-comp-request-list-page.tsx, pages/leave-comp-request-detail-page.tsx (new + detail)

Edited (surgical): shared/constants/app-routes.ts (`hr.leaveCompRequests/New/Detail`), shared/constants/query-keys.ts (3 keys), modules/hr/routes.tsx (nav child «Nghỉ bù» + group `entities` + `matchPaths` + 3 lazy routes), modules/hr/types/leave.ts (`LeaveBalance.comp_days?`, `LeaveType.is_compensatory?`), modules/hr/config/leave-type-crud.tsx (switch «Loại nhận ngày nghỉ bù», showWhen counts_balance, hint), modules/hr/utils/group-leave-balances.ts (+test: comp_days in totals), components/leave-balance-columns.tsx (+test count 6 → 7): column «Nghỉ bù cộng thêm» (defaultHidden), components/leave-balance-breakdown-card.tsx (Stat shown when comp_days != 0), core/authorization/permission-types.ts (+`leave_comp_request`), modules/system/config/permission-groups.ts (entity added to «Nghỉ phép» group so admin can tick it on Phân quyền), modules/approval/helpers/entity-link.ts (label «Phiếu nghỉ bù» + detail route; label list feeds `CAC_LOAI` = flow-designer / switch list), modules/approval/hooks/use-approvals.ts (invalidate `hr.all` after sign).

## Gates (host, frontend-v2)
- `npm run typecheck`: 0 errors
- `npx eslint src/modules/hr src/modules/approval src/shared/constants`: 0 errors, 1 warning (pre-existing `unified-room-booking-table.tsx`)
- `npx vitest run src/modules/hr src/app src/modules/approval`: 176 files / 1841 tests passed. (Also ran `src/modules/system` earlier: green.)
- New tests: 40ish across 5 files — status/action-availability, form validation (past/today/future, days 0/0.25/1.5/NaN, reason whitespace/1000/1001), form component with `@/core/api` mocked: validation blocks with no request; double-click «Gửi duyệt» = 1 PATCH + 1 submit; submit failure after save still calls `onSaved` (so retry does not re-create → no 409); «Lưu nháp» never submits; create path posts employee_id 0.

## Browser verification
NOT done. No chrome-devtools tools available to me. Done instead: dev server serves the new modules (HTTP 200), typecheck/lint/tests green. API smoke as `admin` returned 403 `Không có quyền: create leave_comp_request` — expected D-018 (existing roles don't get the new entity until `SEED_FORCE_SYNC=true` once or tick on Phân quyền → Nghỉ phép › Phiếu nghỉ bù). I did not alter local permissions. Also on local: no leave type has `is_compensatory` on (type 1 «Phép năm» counts_balance=true) — need to turn the new switch on for «Phép năm» before creating a phiếu (else 422 no comp type). Manual E2E (draft past Sunday 01/11/2026 → submit → direct approve → balance «Nghỉ bù cộng thêm») still to run by a human after those two steps.

## Deviations / decisions
1. List uses a «Phạm vi» Select (Của tôi · Cần tôi duyệt · Tất cả trong phạm vi) + status select + search, mirroring the Đơn nghỉ phép list approach, not literal tabs. «Của tôi» filters `employee_id=<user.employee_id>` (not run when account has no employee). «Cần tôi duyệt» is client-filtered, unpaginated (matches backend).
2. «Ngày đi làm max today»: shared `DatePicker` has no max prop (not in my scope to change) → client validation message + backend 422 as the hard gate.
3. Engine decision buttons (Duyệt/Trả về/Từ chối through approval instance) use new `LeaveCompDecisionActions` over `/to-approve`, reusing the generic `useLeaveApprovalDecision` hook; the existing leave components are tied to `LeaveInboxRow`.
4. Status badge reuses `LeaveStatusBadge` (same 1..6 codes, same tones); a test pins `LEAVE_COMP_STATUS` equal to `LEAVE_STATUS`.
5. Two submit variants avoided: only the form's «Gửi duyệt» (save then submit) exists; no header-level submit.
6. No in-app print / attachments for phiếu (not in spec).
7. `src/app/layouts/module-layout.tsx` shows modified in git status — not mine (pre-existing working-tree change).

## Open questions
- Backend help RAG reindex / HDSD for the new screen (menu path «Nhân sự › Nghỉ phép › Nghỉ bù») left to docs/help owner.
- Flow-designer: only the shared label list was found (entity-link `ENTITY_LABELS`); I did not see a separate designer entity list — verify in UI that «Phiếu nghỉ bù» appears in «Bật bộ máy duyệt» once browser is available.
- `LeaveType.is_compensatory` / `LeaveBalance.comp_days` typed optional so older fixtures keep compiling; make required if you prefer.

**Status:** DONE_WITH_CONCERNS (browser E2E not run: no browser tool; local perms/flag need enabling first)
