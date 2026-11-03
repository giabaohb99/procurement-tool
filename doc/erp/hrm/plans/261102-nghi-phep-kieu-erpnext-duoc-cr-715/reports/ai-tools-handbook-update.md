# CR-713 / CR-715 — AI side (MCP, web assistant, Telegram bot, handbook)

Uncommitted on `erp-v2`. No migration.

## Tools
| Tool | Change |
|---|---|
| `draft_leave_comp_request` (NEW, `assistant/tools/leave_comp_tool.py`) | Draft comp-leave request: `work_date`, `days` 0.5/1, `reason` (always asked — required at submit), `employee` (code, on-behalf). Gate `ctx.can(leave_comp_request, create)`; on-behalf = grant scope != own + `apply_scope(Employee,'employee')` + `ensure_can_create_for`; unknown code == out-of-scope code (same text). Pre-runs `get_comp_type` / `check_days` / `check_work_date` (read-only), errors returned verbatim. |
| confirm path (`agent_hub/draft_create.py`) | kind `leave_comp`: create via `comp_request_service.create` (Draft), submit via `comp_request_controller.submit_request`, summary + created_details, label/entity/detail path `/hr/leave-comp-requests/{id}`. Shared by Telegram (core_v2/service via `KIND_BY_TOOL`), MCP and gateway B. |
| `confirm_draft` (MCP, `mcp.py`) | kind enum + `leave_comp`; G7 group gate generalised (`_GROUP_GATED_KINDS`: vehicle_booking, seal_request, leave_comp). |
| `propose_approval` | + `leave_comp_request` (summary, direct approve/reject via comp controller, engine path unchanged). `decision_path` refuses requester when `strict_self_exclusion(entity)` (comp always; leave_request when CR-713 switch on). |
| `my_leave_summary` | per balance: `allocated_days`, `comp_days`, `not_yet_accrued_days`, `accrual_mode(+label)`, `max_negative_days`, `applicable_after_days`, `is_compensatory`; `remaining_days` = `available_days_map`; new `comp_requests` (own, only if `leave_comp_request.read`); glossary. |
| `draft_leave_request` | warnings: backdated (`leave_policy.ensure_not_backdated`), applicable-after (`accrual_service.ensure_applicable`), block periods (`block_period_service.find_conflicts`, + `block_conflicts` field, non-blocking), ứng phép within / beyond `max_negative_days`. |
| `my_approval_tasks` / `my_requests_status` | detail URLs for `leave_request`, `leave_comp_request`. |
| Contract expiry | No AI tool reads labor-contract thresholds (`report_summary` calls the route which already uses `warn_days()/danger_days()`). Nothing to change. |

Registered: `tools/__init__`, `mcp_settings` group `leave` (default ON), `tool_router` group `leave` (+ regex nghỉ bù / làm lễ / Chủ nhật / ứng phép / ngày cấm nghỉ / `nb\d+`), `intent_ledger.TOOL_SUB` (MAKE_LEAVE), `confirm_fields.TOOLS_WITH_USER_TEXT`, `change_service.ENTITY_LABELS`, web system prompt (`assistant/service.py`), chat desc (`core_v2.V2_TOOL_DESC`).

## Handbook
- `seed_handbook/40-nghi-phep.md`: formula + nghỉ bù + cộng dần, how to answer "còn bao nhiêu phép", ứng phép, accrual modes / group quota / applicable-after, ngày cấm nghỉ, phiếu nghỉ bù + tool, HR settings switches, tool result fields, 5 permission keys.
- `seed_handbook/60-nhan-su-ho-so.md`: org-chart visibility switch, tab Nhân viên / Hợp đồng (prefix, anniversaries, contract warn/danger days).
- `handbook_seed.py`: summary of `nghi-phep` (fresh seeds only).
- `scripts/publish_handbook_update.py`: new `--only slug,...` (default behaviour unchanged).
- Local DB published: `nghi-phep` v6 (version id 18), `nhan-su-ho-so` v5 (version id 19); dry-run after = up to date.

## Tests
- New `test/backend/test_assistant_nghi_phep_erpnext_cr715.py` (10).
- Gate tables: `test_assistant_chi_co_quyen_xem.TOOL_GHI`, `test_assistant_pham_vi_doc` count 87 → 88, `test_pham_vi_bo_may_duyet_xuyen_suot` E2.
- Adjusted: `test_assistant_approval_tool::test_loai_chung_tu_chua_co_man_thi_url_rong` (unmapped entity), `test_assistant_ai_duyet_phieu_kh_ai2_7::test_loai_ngoai_danh_sach...` (refusal text).
- Runs: `test_assistant_*` 395 passed (+1 known deselected); `test_agent_hub*` 891 passed, 2 skipped (known 6 deselected, 3 ffmpeg errors); gate/leave/ai_skill set 339 passed + 1 failure `test_canh_do_dai_o_chu_cr538::test_every_write_schema_is_mapped_to_its_table` (leave.QuotaRule*/LeaveEstimateIn/LeavePeriodItem, customs, forum — not AI code); final rerun of touched suites 701 passed.

## Deploy
- After deploy: `python scripts/publish_handbook_update.py --only nghi-phep,nhan-su-ho-so --note "… (duoc-CR-713, duoc-CR-715)"`.

## Open
1. Web assistant has no button for `draft_leave_comp_request` (frontend `reply-offers.ts` DRAFT_TARGETS) — contract below for giao-dien-v2.
2. Running DBs keep the old `nghi-phep` skill summary (publish script does not sync summary) — edit on Bộ skill screen if wanted.
3. `test_canh_do_dai_o_chu_cr538` red from other CR-715 schemas — owner: leave backend.

Frontend contract (if wanted): `tool_calls[].name == "draft_leave_comp_request"`, `rows > 0`, `draft = {kind:"leave_comp_request", employee_id (0 = self), employee_name, work_date "YYYY-MM-DD", days 0.5|1, reason}` → navigate `/hr/leave-comp-requests/new` with `state.assistantDraft`.
