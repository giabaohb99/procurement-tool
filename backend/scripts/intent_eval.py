"""Đo hiểu ý định của bot (ai-CR-138, phase 13.6). Chạy trong container api / agent-api:

    python scripts/intent_eval.py fixed                       # bộ câu mẫu cố định qua bộ phân loại thật (cần khóa AI)
    python scripts/intent_eval.py export --out /tmp/y.csv     # ~200 câu thật để gắn nhãn tay — CHỈ trên dev, không commit
    python scripts/intent_eval.py score --file /tmp/y.csv     # chấm tệp đã điền true_intent / true_sub / entities_ok
    python scripts/intent_eval.py clarify --pivot 2026-10-10  # tỷ lệ «phải hỏi lại» 14 ngày trước / sau mốc

Lõi tính toán ở `app/modules/agent_hub/intent_eval.py`.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal  # noqa: E402
from app.modules.agent_hub import intent_eval  # noqa: E402


def _fixed(db) -> int:
    from app.modules.agent_hub import manager, user_keys

    def classify(text, context, tasks):
        try:
            return manager.run_intent(text, context=context, tasks=tasks)[0]["intent"]
        except Exception as e:  # noqa: BLE001
            return f"loi: {str(e)[:60]}"

    with user_keys.for_admin(db):
        if not user_keys.active_key():
            print("Chưa có khóa AI cho chat chủ bot — không chạy được bộ mẫu.")
            return 2
        res = intent_eval.run_fixed(classify)
    print(f"Đúng {res['correct']}/{res['total']} = {res['accuracy']:.1%} (ngưỡng {res['min_accuracy']:.0%})")
    for text, want, got in res["misses"]:
        print(f"  SAI  «{text}»  mong {want}, ra {got}")
    return 0 if res["accuracy"] >= res["min_accuracy"] else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fixed")
    p = sub.add_parser("export")
    p.add_argument("--out", required=True)
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--limit", type=int, default=200)
    p = sub.add_parser("score")
    p.add_argument("--file", required=True)
    p = sub.add_parser("clarify")
    p.add_argument("--pivot", required=True, help="YYYY-MM-DD")
    p.add_argument("--days", type=int, default=14)
    args = ap.parse_args()

    db = SessionLocal()
    try:
        if args.cmd == "fixed":
            return _fixed(db)
        if args.cmd == "export":
            rows = intent_eval.export_rows(db, days=args.days, limit=args.limit)
            intent_eval.write_csv(rows, Path(args.out))
            print(f"Đã xuất {len(rows)} câu vào {args.out}. Tệp có NGUYÊN VĂN câu hỏi: giữ trên máy dev, gắn nhãn xong thì xóa.")
            return 0
        if args.cmd == "score":
            print(json.dumps(intent_eval.score_rows(intent_eval.read_csv(Path(args.file))), ensure_ascii=False, indent=2))
            return 0
        pivot = datetime.strptime(args.pivot, "%Y-%m-%d")
        print(json.dumps(intent_eval.clarify_rates(db, pivot=pivot, days=args.days), ensure_ascii=False, indent=2))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
