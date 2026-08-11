"""Script cap nhat cot invoice_name (Ten tren hoa don) cho tab_product tu datanhan.txt.

Quy tac:
- Doc du lieu tu datanhan.txt (dinh dang TSV - Tab Separated Values).
- Match theo cot `Ma VTBB` -> Product.code trong `tab_product`.
- Bo qua cac dong co ten hoa don rong hoac la #NA, #N/A, NA, NULL, '-'.
- Bo qua cac dong thieu Ma VTBB.
- Xu ly chuan hoa khoang trang, xuong dong trong dau ngoac kep thanh chuoi hop le tren 1 dong.
- Ho tro che do --dry-run de kiem tra truoc khi commit.
- Xuat file SQL update_invoice_name.sql du phong de review.

Cach chay:
  # Xem truoc thay doi (khong ghi vao DB):
  docker compose exec api python -m scripts.update_invoice_name --dry-run

  # Thuc hien cap nhat that vao DB:
  docker compose exec api python -m scripts.update_invoice_name
"""

import argparse
import csv
import os
import sys
from datetime import datetime

import app.core.all_models  # noqa: F401
from app.core.database import SessionLocal
from app.modules.product.model import Product
from app.modules.user.model import User

NA_VALUES = {"", "#N/A", "#NA", "N/A", "NA", "NULL", "-", "NONE"}


def clean_text(v: str | None) -> str:
    if v is None:
        return ""
    # Normalize multiple whitespaces and newlines
    s = " ".join(str(v).strip().split())
    if s.upper() in NA_VALUES:
        return ""
    return s


def parse_data_file(file_path: str):
    """Doc va parse file datanhan.txt."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Khong tim thay file: {file_path}")

    records = []
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader, None)

        for row_idx, row in enumerate(reader, start=2):
            if not row:
                continue

            hh_code = row[0].strip() if len(row) > 0 else ""
            item_group = row[1].strip() if len(row) > 1 else ""
            vtbb_code = row[2].strip() if len(row) > 2 else ""
            name = row[3].strip() if len(row) > 3 else ""

            # Ten tren hoa don thuong o cot 6 (index 5) hoac cot 5 neu file it cot
            invoice_name = ""
            if len(row) >= 6:
                invoice_name = row[5]
            elif len(row) == 5:
                invoice_name = row[4]

            clean_inv = clean_text(invoice_name)

            records.append({
                "row": row_idx,
                "hh_code": hh_code,
                "item_group": item_group,
                "vtbb_code": vtbb_code,
                "name": name,
                "raw_invoice_name": invoice_name,
                "clean_invoice_name": clean_inv,
            })

    return records


def generate_sql_file(updates: list[tuple[str, str]], output_sql_path: str):
    """Tao file SQL chua cac cau lenh UPDATE de nguoi dung luu tru hoac review."""
    lines = [
        "-- SQL Update invoice_name tu datanhan.txt",
        f"-- Ngay tao: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"-- Tong so ban ghi update: {len(updates)}",
        "START TRANSACTION;\n",
    ]
    for code, inv_name in updates:
        # Escape single quotes in SQL
        escaped_inv = inv_name.replace("'", "''").replace("\\", "\\\\")
        escaped_code = code.replace("'", "''").replace("\\", "\\\\")
        lines.append(f"UPDATE tab_product SET invoice_name = '{escaped_inv}' WHERE code = '{escaped_code}';")

    lines.append("\nCOMMIT;")
    with open(output_sql_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"-> Da xuat file SQL review tai: {output_sql_path}")


def run(file_path: str = "/app/datanhan.txt", dry_run: bool = False):
    if not os.path.exists(file_path):
        # Fallback neu chay tren local hoac thu muc khac
        alt_paths = [
            os.path.join(os.path.dirname(__file__), "..", "datanhan.txt"),
            os.path.join(os.path.dirname(__file__), "..", "..", "datanhan.txt"),
            "datanhan.txt",
            "backend/datanhan.txt",
        ]
        for p in alt_paths:
            if os.path.exists(p):
                file_path = p
                break

    print("=" * 70)
    print(f"BAT DAU CAP NHAT TEN HOA DON (invoice_name)")
    print(f"Nguon du lieu: {file_path}")
    print(f"Che do: {'[DRY-RUN] Chi kiem tra, KHONG ghi vao DB' if dry_run else '[EXECUTE] Ghi de vao DB'}")
    print("=" * 70)

    records = parse_data_file(file_path)
    print(f"Tong so dong doc duoc: {len(records)}")

    db = SessionLocal()
    try:
        sys_user = db.query(User).order_by(User.id).first()
        uid = sys_user.id if sys_user else 1

        products = db.query(Product).all()
        by_code = {p.code: p for p in products if p.code}
        print(f"Tong so san pham trong tab_product: {len(products)}")

        skipped_na_empty = 0
        skipped_no_code = 0
        not_found_in_db = []
        updated_records = []
        already_identical = 0

        for r in records:
            code = r["vtbb_code"]
            inv = r["clean_invoice_name"]

            # 1. Kiem tra neu rong hoac #NA thi bo qua
            if not inv:
                skipped_na_empty += 1
                continue

            # 2. Kiem tra Ma VTBB
            if not code:
                skipped_no_code += 1
                continue

            # 3. Tim san pham trong DB theo code
            prod = by_code.get(code)
            if not prod:
                not_found_in_db.append((code, r["hh_code"], r["name"], inv))
                continue

            # 4. So sanh voi gia tri hien tai
            current_inv = prod.invoice_name or ""
            if current_inv == inv:
                already_identical += 1
                continue

            # Cap nhat
            prod.invoice_name = inv
            prod.updated_by = uid
            updated_records.append((code, inv))

        print("\n" + "-" * 70)
        print("THONG KE CHI TIET:")
        print(f"  - So dong bi bo qua do rong / #NA:               {skipped_na_empty:5d}")
        print(f"  - So dong bi bo qua do khong co Ma VTBB:         {skipped_no_code:5d}")
        print(f"  - So Ma VTBB co trong file nhung khong co DB:     {len(not_found_in_db):5d}")
        print(f"  - So san pham da co ten hoa don giong het file:  {already_identical:5d}")
        print(f"  - So san pham duoc cap nhat (ghi de) moi:        {len(updated_records):5d}")
        print("-" * 70)

        # Xuat file SQL du phong
        sql_out_path = os.path.join(os.path.dirname(file_path), "update_invoice_name.sql")
        generate_sql_file(updated_records, sql_out_path)

        if not dry_run:
            db.commit()
            print("\n>>> DA COMMIT CAP NHAT THANH CONG VAO DATABASE! <<<")
        else:
            db.rollback()
            print("\n>>> [DRY-RUN] Khong co thay doi nao duoc ghi vao DB. <<<")

        # In mau 5 ban ghi duoc cap nhat
        if updated_records:
            print("\nVi du 5 ban ghi duoc cap nhat:")
            for c, inv in updated_records[:5]:
                print(f"  - Code: {c:<12} -> invoice_name: '{inv}'")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cap nhat invoice_name tu file datanhan.txt")
    parser.add_argument("--file", default="/app/datanhan.txt", help="Duong dan toi file datanhan.txt")
    parser.add_argument("--dry-run", action="store_true", help="Chay thu khong commit vao DB")
    args = parser.parse_args()

    run(file_path=args.file, dry_run=args.dry_run)
