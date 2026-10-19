"""Chỉ số đếm gọn từ các bảng phụ (tùy chỉnh đã lưu, bình luận, trợ lý AI, phiếu hỗ trợ, nhập tệp, xuất tệp) — duoc-CR-641, phase 04.

Chỉ ĐẾM, không đọc nội dung bình luận / tin nhắn trợ lý / tiêu đề phiếu (§7.4: snapshot chỉ chứa số và mã).
"""
from collections import defaultdict

from app.core.usage_codes import UnmeasuredReason as Why

from .metric_partial import Partial
from .metric_stats import ratio
from .snapshot_metrics_rhythm import export_spike
from .snapshot_sources import SnapshotSources


def misc_metrics(src: SnapshotSources, uid: int, employee_id: int, rows: list, old_rows: list) -> Partial:
    p = Partial()
    p.put("saved_prefs", src.prefs.get(uid, 0))
    p.put("comments", src.comments.get(uid, 0))
    p.put("assistant_questions", src.assistant_q.get(uid, 0))
    p.put("assistant_changes", src.assistant_chg.get(uid, 0))
    p.put("tickets", src.tickets.get(employee_id, 0) if employee_id else 0)
    batches, total, errors = src.imports.get(uid, (0, 0, 0))
    p.put("imports", batches)
    p.put("import_error_rate", ratio(errors, total))
    spike, _ = export_spike(rows, old_rows, src.window.lo, src.window.week_start)
    p.put("export_rows_spike", spike, Why.BELOW_THRESHOLD)
    return p


def export_entity_weeks(src: SnapshotSources) -> dict[int, int]:
    """{user_id: số tuần (trong W) nhiều nhất mà người đó xuất CÙNG MỘT entity}."""
    weeks: dict[tuple, set] = defaultdict(set)
    for uid, entity, created in src.export_entities:
        weeks[(uid, entity)].add((created - src.window.utc_lo).days // 7)
    best: dict[int, int] = defaultdict(int)
    for (uid, _entity), ws in weeks.items():
        best[uid] = max(best[uid], len(ws))
    return best
