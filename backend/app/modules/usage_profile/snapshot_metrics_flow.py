"""Chỉ số chuỗi phiếu, duyệt, thông báo, phối hợp, việc dự án — tính cho CẢ công ty từ nguồn đã nạp (duoc-CR-641, phase 04).

Mỗi hàm trả `{user_id: Partial}`; không truy vấn DB, không vòng lặp theo người gọi DB.
"""
import json
from collections import defaultdict
from datetime import date, datetime

from app.core.export_xlsx import VN_OFFSET

from app.core.usage_codes import UnmeasuredReason as Why
from app.modules.approval.instance_model import TASK_APPROVED, TASK_PENDING, TASK_REJECTED

from .daily_activity import PARALLEL_WINDOW
from .metric_partial import Partial
from .metric_stats import median, percentile, ratio

SUBMIT = ("submit", "submitted")
RETURNS = ("return", "returned", "reject", "rejected")
BATCH_MIN_SIZE = 5
BATCH_WINDOW = PARALLEL_WINDOW   # cụm ≥ 5 quyết định trong 10 phút
MIN_NOTIFS = 5
MIN_MENTIONS = 3
MIN_TASKS = 5


def chain_metrics(chain_audits: list, utc_lo: datetime, utc_hi: datetime) -> dict[int, Partial]:
    """Chuỗi audit theo phiếu: tạo → sửa… → gửi lần đầu (trong W) → sửa/trả. Gom theo NGƯỜI TẠO."""
    chains: dict[tuple, list] = defaultdict(list)
    for row in chain_audits:   # đã sắp theo id
        chains[(row[1], row[2])].append(row)
    per: dict[int, dict] = defaultdict(lambda: {"drafts": [], "edited": 0, "returned": 0})
    for rows in chains.values():
        creator = next((r[4] for r in rows if r[3] == "create"), None)
        idx = next((i for i, r in enumerate(rows) if r[3] in SUBMIT and r[4] == creator), None)
        if creator is None or idx is None or not (utc_lo <= rows[idx][5] < utc_hi):
            continue
        before, after = rows[:idx], rows[idx + 1:]
        slot = per[creator]
        slot["drafts"].append(sum(1 for r in before if r[3] == "update" and r[4] == creator))
        slot["edited"] += 1 if any(r[3] == "update" and r[4] == creator for r in after) else 0
        slot["returned"] += 1 if any(r[3] in RETURNS and r[4] != creator for r in after) else 0
    out: dict[int, Partial] = {}
    for uid, s in per.items():
        p, n = Partial(), len(s["drafts"])
        p.put("drafts_before_submit_p50", median(s["drafts"]))
        p.put("edits_after_submit_share", ratio(s["edited"], n))
        p.put("returned_rate", ratio(s["returned"], n))
        p.counts["submitted_chain"] = n
        out[uid] = p
    return out


def _sequential_nodes(instances: list) -> set[tuple[int, int]]:
    out: set[tuple[int, int]] = set()
    for inst_id, raw in instances:
        try:
            from app.modules.approval import flow_service
            from app.modules.approval.flow_model import MULTI_SEQUENTIAL
            for node in flow_service.steps(raw or ""):
                if node.multi_mode == MULTI_SEQUENTIAL:
                    out.add((inst_id, node.seq))
        except (ValueError, TypeError, KeyError, AttributeError, json.JSONDecodeError):
            continue   # snapshot hỏng: coi như không tuần tự (tính từ lúc tạo việc)
    return out


def approval_metrics(tasks: list, siblings: list, instances: list, emp_user: dict, utc_lo: datetime,
                     utc_hi: datetime) -> dict[int, Partial]:
    """Tới lượt → xử lý (giờ lịch). Bước "lần lượt" tạo sẵn việc ở trạng thái chờ nên mốc "tới lượt" của người sau
    là lúc người liền trước quyết định (chỉ áp cho bước đọc được là tuần tự trong `flow_snapshot`)."""
    sequential = _sequential_nodes(instances)
    prior: dict[tuple, list] = defaultdict(list)
    for inst, node, order, decided in siblings:
        if decided:
            prior[(inst, node)].append((order, decided))
    waits: dict[int, list[float]] = defaultdict(list)
    pending: dict[int, int] = defaultdict(int)
    for _id, inst, node, order, emp, status, created, decided in tasks:
        uid = emp_user.get(emp)
        if uid is None:
            continue
        if status == TASK_PENDING:
            pending[uid] += 1
            continue
        if status not in (TASK_APPROVED, TASK_REJECTED) or not decided or not (utc_lo <= decided < utc_hi):
            continue
        turn = created
        if (inst, node) in sequential and order > 1:
            before = [d for o, d in prior[(inst, node)] if o < order and d <= decided]
            if before:
                turn = max(turn, max(before))
        waits[uid].append(max(0.0, (decided - turn).total_seconds() / 3600))
    out: dict[int, Partial] = {}
    for uid in set(waits) | set(pending):
        p, ws = Partial(), waits.get(uid, [])
        p.put("approval_wait_p50_h", median(ws) if len(ws) >= MIN_TASKS else None, Why.BELOW_THRESHOLD)
        p.put("approval_wait_p90_h", percentile(ws, 0.9) if len(ws) >= MIN_TASKS else None, Why.BELOW_THRESHOLD)
        p.put("pending_now", pending.get(uid, 0))
        p.counts["tasks_decided"] = len(ws)
        out[uid] = p
    return out


def batch_approval_share(decisions: list) -> dict[int, Partial]:
    """Tỷ lệ quyết định nằm trong cụm ≥ 5 quyết định / 10 phút (đánh dấu bằng mảng hiệu, O(n))."""
    by_user: dict[int, list[datetime]] = defaultdict(list)
    for uid, at in decisions:
        by_user[uid].append(at)
    out: dict[int, Partial] = {}
    for uid, stamps in by_user.items():
        stamps.sort()
        diff = [0] * (len(stamps) + 1)
        left = 0
        for right, ts in enumerate(stamps):
            while ts - stamps[left] > BATCH_WINDOW:
                left += 1
            if right - left + 1 >= BATCH_MIN_SIZE:
                diff[left] += 1
                diff[right + 1] -= 1
        covered, run = 0, 0
        for i in range(len(stamps)):
            run += diff[i]
            covered += 1 if run > 0 else 0
        p = Partial()
        p.put("batch_approval_share", ratio(covered, len(stamps)))
        p.counts["decisions_logged"] = len(stamps)
        out[uid] = p
    return out


def notification_metrics(notifs: list, mentions: list, replies: list) -> dict[int, Partial]:
    per: dict[int, list] = defaultdict(list)
    for uid, is_read, created, read_at in notifs:
        per[uid].append((is_read, created, read_at))
    out: dict[int, Partial] = defaultdict(Partial)
    for uid, rows in per.items():
        p = out[uid]
        p.put("notif_read_rate", ratio(sum(1 for r in rows if r[0]), len(rows)) if len(rows) >= MIN_NOTIFS else None,
              Why.BELOW_THRESHOLD)
        mins = [(r[2] - r[1]).total_seconds() / 60 for r in rows if r[2]]
        p.put("notif_read_p50_min", median(mins) if mins else None, Why.NOT_COLLECTED)
    first_reply: dict[tuple, list[datetime]] = defaultdict(list)
    for uid, entity, entity_id, at in replies:
        first_reply[(uid, entity, entity_id)].append(at)
    delays: dict[int, list[float]] = defaultdict(list)
    for uid, entity, entity_id, at in mentions:
        later = [t for t in first_reply.get((uid, entity, entity_id), ()) if t > at]
        if later:
            delays[uid].append((min(later) - at).total_seconds() / 3600)
    for uid, ds in delays.items():
        out[uid].put("mention_reply_p50_h", median(ds) if len(ds) >= MIN_MENTIONS else None, Why.BELOW_THRESHOLD)
    return out


def work_task_metrics(work_tasks: list, emp_user: dict, window_end: date) -> dict[int, Partial]:
    per: dict[int, dict] = defaultdict(lambda: {"done": 0, "on_time": 0, "overdue": 0})
    for emp, due, completed, status in work_tasks:
        uid = emp_user.get(emp)
        if uid is None:
            continue
        if completed is not None:
            per[uid]["done"] += 1
            #  `completed_at` lưu UTC, `due_date` là ngày VN → đổi sang ngày VN trước khi so (việc xong 00:00–06:59 VN
            #  ngày D+1 nằm ở ngày D theo UTC nên trước đây bị tính "đúng hạn").
            per[uid]["on_time"] += 1 if (completed + VN_OFFSET).date().isoformat() <= due else 0
        elif due < window_end.isoformat():   # "quá hạn" tính tại CUỐI cửa sổ (loại trừ), không phải hôm nay → dựng lại tuần cũ ra cùng số
            per[uid]["overdue"] += 1
    out: dict[int, Partial] = {}
    for uid, s in per.items():
        p = Partial()
        p.put("work_on_time_rate", ratio(s["on_time"], s["done"]))
        p.put("work_overdue_open", s["overdue"])
        out[uid] = p
    return out
