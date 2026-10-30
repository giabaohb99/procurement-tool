# -*- coding: utf-8 -*-
"""Nạp cấu hình "Tra cứu thị trường" — duoc-CR-684 (từ tệp CauHinh_TraCuuThiTruong_20261026.xlsx).

Chạy (local):
  docker compose exec -T api python scripts/load_customs_lookup_config_cr684.py --dry-run
  docker compose exec -T api python scripts/load_customs_lookup_config_cr684.py
Prod: thêm `-f docker-compose.yml -f docker-compose.production.yml` — xem doc/tai-lieu-ky-thuat/hai-quan-tra-cuu-thi-truong-nap-cau-hinh-cr684.md.

Nguồn dữ liệu DUY NHẤT: `scripts/data/cau-hinh-tra-cuu-thi-truong-cr684.json` (có `--data` để đổi tệp).
Nạp gì (đều đi qua ORM — KHÔNG dùng `mysql -e` với tiếng Việt, sẽ hỏng dấu):
  · từ khóa Thành phẩm / Nguyên liệu → tab_customs_kind_keyword   (CHỈ THÊM dòng chưa có)
  · nhóm từ đồng nghĩa              → tab_customs_search_synonym  (có rồi thì GỘP thêm từ mới)
  · mã dạng chế phẩm                → tab_customs_formulation_code (chưa có thì thêm; có rồi chỉ điền ô trống)

Chạy lại bao nhiêu lần cũng được (idempotent). Không bao giờ đè giá trị người dùng đã sửa trên màn
hình: từ khóa đã có (kể cả đã tắt / khác loại) được giữ nguyên và ghi vào báo cáo.
Thêm từ khóa xong tự gắn lại nhãn cho mọi dòng hàng (cùng `POST /api/customs/kinds/retag`), trừ
khi `--no-retag`; khi đó phải bấm "Gắn lại nhãn" trên màn Tra cứu thị trường → Cấu hình.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # chạy được cả `python scripts/x.py`

import app.core.all_models  # noqa: E402,F401 — nạp đủ mapper
from sqlalchemy.orm import Session  # noqa: E402

from app.modules.customs.ingredient import retag_all  # noqa: E402
from app.modules.customs.model import (CustomsFormulationCode, CustomsKindKeyword,  # noqa: E402
                                       CustomsSearchSynonym)

DEFAULT_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data",
                            "cau-hinh-tra-cuu-thi-truong-cr684.json")
SYN_MAX, NOTE_MAX = 1000, 255


def _fold(s: str) -> str:
    return " ".join((s or "").split()).casefold()


def _stat() -> dict:
    return {"new": [], "present": [], "merged": [], "skipped": []}


def load_keywords(db: Session, items: list[dict]) -> dict:
    rep = _stat()
    existing = {_fold(r.keyword): r for r in db.query(CustomsKindKeyword)}
    for it in items:
        key = " ".join(it["keyword"].split())
        row = existing.get(_fold(key))
        if row is None:
            if len(key) > 100 or len(it.get("note", "")) > NOTE_MAX:
                rep["skipped"].append(f"{key}: vượt độ dài cột")
                continue
            row = CustomsKindKeyword(keyword=key, kind=int(it["kind"]), note=it.get("note", ""), is_active=True)
            db.add(row)
            existing[_fold(key)] = row
            rep["new"].append(key)
        elif row.kind != int(it["kind"]) or not row.is_active:
            rep["skipped"].append(f"{key}: đã có nhưng khác loại/đang tắt — giữ nguyên")
        else:
            rep["present"].append(key)
    return rep


def _merge_synonyms(current: str, add: list[str], term: str) -> tuple[str, bool]:
    have = [x.strip() for x in (current or "").split(";") if x.strip()]
    seen = {_fold(x) for x in have} | {_fold(term)}
    changed = False
    for w in add:
        w = " ".join(w.split())
        if w and _fold(w) not in seen:
            have.append(w)
            seen.add(_fold(w))
            changed = True
    return "; ".join(have), changed


def load_synonyms(db: Session, items: list[dict]) -> dict:
    rep = _stat()
    existing = {_fold(r.term): r for r in db.query(CustomsSearchSynonym)}
    for it in items:
        term = " ".join(it["term"].split())
        row = existing.get(_fold(term))
        if row is None:
            merged, _ = _merge_synonyms("", it["synonyms"], term)
            if len(term) > 100 or len(merged) > SYN_MAX:
                rep["skipped"].append(f"{term}: vượt độ dài cột")
                continue
            row = CustomsSearchSynonym(term=term, synonyms=merged, note=it.get("note", "")[:NOTE_MAX], is_active=True)
            db.add(row)
            existing[_fold(term)] = row
            rep["new"].append(term)
            continue
        merged, changed = _merge_synonyms(row.synonyms, it["synonyms"], term)
        if not changed:
            rep["present"].append(term)
        elif len(merged) > SYN_MAX:
            rep["skipped"].append(f"{term}: gộp xong vượt {SYN_MAX} ký tự")
        else:
            row.synonyms = merged
            rep["merged"].append(f"{term} → {merged}")
    return rep


def load_formulation_codes(db: Session, items: list[dict]) -> dict:
    rep = _stat()
    existing = {_fold(r.code): r for r in db.query(CustomsFormulationCode)}
    for it in items:
        code = " ".join(it["code"].split()).upper()
        row = existing.get(_fold(code))
        if row is None:
            row = CustomsFormulationCode(code=code, name_en=it.get("name_en", ""), name_vi=it.get("name_vi", ""),
                                         description=it.get("description", ""), is_active=True)
            db.add(row)
            existing[_fold(code)] = row
            rep["new"].append(code)
            continue
        filled = False
        for col in ("name_en", "name_vi", "description"):  # chỉ điền ô trống, không đè
            if not getattr(row, col) and it.get(col):
                setattr(row, col, it[col])
                filled = True
        (rep["merged"] if filled else rep["present"]).append(code)
    return rep


def run(db: Session, data: dict, dry_run: bool = False, retag: bool = True) -> dict:
    """Nạp cả ba nhóm trong MỘT giao dịch; `dry_run` thì hoàn tác. Trả báo cáo từng nhóm."""
    report = {
        "kind_keywords": load_keywords(db, data["kind_keywords"]),
        "synonym_groups": load_synonyms(db, data["synonym_groups"]),
        "formulation_codes": load_formulation_codes(db, data["formulation_codes"]),
        "retag": None,
    }
    if dry_run:
        db.rollback()
        return report
    db.commit()
    if retag and report["kind_keywords"]["new"]:
        report["retag"] = retag_all(db)
    return report


def _print(report: dict, dry_run: bool) -> None:
    print("== DRY-RUN (không ghi gì) ==" if dry_run else "== ĐÃ GHI ==")
    for name, rep in report.items():
        if name == "retag":
            continue
        print(f"[{name}] mới {len(rep['new'])} · đã có {len(rep['present'])} · gộp {len(rep['merged'])} · bỏ qua {len(rep['skipped'])}")
        for label in ("new", "merged", "skipped"):
            for line in rep[label]:
                print(f"   {label}: {line}")
    if report["retag"] is not None:
        print(f"[retag] {report['retag']}")
    elif not dry_run:
        print("[retag] không chạy — nếu có từ khóa mới hãy bấm 'Gắn lại nhãn' trên màn Tra cứu thị trường → Cấu hình.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="chỉ báo cáo, không ghi")
    ap.add_argument("--no-retag", action="store_true", help="không tự gắn lại nhãn sau khi thêm từ khóa")
    ap.add_argument("--data", default=DEFAULT_DATA, help="tệp JSON nguồn")
    args = ap.parse_args()
    with open(args.data, encoding="utf-8") as fh:
        data = json.load(fh)
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        report = run(db, data, dry_run=args.dry_run, retag=not args.no_retag)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    _print(report, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
