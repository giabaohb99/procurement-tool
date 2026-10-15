"""Chạy bộ hội thoại mẫu của lõi mới (ai-CR-203, doc/agent-hub/20 §7 + §10 việc 3).

Chạy TRONG container agent-hub ở máy dev (cần khóa model thật của chat chủ bot + ERP dev để đọc):
    docker exec agent-hub-agent-api-1 python scripts/eval_core_v2.py              # cả 20 mẫu, có model chấm
    docker exec agent-hub-agent-api-1 python scripts/eval_core_v2.py --only 03 05  # vài mẫu
    docker exec agent-hub-agent-api-1 python scripts/eval_core_v2.py --no-judge    # chỉ luật cứng (rẻ hơn)

Không ghi gì thật (xem `core_eval`): ghi nháp, công cụ ghi, hoàn tác, vé sửa mã chỉ được ghi sổ; tin của chat thử bị xóa
sau mỗi mẫu. Tốn tiền model: khoảng 30 lượt gọi + 20 lượt chấm mỗi lần chạy đủ.
Mã thoát 0 = đạt hết, 1 = có mẫu trượt, 2 = chưa có --yes (chỉ in ước chi phí).

LUẬT (đại ca 15/10 chiều, sau khi ví trạm bị trừ 27 USD / ngày): chỉ chạy khi ĐẠI CA GẬT từng lần; sửa phần nào chạy
--only các mẫu liên quan; chạy đủ 20 mẫu chỉ khi đổi lõi lớn. Không có --yes thì script chỉ in ước chi phí rồi thoát.
"""
import argparse
import json
import sys
import time


#  Ước thô theo số đo 15/10: mỗi lượt ~80k token vào (trong đó ~20k ghi bộ đệm) + ~500 ra; mỗi lượt chấm ~6k vào.
EST_TURN_IN, EST_TURN_WRITE, EST_TURN_OUT, EST_JUDGE_IN = 80_000, 20_000, 500, 6_000


def estimate(samples, *, judge: bool) -> str:
    from app.modules.agent_hub import core_v2
    from app.modules.agent_hub.constants import estimate_cost_usd

    turns = sum(len(s.turns) for s in samples)
    model = core_v2.lane_model(core_v2.LANE_NORMAL) or "claude-sonnet-5-5"
    cost = estimate_cost_usd(model, turns * EST_TURN_IN, turns * EST_TURN_OUT, cache_write=turns * EST_TURN_WRITE)
    if judge:
        cost += estimate_cost_usd(model, len(samples) * EST_JUDGE_IN, len(samples) * 100)
    return (f"Ước: {len(samples)} mẫu · {turns} lượt · model luồng thường {model} · khoảng {cost:.2f} USD "
            "(ước thô; việc nặng đi Sonnet đắt hơn).")


def main() -> int:
    ap = argparse.ArgumentParser(description="Bộ hội thoại mẫu lõi v2")
    ap.add_argument("--only", nargs="*", help="Mã mẫu cần chạy (vd 03 05)")
    ap.add_argument("--no-judge", action="store_true", help="Bỏ model chấm, chỉ luật cứng")
    ap.add_argument("--json", help="Ghi kết quả chi tiết ra tệp JSON")
    ap.add_argument("--yes", action="store_true", help="Đã được đại ca gật — chạy thật (tốn tiền model)")
    args = ap.parse_args()

    import app.core.all_models  # noqa: F401  — nạp đủ model trước khi đụng DB (User ↔ StoredFile…)
    from app.core.database import SessionLocal
    from app.modules.agent_hub import core_eval
    from app.modules.agent_hub.core_eval_samples import SAMPLES
    from app.modules.agent_hub.timeutil import now_local

    samples = [s for s in SAMPLES if not args.only or s.id in args.only]
    print(estimate(samples, judge=not args.no_judge))
    if not args.yes:
        print("Chưa chạy: thêm --yes khi đại ca đã gật lần chạy này.")
        return 2
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
