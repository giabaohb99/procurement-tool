"""bao-CR-718: đo các câu của màn Tra cứu thị trường trên bảng thử ~328 nghìn dòng (MySQL 8.4 riêng).

Chạy trong image api trỏ vào MySQL thử (DB_HOST...), có Redis (REDIS_URL):  python do-toc-do.py [nhan] [--explain]
In: thời gian (ms, lấy trung vị 3 lần sau 1 lần làm nóng) cho từng đường + EXPLAIN của câu chậm.
"""
import statistics
import sys
import time

from sqlalchemy import func, text

import app.main  # noqa: F401  (đăng ký đủ model)
from app.core.database import SessionLocal
from app.modules.customs import service
from app.modules.customs.model import CustomsLine
from app.modules.customs.search_service import build_keyword_condition

LABEL = sys.argv[1] if len(sys.argv) > 1 else "truoc"
PAGE = 50
db = SessionLocal()


def timed(fn, n=3):
    fn()
    ts = []
    for _ in range(n):
        t = time.perf_counter()
        fn()
        ts.append((time.perf_counter() - t) * 1000)
    return statistics.median(ts)


def base_filters(**kw):
    f = {k: "" for k in ("q", "ingredient", "hs_code", "formulation", "origin", "unit", "currency", "incoterm",
                         "price_min", "price_max", "qty_min", "qty_max", "rate_min", "rate_max", "date_from", "date_to")}
    f.update({"importer_id": [], "partner_id": [], "batch_id": [], "product_kind": []})
    f.update(kw)
    return f


top_imp = db.execute(text("select importer_id from tab_customs_line group by importer_id order by count(*) desc limit 1")).scalar()
SCEN = {
    "mo-man (khong loc)": base_filters(),
    "q=abamectin": base_filters(q="abamectin"),
    "q=abamectin 3.6 -TC": base_filters(q="abamectin 3.6 -TC"),
    "q=glyphosate + 2025": base_filters(q="glyphosate", date_from="2025-01-01", date_to="2025-12-31"),
    "hs=3808": base_filters(hs_code="3808"),
    "importer top": base_filters(importer_id=[str(top_imp)]),
    "nam 2025": base_filters(date_from="2025-01-01", date_to="2025-12-31"),
    "kind=2": base_filters(product_kind=["2"]),
    "q=xyzkhongco": base_filters(q="xyzkhongco"),
}

print(f"## {LABEL} — {db.execute(text('select count(*) from tab_customs_line')).scalar()} dòng")
print("| Kịch bản | đếm total (ms) | trang 1 (ms) | trang 100 (ms) | list_lines lần đầu (ms) | list_lines lật trang (ms) |")
print("|---|---|---|---|---|---|")
import redis
from app.core.config import settings
R = redis.Redis.from_url(settings.REDIS_URL)


def cold(fn):
    R.flushall()
    t = time.perf_counter()
    fn()
    return (time.perf_counter() - t) * 1000
for name, f in SCEN.items():
    cnt = timed(lambda: service.apply_line_filters(db.query(func.count(CustomsLine.id)), f).scalar())
    p1 = timed(lambda: service.apply_line_filters(db.query(CustomsLine), f)
               .order_by(CustomsLine.reg_date.desc(), CustomsLine.id.desc()).limit(PAGE).all())
    p100 = timed(lambda: service.apply_line_filters(db.query(CustomsLine), f)
                 .order_by(CustomsLine.reg_date.desc(), CustomsLine.id.desc()).offset(99 * PAGE).limit(PAGE).all(), n=1)
    first = cold(lambda: service.list_lines(db, f, 0, PAGE))
    full = timed(lambda: service.list_lines(db, f, PAGE, PAGE))
    print(f"| {name} | {cnt:.0f} | {p1:.0f} | {p100:.0f} | {first:.0f} | {full:.0f} |")

print()
print("| Đường mở màn | ms |")
print("|---|---|")
print(f"| /coverage | {timed(lambda: service.get_coverage(db)):.0f} |")
print(f"| /options lần đầu | {cold(lambda: service.list_options(db)):.0f} |")
print(f"| /options lần sau | {timed(lambda: service.list_options(db)):.0f} |")
print(f"| /parties q=cong | {timed(lambda: service.search_parties(db, 1, 'cong')):.0f} |")
print(f"| /alerts q=abamectin | {timed(lambda: service.match_alerts(db, base_filters(q='abamectin'))):.0f} |")
print(f"| /stats q=abamectin | {timed(lambda: service.compute_stats(db, base_filters(q='abamectin'), 'month', 'adjusted')):.0f} |")
print(f"| /importers q=abamectin | {timed(lambda: service.rank_importers(db, base_filters(q='abamectin'))):.0f} |")

if "--explain" in sys.argv:
    def sql(q):
        return str(q.statement.compile(db.bind, compile_kwargs={"literal_binds": True}))
    for name in ("mo-man (khong loc)", "q=abamectin"):
        f = SCEN[name]
        for title, q in (("count", service.apply_line_filters(db.query(func.count(CustomsLine.id)), f)),
                         ("page", service.apply_line_filters(db.query(CustomsLine.id), f)
                          .order_by(CustomsLine.reg_date.desc(), CustomsLine.id.desc()).limit(PAGE))):
            print(f"\n### EXPLAIN {name} / {title}")
            for r in db.execute(text("EXPLAIN ANALYZE " + sql(q))).all():
                print(r[0][:1500])
