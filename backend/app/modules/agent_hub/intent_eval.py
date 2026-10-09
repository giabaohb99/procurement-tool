"""Đo độ đúng của hiểu ý định (ai-CR-138, phase 13.6). Lõi tính toán — CLI ở `scripts/intent_eval.py`.

Ba phép đo:
  1. Bộ câu mẫu CỐ ĐỊNH (`test/backend/data/intent_samples.json`) chạy qua bộ phân loại thật → tỷ lệ đúng. Đổi model /
     luật mà tụt dưới `min_accuracy` là chặn (bài kiểm chạy khi có AI_EVAL=1 và khóa AI).
  2. Gắn nhãn tay: xuất ~200 câu thật trên DEV (nhãn máy + đối tượng + nguyên văn lấy qua `message_id` — tệp xuất CHỈ để
     trên máy dev, không commit), người gắn điền cột `true_intent` / `true_sub`, rồi chấm → độ đúng nhãn lớn, nhãn con.
  3. Tỷ lệ «phải hỏi lại» trước / sau một mốc (vd ngày bật 13.5), theo kênh.
"""
from __future__ import annotations

import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import intent_ledger as il
from .model import AgentIntent, AgentMessage

EXPORT_FIELDS = ("ledger_id", "created_at", "channel", "text", "intent", "sub_intent", "entities", "outcome",
                 "true_intent", "true_sub", "entities_ok")


def samples_path() -> Path:
    here = Path(__file__).resolve()
    for base in here.parents:
        p = base / "test" / "backend" / "data" / "intent_samples.json"
        if p.exists():
            return p
    raise FileNotFoundError("không thấy test/backend/data/intent_samples.json")


def load_samples(path: Path | None = None) -> dict:
    data = json.loads((path or samples_path()).read_text(encoding="utf-8"))
    for s in data["samples"]:
        if s["intent"] not in il.INTENT_CODES.values():
            raise ValueError(f"nhãn lạ trong bộ mẫu: {s['intent']!r}")
    return data


def run_fixed(classify, data: dict | None = None) -> dict:
    """`classify(text, context, tasks) -> nhãn lớn`. Trả {total, correct, accuracy, misses: [(câu, mong, ra)]}."""
    data = data or load_samples()
    misses = []
    for s in data["samples"]:
        got = classify(s["text"], s.get("context", ""), data["tasks"] if s.get("tasks") else "")
        if got != s["intent"]:
            misses.append((s["text"], s["intent"], got))
    total = len(data["samples"])
    correct = total - len(misses)
    return {"total": total, "correct": correct, "accuracy": round(correct / total, 3) if total else 0.0,
            "min_accuracy": data.get("min_accuracy", 0.0), "misses": misses}


def _question_text(db: Session, row: AgentIntent) -> str:
    if not row.message_id:
        return ""
    if row.channel == il.Channel.WEB:
        from app.modules.assistant.model import AssistantMessage

        msg = db.get(AssistantMessage, int(row.message_id))
        return (msg.content or "") if msg is not None else ""
    msg = db.get(AgentMessage, int(row.message_id))
    return (msg.body or "") if msg is not None else ""


def export_rows(db: Session, *, days: int = 30, limit: int = 200, seed: int = 0) -> list[dict]:
    """Lấy ngẫu nhiên tối đa `limit` dòng sổ có con trỏ tin. Kèm nguyên văn — CHỈ dùng trên dev để gắn nhãn tay."""
    since = datetime.utcnow() - timedelta(days=days)
    rows = list(db.scalars(select(AgentIntent).where(AgentIntent.created_at >= since, AgentIntent.message_id > 0)))
    random.Random(seed).shuffle(rows)
    out = []
    for r in rows[:limit]:
        out.append({"ledger_id": r.id, "created_at": r.created_at.isoformat() if r.created_at else "",
                    "channel": il.Channel(r.channel).name.lower() if r.channel in il.Channel._value2member_map_ else "",
                    "text": " ".join(_question_text(db, r).split())[:1000],
                    "intent": il.INTENT_CODES.get(il.Intent(r.intent), "") if r.intent in il.Intent._value2member_map_
                    else "",
                    "sub_intent": il.sub_code(r.sub_intent),
                    "entities": json.dumps(r.entities or [], ensure_ascii=False), "outcome": r.outcome,
                    "true_intent": "", "true_sub": "", "entities_ok": ""})
    return out


def write_csv(rows: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=EXPORT_FIELDS)
        w.writeheader()
        w.writerows(rows)


def score_rows(rows: list[dict]) -> dict:
    """Chấm tệp đã gắn nhãn tay. Dòng để trống `true_*` thì không tính ở phép đo đó."""
    def rate(pairs):
        pairs = [(a, b) for a, b in pairs if b]
        ok = sum(1 for a, b in pairs if a == b)
        return {"labelled": len(pairs), "correct": ok, "accuracy": round(ok / len(pairs), 3) if pairs else None}

    big = rate([(r.get("intent", ""), (r.get("true_intent") or "").strip()) for r in rows])
    sub = rate([(r.get("sub_intent", ""), (r.get("true_sub") or "").strip()) for r in rows])
    ent = [str(r.get("entities_ok") or "").strip().lower() for r in rows]
    ent = [x for x in ent if x]
    confusion: dict[str, int] = {}
    for r in rows:
        t = (r.get("true_intent") or "").strip()
        if t and t != r.get("intent"):
            key = f"{t} -> {r.get('intent')}"
            confusion[key] = confusion.get(key, 0) + 1
    return {"intent": big, "sub": sub,
            "entities": {"labelled": len(ent), "ok": sum(1 for x in ent if x in ("1", "y", "yes", "co", "có", "dung",
                                                                                 "đúng"))},
            "confusion": sorted(confusion.items(), key=lambda x: -x[1])[:10]}


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def clarify_rates(db: Session, *, pivot: datetime, days: int = 14) -> dict:
    """Tỷ lệ câu bot phải hỏi lại trong `days` ngày TRƯỚC và SAU mốc `pivot`, theo kênh."""
    out: dict[str, dict] = {}
    for label, start, end in (("truoc", pivot - timedelta(days=days), pivot), ("sau", pivot, pivot + timedelta(days=days))):
        rows = db.scalars(select(AgentIntent).where(AgentIntent.created_at >= start, AgentIntent.created_at < end))
        stats: dict[str, list[int]] = {}
        for r in rows:
            ch = il.Channel(r.channel).name.lower() if r.channel in il.Channel._value2member_map_ else "khac"
            s = stats.setdefault(ch, [0, 0])
            s[0] += 1
            s[1] += int(r.outcome == il.Outcome.CLARIFY)
        out[label] = {ch: {"total": t, "clarify": c, "rate": round(c / t, 3) if t else None}
                      for ch, (t, c) in sorted(stats.items())}
    return out
