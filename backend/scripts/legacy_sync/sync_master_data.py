"""Đóng dấu `legacy_id` lên công ty + phòng ban, và tạo các phòng ban còn thiếu.

Đây là bước NỀN của việc đồng bộ app đặt xe cũ: mọi phiếu nạp về sau đều phải
tra ra công ty và phòng ban bên ERP, nên hai bảng danh mục này phải khớp trước.

CHẠY ĐƯỢC NHIỀU LẦN. Lần hai trở đi không tạo thêm gì, không sửa gì — mọi thứ
tra theo `legacy_id` chứ không theo tên, nên tên hai bên có trôi cũng không đẻ
bản ghi trùng.

Mặc định chỉ XEM TRƯỚC, không ghi. Muốn ghi thật thì thêm `--apply`.

    python -m scripts.legacy_sync.sync_master_data --export /tmp/fb-export.json
    python -m scripts.legacy_sync.sync_master_data --export /tmp/fb-export.json --apply

Bản kết xuất Firebase chứa dữ liệu cá nhân thật, KHÔNG để trong kho mã. Nạp vào
container bằng `docker compose cp` rồi trỏ `--export` vào đường dẫn tạm đó.
"""

import argparse
import json
import sys

from sqlalchemy import select, text

import app.core.all_models  # noqa: F401  nạp đủ model để SQLAlchemy dựng xong quan hệ
from app.core.database import SessionLocal
from app.modules.company.model import Company
from app.modules.department.model import Department
from scripts.legacy_sync.mapping import (BRAND_TO_COMPANY_ID,
                                         DEPARTMENT_MERGED_INTO_ERP,
                                         DEPARTMENT_REFERENCE_COLUMNS,
                                         DEPARTMENT_TO_ERP_ID)


def _load_export(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _node_name(node) -> str:
    """Lấy tên từ một nút app cũ. Vài nút cũ lưu thẳng chuỗi thay vì object."""
    if isinstance(node, dict):
        return (node.get("name") or "").strip()
    return str(node or "").strip()


def _next_department_code(db) -> "callable":
    """Sinh mã phòng ban kế tiếp theo đúng dãy `PBAnnn` ERP đang dùng.

    Trả về một hàm không tham số để gọi nhiều lần trong cùng phiên mà không đụng
    mã nhau — phòng mới chưa commit nên không truy vấn lại DB được.
    """
    used = {c for (c,) in db.execute(select(Department.code))}
    counter = {"n": 0}
    for code in used:
        if code.startswith("PBA") and code[3:].isdigit():
            counter["n"] = max(counter["n"], int(code[3:]))

    def _next() -> str:
        while True:
            counter["n"] += 1
            code = f"PBA{counter['n']:03d}"
            if code not in used:
                used.add(code)
                return code

    return _next


def _count_department_references(db, department_id: int) -> list[tuple[str, str, int]]:
    """Đếm mọi chỗ trong hệ đang trỏ vào một phòng ban. Bảng chưa có thì bỏ qua."""
    hits = []
    for table, column in DEPARTMENT_REFERENCE_COLUMNS:
        try:
            n = db.execute(
                text(f"SELECT COUNT(*) FROM {table} WHERE {column} = :i"),
                {"i": department_id},
            ).scalar()
        except Exception:
            db.rollback()
            continue
        if n:
            hits.append((table, column, n))
    return hits


def clean_merged_duplicates(db, apply: bool) -> int:
    """Dọn phòng ban bản trùng đã tạo ở lượt chạy TRƯỚC khi chốt gộp.

    Lượt chạy đầu (trước khi đại ca chốt) đã tạo mới bốn phòng gần trùng. Nay
    bốn khóa đó trỏ thẳng vào phòng ban ERP, nên các dòng tự tạo kia thành rác.

    CHỈ xóa khi KHÔNG CÒN GÌ TRỎ VÀO. Còn tham chiếu thì in ra rồi để nguyên —
    xóa một phòng ban đang có người hoặc có phiếu là làm hỏng dữ liệu thật, đó
    là việc của người chứ không phải của script.
    """
    print("\n=== DON BAN TRUNG (da chot gop ve phong ban ERP) ===")
    removed = 0
    for key, (erp_id, old_name, erp_name, ticket_count) in DEPARTMENT_MERGED_INTO_ERP.items():
        rows = db.execute(
            select(Department).where(Department.legacy_id == key)
        ).scalars().all()
        stray = [d for d in rows if d.id != erp_id]
        if not stray:
            print(f"  SACH   {key:<24} \"{old_name}\" -> id {erp_id} \"{erp_name}\""
                  f"  ({ticket_count} phieu)")
            continue
        for dept in stray:
            refs = _count_department_references(db, dept.id)
            if refs:
                detail = ", ".join(f"{t}.{c}={n}" for t, c, n in refs)
                print(f"  GIU LAI id {dept.id} \"{dept.name}\": con tro vao — {detail}")
                continue
            print(f"  XOA    id {dept.id} \"{dept.name}\" (ban trung tu tao, "
                  f"0 tham chieu) -> dung id {erp_id} \"{erp_name}\"")
            removed += 1
            if apply:
                db.delete(dept)
    return removed


def sync_companies(db, brands: dict, apply: bool) -> int:
    """Đóng dấu `legacy_id` lên 11 công ty đã có sẵn bên ERP."""
    print("=== CONG TY ===")
    changed = 0
    for key, company_id in BRAND_TO_COMPANY_ID.items():
        old_name = _node_name(brands.get(key))
        company = db.get(Company, company_id)
        if company is None:
            print(f"  LOI   {key} -> id {company_id}: khong co cong ty nay ben ERP")
            continue
        if not old_name:
            print(f"  CANH BAO {key}: ban ket xuat khong con thuong hieu nay")
        if company.legacy_id == key:
            print(f"  DA CO  {key} = id {company_id:<3} {company.name}")
            continue
        if company.legacy_id:
            print(f"  LOI   id {company_id} dang mang legacy_id khac: "
                  f"{company.legacy_id!r}, khong de len")
            continue
        print(f"  DAT    {key} -> id {company_id:<3} {company.name}"
              f"   (app cu: {old_name})")
        if apply:
            company.legacy_id = key
        changed += 1
    return changed


def sync_departments(db, departments: dict, apply: bool) -> tuple[int, int]:
    """Đóng dấu `legacy_id` lên phòng ban đã có, tạo phòng ban còn thiếu."""
    print("\n=== PHONG BAN ===")
    stamped = created = 0
    next_code = _next_department_code(db)

    #  Phòng đã có bên ERP: chỉ đóng dấu.
    for key, dept_id in DEPARTMENT_TO_ERP_ID.items():
        dept = db.get(Department, dept_id)
        if dept is None:
            print(f"  LOI   {key} -> id {dept_id}: khong co phong ban nay ben ERP")
            continue
        if dept.legacy_id == key:
            print(f"  DA CO  {key:<24} = id {dept_id:<3} {dept.name}")
            continue
        if dept.legacy_id:
            print(f"  LOI   id {dept_id} dang mang legacy_id khac: "
                  f"{dept.legacy_id!r}, khong de len")
            continue
        print(f"  DAT    {key:<24} -> id {dept_id:<3} {dept.name}")
        if apply:
            dept.legacy_id = key
        stamped += 1

    #  Phòng chưa có: tạo mới, tên chép NGUYÊN VĂN từ app cũ (H-10).
    known = set(DEPARTMENT_TO_ERP_ID)
    existing = {d.legacy_id: d for (d,) in db.execute(
        select(Department).where(Department.legacy_id != "")).all()}
    for key in sorted(departments):
        if key in known:
            continue
        name = _node_name(departments[key])
        if not name:
            print(f"  BO QUA {key}: khong co ten")
            continue
        found = existing.get(key)
        if found is not None:
            print(f"  DA TAO {key:<24} = id {found.id:<3} {found.name}")
            continue
        print(f"  TAO    {key:<24} -> \"{name}\"")
        created += 1
        if apply:
            db.add(Department(
                code=next_code(),
                name=name,
                company_id=0,   # dùng chung mọi pháp nhân, như 18 phòng sẵn có
                kind=1,
                legacy_id=key,
            ))

    return stamped, created


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", required=True,
                        help="duong dan ban ket xuat JSON tu Firebase")
    parser.add_argument("--apply", action="store_true",
                        help="ghi that; bo qua thi chi xem truoc")
    args = parser.parse_args()

    data = _load_export(args.export)
    for node in ("brands", "departments"):
        if node not in data:
            print(f"LOI: ban ket xuat thieu nut {node!r}")
            return 1

    db = SessionLocal()
    try:
        n_company = sync_companies(db, data["brands"], args.apply)
        #  Dọn TRƯỚC khi đóng dấu: bản trùng đang giữ đúng khóa mà ta sắp gắn
        #  cho phòng ban ERP, để lại thì một khóa nằm ở hai dòng.
        n_removed = clean_merged_duplicates(db, args.apply)
        n_stamp, n_create = sync_departments(db, data["departments"], args.apply)
        if args.apply:
            db.commit()
        print(f"\n  cong ty dong dau : {n_company}")
        print(f"  ban trung da xoa : {n_removed}")
        print(f"  phong ban dong dau: {n_stamp}")
        print(f"  phong ban tao moi : {n_create}")
        print("\n  " + ("DA GHI VAO DB." if args.apply
                        else "MOI CHI XEM TRUOC — them --apply de ghi that."))
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
