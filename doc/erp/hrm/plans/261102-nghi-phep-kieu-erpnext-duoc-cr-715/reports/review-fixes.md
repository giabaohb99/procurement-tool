# CR-715 review fixes

Migration: `lvcmp716` (down `lvcmp715`), file `backend/migrations/versions/lvcmp716_phieu_nghi_bu_chot_loai_nam_va_khoa_ngay.py`. Hand-written, idempotent, backfills old rows. Applied on local dev DB (upgrade, downgrade, upgrade verified).

Tests: `test/backend/test_nghi_phep_review_cr715.py` (new, 16), plus edits in `test_nghi_phep_ngay_cam_cr715.py` (+1), `test_nghi_phep_nghi_bu_cr715.py` (self-approval updates), FE tests.

| # | Change | Test |
|---|---|---|
| 1 | `entity_hooks.fire`: `db.rollback()` before re-raising `HookVeto` (VN comment). MCP `_confirm_proposal` except + generic tool except now `db.rollback()`. | `test_veto_then_caller_commits_leaves_nothing_half_approved` (verified red without rollback) |
| 2 | `comp_request_service.try_claim/claim`: atomic `UPDATE ... WHERE id AND status IN (expected)`, rowcount check, 409 "Phiếu vừa được xử lý bởi lượt khác — tải lại trang". Used by submit (`prepare_submit` claims before engine start), direct approve (`bridge.approve_now`), direct reject, cancel (claim before revoke, rollback if revoke fails), update, soft_delete, engine hooks (`_set_status` silent on lose, `_on_approved` → HookVeto). FE: new `useSingleFlight` hook (useRef) on delete/approve/reject/cancel in detail page + engine decision dialog; form submit already had ref. | `test_double_direct_approve_second_gets_409_and_credits_once`, `test_stale_direct_approve_reject_cancel_submit_all_get_409`, `test_double_submit_second_gets_409_without_second_instance`, `test_cancel_loses_to_concurrent_cancel_and_does_not_revoke_twice`, `use-single-flight.test.ts` |
| 3 | Columns `comp_leave_type_id`, `balance_year`. Type resolved + stored at submit (422 if none). Approve/cancel use stored type; invalid at engine approval → `HookVeto` 422. | `test_submit_stores_type_and_later_catalog_change_does_not_move_credit`, `test_engine_approval_with_invalid_stored_type_is_vetoed_even_if_caller_commits` |
| 4 | `balance_year = max(work_date.year, vn_today().year)` stored at approval; revoke uses stored type+year (`get_balance`, no `get_comp_type`). | `test_work_date_last_year_credits_current_year_and_cancel_uses_stored_year` |
| 5 | Schema range 2000-2100 (create+update); service rule work_date >= 1/1 of (today.year-1), VN 422. | `test_schema_rejects_year_outside_2000_2100`, `test_service_rejects_work_date_older_than_start_of_last_year` |
| 6 | `self_approval_policy.ALWAYS_STRICT_ENTITIES = {"leave_comp_request"}`: strict exclusion + `ensure_not_self_approval` regardless of setting; `leave_request` still follows setting. Existing tests updated (setting off now blocks too). | `test_strict_self_exclusion_covers_comp_entity`, `test_direct_approve_blocked_for_self_regardless_of_setting`, `test_engine_named_step_on_taker_goes_to_fallback_even_when_setting_off` |
| 7 | `balance_report_spec.rows_of`: OUTER JOIN `LeaveType.accrual_mode` + aliased `Employee.hire_date` inside the existing balance query, `accrual_holdback` per row in Python. Query count unchanged (0 extra). | `test_balance_report_remaining_matches_available_days`, `test_balance_report_query_count_is_constant` |
| 8 | `available_days` uses `LeaveAccrualMode.MONTHLY`, accepts preloaded `leave_type`/`hire_date`; new `available_days_map` (3 queries for any row count) used in balance list, my-balance list, assistant `leave_tool`. | `test_available_days_map_matches_single_calls_with_constant_queries` |
| 9 | `/tools/my-balance` returns `max_negative_days`; hint box warns only when overrun > `max_negative_days`. | `test_my_balance_returns_max_negative_days`, 2 vitest cases in `leave-balance-hint-box.test.tsx` |
| 10 | Form edit mode: picker hidden, read-only taker line. | 2 vitest cases in `leave-comp-request-form.test.tsx` |
| 11 | `hasQuota` counts `comp_days`; `LeaveBalanceCard` extras show `+N nghỉ bù`. | `leave-balance-quota.test.ts`, new `leave-balance-card.test.tsx` |
| 12 | DONE (not skipped): nullable `active_key` String(40) with UNIQUE index `uq_leave_comp_active_key`; `"{employee_id}:{work_date}"` while active, NULL on REJECTED/CANCELLED/deleted (set inside the same claim UPDATE). Create/update lose with IntegrityError -> 409. Withdraw/return keep key. | `test_unique_active_key_blocks_duplicate_insert_that_skips_service_check`, `test_active_key_released_by_cancel_reject_and_delete`, `test_edit_into_taken_date_is_409` |

## API shape changes (callers)
- `service.prepare_submit(db, obj, user=None)` now CLAIMS the row (Draft/Returned -> Pending) without commit; `engine.start` commits it. `mark_submitted` only writes `approval_instance_id`, no longer touches status.
- `bridge._on_approved` hook kept; core is `bridge.approve_now(db, obj, actor, error_cls)`.

## Design notes
- Claim helper does NOT `flush` before the UPDATE (would write stale ORM state of the losing caller); `refresh` after.
- Same-tick concurrency is simulated in tests by stale ORM objects (SQLite in-memory has no real parallel sessions).

## Gates
- `-k "nghi_phep or leave or cr715 or cr713 or quy_phep"`: 681 passed.
- `-k "approval or duyet or mcp or agent_hub"` (one combined run gets killed by the 2GB api limit at ~85%, so split): `approval` 40 passed; `duyet` 1072 passed + 1 known failure (`test_luong_nhieu_buoc_chi_nguoi_co_viec_cho`); `mcp or agent_hub` 939 passed, 6 failed, 3 errors. The 6 failures (`test_agent_hub.py` x5: MCP tool listing incl. `propose_document_update`/`search_docs`, meeting-minutes flow; `test_agent_hub_cong_mcp_cr207.py::test_khoa_chi_doc_chi_thay_tool_chi_doc`) fail IDENTICALLY with `agent_hub/mcp.py` restored to HEAD, so they are not caused by this change (tool-catalog drift from other uncommitted work).
- Host frontend-v2: `npm run typecheck` 0 errors; `npx eslint src/modules/hr` 0 errors, 1 pre-existing warning (unified-room-booking-table.tsx); `npx vitest run src/modules/hr` 132 files / 1476 tests passed.

## Unresolved
- Rules doc `.claude/rules/hr-leave.md` (CR-715 section) not edited per constraints; should note: comp request always blocks self-approval, `active_key`, stored type/year, `fire` rolls back on HookVeto.
- Old `/tools/my-balance` clients ignoring `max_negative_days` fall back to 0 (FE treats undefined as 0).
