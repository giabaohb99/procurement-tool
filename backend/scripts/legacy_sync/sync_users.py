"""Đóng dấu `legacy_id` lên `tab_employee` theo tài khoản app đặt xe cũ.

Mọi phiếu bên app cũ đều mang `createdBy` là UID Firebase. Không dựng được bảng
tra UID -> hồ sơ nhân sự thì phiếu nạp sang ERP sẽ mất người lập, nên bước này
phải xong trước khi nạp phiếu.

CÁCH KHỚP — chỉ MỘT đường tự động: EMAIL, và chỉ nhận khi 1-1 tuyệt đối. Tên
KHÔNG dùng để khớp (QĐ-K). Bản đo 16/09/2026 cho thấy vì sao: 14 ca "tên trùng
mà email khác" gồm cả hộp thư dùng chung `assistant.n2sbiovn@gmail.com` đang
mang tên một nhân viên thật — khớp theo tên là gán nhầm phiếu cho người khác,
và gán nhầm thì không ai phát hiện ra.

Ca không 1-1 thì script XẾP RA BÁO CÁO chứ không đoán. Người soát rồi ghi vào
`USER_MANUAL_MAP` / `USER_SKIPPED` bên `mapping.py`, chạy lại là script thi hành.

CHẠY ĐƯỢC NHIỀU LẦN. Mặc định chỉ xem trước, `--apply` mới ghi.

    python -m scripts.legacy_sync.sync_users --export /tmp/fb-export.json
    python -m scripts.legacy_sync.sync_users --export /tmp/fb-export.json --apply

Bản kết xuất Firebase chứa dữ liệu cá nhân thật của 136 người, KHÔNG để trong
kho mã. Nạp vào container bằng `docker compose cp` rồi trỏ `--export` vào đó.
"""

import argparse
import collections
import json
import re
import sys
import unicodedata

from sqlalchemy import select

import app.core.all_models  # noqa: F401  nạp đủ model để SQLAlchemy dựng xong quan hệ
from app.core.database import SessionLocal
from app.modules.employee.model import Employee
from app.modules.legacy_datxe.mapping import USER_MANUAL_MAP, USER_SKIPPED


def _load_export(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _norm_email(value) -> str:
    return (value or "").strip().lower()


def _norm_name(value) -> str:
    """Bỏ dấu, bỏ hoa thường, gom khoảng trắng. CHỈ dùng để GỢI Ý, không để khớp."""
    text = unicodedata.normalize("NFD", (value or "").strip().lower())
    text = text.replace("đ", "d")  # đ không phải d + dấu nên NFD không tách
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", "", re.sub(r"\s+", " ", text)).strip()


def _count_tickets_by_user(requests: dict) -> collections.Counter:
    """Đếm phiếu theo người lập — dùng để xếp báo cáo theo mức nặng nhẹ."""
    return collections.Counter(r.get("createdBy") for r in requests.values()
                               if isinstance(r, dict))


def _index_employees_by_email(db) -> dict[str, list[Employee]]:
    """Gom hồ sơ nhân sự theo email. Nhận cả email công ty lẫn email cá nhân."""
    index: dict[str, list[Employee]] = collections.defaultdict(list)
    for emp in db.execute(select(Employee)).scalars():
        for field in (emp.email, emp.personal_email):
            key = _norm_email(field)
            if key and emp not in index[key]:
                index[key].append(emp)
    return index


def classify_users(db, users: dict) -> dict[str, list]:
    """Xếp từng tài khoản app cũ vào một nhóm. Không ghi gì xuống DB.

    Nhóm `khop` là nhóm DUY NHẤT được đóng dấu tự động; bốn nhóm còn lại chờ
    người chốt.
    """
    by_email = _index_employees_by_email(db)
    fb_by_email: dict[str, list[str]] = collections.defaultdict(list)
    for uid, node in users.items():
        fb_by_email[_norm_email(node.get("email"))].append(uid)

    #  Chỉ số theo TÊN dùng cho GỢI Ý trong báo cáo, không tham gia khớp.
    by_name: dict[str, list[Employee]] = collections.defaultdict(list)
    for group in by_email.values():
        for emp in group:
            if emp not in by_name[_norm_name(emp.full_name)]:
                by_name[_norm_name(emp.full_name)].append(emp)
    for emp in db.execute(select(Employee)).scalars():
        if emp not in by_name[_norm_name(emp.full_name)]:
            by_name[_norm_name(emp.full_name)].append(emp)

    buckets: dict[str, list] = {k: [] for k in
                                ("khop", "tay", "bo", "erp_trung",
                                 "app_cu_trung", "goi_y_ten", "khong_thay")}
    for uid, node in users.items():
        email = _norm_email(node.get("email"))
        found = by_email.get(email, [])
        hint = by_name.get(_norm_name(node.get("displayName")), [])
        if uid in USER_SKIPPED:
            buckets["bo"].append((uid, node, USER_SKIPPED[uid]))
        elif uid in USER_MANUAL_MAP:
            buckets["tay"].append((uid, node, USER_MANUAL_MAP[uid]))
        elif len({e.id for e in found}) > 1:
            buckets["erp_trung"].append((uid, node, found))
        elif len(fb_by_email[email]) > 1 and found:
            buckets["app_cu_trung"].append((uid, node, found[0]))
        elif found:
            buckets["khop"].append((uid, node, found[0]))
        elif hint:
            buckets["goi_y_ten"].append((uid, node, hint))
        else:
            buckets["khong_thay"].append((uid, node, None))
    return buckets


def stamp_employees(db, pairs: list[tuple[str, dict, Employee]],
                    apply: bool) -> int:
    """Gắn `legacy_id` cho từng cặp đã chắc chắn. Không bao giờ đè khóa khác."""
    stamped = 0
    for uid, node, emp in pairs:
        name = (node.get("displayName") or "").strip()
        if emp.legacy_id == uid:
            continue
        if emp.legacy_id:
            print(f"  LOI    id {emp.id} ({emp.full_name}) dang mang legacy_id "
                  f"khac: {emp.legacy_id!r}, khong de len")
            continue
        print(f"  DAT    id {emp.id:<4} {emp.full_name:<28} <- {name}")
        if apply:
            emp.legacy_id = uid
        stamped += 1
    return stamped


def _report(title: str, rows: list, tickets: collections.Counter,
            render) -> None:
    if not rows:
        return
    total = sum(tickets.get(uid, 0) for uid, *_ in rows)
    print(f"\n=== {title} — {len(rows)} nguoi, {total} phieu ===")
    for row in sorted(rows, key=lambda r: -tickets.get(r[0], 0)):
        print(f"  {tickets.get(row[0], 0):>4} phieu  {render(row)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", required=True,
                        help="duong dan ban ket xuat JSON tu Firebase")
    parser.add_argument("--apply", action="store_true",
                        help="ghi that; bo qua thi chi xem truoc")
    args = parser.parse_args()

    data = _load_export(args.export)
    for node in ("users", "requests"):
        if node not in data:
            print(f"LOI: ban ket xuat thieu nut {node!r}")
            return 1
    users = data["users"]
    tickets = _count_tickets_by_user(data["requests"])

    db = SessionLocal()
    try:
        buckets = classify_users(db, users)

        print("=== DONG DAU (email khop 1-1) ===")
        n_auto = stamp_employees(db, buckets["khop"], args.apply)

        manual = []
        for uid, node, emp_id in buckets["tay"]:
            emp = db.get(Employee, emp_id)
            if emp is None:
                print(f"  LOI    khai tay {uid} -> id {emp_id}: khong co ho so nay")
                continue
            manual.append((uid, node, emp))
        if manual:
            print("\n=== DONG DAU (nguoi chot tay) ===")
        n_manual = stamp_employees(db, manual, args.apply)

        if args.apply:
            db.commit()

        def _name(row):
            uid, node = row[0], row[1]
            live = "on " if node.get("isActive") else "off"
            return (f"{live} {(node.get('displayName') or ''):<26} "
                    f"{_norm_email(node.get('email')):<36}")

        _report("HO SO ERP TRUNG — mot email ra nhieu ho so",
                buckets["erp_trung"], tickets,
                lambda r: _name(r) + "ho so: "
                + ", ".join(f"id {e.id} (pb {e.department_id})" for e in r[2]))
        _report("TAI KHOAN APP CU TRUNG — mot email ra nhieu UID",
                buckets["app_cu_trung"], tickets,
                lambda r: _name(r) + f"ho so: id {r[2].id}  uid {r[0]}")
        _report("EMAIL KHAC NHAU MA TEN TRUNG — GOI Y, dai ca chot roi ghi vao "
                "USER_MANUAL_MAP",
                buckets["goi_y_ten"], tickets,
                lambda r: _name(r) + "co the la: " + ", ".join(
                    f"id {e.id} \"{e.full_name}\" <{e.email or 'chua co email'}>"
                    for e in r[2]) + f"   uid {r[0]}")
        _report("KHONG THAY HO SO — ca email lan ten deu khong co ben ERP",
                buckets["khong_thay"], tickets, _name)
        _report("DA CHOT BO", buckets["bo"], tickets,
                lambda r: _name(r) + f"ly do: {r[2]}")

        done = sum(1 for _, _, e in buckets["khop"] + manual if e.legacy_id)
        cho = sum(len(buckets[k]) for k in
                  ("erp_trung", "app_cu_trung", "goi_y_ten", "khong_thay"))
        print(f"\n  tai khoan app cu   : {len(users)}")
        print(f"  dong dau tu dong   : {n_auto}")
        print(f"  dong dau chot tay  : {n_manual}")
        print(f"  da co dau tu truoc : {done - n_auto - n_manual if args.apply else done}")
        print(f"  cho nguoi chot     : {cho}")
        print(f"  da chot bo         : {len(buckets['bo'])}")
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
