# Load test — 5 report summary endpoints — BLOCKED at scratch-DB setup

## Status: BLOCKED

Hard rule: "create a SCRATCH database ... via a Python/SQLAlchemy script run inside the `api`
container using the app's configured DB URL ... If the app DB user lacks CREATE DATABASE
privilege, report BLOCKED with the exact error instead of working around it."

Verified inside `api` container using `app.core.config.settings` (no .env read):

```
db_url = mysql+pymysql://app:app_password@db:3306/procurement?charset=utf8mb4
SHOW GRANTS FOR CURRENT_USER():
  GRANT USAGE ON *.* TO `app`@`%`
  GRANT ALL PRIVILEGES ON `procurement`.* TO `app`@`%`
```

Attempted `CREATE DATABASE IF NOT EXISTS procurement_bench` with this same engine:

```
OperationalError: (pymysql.err.OperationalError) (1044, "Access denied for user
'app'@'%' to database 'procurement_bench'")
```

The `app` MySQL user is scoped to `procurement.*` only — no global `CREATE` privilege, so it
cannot create a sibling scratch database on the same server. Per the task's explicit instruction
I did not fall back to a root/admin MySQL credential (that would defeat the isolation guarantee
the rule exists for — never write to the real app DB — and no such credential was handed to me
via the app's own config). Confirmed no side effect: `SHOW DATABASES` after the failed attempt
still lists only `information_schema · performance_schema · procurement` — nothing was created,
nothing to clean up. No code was modified.

**To unblock:** either grant the `app` user `CREATE`/`DROP` on `procurement_bench.*` (or
global `CREATE`), or hand me a credential (e.g. MySQL root) that has it — whichever the team
is comfortable with, since the scratch DB approach itself (copy schema+data, multiply rows with
ID offsets, measure, drop) is otherwise ready to execute (see plan below).

## What's ready to go the moment privilege is granted

I fully mapped the query paths for all 5 endpoints so the load-test script can be written
immediately without further exploration:

| Endpoint | Data path | Notes on scaling risk |
|---|---|---|
| `/api/reports/procurement/summary` (`report/procurement_summary_service.py` + `procurement_summary_rows.py`) | Loads **all** `PurchaseOrder` rows (status ∈ approved/partial/received/completed) whose `order_date` falls in either of the (≤2) requested ranges, then **all** `POItem` for those POs, then **all** `PODelivery` for those items (`received_qty>0`) — 3 unbounded-by-period queries. Separately loads **all** `Payable` in range, resolves `real_po_ids` (extra query), then `_resolve_po_context` (2 more queries: PO + POItem again). ~7 round trips, all materialized fully into Python, aggregated by `report_aggregate.aggregate()` (pure-Python groupby, not SQL `GROUP BY`). | Heaviest of the 5 — quadratic-ish with PO×item×delivery fanout; best 30× stress candidate. |
| `/api/reports/pr-lines/summary` (`pr_lines_period_service.py`) | `_pr_lines_base_query` (report/service.py:461) joins `PurchaseRequest`+`PurchaseRequestItem`, then `.with_entities(...)` selects 6 flat columns only — lightweight per row, single query per period (×2 for compare). Plus 1 query for distinct assignee codes + 1 for employee names. | Lighter — column-trimmed, SQL-filtered by date. |
| `/api/purchase-progress/summary` (`purchase_progress/summary_service.py`) | `_build_query` outer-joins `PurchaseOrder`→`POItem`→`PODelivery` (fans out one row per delivery, NULL row for items with none), `with_entities(11 cols)`, run **twice** per fetch (once filtered by `order_date`, once by `PODelivery.received_date` — so 4 queries total across current+compare periods). No Python-side N+1 beyond that. | Row count = Σ deliveries per PO in scope; multiplies with the PODelivery table. |
| `/api/survey-progress/summary` (`survey_progress/summary_service.py` + `controller._decorate`) | `_build_query` joins `SurveyRequest`+`SurveyRequestLine`, filtered by `request_date`; then `_decorate()` does 4 more queries per call (chosen options `IN`, options count `GROUP BY`, Employee, Company) — called twice (current+compare) = up to 10 queries/request. Per-row Python date-diff logic in `ex.row_values`. | Moderate; N+1-ish batched queries, not per-row, but still 2× multiplier for compare mode. |
| `/api/survey-report/summary` (`survey/service.report_rows_in_range`) | Best-optimized of the 5 (per its own docstring, added specifically because the naive version scanned >7000 rows/year): 2 SQL-filtered queries on `contact_date` (with an index-friendly split to dodge an OR-across-tables full scan), 1 more for the parent `Survey` rows. | Lightest — already has a documented perf fix; good "control" case. |

Common thread across all 5: **none use SQL `GROUP BY`** — every one loads matching rows (or a
narrow tuple projection of them) into Python and aggregates via `report_aggregate.aggregate()` /
`report_compute.compute_metrics()`. This is architecturally consistent with the repo's chosen
design (`report_aggregate.py` docstring explicitly says "CỘNG bằng Python ... chạy y hệt SQLite
(test)/MySQL (prod)"), so the dominant scaling factor is expected to be **row-fetch count**, not
query-plan complexity — SQL time should stay roughly linear via existing indexes
(`order_date`, `request_date`, `incur_date`, `survey_id`, `po_id` etc. are already indexed per
the models), while Python aggregation time should grow *faster* than linear once row counts get
into the tens of thousands, because of the nested dict/list bucketing in `bucket_rows` and the
repeated `compute_metrics` passes per dimension/group.

## Current local DB volumes (read-only, for scaling context)

Actual row counts in the live local dev/demo DB (`procurement`), i.e. what 1× actually is:

| Table | Total rows | By year (date column used) |
|---|---|---|
| `tab_purchase_order` | 96 | 2026: 96 |
| `tab_purchase_request` | 72 | 2026: 71 |
| `tab_survey` | 2,711 | 2024: 2 · 2025: 1,750 · 2026: 947 · (2 garbage rows: `"206-"`, `"2525"` — bad `received_date` data, pre-existing, unrelated to this task) |
| `tab_survey_request` | 43 | 2026: 43 |
| `tab_payable` | 182 | 2026: 182 |
| `tab_po_item` | 113 | — |
| `tab_po_delivery` | 103 | — |
| `tab_purchase_request_item` | 101 | — |
| `tab_survey_supplier_line` | 53 | — |
| `tab_survey_product_line` | 5,150 | — |
| `tab_survey_request_line` | 91 | — |

This is demo/local data, far below any real prod volume — DEGO Holding's actual prod DB (per
`CLAUDE.md`, 141 tables, live since Sept 2026) almost certainly has meaningfully more PO/survey
rows/year than this local seed. **Caveat for whoever runs the load test next:** 10×/30× off *this*
1× baseline (96 PO/yr, 2,700 surveys total) does not equate to "10×/30× of real usage" — it
should be read as "what if PO/survey volume grew to ~1,000/~29,000 rows respectively", not as a
calibrated multiple of current prod load. Recommend re-running the same scaling method against a
prod-volume snapshot (or just asking for real prod row counts) before trusting the ms numbers as
capacity-planning input.

## Next steps (once unblocked)

1. Grant `app`@`%` `CREATE, DROP` (ideally scoped to `procurement_bench.*` via
   `GRANT CREATE, DROP ON \`procurement_bench\`.* TO 'app'@'%'` — MySQL allows granting on a
   not-yet-existing DB name) — or supply an alternate credential with that privilege.
2. Re-invoke this task; the model/query analysis above already covers everything needed to write
   the copy+multiply+measure script without further code exploration.

## Concerns

- The blocker is a MySQL privilege gap, not a code/design problem — nothing in the report module
  itself prevented the plan.
- No files were modified, no scratch DB was created, nothing to clean up.

## Unresolved questions

1. Who can grant `CREATE`/`DROP` on a `procurement_bench` DB to the `app` MySQL user (or provide
   a credential that already has it)? Needed to unblock.
2. Should the re-run use this local demo DB as baseline (as instructed), or would a snapshot of
   real prod volumes give more actionable capacity-planning numbers — see caveat above.
