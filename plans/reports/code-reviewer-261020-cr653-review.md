# Review duoc-CR-653 «Quyền mặc định theo chức vụ» (uncommitted, erp-v2)

## Scope
- BE: position_role_service/controller, employee/service.py, user/service.py+controller+model, import (apply/revert), audit.py, action_catalog, migration jobposrole01, scripts/de_xuat_quyen_theo_chuc_vu.py
- FE: job-position-roles-panel, hooks/api/types, position-grant-badge, user-permission-detail-page
- Verify: 4 CR-653 pytest files 29/29 pass; FE typecheck 0 err, eslint (touched files) 0, vitest panel+permission page 15/15; `alembic heads` = single head `d0uiact01` (CR-654) whose down_revision is `jobposrole01`
- Probes (throwaway pytest in container /tmp, removed): P1 self-escalation CONFIRMED, P2 orphan role CONFIRMED, P3 dedup keeps system row CONFIRMED, P4 manual removal undone by Áp lại CONFIRMED

## Critical

### C1. HR self-escalation: change OWN position → system grants bundle to self (CONFIRMED)
- `employee/controller.py:310-332` PATCH `/api/employees/{eid}` only runs L1 `block_edit_own_department` when department changes. Position has no L1. `update_employee_core` (`employee/service.py:387-390`) then calls `sync_employee_roles` for the actor's own account.
- Probe: user with only `employee.write` (scope all, AND separately scope **own**) PATCHes own `position_id` → 200; next profile has `role.write` + `user.write` + `payment_request.approve` from the bundle. Scope `own` is enough because the employee scope's `self` maps to `id`.
- Same hole, all unguarded for position:
  - Excel import, catalog-position branch (`import_tool/employee_import.py:262-268` guards only dept), plus the free-text branch;
  - import revert (`employee_import_revert.py:152` guards only dept/company; sync at :206);
  - work-history apply `_apply_appoint/transfer` (`work_history_apply_service.py:66-71` guards only dept);
  - set-password/provision for self is n/a (already has an account).
- So the answer to "does L1 cover position?": **No.** The owner-accepted side effect ("HR saving a profile grants the bundle") turns into "HR grants themselves any bundle", which includes roles with `role.write` (bundle editing) — the whole "bundle editing needs role rights" boundary collapses.
- Fix (pick one, A preferred):
  - (A) In `sync_employee_roles`/`_sync_user`, never GRANT to the account whose `user.id == actor_id`, unless the actor is admin. Revoking is OK. Defer self-grants like reapply does, and return a "skipped_self" flag. This covers all 4 paths in one place.
  - (B) Add `block_edit_own_position(db, eid, actor)` (same as `block_edit_own_department`), run when the position changes, at all 4 call sites (PATCH, import both branches, revert, work-history apply). Easy to miss one again.
- Add a test per path: actor = holder of the employee being edited.

## High

### H1. HR mints a usable account carrying bundle roles via set-password
- `employee/controller.py:260-293`: `employee.write` (scope all) on an employee with no account → `provision_user` → `grant_on_account_creation` (`user/service.py:197-201`). HR also sets the employee's position and email first, so HR ends up holding a password for an account with any non-admin bundle (incl. role.write/user.write if such a bundle exists).
- Before CR-653 the minted account got only `employee`. This is the same class as the documented reset-password policy hole (`_block_set_password_out_of_scope` docstring) but strictly stronger: no existing powerful account is needed.
- Fix: in `grant_on_account_creation`, apply L2 (`block_role_escalation`-style filtering: grant only bundle roles whose perms ⊆ actor perms, or skip and report). Or provision with the default role only when the actor lacks `role.write`/`user.write`, and leave bundle grants to «Áp lại».

### H2. Bundle self-edit: role.write holder edits the bundle of their OWN position
- `position_role_controller.py:35-50` + `reapply_to_holders:219-240`: «skip self» only skips the reapply moment. The next trigger for the actor (any position change, unlock, or one HR colleague's save) grants it.
- L2 ignores scope by design. So a non-admin with role.write, holding position P, can add role R (same entity×action pairs, wider scope e.g. `all`) to P's bundle, then gets the wider scope with one HR save, without passing the L1 that the permission page enforces (`block_edit_own_role` analogue).
- Fix: in PUT, if the actor (non-admin) currently holds this position (`Employee.position_id == position_id` for `actor.employee_id`) and `added` is non-empty → 403 with SELF_CHANGE_MESSAGE. Combined with C1(A) this closes it.

### H3. Deleted role stays in bundle → sync inserts orphan `tab_user_role` rows (CONFIRMED)
- `role/references.py:21-28` does not register `JobPositionRole`, so `delete_role` succeeds for a role that is only in bundles. The bundle row survives (no FK).
- `bundle_role_ids` (`position_role_service.py:46-50`) does not join `Role`. The next position change inserts `UserRole(role_id=<deleted>)` — exactly the garbage-row bug `delete_role` comments describe. `reapply` L2 also passes because `permissions_of_roles` of a missing role is ∅.
- Fix: register `rg.Reference(JobPositionRole, "role_id", "quyền mặc định chức vụ")` in `role/references.py` (block delete), AND/OR join `Role` in `bundle_role_ids`. Also clean bundle rows on position hard-delete (`_block_delete_position_in_use` only checks holders → orphan `tab_job_position_role` after a delete).

## Medium

### M1. Admin cannot "pin" a system role; manual removal silently undone (CONFIRMED P3/P4)
- `assign_roles` (`user/service.py:304-318`) keeps an existing system row as-is when the admin re-saves it ticked. The badge says «Theo chức vụ» but there is no way to convert it to a hand grant in one save.
- If the admin unticks a bundle role on purpose, the next «Áp lại», position re-entry or unlock re-grants it. No opt-out marker exists, and the permission page doesn't warn.
- The dedup in `assign_roles` keeps the lowest-id row. With a hand+system duplicate (possible, see M2), it deletes the HAND row and keeps the system row (probe: `[(rid, 99)]`). The hand grant then later gets revoked by a position change.
- Fix: dedup should prefer a `granted_by_position_id == 0` row. Decide the semantics: a role explicitly submitted by an admin is converted to hand (`granted_by_position_id = 0`) only when the admin ticks it newly. Or add an explicit "pin" action. At least show a warning on the permission page when unticking a badge role.

### M2. No uniqueness on `tab_user_role(user_id, role_id)` + read-then-insert reconcile
- `_sync_user` (`position_role_service.py:83-104`) and `assign_roles` both read rows, then insert. Concurrent writers (HR save + Áp lại, two Áp lại from 2 tabs, a Celery import + UI save) double-insert. MySQL RR doesn't prevent it (see the prior repo finding: FOR UPDATE + plain SELECT still double-inserts).
- Effects: duplicate rows; combined with M1, a hand grant can be lost.
- Fix: a unique index `uq_user_role(user_id, role_id)` in this migration (dedupe first, preferring marker 0), and catch IntegrityError → treat as already held. Or lock the user row (`SELECT … FOR UPDATE` on `tab_user`) at the start of `_sync_user`/`assign_roles`.

### M3. Revocation latency across processes
- `perm_cache_clear` is process-local (`core/auth.py:135`). Prod runs `uvicorn --workers 2` and the employee import runs in Celery (`import_tool/tasks.py`). `_clear_cache_after_commit` in the worker or the other API worker doesn't reach the process serving the user, so revoked roles keep working ≤60 s. This is pre-existing for all permission writes, but CR-653 adds bulk revocations (import, Áp lại).
- Accept and document, or move the cache version to Redis (a stamp per user_id).

### M4. Proposal script default `--min-holders 1` proposes a single holder's entire role set
- `scripts/de_xuat_quyen_theo_chuc_vu.py:93-95,180`: with 1 holder, every role = 100% → «CÓ». `--apply` writes them; the «MẪU NHỎ» warning is only in the Markdown.
- It excludes only the `admin` code: legacy `ADMINISTRATOR`, role.write/user.write roles, etc. can go into bundles. With C1/H1 open, that hands them to anyone HR touches.
- Writes have no audit row and no L2 (it's an ops script, but `record(..., "set_position_roles")` would be cheap).
- Fix: default `--min-holders 3`; never mark `proposed` when holders < min (already so) but make the default safe; exclude roles granting `role`/`user` write; audit on apply.
- Read-only default + `--apply --yes` + writes only `tab_job_position_role`: OK.

### M5. Bundles may contain permission-management roles
- The controller blocks only `admin` (`position_role_controller.py:39-42`). A bundle role with `role.write`/`user.write` means anyone with `employee.write` decides who becomes a permission manager (HR-side position edit, owner-accepted).
- Recommend rejecting roles whose matrix has any `role.*`/`user.write`/`user.create` (and legacy `ADMINISTRATOR`) at PUT, and re-filtering `admin` in `bundle_role_ids` (defence in depth: today the only admin gate is in the controller; the service + script path don't block it at grant time).

## Low
- L1. `set_bundle` commits (`:195`) then audit commits separately. `reapply` commits (`:240`) then audits: an audit failure leaves an unaudited change. Use `record(commit=False)` before the single commit. Concurrent PUTs → `uq_job_position_role` IntegrityError → 500 (catch → 409).
- L2. `provision_user`: 3 separate commits (user, default roles, bundle). A failure between them leaves the account without its bundle. Pre-existing pattern.
- L3. Employee hard-delete → `detach_users` sets `employee_id=0` and locks, but keeps system rows. A later `set_active(True)` skips sync (`user.employee_id` is 0), so the unlinked account regains old-position roles. Revoke system rows in `detach_users`, or sync with "no position".
- L4. Reapply summary `holders` includes the skipped self. The toast «Đã áp lại cho N người» over-counts by 1.
- L5. FE Save (`job-position-roles-panel.tsx` Lưu button) is guarded only by `disabled={save.isPending}`. It violates the useRef rule in `.claude/rules/frontend-v2-ui-conventions.md:49`. Double-click → 2 PUTs → possible 500 (uq). Áp lại is effectively protected by the singleton `confirm` (resolves the earlier one false).
- L6. FE buttons lack `type="button"`. Not a live bug: the CRUD tabs render outside `#crud-detail-form` (`crud-detail-page.tsx:207` vs :367). Add it anyway for safety if the panel is reused.
- L7. L2 on the permission page (`user/controller.py:91`) checks ALL submitted role_ids. Managers without bundle-role perms now get 403 editing any holder (system rows count). Pre-existing semantics, but bundles make it frequent.

## Checks that passed
- `record(commit=False)` sits only in the sync/audit path. The callers (`update_employee`, import savepoint, revert, set_active) own the commit. The dry-run savepoint rollback drops both the rows and the audit (test exists).
- Cache cleared before and after_commit for every changed user in the same process.
- Marker semantics:
  - hand+bundle duplicate → no extra row, hand untouched;
  - X→Y keeps a common role (relabels the marker);
  - clearing the position revokes system rows only;
  - locked/resigned users skipped; unlock reconciles.
- `UserScope` is keyed by (user, role), not by the user_role row id, so reconciling vs delete/insert loses no scope data. As before, scope rows of a revoked role linger and revive on re-grant.
- Migration matches the model (BigInteger NOT NULL default 0 + index, unique pair, AuditMixin columns). Idempotent guards; downgrade OK (documented: auto rows become hand rows).
- FE gating `can('role','read'|'write')`, the confirm on Áp lại with holder count, the admin hidden from options.

## Recommended order
1. C1 (block self-grant in `_sync_user`, + tests for all 4 paths) — blocking.
2. H1, H2, H3 (L2 at provision; self-position bundle edit; role-delete reference + Role join).
3. M2 unique index (same migration, before first deploy), M1 dedup preference.
4. M4/M5 script defaults + bundle content policy.
5. Commit order: CR-653 migration must land before/with CR-654 (`d0uiact01.down_revision = jobposrole01`).

## Unresolved questions
1. Should bundles be allowed to contain roles granting `role`/`user` write? (M5)
2. When an admin re-saves a system-granted role, should it become a hand grant (pin)? And should a manual removal opt the user out of the bundle? (M1)
3. Provision via `employee.write` set-password: grant the full bundle, the L2-filtered bundle, or none? (H1)
