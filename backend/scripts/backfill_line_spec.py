"""Backfill "Xuat xu / TSKT / chat lieu" xuong dong hang sau khi chay lai Thong so ky thuat SP.

BOI CANH
--------
`Product.specs` ("Thong so ky thuat") duoc COPY xuong dong hang luc TAO dong DMH
(xem `purchase_order/service.py::_save_items`). Dong tao TRUOC khi SP co specs se
mang gia tri rong vinh vien — nap lai data SP khong tu chay nguoc xuong dong hang.
Script nay chay nguoc phan con thieu do.

PHAM VI (chi 2 cho, da ra soat toan bo model)
  1. `tab_po_item.spec`                  -- ban sao SONG, dung de in / xuat DMH
  2. `tab_purchase_history.extra['spec']`-- anh chup luc dong "Hoan thanh", ghi 1 lan
`tab_pr_item` (YCMH) KHONG co cot spec; khao sat (`snap_spec`) la nguoi dung tu nhap
theo tung phuong an bao gia, khong phai ban sao cua SP -> khong dung toi.

NGUYEN TAC AN TOAN
  - CHI dien vao o DANG RONG. Khong bao gio de len gia tri da co: dong hang cho phep
    sua tay, de len la xoa mat chinh sua cua nguoi dung.
  - Khong bao gio XOA: dong co spec ma SP hien rong thi giu nguyen (co the la hang
    dat rieng, nguoi mua go tay).
  - Dong lich su LEGACY (po_id = 0, nhap tu Excel truoc khi co he thong) KHONG dung toi:
    do la anh chup cua lan mua NAM XUA, dien specs HOM NAY vao la bia dat du lieu.
  - Lich su chi lay theo dong DMH that (`po_item_id`), lay dung spec cua dong do.

CACH CHAY
  # xem truoc, khong ghi gi:
  docker exec -w /app <api-container> python scripts/backfill_line_spec.py
  # ghi that:
  docker exec -w /app <api-container> python scripts/backfill_line_spec.py --apply
"""
import argparse
import json
import sys

import app.core.all_models  # noqa: F401  (nap het model truoc khi mo session)
from app.core.database import SessionLocal
from app.modules.product.model import Product
from app.modules.purchase_history.model import PurchaseHistory
from app.modules.purchase_order.model import POItem


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Ghi that (mac dinh chi xem truoc)")
    ap.add_argument("--limit-log", type=int, default=15, help="So dong in ra lam mau")
    args = ap.parse_args()

    db = SessionLocal()
    try:
        specs = {
            (c or "").strip(): (s or "").strip()
            for c, s in db.query(Product.code, Product.specs).all()
        }
        specs = {c: s for c, s in specs.items() if c and s}
        print(f"[i] San pham co Thong so ky thuat: {len(specs)}")

        # ── 1. Dong hang DMH ──────────────────────────────────────────────────
        sua_item: list[POItem] = []
        giu_nguyen = 0
        for it in db.query(POItem).all():
            moi = specs.get((it.product_code or "").strip(), "")
            if not moi:
                continue
            if (it.spec or "").strip():
                if (it.spec or "").strip() != moi:
                    giu_nguyen += 1
                continue
            sua_item.append(it)

        print(f"[1] tab_po_item.spec : dien {len(sua_item)} dong "
              f"(giu nguyen {giu_nguyen} dong da co gia tri KHAC voi SP)")
        for it in sua_item[: args.limit_log]:
            print(f"    #{it.id} {it.product_code} <- {specs[(it.product_code or '').strip()][:70]}")
        if len(sua_item) > args.limit_log:
            print(f"    ... con {len(sua_item) - args.limit_log} dong")

        if args.apply:
            for it in sua_item:
                it.spec = specs[(it.product_code or "").strip()]
            db.flush()

        # ── 2. Anh chup lich su mua hang ──────────────────────────────────────
        # Sau buoc 1, `POItem.spec` da la nguon dung -> lay theo dong DMH, khong lay
        # thang tu SP (dong hang co the duoc sua tay khac SP, anh chup phai theo dong).
        spec_dong = {
            i: (s or "").strip()
            for i, s in db.query(POItem.id, POItem.spec).all()
        }
        # Ap ket qua buoc 1 vao map ke ca khi DRY-RUN, neu khong ban xem truoc se bao
        # "0 dong" chi vi dong DMH luc do van con rong — sai voi ket qua chay that.
        for it in sua_item:
            spec_dong[it.id] = specs[(it.product_code or "").strip()]

        sua_hist: list[tuple[PurchaseHistory, str, dict]] = []
        bo_legacy = 0
        for h in db.query(PurchaseHistory).all():
            try:
                ex = json.loads(h.extra) if h.extra else {}
            except Exception:
                ex = {}
            if not isinstance(ex, dict):
                ex = {}
            if (ex.get("spec") or "").strip():
                continue
            if not h.po_item_id or h.po_item_id not in spec_dong:
                # legacy (nhap Excel) hoac dong DMH da bi xoa -> khong bia du lieu
                if specs.get((h.product_code or "").strip(), ""):
                    bo_legacy += 1
                continue
            moi = spec_dong[h.po_item_id]
            if not moi:
                continue
            sua_hist.append((h, moi, ex))

        print(f"[2] tab_purchase_history.extra.spec : dien {len(sua_hist)} dong "
              f"(BO QUA {bo_legacy} dong legacy/khong con dong DMH)")
        for h, moi, _ in sua_hist[: args.limit_log]:
            print(f"    #{h.id} {h.po_code or 'legacy'} {h.product_code} <- {moi[:70]}")
        if len(sua_hist) > args.limit_log:
            print(f"    ... con {len(sua_hist) - args.limit_log} dong")

        if args.apply:
            for h, moi, ex in sua_hist:
                ex["spec"] = moi
                h.extra = json.dumps(ex, ensure_ascii=False)
            db.commit()
            print("[OK] Da ghi.")
        else:
            db.rollback()
            print("[!] DRY-RUN — chua ghi gi. Them --apply de thuc hien.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
