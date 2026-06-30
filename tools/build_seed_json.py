# -*- coding: utf-8 -*-
"""Đọc doc/datamau/*.txt -> xuất JSON chuẩn vào backend/app/seed_data/*.json."""
import csv
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "doc", "datamau")
OUT = os.path.join(HERE, "..", "backend", "app", "seed_data")
os.makedirs(OUT, exist_ok=True)


def rows(name):
    path = os.path.join(SRC, name)
    with open(path, encoding="utf-8", errors="replace") as f:
        return list(csv.reader(f, delimiter="\t"))


def clean(s):
    return (s or "").strip()


def clean_mst(s):
    d = "".join(ch for ch in (s or "") if ch.isdigit())
    return d[:13]


def col(name):
    """File 1 cột (bỏ header)."""
    out = []
    for i, r in enumerate(rows(name)):
        if i == 0 or not r:
            continue
        v = clean(r[0])
        if v:
            out.append(v)
    return out


# Công ty (pháp nhân)
companies = []
seen_company = set()
for i, r in enumerate(rows("congty.txt")):
    if i == 0 or len(r) < 2 or not clean(r[0]):
        continue
    code = clean(r[0])[:25]
    if code.upper() in seen_company:
        continue
    seen_company.add(code.upper())
    companies.append({"code": code, "name": clean(r[1]),
                      "address": clean(r[2]) if len(r) > 2 else "",
                      "tax_code": clean_mst(r[3]) if len(r) > 3 else ""})

# Nhà cung cấp (bán hàng + vận chuyển)
suppliers = []
seen_supplier = set()
for i, r in enumerate(rows("nhacungcap.txt")):
    if i == 0 or len(r) < 2 or not clean(r[1]):
        continue
    code = clean(r[1])[:25]
    if code.upper() in seen_supplier:
        continue
    seen_supplier.add(code.upper())
    suppliers.append({"code": code, "name": clean(r[0]),
                      "address": clean(r[2]) if len(r) > 2 else "",
                      "tax_code": clean_mst(r[3]) if len(r) > 3 else "",
                      "supplier_type": "goods"})

# NCC vận chuyển
for name in col("nccvanchuyen.txt"):
    code = name[:25]
    if code.upper() in seen_supplier:
        continue
    seen_supplier.add(code.upper())
    suppliers.append({"code": code, "name": name, "address": "", "tax_code": "",
                      "supplier_type": "transport"})

# Kho
warehouses = []
seen_warehouse = set()
for i, r in enumerate(rows("kho.txt")):
    if i == 0 or len(r) < 2 or not clean(r[1]):
        continue
    code = clean(r[1])[:25]
    if code.upper() in seen_warehouse:
        continue
    seen_warehouse.add(code.upper())
    warehouses.append({"code": code, "name": clean(r[0]),
                       "address": clean(r[2]) if len(r) > 2 else ""})

# Đơn vị tính
units = []
seen_unit = set()
for u in col("donvitinh.txt"):
    name = u.strip()
    if name.upper() in seen_unit:
        continue
    seen_unit.add(name.upper())
    units.append({"name": name})

# Phân loại (item group) + thời gian quy định
item_groups = []
seen_group = set()
for i, r in enumerate(rows("phanloai.txt")):
    if i == 0 or not r or not clean(r[0]):
        continue
    name = clean(r[0])
    if name.upper() in seen_group:
        continue
    seen_group.add(name.upper())
    item_groups.append({"name": name,
                        "std_days": clean(r[1]) if len(r) > 1 else "",
                        "note": clean(r[2]) if len(r) > 2 else "",
                        "apply_date": clean(r[3]) if len(r) > 3 else ""})

# Thương hiệu / bộ phận
brands = []
seen_brand = set()
for i, r in enumerate(rows("thuonghieu.txt")):
    if i == 0 or not r or not clean(r[0]):
        continue
    key = clean(r[0])
    code = key[:25]
    if code.upper() in seen_brand:
        continue
    seen_brand.add(code.upper())
    brands.append({"code": code, "department": clean(r[1]) if len(r) > 1 else ""})

# Dropdown khác (datangoai): 4 cột song song
vc_units, nspt, vat_opts, payment_terms = [], [], [], []
for i, r in enumerate(rows("datangoai.txt")):
    if i == 0:
        continue
    toks = [clean(x) for x in r if clean(x)]
    if len(toks) >= 1 and toks[0]:
        vc_units.append(toks[0])
    if len(toks) >= 2:
        nspt.append(toks[1])
    if len(toks) >= 3:
        vat_opts.append(toks[2])
    if len(toks) >= 4:
        payment_terms.append(toks[3])

data = {
    "companies": companies,
    "suppliers": suppliers,
    "warehouses": warehouses,
    "units": units,
    "item_groups": item_groups,
    "brands": brands,
    "options": {"shipping_units": vc_units, "nspt": nspt, "vat": vat_opts, "payment_terms": payment_terms},
}

for k, v in data.items():
    with open(os.path.join(OUT, f"{k}.json"), "w", encoding="utf-8") as f:
        json.dump(v, f, ensure_ascii=False, indent=2)

print("Đã xuất JSON vào backend/app/seed_data/")
for k, v in data.items():
    n = len(v) if isinstance(v, list) else sum(len(x) for x in v.values())
    print(f"  {k}: {n}")
