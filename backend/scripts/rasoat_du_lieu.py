"""RÀ SOÁT (CHỈ ĐỌC — không sửa gì) trên môi trường đang chạy.

1. Công nợ âm / lệch (hệ quả lỗi phân bổ tiền đã fix ở commit 82ce6ad)
2. Dòng ĐMH bị kẹt (đủ điều kiện tiến bước nhưng trạng thái chưa tiến)
3. Tài khoản mồ côi (không gắn hồ sơ nhân sự / nhân sự đã xoá)
4. Tài khoản chưa được gán vai trò

Chạy TRONG container api:
    docker compose exec -T api python -m scripts.rasoat_du_lieu                 # local
    docker exec -e PYTHONPATH=/app <api> python /tmp/rasoat_du_lieu.py          # VPS (docker cp vào trước)
"""
import sys

from app.core import all_models  # noqa: F401  (nạp đủ model cho mapper)
from app.core.database import SessionLocal
from app.modules.employee.model import Employee
from app.modules.payable.model import Payable
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_order.service import (PROG_CANCELLED, PROG_COMPLETED, PROG_PAUSED,
                                                PROGRESS_ORDER, highest_satisfied_step)
from app.modules.role.model import Role
from app.modules.user.model import User, UserRole

db = SessionLocal()
out = []


def p(s=""):
    out.append(str(s))
    print(s, flush=True)


# ---------------------------------------------------------------- 1. CÔNG NỢ
p("=" * 78)
p("1. CÔNG NỢ ÂM / LỆCH")
p("=" * 78)
pays = db.query(Payable).all()
neg, mismatch = [], []
for x in pays:
    total, paid, rem = float(x.total or 0), float(x.paid_amount or 0), float(x.remaining or 0)
    if total - paid < -0.01:
        neg.append(x)
    if abs(rem - (total - paid)) > 0.01:
        mismatch.append(x)
p(f"Tổng khoản nợ: {len(pays)}")
p(f"Trả DƯ (paid > total): {len(neg)}")
for x in neg:
    p(f"  - #{x.id} {x.po_code or '-':<12} HĐ {x.invoice_no or '-':<12} {x.supplier_name[:28]:<28} "
      f"total={float(x.total or 0):>15,.0f} paid={float(x.paid_amount or 0):>15,.0f} "
      f"du={float(x.paid_amount or 0) - float(x.total or 0):>13,.0f} [{x.status}]")
p(f"Cột remaining lệch (total-paid): {len(mismatch)}")
for x in mismatch[:30]:
    p(f"  - #{x.id} {x.po_code or '-':<12} remaining={float(x.remaining or 0):>15,.0f} "
      f"nhung total-paid={float(x.total or 0) - float(x.paid_amount or 0):>15,.0f}")

# khoản còn nợ nhưng cùng (po_code, invoice_no) đã có khoản trả dư -> dấu hiệu bị dồn tiền
p("")
p("Nhóm (ĐMH + số HĐ) vừa có khoản trả DƯ vừa có khoản CÒN NỢ (dấu hiệu bị dồn tiền):")
g = {}
for x in pays:
    g.setdefault((x.po_code or "", (x.invoice_no or "").strip()), []).append(x)
suspect = 0
for k, items in g.items():
    if not k[1]:
        continue
    du = [i for i in items if float(i.total or 0) - float(i.paid_amount or 0) < -0.01]
    no = [i for i in items if float(i.total or 0) - float(i.paid_amount or 0) > 0.01]
    if du and no:
        suspect += 1
        p(f"  - {k[0]} / HĐ {k[1]}: du={[i.id for i in du]} conno={[i.id for i in no]}")
p(f"  => {suspect} nhóm")

# ------------------------------------------------------------ 2. DÒNG ĐMH KẸT
p("")
p("=" * 78)
p("2. DÒNG ĐMH ĐỦ ĐIỀU KIỆN NHƯNG TRẠNG THÁI CHƯA TIẾN")
p("=" * 78)
items = (db.query(POItem)
         .filter(POItem.progress_status.notin_([PROG_COMPLETED, PROG_CANCELLED, PROG_PAUSED]))
         .all())
p(f"Số dòng đang mở: {len(items)}")
stuck = []
po_cache = {}
for it in items:
    po = po_cache.get(it.po_id) or db.get(PurchaseOrder, it.po_id)
    if not po:
        continue
    po_cache[it.po_id] = po
    cur = PROGRESS_ORDER.index(it.progress_status) if it.progress_status in PROGRESS_ORDER else 0
    top = highest_satisfied_step(db, po, it)
    if top > cur:
        stuck.append((po, it, it.progress_status, PROGRESS_ORDER[top]))
p(f"Dòng lẽ ra phải tiến: {len(stuck)}  (trong đó lên '{PROG_COMPLETED}': "
  f"{sum(1 for s in stuck if s[3] == PROG_COMPLETED)})")
for po, it, cur, tgt in stuck[:60]:
    p(f"  - {po.code:<12} dong#{it.id:<6} {(it.product_name or '')[:32]:<32} {cur:<22} -> {tgt}")

# --------------------------------------------------------- 3+4. TÀI KHOẢN
p("")
p("=" * 78)
p("3. TÀI KHOẢN MỒ CÔI / CHƯA GÁN VAI TRÒ")
p("=" * 78)
users = db.query(User).all()
emps = {e.id: e for e in db.query(Employee).all()}
roles = {r.id: r for r in db.query(Role).all()}
by_user = {}
for ur in db.query(UserRole).all():
    by_user.setdefault(ur.user_id, []).append(ur.role_id)

orphan_no_emp, orphan_dead_emp, no_role, emp_inactive = [], [], [], []
for u in users:
    e = emps.get(u.employee_id) if u.employee_id else None
    if not u.employee_id:
        orphan_no_emp.append(u)
    elif not e:
        orphan_dead_emp.append(u)
    elif not e.is_active:
        emp_inactive.append(u)
    if not by_user.get(u.id):
        no_role.append(u)

p(f"Tổng tài khoản: {len(users)}  (đang hoạt động: {sum(1 for u in users if u.is_active)})")


def show(title, lst):
    p("")
    p(f"{title}: {len(lst)}")
    for u in lst:
        e = emps.get(u.employee_id) if u.employee_id else None
        rn = ", ".join(roles[r].name for r in by_user.get(u.id, []) if r in roles) or "—"
        p(f"  - #{u.id:<5} email={u.email or '(rong)':<40} emp_id={u.employee_id or 0:<6} "
          f"nhansu={(e.code + ' ' + e.full_name) if e else '(KHONG CO)':<32} "
          f"active={int(bool(u.is_active))} vaitro={rn}")


show("A. Không gắn nhân sự (employee_id = 0)", orphan_no_emp)
show("B. Nhân sự đã bị xoá (employee_id trỏ vào hồ sơ không còn)", orphan_dead_emp)
show("C. Nhân sự đã nghỉ (is_active = 0)", emp_inactive)
show("D. Chưa gán vai trò nào", no_role)

# dấu vết hoạt động của các tài khoản mồ côi / chưa gán quyền
p("")
p("Dấu vết hoạt động (nhật ký thao tác + chứng từ đã tạo) của các tài khoản trên:")
from sqlalchemy import text  # noqa: E402
cand = {u.id for u in orphan_no_emp + orphan_dead_emp + no_role}
if cand:
    ids = ",".join(str(i) for i in sorted(cand))
    rows = db.execute(text(
        f"SELECT created_by, COUNT(*) c FROM tab_audit_log WHERE created_by IN ({ids}) GROUP BY created_by")).all()
    amap = {r[0]: r[1] for r in rows}
    tables = ["tab_purchase_request", "tab_purchase_order", "tab_survey",
              "tab_survey_request", "tab_payment_request", "tab_ticket"]
    dmap = {}
    for t in tables:
        try:
            rows = db.execute(text(
                f"SELECT created_by, COUNT(*) c FROM {t} WHERE created_by IN ({ids}) GROUP BY created_by")).all()
        except Exception:
            continue
        for uid, c in rows:
            dmap.setdefault(uid, []).append(f"{t.replace('tab_', '')}={c}")
    for uid in sorted(cand):
        p(f"  - #{uid:<5} nhat_ky={amap.get(uid, 0):<5} chung_tu={', '.join(dmap.get(uid, [])) or 'khong co'}")

db.close()
with open("/tmp/rasoat.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("\n[da ghi /tmp/rasoat.txt]", file=sys.stderr)
