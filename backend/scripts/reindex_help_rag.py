# -*- coding: utf-8 -*-
"""Nạp chỉ mục vector cho HDSD + FAQ — CHẠY TAY, ngay trong tiến trình, không qua celery.

Vì sao có script này (bao-CR-451). Hook nạp chỉ mục bắn từ *service* của Trung tâm trợ giúp,
còn mọi script seed bài HDSD ghi thẳng ORM — bài do seed dựng ra vì thế KHÔNG BAO GIỜ vào kho
vector, trợ lý AI trả lời như thể bài đó không tồn tại. Rà ngày 21/09/2026 trên máy chủ thử
nghiệm thấy kho chỉ có 55/87 bài, và 32 bài hụt đúng là 32 bài do seed dựng. Chạy seed xong
thì chạy tiếp script này là xong chuyện.

Khác nút bấm ở màn *Cấu hình hệ thống* → tab *Trợ lý AI*: nút kia xếp hàng cho celery-worker
(tiện, nhưng cần worker sống và nhìn kết quả phải mở log worker). Script này nhúng ngay tại
chỗ và in từng dòng ra màn hình, nên dùng được cả khi worker chết và biết chính xác bài nào
hỏng. Hai đường dùng chung một hàm `indexer.reindex_source`, không có bản chép thứ hai.

Chạy trong container api:
    # nạp bù phần còn thiếu (mặc định) — rẻ, chạy lại vô hại
    docker compose exec -T api python scripts/reindex_help_rag.py
    # xem sẽ nạp gì mà không gọi mạng
    docker compose exec -T api python scripts/reindex_help_rag.py --dry-run
    # dựng lại toàn bộ: chỉ khi đổi model nhúng hoặc nghi kho lệch nội dung
    docker compose exec -T api python scripts/reindex_help_rag.py --all

Chạy lại vô hại: point id tất định theo (nguồn, id, số thứ tự đoạn) nên nạp đè đúng chỗ.

Bẫy đã gặp. Khóa Gemini có trần request/phút — nạp 32 bài liền tay là dính 429 ở bài cuối.
Vì thế mặc định NGHỈ giữa hai nguồn và thử lại có giãn cách khi lỗi; đừng hạ `--sleep` về 0
trên môi trường thật trừ khi đang nạp vài bài lẻ.
"""
import argparse
import sys
import time

sys.path.insert(0, "/app")

import app.core.all_models  # noqa: E402,F401 — đăng ký mapper trước khi mở session
from app.core.config import settings  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.modules.assistant.rag import indexer  # noqa: E402

LABELS = {indexer.SRC_HELP: "bài HDSD", indexer.SRC_FAQ: "câu FAQ"}


def parse_args():
    p = argparse.ArgumentParser(description="Nạp chỉ mục vector cho HDSD + FAQ (chạy tay)")
    p.add_argument("--all", action="store_true",
                   help="Dựng lại TOÀN BỘ thay vì chỉ nạp bù phần thiếu")
    p.add_argument("--dry-run", action="store_true",
                   help="Chỉ liệt kê sẽ nạp gì, không gọi nhúng, không ghi kho")
    p.add_argument("--sleep", type=float, default=2.0,
                   help="Giây nghỉ giữa hai nguồn, tránh chạm trần request/phút (mặc định 2)")
    p.add_argument("--retry", type=int, default=4,
                   help="Số lần thử mỗi nguồn khi lỗi (mặc định 4)")
    p.add_argument("--retry-wait", type=float, default=35.0,
                   help="Giây chờ trước khi thử lại (mặc định 35 — đủ qua một cửa sổ 429)")
    return p.parse_args()


def index_one(db, source, source_id, args):
    """Nạp một nguồn, thử lại khi lỗi. Trả số đoạn, hoặc None nếu thua hẳn."""
    for attempt in range(1, max(1, args.retry) + 1):
        try:
            return indexer.reindex_source(db, source, source_id)
        except Exception as e:  # noqa: BLE001 — một bài hỏng không được làm đứt cả mẻ
            last = attempt >= max(1, args.retry)
            print(f"    lỗi lần {attempt}/{args.retry}: {e}", flush=True)
            if last:
                return None
            time.sleep(args.retry_wait)
    return None


def main():
    args = parse_args()
    if not settings.AI_RAG_ENABLED:
        print("AI_RAG_ENABLED đang tắt — bật cờ đó rồi chạy lại.")
        return 1

    db = SessionLocal()
    try:
        stats = indexer.index_status(db)
        print(f"Kho vector hiện có: {stats['help_indexed']}/{stats['help_total']} bài HDSD, "
              f"{stats['faq_indexed']}/{stats['faq_total']} câu FAQ, "
              f"thừa {stats['orphans']} nguồn đã xóa dưới DB.")

        refs = indexer.all_source_refs(db) if args.all else indexer.missing_source_refs(db)
        mode_label = "TOÀN BỘ" if args.all else "phần còn thiếu"
        print(f"Sẽ nạp {mode_label}: {len(refs)} nguồn.")
        if not refs:
            print("Không có gì phải nạp.")
            return 0

        if args.dry_run:
            for source, source_id in refs:
                print(f"  (thử) {LABELS.get(source, source)} #{source_id}")
            print("Chạy thử, chưa nạp gì.")
            return 0

        ok = failed = chunks = 0
        for i, (source, source_id) in enumerate(refs, start=1):
            print(f"  [{i}/{len(refs)}] {LABELS.get(source, source)} #{source_id} ...",
                  end=" ", flush=True)
            n = index_one(db, source, source_id, args)
            if n is None:
                failed += 1
                print("THUA")
            else:
                ok += 1
                chunks += n
                print(f"{n} đoạn")
            if i < len(refs) and args.sleep > 0:
                time.sleep(args.sleep)

        after = indexer.index_status(db)
        print(f"Xong: {ok} nguồn nạp được ({chunks} đoạn), {failed} nguồn thua.")
        print(f"Kho vector sau khi nạp: {after['help_indexed']}/{after['help_total']} bài HDSD, "
              f"{after['faq_indexed']}/{after['faq_total']} câu FAQ.")
        # Thua nguồn nào thì trả mã lỗi: chạy trong kịch bản deploy còn biết mà dừng lại.
        return 1 if failed else 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
