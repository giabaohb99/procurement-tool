"""Chạy bộ hội thoại mẫu của lõi mới (ai-CR-203, doc/agent-hub/20 §7 + §10 việc 3).

Chạy TRONG container agent-hub ở máy dev (cần khóa model thật của chat chủ bot + ERP dev để đọc):
    docker exec agent-hub-agent-api-1 python scripts/eval_core_v2.py              # cả 20 mẫu, có model chấm
    docker exec agent-hub-agent-api-1 python scripts/eval_core_v2.py --only 03 05  # vài mẫu
    docker exec agent-hub-agent-api-1 python scripts/eval_core_v2.py --no-judge    # chỉ luật cứng (rẻ hơn)

Không ghi gì thật (xem `core_eval`): ghi nháp, công cụ ghi, hoàn tác, vé sửa mã chỉ được ghi sổ; tin của chat thử bị xóa
sau mỗi mẫu. Tốn tiền model: khoảng 30 lượt gọi + 20 lượt chấm mỗi lần chạy đủ.
Mã thoát 0 = đạt hết, 1 = có mẫu trượt.
"""
import argparse
import json
import sys
import time


def main() -> int:
    ap = argparse.ArgumentParser(description="Bộ hội thoại mẫu lõi v2")
    ap.add_argument("--only", nargs="*", help="Mã mẫu cần chạy (vd 03 05)")
    ap.add_argument("--no-judge", action="store_true", help="Bỏ model chấm, chỉ luật cứng")
    ap.add_argument("--json", help="Ghi kết quả chi tiết ra tệp JSON")
    args = ap.parse_args()

    import app.core.all_models  # noqa: F401  — nạp đủ model trước khi đụng DB (User ↔ StoredFile…)
    from app.core.database import SessionLocal
    from app.modules.agent_hub import core_eval
    from app.modules.agent_hub.core_eval_samples import SAMPLES
    from app.modules.agent_hub.timeutil import now_local

    samples = [s for s in SAMPLES if not args.only or s.id in args.only]
    db = SessionLocal()
    try:
        chat, user = core_eval.owner_context(db)
        tag = time.strftime("%m%d%H%M")
        results = []
        for s in samples:
            print(f"... mẫu {s.id} {s.title}", flush=True)
            results.append(core_eval.run_sample(db, s, owner_chat=chat, owner_user=user, tag=tag, today=now_local().date(),
                                                use_judge=not args.no_judge))
    finally:
        db.close()
    print(core_eval.report(results))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump([core_eval.as_dict(r) for r in results], f, ensure_ascii=False, indent=1, default=str)
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
