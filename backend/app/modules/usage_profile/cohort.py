"""Chọn nhóm so sánh (cohort) và trung vị nhóm (thuần) — duoc-CR-641, phase 04.

Luật: (1) tập đo = người có dữ liệu trong W; (2) vai trò ứng viên = vai trò của người đó TRỪ vai trò quản trị;
(3) chọn vai trò CỤ THỂ NHẤT có ≥ 5 người trong tập đo (ít thành viên nhất trong số đạt ngưỡng; hòa → role_id nhỏ) —
nếu chọn vai trò đông nhất thì "Nhân viên" chung ai cũng có sẽ làm mọi người so với cả công ty;
(4) không vai trò nào đạt → pháp nhân nếu ≥ 5, ngược lại toàn công ty;
(5) trung vị nhóm tính trên thành viên CÓ giá trị (bỏ người `unmeasured`), chính người đó nằm trong trung vị.
"""
from collections import defaultdict
from dataclasses import dataclass

from app.core.usage_codes import CohortKind

from .metric_stats import median, percentile

MIN_COHORT = 5
ADMIN_ROLE_CODES = frozenset({"admin", "ADMINISTRATOR"})   # cùng danh sách report_access/seed_defaults


@dataclass(frozen=True)
class Cohort:
    kind: int
    key: int
    size: int


def assign_cohorts(measured: dict[int, int], user_roles: list, roles: dict, min_size: int = MIN_COHORT
                   ) -> dict[int, Cohort]:
    """measured: {user_id: company_id}. Trả {user_id: Cohort}."""
    role_users: dict[int, set[int]] = defaultdict(set)
    user_role_ids: dict[int, list[int]] = defaultdict(list)
    for uid, rid in user_roles:
        if uid in measured and roles.get(rid, ("", ""))[0] not in ADMIN_ROLE_CODES:
            role_users[rid].add(uid)
            user_role_ids[uid].append(rid)
    company_size: dict[int, int] = defaultdict(int)
    for company in measured.values():
        company_size[company or 0] += 1
    out: dict[int, Cohort] = {}
    for uid, company in measured.items():
        eligible = [(len(role_users[r]), r) for r in user_role_ids.get(uid, ()) if len(role_users[r]) >= min_size]
        if eligible:
            size, rid = min(eligible)
            out[uid] = Cohort(int(CohortKind.ROLE), rid, size)
        elif company and company_size[company] >= min_size:
            out[uid] = Cohort(int(CohortKind.COMPANY), company, company_size[company])
        else:
            out[uid] = Cohort(int(CohortKind.ALL), 0, len(measured))
    return out


def cohort_stats(cohorts: dict[int, Cohort], values: dict[int, dict]) -> dict[tuple, dict[str, tuple]]:
    """{(kind,key): {metric: (median, p75)}} — values: {user_id: {metric: số}}."""
    members: dict[tuple, list[int]] = defaultdict(list)
    for uid, c in cohorts.items():
        members[(c.kind, c.key)].append(uid)
    out: dict[tuple, dict[str, tuple]] = {}
    for ck, uids in members.items():
        keys = {k for u in uids for k in values.get(u, {})}
        out[ck] = {}
        for k in keys:
            xs = [values[u][k] for u in uids if k in values.get(u, {})]
            out[ck][k] = (median(xs), percentile(xs, 0.75))
    return out
