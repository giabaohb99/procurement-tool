"""ĐỀ XUẤT gói quyền mặc định cho từng chức vụ từ vai trò người đang giữ (duoc-CR-653).

Với mỗi chức vụ: đếm các tài khoản đang giữ chức vụ (hồ sơ còn làm, tài khoản đang mở), xem mỗi
vai trò có bao nhiêu người trong số đó giữ. Vai trò có tỷ lệ >= ngưỡng (mặc định 60%) được ĐỀ XUẤT vào gói.
Không bao giờ đề xuất: vai trò quản trị (admin/ADMINISTRATOR) và vai trò có ghi/tạo/xóa trên Vai trò / Tài khoản
(review CR-653 M4/M5). Mặc định chỉ đề xuất chức vụ có >= 3 người (mẫu nhỏ thì cả bộ vai trò của một người thành "gói").

Mặc định CHỈ ĐỌC (dry-run), in ra Markdown (hoặc CSV bằng --format csv).
`--apply --yes` mới ghi gói vào `tab_job_position_role` — chỉ THÊM vai trò đề xuất còn thiếu, không bớt gói
đã có, và KHÔNG cấp gì cho ai: quản trị bấm "Áp lại cho người đang giữ chức vụ" trên màn Chức vụ sau.

Chạy: docker compose exec -T api python -m scripts.de_xuat_quyen_theo_chuc_vu [--threshold 0.6]
        [--min-holders 3] [--format md|csv] [--out file] [--apply --yes]
"""
import argparse
import csv
import io
import sys

from sqlalchemy.orm import Session

DEFAULT_THRESHOLD = 0.6
DEFAULT_MIN_HOLDERS = 3


def compute_proposal(db: Session, threshold: float = DEFAULT_THRESHOLD, min_holders: int = DEFAULT_MIN_HOLDERS) -> list[dict]:
    """Chỉ đọc. Trả mỗi chức vụ một dict: holders, roles[{role_id, code, name, count, pct, proposed, in_bundle}]."""
    from app.modules.employee.position_role_service import forbidden_role_ids
    from app.modules.employee.model import Employee
    from app.modules.employee.position_model import JobPosition
    from app.modules.employee.position_role_service import employee_eligible
    from app.modules.role.model import Role
    from app.modules.user.model import User, UserRole

    forbidden = forbidden_role_ids(db)
    roles = {r.id: r for r in db.query(Role).all()}
    role_by_user: dict[int, set[int]] = {}
    for uid, rid in db.query(UserRole.user_id, UserRole.role_id).all():
        role_by_user.setdefault(uid, set()).add(rid)
    from app.modules.employee.position_model import JobPositionRole
    bundles: dict[int, set[int]] = {}
    for pid, rid in db.query(JobPositionRole.job_position_id, JobPositionRole.role_id).all():
        bundles.setdefault(pid, set()).add(rid)

    holders_by_pos: dict[int, list[int]] = {}
    for emp, user in (db.query(Employee, User).join(User, User.employee_id == Employee.id)
                      .filter(Employee.position_id > 0).all()):
        if employee_eligible(emp, user):
            holders_by_pos.setdefault(emp.position_id, []).append(user.id)

    out = []
    for pos in db.query(JobPosition).order_by(JobPosition.name, JobPosition.id).all():
        uids = holders_by_pos.get(pos.id, [])
        n = len(uids)
        counts: dict[int, int] = {}
        for uid in uids:
            for rid in role_by_user.get(uid, ()):
                if rid not in forbidden and rid in roles:
                    counts[rid] = counts.get(rid, 0) + 1
        rows = []
        for rid, c in sorted(counts.items(), key=lambda kv: (-kv[1], roles[kv[0]].name)):
            pct = c / n if n else 0.0
            rows.append({"role_id": rid, "code": roles[rid].code, "name": roles[rid].name, "count": c,
                         "pct": pct, "proposed": n >= min_holders and pct >= threshold,
                         "in_bundle": rid in bundles.get(pos.id, set())})
        out.append({"position_id": pos.id, "position_code": pos.code, "position_name": pos.name,
                    "is_active": bool(pos.is_active), "holders": n, "roles": rows,
                    "current_bundle": sorted(bundles.get(pos.id, set()))})
    return out


def render_markdown(proposal: list[dict], threshold: float, min_holders: int) -> str:
    lines = ["# Đề xuất quyền mặc định theo chức vụ", "",
             f"Ngưỡng: vai trò có ở >= {threshold:.0%} số người giữ chức vụ (và chức vụ có >= {min_holders} người). "
             "Chỉ tính tài khoản đang mở của hồ sơ còn làm; bỏ vai trò Quản trị hệ thống.", ""]
    with_roles = [p for p in proposal if p["holders"]]
    lines += [f"Tổng: {len(proposal)} chức vụ, {len(with_roles)} chức vụ có người giữ có tài khoản.", ""]
    for p in proposal:
        if not p["holders"]:
            continue
        lines += [f"## {p['position_name']} (#{p['position_id']}, {p['position_code']}) — {p['holders']} người"
                  + (" — MẪU NHỎ (<3 người), chỉ để tham khảo" if p["holders"] < 3 else ""), ""]
        if not p["roles"]:
            lines += ["_Không ai có vai trò nào._", ""]
            continue
        lines += ["| Vai trò | Số người | Tỷ lệ | Đề xuất | Đã có trong gói |", "|---|---:|---:|:-:|:-:|"]
        for r in p["roles"]:
            lines.append(f"| {r['name']} (`{r['code']}`) | {r['count']}/{p['holders']} | {r['pct']:.0%} | "
                         f"{'CÓ' if r['proposed'] else ''} | {'có' if r['in_bundle'] else ''} |")
        lines.append("")
    empty = [p["position_name"] for p in proposal if not p["holders"]]
    if empty:
        lines += ["## Chức vụ chưa có người giữ (không đề xuất được)", "", ", ".join(empty), ""]
    return "\n".join(lines)


def render_csv(proposal: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["position_id", "position_name", "holders", "role_code", "role_name", "count", "pct", "proposed", "in_bundle"])
    for p in proposal:
        for r in p["roles"]:
            w.writerow([p["position_id"], p["position_name"], p["holders"], r["code"], r["name"], r["count"],
                        f"{r['pct']:.2f}", int(r["proposed"]), int(r["in_bundle"])])
    return buf.getvalue()


def apply_proposal(db: Session, proposal: list[dict]) -> int:
    """Ghi gói (chỉ thêm). Không đụng tab_user_role. Trả số dòng gói đã thêm."""
    from app.modules.employee.position_model import JobPositionRole

    from app.core.audit import record

    added = 0
    for p in proposal:
        new = [r for r in p["roles"] if r["proposed"] and not r["in_bundle"]]
        for r in new:
            db.add(JobPositionRole(job_position_id=p["position_id"], role_id=r["role_id"]))
            added += 1
        if new:
            #  M4: mỗi chức vụ một dòng nhật ký (người thao tác 0 = script vận hành), cùng giao dịch với việc ghi gói.
            record(db, 0, "job_position", p["position_id"], "set_position_roles",
                   f"Script đề xuất ghi gói quyền mặc định của '{p['position_name']}': thêm "
                   + ", ".join(r["name"] for r in new), commit=False)
    db.commit()
    return added


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    ap.add_argument("--min-holders", type=int, default=DEFAULT_MIN_HOLDERS)
    ap.add_argument("--format", choices=["md", "csv"], default="md")
    ap.add_argument("--out", default="")
    ap.add_argument("--apply", action="store_true", help="ghi gói vào DB (cần thêm --yes)")
    ap.add_argument("--yes", action="store_true")
    args = ap.parse_args(argv)
    if not 0 < args.threshold <= 1:
        ap.error("--threshold phải trong (0, 1]")
    if args.apply and not args.yes:
        ap.error("--apply cần kèm --yes để xác nhận (mặc định chỉ chạy thử)")

    import app.core.all_models  # noqa: F401
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        proposal = compute_proposal(db, args.threshold, args.min_holders)
        text = (render_csv(proposal) if args.format == "csv"
                else render_markdown(proposal, args.threshold, args.min_holders))
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(text)
        else:
            sys.stdout.write(text + "\n")
        if args.apply:
            n = apply_proposal(db, proposal)
            print(f"[APPLY] Đã thêm {n} dòng vào gói quyền mặc định. Chưa cấp cho ai — dùng nút 'Áp lại'.",
                  file=sys.stderr)
        else:
            print("[DRY-RUN] Không ghi gì. Thêm --apply --yes để ghi gói.", file=sys.stderr)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
