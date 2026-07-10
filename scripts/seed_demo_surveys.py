# -*- coding: utf-8 -*-
"""Tạo 3 phiếu khảo sát mẫu (nháp, đầy đủ dòng) — chạy TRONG container api:
   docker compose exec -T api python - < scripts/seed_demo_surveys.py
"""
import app.main  # noqa: F401
from sqlalchemy import text
from app.core.database import SessionLocal
from app.modules.survey.schema import SurveyCreate, SupplierLineIn, ProductLineIn
from app.modules.survey import service as ss

db = SessionLocal()
SUP = [(r[0], r[1]) for r in db.execute(text("select code,name from tab_supplier where is_active=1 limit 5")).all()]
if not SUP:
    SUP = [("NCC-A", "Nhà cung cấp A"), ("NCC-B", "Nhà cung cấp B"), ("NCC-C", "Nhà cung cấp C")]
GROUPS = [r[0] for r in db.execute(text("select name from tab_item_group limit 3")).all()] or ["Nhãn", "Nhãn Metalize", "Nhãn Thùng"]
UNITS = [r[0] for r in db.execute(text("select name from tab_unit limit 3")).all()] or ["Cái", "Bộ", "Kg"]
# NSPT phụ trách = nhân sự phòng Thu mua (dept 20 = "Sản xuất -Thu mua"; fallback: nhân viên bất kỳ)
EMP = [r[0] for r in db.execute(text("select full_name from tab_employee where department_id=20 and coalesce(full_name,'')<>'' order by id limit 5")).all()] \
    or [r[0] for r in db.execute(text("select full_name from tab_employee where coalesce(full_name,'')<>'' and id>2 order by id limit 5")).all()] \
    or ["Nhân viên thu mua"]


def sup_line(k):
    c, n = SUP[k % len(SUP)]
    return SupplierLineIn(
        contact_date="2026-07-01", reply_date="2026-07-03", result_date="2026-07-05",
        supplier_code=c, supplier_name=n, tax_code="030112%02d00" % k,
        reg_address="So %d KCN Tan Tao, TP.HCM" % (10 + k), warehouse_address="Kho %d, Long An" % (k + 1),
        google_maps="https://maps.google.com/?q=demo", contact_person="A. Tuan %d" % (k + 1),
        contact_phone="090%d123456" % (k % 10), supply_group="Bao bi giay",
        quote_folder="https://drive.google.com/demo", source_of_information="Gioi thieu",
        production_tech="In flexo 6 mau", production_time="7-10 ngay",
        nvkd_eval="NCC uy tin, phan hoi nhanh", invoice_policy="VAT day du", reliability="Cao",
        delivery_policy="Giao tan kho", debt_policy="Cong no 30 ngay", defect_return="Doi tra trong 7 ngay",
        nspt_note="Dat yeu cau", nspt_reason="", line_approve="Chờ duyệt", line_approve_note="", note="NCC demo")


def prod_line(k):
    c, _ = SUP[k % len(SUP)]
    return ProductLineIn(
        contact_date="2026-07-01", reply_date="2026-07-03", result_date="2026-07-05",
        supplier_code=c, internal_code="VTBB-%d" % (100 + k), product_name="Nhan decal cuon mau %d" % (k + 1),
        spec="Kho %dmm, cuon 1000m" % (50 + k * 10), origin="Viet Nam", quote_unit=UNITS[k % len(UNITS)],
        moq=1000, price_by_volume=1200 + k * 100, volume_range="1.000-5.000", vat=8, request_qty=2000,
        internal_unit=UNITS[k % len(UNITS)], amount_converted=0, shipping_cost=200000, delivery_time="5-7 ngay",
        delivery_place="Kho DEGO Long An", quote_file="", sample_ready=True, sample_date="2026-07-04",
        sample_qty=5, lab_result="Dat", lab_note="Mau chuan", nspt_note="OK", nspt_reason="",
        line_approve="Chờ duyệt", line_approve_note="", note="SP demo")


ids = []
for i in range(3):
    data = SurveyCreate(
        item_group=GROUPS[i % len(GROUPS)],
        requirement_detail="[DEMO nhap %d] Khao sat bao bi nhan decal, can bao gia 3 NCC." % (i + 1),
        received_date="2026-07-01", request_qty=2000, market_price=1500, nspt=EMP[i % len(EMP)],
        supplier_lines=[sup_line(i * 3 + j) for j in range(3)],
        product_lines=[prod_line(i * 3 + j) for j in range(3)])
    s = ss.create_survey(db, data, 1)
    ids.append((s.code, s.status))
db.close()
for code, st in ids:
    print("Created:", code, st)
