"""Đường đi A→B→C giữa các màn (thuần) — duoc-CR-641, phase 04.

Chuỗi PAGE_VIEW tách theo (user, session_id, tab_key): mở nhiều tab xen kẽ KHÔNG tạo bộ ba giả. Bước lặp liền nhau
(F5, đổi bộ lọc trong cùng màn) gộp làm một. "Vòng" = A→B→A (a == c, b ≠ a). Chỉ dùng được trong 90 ngày (sự kiện thô).
"""
from collections import Counter, defaultdict

from app.core.usage_codes import UnmeasuredReason as Why

from .metric_partial import Partial
from .metric_stats import ratio

MIN_TRIPLES = 10
TOP_PATHS = 5


def path_metrics(pageviews: list) -> dict[int, Partial]:
    """pageviews: [(user_id, session_id, tab_key, occurred_at, route)] đã sắp theo thời gian."""
    seqs: dict[tuple, list[str]] = defaultdict(list)
    for uid, session, tab, _at, route in pageviews:
        seq = seqs[(uid, session, tab)]
        if not seq or seq[-1] != route:
            seq.append(route)
    triples: dict[int, Counter] = defaultdict(Counter)
    for (uid, _s, _t), seq in seqs.items():
        for a, b, c in zip(seq, seq[1:], seq[2:]):
            triples[uid][(a, b, c)] += 1
    out: dict[int, Partial] = {}
    for uid, counter in triples.items():
        total = sum(counter.values())
        loops = sum(n for (a, b, c), n in counter.items() if a == c and a != b)
        p = Partial()
        p.lists["top_paths"] = [[a, b, c, n] for (a, b, c), n in counter.most_common(TOP_PATHS)]
        p.put("loop_share", ratio(loops, total) if total >= MIN_TRIPLES else None, Why.BELOW_THRESHOLD)
        p.counts["path_triples"] = total
        out[uid] = p
    return out
