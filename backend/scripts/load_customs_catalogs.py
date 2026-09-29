# -*- coding: utf-8 -*-
"""Nạp DANH MỤC THAM KHẢO của phân hệ Tra cứu giá hải quan (bao-CR-470, HQ4 + HQ6).

Chạy: docker compose exec -T api python -m scripts.load_customs_catalogs --src <thư mục app>

`--src` là thư mục `app/` của phần mềm HaiQuan Manager (chứa `HaiQuan_Manager.html`,
`bvtv_data.js`, `bieu_thue_2026.js`). Dữ liệu đó là của bên thứ ba — CỐ Ý không chép
vào repo; repo chỉ giữ cách đọc.

Nạp gì:
  - Từ khóa hoạt chất (`ACTIVE_INGREDIENTS`, ~100)      → tab_customs_ingredient_alias  (thay toàn bộ)
  - (29/09/2026) Danh mục thuốc BVTV KHÔNG còn nạp ở đây. Nguồn chuyển sang bản cào
    danhmuc.thuocbvtv.com — có số đăng ký, hiệu lực, phạm vi sử dụng — nạp bằng nút «Nạp danh
    mục» của mục Thuốc BVTV (`pesticide_service.replace_catalog`). Nạp lại từ `bvtv_data.js`
    sẽ thay toàn bộ bảng bằng bản thiếu cột và xóa sạch phạm vi sử dụng.
  - Biểu thuế XNK 2026 (`bieu_thue_2026.js`)            → tab_customs_tariff            (thay toàn bộ)
  - NĐ 24/2026 PL I–IV, TT 75/2025 cấm, TT 01/2026 công bố → tab_customs_regulation     (CHỈ THÊM)

⚠️ Danh mục pháp lý CHỈ THÊM dòng chưa có (so theo danh sách + số CAS + tên), KHÔNG đè:
bảng đó sửa được trên màn hình (người phụ trách cập nhật ngưỡng khi nghị định đổi), nạp
lại mà đè là xóa mất công người ta sửa. Ba bảng còn lại là dữ liệu tham khảo thuần, thay
toàn bộ cho khớp nguồn.

Xong thì gắn lại hoạt chất + hàm lượng cho MỌI dòng hàng đã nạp (`retag_all`).
"""
import argparse
import json
import os
import re
import sys

import app.core.all_models  # noqa: F401 — nạp đủ mapper
from sqlalchemy import delete, insert

from app.core.database import SessionLocal
from app.modules.customs.constants import RegulationList
from app.modules.customs.ingredient import retag_all
from app.modules.customs.model import CustomsIngredientAlias, CustomsRegulation, CustomsTariff

_CHUNK = 2000


def _js_to_json(body: str) -> str:
    """Mảng JS của phần mềm nguồn → JSON: đổi chuỗi nháy đơn sang nháy kép, bỏ chú
    thích `//`, bỏ dấu phẩy thừa cuối mảng. Đọc TỪNG KÝ TỰ và biết đang ở trong chuỗi
    hay không — tên hóa chất có sẵn ngoặc vuông (`Benzo[b]…`), tách bằng biểu thức
    chính quy theo `[...]` là cắt nhầm giữa tên."""
    out, i, n = [], 0, len(body)
    while i < n:
        ch = body[i]
        if ch == "'":
            j, buf = i + 1, []
            while j < n and body[j] != "'":
                if body[j] == "\\" and j + 1 < n:
                    j += 1
                buf.append(body[j])
                j += 1
            out.append(json.dumps("".join(buf), ensure_ascii=False))
            i = j + 1
        elif body.startswith("//", i):
            nl = body.find("\n", i)
            i = nl if nl >= 0 else n
        else:
            out.append(ch)
            i += 1
    return re.sub(r",\s*([\]}])", r"\1", "".join(out))


def _js_array(source: str, name: str) -> list[list]:
    """`const NAME = [ [...], ... ];` → list Python."""
    m = re.search(r"(?:const|var|let)\s+" + name + r"\s*=\s*\[", source)
    if not m:
        raise SystemExit(f"Không thấy mảng {name} trong tệp nguồn")
    start = m.end() - 1
    depth, in_str, k = 0, False, start
    while k < len(source):
        c = source[k]
        if c == "'" and source[k - 1] != "\\":
            in_str = not in_str
        elif not in_str and c == "[":
            depth += 1
        elif not in_str and c == "]":
            depth -= 1
            if depth == 0:
                break
        k += 1
    return json.loads(_js_to_json(source[start:k + 1]))


def _js_objects(source: str, name: str) -> list[dict]:
    m = re.search(r"(?:const|var|let)\s+" + name + r"\s*=\s*\[", source)
    body = source[m.end():source.find("];", m.end())]
    return [dict(re.findall(r"(\w+)\s*:\s*'((?:[^'\\]|\\.)*)'", obj)) for obj in re.findall(r"\{([^{}]*)\}", body)]


def _replace_all(db, model, rows: list[dict]) -> int:
    db.execute(delete(model))
    for i in range(0, len(rows), _CHUNK):
        db.execute(insert(model), rows[i:i + _CHUNK])
    return len(rows)


def load_aliases(db, page: str) -> int:
    rows = {k.upper(): c for k, c in _js_array(page, "ACTIVE_INGREDIENTS")}
    return _replace_all(db, CustomsIngredientAlias,
                        [{"keyword": k, "canonical": c} for k, c in rows.items()])


def load_tariff(db, src: str) -> int:
    raw = open(os.path.join(src, "bieu_thue_2026.js"), encoding="utf-8").read()
    data = json.loads(raw[raw.index("["):raw.rindex("]") + 1])
    rows = [{"hs_code": str(d.get("h", ""))[:10], "name_vn": d.get("vn", ""), "name_en": d.get("en", ""),
             "unit": str(d.get("dvt", ""))[:40], "rate_normal": str(d.get("tt", ""))[:20],
             "rate_mfn": str(d.get("ud", ""))[:20], "rate_vat": str(d.get("vat", ""))[:20],
             "fta_json": json.dumps(d.get("fta") or {}, ensure_ascii=False), "policy": d.get("cs", "")}
            for d in data if d.get("h")]
    return _replace_all(db, CustomsTariff, rows)


def load_regulations(db, page: str) -> int:
    nd24 = "NĐ 24/2026/NĐ-CP"
    wanted = []
    for en, vi, cas in _js_array(page, "ND24_PL1"):
        wanted.append((RegulationList.ND24_PL1, en, vi, cas, "", None, None, nd24 + " Phụ lục I", ""))
    for name, cas in _js_array(page, "ND24_PL2"):
        wanted.append((RegulationList.ND24_PL2, name, "", cas, "", None, None, nd24 + " Phụ lục II", ""))
    kinds = {"precursor_drugs": "Tiền chất ma túy", "cwc_precursor": "Tiền chất vũ khí hóa học",
             "explosive_precursor": "Tiền chất nổ"}
    for name, cas, kind in _js_array(page, "ND24_PL3"):
        wanted.append((RegulationList.ND24_PL3, name, "", cas, kinds.get(kind, kind), None, None,
                       nd24 + " Phụ lục III", ""))
    for name, cas, kg in _js_array(page, "ND24_PL4"):
        wanted.append((RegulationList.ND24_PL4, name, "", cas, "", kg, None, nd24 + " Phụ lục IV", ""))
    for row in _js_array(page, "BANNED_CHEMICALS"):
        name, cas, year, basis, note = (row + [""] * 5)[:5]
        wanted.append((RegulationList.BANNED_TT75, name, "", cas, "", None, year or None, basis, note))
    for obj in _js_objects(page, "HC_CONG_BO"):
        wanted.append((RegulationList.PUBLISH_TT01, obj.get("name", ""), "", obj.get("cas", ""),
                       obj.get("formula", ""), None, None, "TT 01/2026/TT-BCT Phụ lục XIX", ""))
    have = {(r.list_code, r.cas_no, r.name) for r in db.query(CustomsRegulation)}
    added = 0
    for code, name, vi, cas, cat, kg, year, basis, note in wanted:
        key = (int(code), str(cas)[:40], str(name)[:500])
        if key in have:
            continue
        have.add(key)
        db.add(CustomsRegulation(list_code=int(code), name=key[2], name_vi=str(vi)[:500], cas_no=key[1],
                                 category=str(cat)[:100], threshold_kg=kg, banned_year=year,
                                 legal_basis=str(basis)[:255], note=str(note)[:500], is_active=True))
        added += 1
    return added


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="thư mục app/ của HaiQuan Manager")
    args = ap.parse_args()
    page = open(os.path.join(args.src, "HaiQuan_Manager.html"), encoding="utf-8", errors="replace").read()
    db = SessionLocal()
    try:
        print("Từ khóa hoạt chất :", load_aliases(db, page))
        print("Biểu thuế (mã HS) :", load_tariff(db, args.src))
        print("Danh mục pháp lý  : thêm", load_regulations(db, page), "dòng mới")
        db.commit()
        res = retag_all(db)
        print(f"Gắn lại hoạt chất : {res['tagged']}/{res['total']} dòng hàng")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
