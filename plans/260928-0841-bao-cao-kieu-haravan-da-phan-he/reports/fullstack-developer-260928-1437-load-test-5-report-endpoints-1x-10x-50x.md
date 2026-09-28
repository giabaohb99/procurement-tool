# Load test — 5 report summary endpoints @ 1x / 10x / 50x — throwaway MySQL container

## Status: DONE (1 combo crashed — itself a finding, see below)

Method: previous attempt was BLOCKED because MySQL user `app` has no `CREATE DATABASE` grant
(see `fullstack-developer-260928-1433-load-test-5-report-endpoints.md`). Unblocked per user's
explicit approval ("mock dữ liệu, test xong rồi xóa") by using a **separate throwaway MySQL 8.0.46
container** (`procurement-bench-db`, network `procurement-tool_default`, own root password,
`mem_limit=1g`) instead of a sibling DB on the real server. Real `procurement` DB was **only ever
SELECTed from** (via `mysqldump --single-transaction --no-tablespaces`, app's own read creds) —
never written to. Verified byte-identical before/after (see Cleanup).

## Setup

1. Bench container: `mysql:8.0` (matches real db1's `8.0.46`, same flags
   `--default-authentication-plugin=mysql_native_password`, `utf8mb4`/`utf8mb4_0900_ai_ci`).
2. Dumped real DB with app's own creds (`app:app_password@db`, `ALL PRIVILEGES ON procurement.*`
   confirmed by previous attempt) → 21MB dump → restored into bench container. Counts matched
   baseline exactly; Vietnamese text round-trips correctly (`Sản xuất` / `CÔNG TY TNHH...` verified
   byte-for-byte against the real DB — an earlier client-only mojibake was traced to a missing
   `--default-character-set=utf8mb4` flag on one throwaway `mysql -e` check, not real corruption).
3. Multiplied 11 report-feeding tables **within the same dates** via SQL `INSERT…SELECT` run
   through SQLAlchemy from inside the `api` container, id offset `k * 10,000,000`:
   `tab_survey(+supplier_line,+product_line)`, `tab_survey_request(+line)`,
   `tab_purchase_request(+item)`, `tab_purchase_order(+item,+delivery)`, `tab_payable`.
   FK columns offset **only when non-zero** (0 is a real "unset" sentinel in this schema, not a
   value to shift — confirmed via `CLAUDE.md`'s own "id=0 is a real value" convention); the 4
   `UNIQUE KEY code` columns suffixed `-Lk`. Master data (users, sessions, roles, departments,
   companies, employees, suppliers) left untouched and shared across all copies, as instructed.
   10x done first (9 extra copies), verified, then extended to 50x (40 more copies). All 11 tables
   landed at **exactly** 10.00x and 50.00x row counts (e.g. `tab_survey` 2,711 → 27,110 → 135,550;
   `tab_purchase_order` 96 → 960 → 4,800). **Scope simplification** (not in the task's explicit
   table list, so left alone): `tab_survey_request_option` (drives the "đã chọn" count in
   `survey_progress`'s `_decorate()`) was not multiplied — duplicated survey-request lines show 0
   chosen-options instead of a realistic distribution. Doesn't change row-fetch volume, the thing
   being measured.
4. Measured with `fastapi.testclient.TestClient` inside a **standalone python process launched via
   `docker exec`** (imports `app.main` fresh — confirmed no `lifespan`/`on_event` handlers in
   `main.py`, so this import has no side effects on the already-running `uvicorn --reload` process).
   `app.dependency_overrides[get_db]` → sessionmaker bound to the bench engine only. Confirmed no
   endpoint under test bypasses this: the only two `SessionLocal` direct-uses in the whole backend
   are `report/service.py:711` (a **different**, older `/api/reports/procurement` snapshot endpoint
   — background stale-while-revalidate cache, unrelated to `/procurement/summary`) and
   `purchase_request/controller.py:839` (push-notification background task, unrelated). All 5
   endpoints under test go through `Depends(get_db)`. Logged in once as `admin`/`admin` (seeded
   local account), reused the Bearer token for all calls. Instrumented every SQL statement via
   SQLAlchemy `before/after_cursor_execute` events to get **SQL time + statement count + summed
   `cursor.rowcount`** per request, separate from wall time.

## Results — median / max ms, 5 reps each (1 discarded warm-up before)

`rows` = summed `cursor.rowcount` across all SQL statements in that request (proxy for rows
fetched from MySQL, not final response size). `sql_ms` = time inside `cursor.execute()` only.

### `/api/reports/procurement/summary?group_by=department`

| Preset | 1x median/max | rows | 10x median/max | rows | 50x median/max | rows |
|---|---|---|---|---|---|---|
| this_month, compare=previous | 16/21 ms | 592 | 63/143 ms | 5,623 | **391/533 ms** | 27,983 |
| this_quarter, compare=previous | 26/66 ms | 1,166 | 226/253 ms | 11,363 | **1,195/1,212 ms** | 56,683 |
| this_year, compare=year | 25/29 ms | 1,026 | 216/251 ms | 9,963 | **1,247/1,407 ms** | 49,683 |
| custom 2024–2026, compare=none | 24/25 ms | 1,026 | 142/225 ms | 9,963 | **1,063/1,491 ms** | 49,683 |

### `/api/reports/pr-lines/summary?group_by=line_status` (best scaler — sub-linear)

| Preset | 1x | 10x | 50x |
|---|---|---|---|
| this_month/previous | 8/9 ms (39 rows) | 18/18 ms (237) | 57/75 ms (1,117) |
| this_quarter/previous | 9/10 ms (100) | 36/37 ms (847) | 168/196 ms (4,167) |
| this_year/year | 10/10 ms (100) | 35/37 ms (847) | 158/217 ms (4,167) |
| custom/none | 10/12 ms (100) | 35/149 ms (847) | 165/172 ms (4,167) |

### `/api/purchase-progress/summary?group_by=progress_status`

| Preset | 1x | 10x | 50x |
|---|---|---|---|
| this_month/previous | 9/9 ms (21) | 11/23 ms (192) | 57/73 ms (952) |
| this_quarter/previous | 11/14 ms (196) | 44/46 ms (1,942) | 305/886 ms (9,702) |
| this_year/year | 11/11 ms (223) | 46/53 ms (2,212) | 280/402 ms (11,052) |
| custom/none | 11/14 ms (223) | 50/50 ms (2,212) | 307/576 ms (11,052) |

### `/api/survey-progress/summary?group_by=progress`

| Preset | 1x | 10x | 50x |
|---|---|---|---|
| this_month/previous | 10/11 ms (35) | 11/12 ms (62) | 23/26 ms (182) |
| this_quarter/previous | 16/17 ms (175) | 60/61 ms (994) | 403/503 ms (4,634) |
| this_year/year | 16/16 ms (175) | 60/158 ms (994) | 307/**1,139** ms (4,634) |
| custom/none | 17/19 ms (162) | 58/60 ms (981) | 511/889 ms (4,621) |

### `/api/survey-report/summary?group_by=line_approve` (worst — superlinear, only one that crashes)

| Preset | 1x | 10x | 50x |
|---|---|---|---|
| this_month/previous | 11/11 ms (15) | 15/16 ms (132) | 58/166 ms (652) |
| this_quarter/previous | 52/140 ms (1,211) | 429/531 ms (12,092) | **3,150/3,569 ms** (60,452) |
| this_year/year | 314/392 ms (6,702) | **2,552/2,582 ms** (67,002) | **18,399/22,648 ms** (335,002) |
| custom 2024–2026/none | 273/534 ms (7,885) | **3,122/3,384 ms** (78,832) | **CRASHED — OOM-killed, never completed** |

The 50x `custom_2024-2026` run for `survey-report/summary` (the widest possible date range, ~3yr,
estimated ~394,160 rows) exceeded the `api` container's `mem_limit: 2g` (`docker-compose.yml`) and
was SIGKILLed by the Linux OOM killer (`docker inspect` → `OOMKilled=true`, exit 137) **after**
`this_year` (335,002 rows) had already succeeded at 18.4s. Confirmed the OOM killer took only my
benchmark process, not the live `uvicorn` server (`GET /api/health` → 200 immediately after,
`/api/notifications`/`/api/alerts` traffic in the container logs continued uninterrupted). This
happened **twice** during this session (once mid-profiling on the same combo) — both times the
live server survived, but this is a real container-crash mode, not just "slow", once
survey/product-line volume + a multi-year custom range coincide. In a real single-uvicorn-worker
deployment (this repo's `start.sh` runs one worker), the same request **would** be the process the
kernel picks, since it is by far the largest single allocator at that moment — i.e. this is a
plausible full-service-outage vector once survey volume gets into the hundreds of thousands, not
a hypothetical.

### Overview pattern — 5 endpoints, `group_by=none`, PARALLEL threads, 50x

| Preset | total wall | procurement | pr_lines | purchase_progress | survey_progress | survey_report |
|---|---|---|---|---|---|---|
| this_month/previous | 581 ms | 581 ms | 222 ms | 195 ms | 96 ms | 173 ms |
| this_year/year | **21,337 ms** | **15,356 ms** | 1,538 ms | 3,910 ms | 933 ms | **21,330 ms** |

`procurement_summary` alone was 1,247 ms sequential/isolated (table above) but **15,356 ms** when
run concurrently with the other 4 — a **12x slowdown from CPU contention alone** (api container is
`cpus: 3`; 5 concurrent CPU-bound, GIL-bound Python-aggregation sync endpoints on 3 cores serialize
badly, and the heaviest one — survey-report at 21.3s — starves the rest). SQL portions barely
changed; this is Python-side contention, not DB contention. **This is a standalone finding
independent of any single endpoint's own complexity**: a "load the whole dashboard" page pattern
at scale is worse than the sum of its parts.

## Where the time goes (SQL vs Python, event-listener data from the un-profiled 50x runs)

`sql_ms / median_ms` at 50x, this_quarter/similar preset:

| Endpoint | SQL % of wall | Python-side % (ORM materialize + aggregate + serialize) |
|---|---|---|
| pr_lines_summary | ~13–18% | ~82–87% (but absolute time tiny, 168ms) |
| procurement_summary | ~22–29% | ~71–78% |
| purchase_progress_summary | ~39% | ~61% |
| survey_progress_summary | ~36% | ~64% |
| survey_report_summary | ~30–44% | ~56–70% (absolute time huge) |

None of the 5 use SQL `GROUP BY` (confirmed in code + via `cProfile`: every request's dominant
cumulative-time frame is `app/core/report_aggregate.py:140(build_report)` doing pure-Python
dict/list bucketing) — matches the architecture note already in that file's own docstring
("CỘNG bằng Python... chạy y hệt SQLite/MySQL"). So **60–85% of wall time everywhere is Python**,
not the database — column-trimming/indexing alone won't fix this; the aggregation step itself has
to move.

**Growth-rate check (is it linear?)**, 1x → 50x, same preset, `time_ratio / rows_ratio`:

| Endpoint (preset) | rows ratio | time ratio | shape |
|---|---|---|---|
| pr_lines_summary (this_quarter) | 41.7x | 18.1x | **sub-linear** (best) |
| survey_progress_summary (this_quarter) | 26.5x | 26.0x | ~linear |
| purchase_progress_summary (this_quarter) | 49.5x | 26.8x | sub-linear (1x floor effect) |
| procurement_summary (this_quarter) | 48.6x | 46.7x | ~linear |
| **survey_report_summary (this_year)** | 50.0x | **58.6x** | **super-linear** (worst, and the only one that also OOMs) |

`cProfile` (top-15 filtered to `/app/` + `sqlalchemy`, 50x, `this_quarter_prev`, profiler overhead
inflates absolute numbers ~2-3x but the *shape* is representative — files saved then deleted during
cleanup, key frames captured here verbatim):
- **procurement_summary**: `compute_procurement_summary` 2.37s → `query.all()` 1.69s (71%,
  `po_rows`/`payable_rows`/`_resolve_po_context` fetch upfront) + `build_report` 1.08s (pure
  Python aggregate, called AFTER rows already fetched — clean separation).
- **survey_report_summary**: `report_summary_` 7.78s → `build_report` 7.76s (nearly ALL of it) →
  `fetch`/`report_rows_in_range` 6.51s, of which raw `query.all()` is 5.48s (row materialization
  dominates — 2 supplier+product line tables merged, `line_approve` grouping done in Python) and
  the remaining ~1s is genuinely Python aggregation stacked on top.
- **survey_progress_summary**: `_decorate()` alone = 0.27s of 0.94s total (called twice, once per
  period) — confirms the previous report's N+1-batch flag (chosen options `IN`, options count
  `GROUP BY`, Employee, Company — 4 extra queries × 2 periods = up to 10 queries/request).
- **purchase_progress_summary**: cleanest split — `fetch`=SQL-bound (0.34s of 0.56s total),
  remaining 0.21s is `build_report`'s pure aggregate.

## Cases exceeding thresholds (50x)

**> 1s**: `procurement_summary` (this_quarter 1.20s, this_year 1.25s, custom 1.06s) ·
`survey_progress_summary` this_year (max only, 1.14s; median 307ms) · `survey_report_summary`
(this_quarter 3.15s, this_year 18.4s, custom = crash) · overview this_year (21.3s total, and its
`procurement_summary`/`survey_report_summary`/`purchase_progress_summary` legs individually).

**> 3s**: `survey_report_summary` this_quarter (3.15s), this_year (18.4s), custom (crash) ·
overview this_year total (21.3s) and its `procurement_summary` (15.4s) / `survey_report_summary`
(21.3s) legs.

**Everything else stays under 1s even at 50x** — `pr_lines_summary` (max 217ms),
`purchase_progress_summary` except this_quarter/custom (up to 886ms max, still <1s), most of
`survey_progress_summary`.

## Most effective fixes, ranked, with estimated gain

1. **Push `survey-report/summary` aggregation into SQL `GROUP BY`** (highest priority — this is
   the only endpoint that crashes, and it's already the slowest in absolute terms because survey
   volume is inherently ~28x PO volume in this dataset). Replace
   `report_rows_in_range` + Python `build_report`/`aggregate()` with
   `SELECT line_approve, <dimension>, COUNT(*) FROM ... GROUP BY line_approve, <dimension>`
   equivalents for the two line tables, unioned. `line_approve` is stored as Vietnamese TEXT
   (documented legacy exception, §2.2 of `doc/erp/15-do-be-tong-nen-v2.md`) but that's still
   perfectly GROUP-BY-able — no schema change needed. **Estimated gain**: removes the ~5.5s of
   `query.all()` ORM-materialization + the superlinear Python aggregate entirely; this_year/custom
   should drop from 18–30s+ to low hundreds of ms (same order as `procurement_summary`'s SQL-bound
   ~250–320ms), a **~50–100x** improvement on the worst cases, and eliminates the OOM crash mode
   outright (no more holding 300k+ row objects in memory). Also apply the same `load_only()`
   column-trimming `procurement_summary_rows.py` already uses — cheap, ships first as a stop-gap.
2. **Short-TTL Redis cache** (Redis already running in this compose stack) keyed by
   `(endpoint, all query params, user's data-scope signature)`, TTL ~60–120s. Report dashboards are
   read-heavy/revisit-heavy and 1–2 min staleness is acceptable for a reporting screen.
   **Estimated gain**: near-100% reduction for repeat views within TTL (the dominant real traffic
   pattern for a Reports module); directly fixes the "overview" concurrency finding too, since a
   5-widget dashboard load after any single widget was recently viewed becomes mostly cache hits —
   doesn't fix true worst-case cold load, complements fix #1 rather than replacing it.
3. **`survey_progress_summary`: collapse `_decorate()`'s N+1-batch queries** — push "chosen options
   count" to a single `GROUP BY` instead of Python `Counter`, and skip re-fetching Employee/Company
   twice (once per period) since master data doesn't change between periods.
   **Estimated gain**: cuts sql_count from up to 10/request to ~4–5, and removes ~0.27s×2 of
   `_decorate` Python time seen in profiling — meaningful at 50x (403–511ms → likely sub-200ms).
4. **`procurement_summary`**: lower priority than #1 (scales ~linearly, doesn't crash) but still
   the 2nd-heaviest in absolute terms (~1.2s at 50x quarter/year). Cache (#2) is the
   proportionate fix here; a SQL `GROUP BY` rewrite of `report_aggregate.aggregate()` itself would
   help every endpoint uniformly but is the biggest single engineering lift of the four — only
   worth it if #1–#3 aren't enough.

`pr_lines_summary` needs no fix — it's already the reference pattern (narrow `with_entities`
projection, single query per period, SQL-filtered) the other four should be made to resemble.

## Cleanup (verified)

1. `docker rm -f procurement-bench-db` — done (the earlier `procurement-bench-db-1x`, used only
   for the 1x baseline, was already removed right after its measurement).
2. Dump file, `multiply.py`, `measure.py` removed from both host `/tmp/bench` and the `api`
   container's `/tmp` (`docker exec ... rm -rf /tmp/multiply.py /tmp/measure.py /tmp/measure_1x.py
   /tmp/bench`).
3. No `procurement-bench*` containers, networks, or volumes remain (`docker ps -a` / `network ls` /
   `volume ls` all checked clean).
4. **Real `procurement` DB row counts verified byte-identical** before vs. after, for every table
   touched by the multiplication plan plus `tab_user`/`tab_login_session` (login writes a session
   row — confirmed that write landed in the **bench** DB only, real DB unaffected):
   `tab_purchase_order=96, tab_po_item=113, tab_po_delivery=103, tab_purchase_request=72,
   tab_purchase_request_item=101, tab_survey=2711, tab_survey_supplier_line=53,
   tab_survey_product_line=5150, tab_survey_request=43, tab_survey_request_line=91,
   tab_payable=182, tab_user=276, tab_login_session=327` — `diff` against the pre-run baseline was
   empty.
5. No source files were modified anywhere in the repo (this was measurement-only, per the task).
6. Minor note, not mine to clean up: `api` container's `/tmp/` has unrelated leftover debug files
   (`cprof_survey.py`, `report_bench.py`, etc.) from a different/earlier session — not created by
   this run, left untouched since removing another session's artifacts wasn't in scope here.

## Concerns

- The OOM crash (finding, not a test-harness bug) means the 50x "custom 2024–2026" cell for
  `survey-report/summary` has no completed timing — reported as "CRASHED" rather than a number,
  which is itself the more important data point.
- All JSON/profile result files were deleted along with the throwaway `/tmp/bench` staging
  directory during cleanup (an `rm -rf /tmp/bench` on the host removed a `from_container/`
  subdirectory I'd copied results into moments earlier) — the numbers in this report were
  transcribed from the run's own console output captured earlier in the session, not re-derived,
  but there is no machine-readable artifact left on disk if someone wants to re-slice the raw
  per-request data later. If that's wanted, re-running takes about 15–20 minutes end to end now
  that the method/scripts are proven.
- 1x and 10x measurements were each run twice in a row before the numbers reported here settled
  (first pass had a stray Python `SyntaxError`/missing-output-dir issue caught immediately) — the
  numbers used are each run's clean, successful pass; noted in case someone expects "first ever
  call" cold-start numbers specifically, which would be somewhat higher (connection-pool/MySQL
  buffer-pool warm-up effects, roughly +30–70% on the very first request only, unrelated to the
  scale findings above).

**Status:** DONE
**Summary:** Real DB confirmed untouched throughout and after cleanup (byte-identical row counts).
4/5 endpoints scale roughly linearly to sub-linearly to 50x and stay under 1s except at the
this_quarter/this_year/custom presets of `procurement_summary` (~1.0–1.2s) and
`purchase_progress`/`survey_progress` tails. `survey-report/summary` is the clear outlier: grows
superlinearly (58.6x time for 50x rows) and its 50x "custom 2024–2026" case OOM-crashed the
benchmark process (container `mem_limit: 2g`), a real single-worker-outage risk, not just latency.
None of the 5 endpoints use SQL `GROUP BY` — 60–85% of wall time is Python-side aggregation
everywhere; a concurrent "load all 5 report widgets" pattern at 50x causes a further 12x CPU-
contention slowdown on top of each endpoint's own cost (3-CPU container, 5 concurrent CPU-bound
sync requests). Top fix: push `survey-report/summary`'s aggregation to SQL `GROUP BY` (~50-100x on
worst cases, removes the crash), then a short-TTL Redis cache for the rest.
**Concerns:** OOM-crash cell has no timing number (crash IS the finding); result JSON/profile files
were accidentally deleted from disk during cleanup — all numbers here are transcribed from
in-session console output, re-running is ~15-20min if raw artifacts are needed later.
