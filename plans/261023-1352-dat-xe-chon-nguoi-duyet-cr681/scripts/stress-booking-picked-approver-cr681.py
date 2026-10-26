"""Ép tải duoc-CR-681 trên MySQL THẬT qua HTTP (uvicorn trong container api).

    docker compose cp plans/261023-1352-dat-xe-chon-nguoi-duyet-cr681/scripts/stress-booking-picked-approver-cr681.py api:/tmp/s.py
    docker compose exec -T api env PYTHONPATH=/app python /tmp/s.py

Dựng 60 người tạo phiếu + 6 điều phối (phạm vi công ty, rải 3 pháp nhân) tên `ST681-*`, một luồng thử
cách 9 ưu tiên cao. Đo:
  A. 60 người cùng GỬI DUYỆT (bộ máy BẬT), mỗi người chọn ngẫu nhiên một điều phối (bất kể công ty):
     mỗi phiếu đúng 1 việc chờ, giao đúng người đã chọn, đúng 1 thư `dx_submitted` tới người đó.
  B. Như A nhưng bộ máy TẮT: chuông + thư chỉ tới người đã chọn.
  C. 150 lượt GET /pick-options cùng lúc.
  D. Chọn người không có quyền / chính mình / công ty không tồn tại → 422, không tạo phiếu.
Xong dọn sạch (phiếu, phiên, việc, chuông, thư, luồng, tài khoản, vai trò).
"""
import concurrent.futures as cf
import json
import random
import time
from types import SimpleNamespace

import httpx

import app.core.all_models  # noqa: F401
from app.core.auth import create_access_token, perm_cache_clear
from app.core.database import SessionLocal
from app.modules.approval.flow_model import (APPROVER_PERMISSION, SKIP_NONE, ApprovalFlow, ApprovalNode,
                                             ApprovalSwitch)
from app.modules.approval.instance_model import ApprovalAction, ApprovalInstance, ApprovalTask
from app.modules.employee.model import Employee
from app.modules.login_session.model import LoginSession
from app.modules.login_session.service import start_session
from app.modules.notification.model import EmailLog, Notification
from app.modules.role.model import Permission, Role
from app.modules.user.model import User, UserRole
from app.modules.vehicle_booking.model import VehicleBooking

BASE = "http://127.0.0.1:8000"
PREFIX = "ST681-"
N_CREATORS, N_APPROVERS = 60, 6
rnd = random.Random(681)
VIEWERS: dict = {}


def _token(db, user):
    sess = start_session(db, user, ip="127.0.0.1", user_agent="ep-tai-cr681")
    return {"Authorization": f"Bearer {create_access_token(user.id, sess.token_id, sess.token_version)}"}


def cleanup(db):
    flows = [f.id for f in db.query(ApprovalFlow).filter(ApprovalFlow.code == f"{PREFIX}FLOW")]
    bookings = [b.id for b in db.query(VehicleBooking).filter(VehicleBooking.purpose.like(f"{PREFIX}%"))]
    if bookings:
        inst = [i.id for i in db.query(ApprovalInstance).filter(ApprovalInstance.entity == "vehicle_booking",
                                                               ApprovalInstance.entity_id.in_(bookings))]
        if inst:
            db.query(ApprovalTask).filter(ApprovalTask.instance_id.in_(inst)).delete(False)
            db.query(ApprovalAction).filter(ApprovalAction.instance_id.in_(inst)).delete(False)
            db.query(ApprovalInstance).filter(ApprovalInstance.id.in_(inst)).delete(False)
        db.query(Notification).filter(Notification.link.in_([f"/vehicle-booking/{b}" for b in bookings]
                                                            + [f"/vehicle-bookings/{b}" for b in bookings])).delete(False)
        db.query(VehicleBooking).filter(VehicleBooking.id.in_(bookings)).delete(False)
    db.query(EmailLog).filter(EmailLog.to_email.like("st681-%")).delete(False)
    if flows:
        db.query(ApprovalNode).filter(ApprovalNode.flow_id.in_(flows)).delete(False)
        db.query(ApprovalFlow).filter(ApprovalFlow.id.in_(flows)).delete(False)
    emps = [e.id for e in db.query(Employee).filter(Employee.code.like(f"{PREFIX}%"))]
    users = [u.id for u in db.query(User).filter(User.employee_id.in_(emps))] if emps else []
    if users:
        db.query(Notification).filter(Notification.user_id.in_(users)).delete(False)
        db.query(LoginSession).filter(LoginSession.user_id.in_(users)).delete(False)
        db.query(UserRole).filter(UserRole.user_id.in_(users)).delete(False)
        db.query(User).filter(User.id.in_(users)).delete(False)
    if emps:
        db.query(Employee).filter(Employee.id.in_(emps)).delete(False)
    roles = [r.id for r in db.query(Role).filter(Role.code.like(f"{PREFIX}%"))]
    if roles:
        db.query(Permission).filter(Permission.role_id.in_(roles)).delete(False)
        db.query(Role).filter(Role.id.in_(roles)).delete(False)
    db.commit()
    perm_cache_clear()


def setup(db):
    cleanup(db)
    creator_role = Role(code=f"{PREFIX}creator", name="ST681 người đặt xe")
    approver_role = Role(code=f"{PREFIX}approver", name="ST681 điều phối công ty")
    db.add_all([creator_role, approver_role])
    db.flush()
    db.add_all([Permission(role_id=creator_role.id, entity="vehicle_booking", can_read=True, can_create=True,
                           can_write=True, scope="own"),
                Permission(role_id=approver_role.id, entity="vehicle_booking", can_read=True, can_approve=True,
                           scope="company")])
    companies = [c for (c,) in db.query(Employee.company_id).filter(Employee.company_id > 0).distinct().limit(3)]

    def person(code, role, company):
        emp = Employee(code=code, full_name=f"Ep tai {code}", company_id=company, is_active=True)
        db.add(emp)
        db.flush()
        user = User(email=f"st681-{code.lower()}@local.test", employee_id=emp.id, is_active=True)
        db.add(user)
        db.flush()
        db.add(UserRole(user_id=user.id, role_id=role.id))
        return user

    approvers = [person(f"{PREFIX}A{i}", approver_role, companies[i % len(companies)]) for i in range(N_APPROVERS)]
    viewer_role = Role(code=f"{PREFIX}viewer", name="ST681 xem phạm vi công ty")
    db.add(viewer_role)
    db.flush()
    db.add(Permission(role_id=viewer_role.id, entity="vehicle_booking", can_read=True, scope="company"))
    viewers = {cid: person(f"{PREFIX}V{cid}", viewer_role, cid) for cid in companies}
    creators = [person(f"{PREFIX}C{i:02d}", creator_role, companies[i % len(companies)]) for i in range(N_CREATORS)]
    flow = ApprovalFlow(entity="vehicle_booking", code=f"{PREFIX}FLOW", name="ST681 theo quyền", is_active=True,
                        priority=999, created_by=1, updated_by=1)
    db.add(flow)
    db.flush()
    db.add(ApprovalNode(flow_id=flow.id, seq=1, name="Người duyệt đã chọn", approver_kind=APPROVER_PERMISSION,
                        approver_ref="vehicle_booking", skip_duplicate=SKIP_NONE, created_by=1, updated_by=1))
    db.commit()
    heads = {u.id: _token(db, u) for u in creators + approvers + list(viewers.values())}
    db.commit()
    global VIEWERS
    VIEWERS = {cid: SimpleNamespace(id=u.id) for cid, u in viewers.items()}
    #  Bản chụp GIÁ TRỊ — luồng con không được đụng đối tượng ORM của phiên này (hết hạn sau commit).
    plain = lambda u: SimpleNamespace(id=u.id, employee_id=u.employee_id, email=u.email)  # noqa: E731
    return [plain(u) for u in creators], [plain(u) for u in approvers], heads, companies


def set_engine(db, on: bool):
    row = db.query(ApprovalSwitch).filter_by(entity="vehicle_booking").first()
    before = bool(row and row.is_enabled)
    if row is None:
        row = ApprovalSwitch(entity="vehicle_booking", is_enabled=on)
        db.add(row)
    row.is_enabled = on
    db.commit()
    return before


def body(tag, company, approver_id):
    return {"request_type": 1, "purpose": f"{PREFIX}{tag}", "start_location": "VP", "end_location": "Q7",
            "start_time": "2026-12-01T08:00", "end_time": "2026-12-01T10:00", "passenger_count": 1,
            "company_id": company, "first_approver_id": approver_id}


def pct(v, p):
    return round(sorted(v)[min(len(v) - 1, int(len(v) * p))], 1) if v else None


def submit_wave(c, creators, approvers, heads, companies, tag):
    picks = {u.id: rnd.choice(approvers) for u in creators}
    chosen = {u.id: rnd.choice(companies) for u in creators}

    def one(u):
        t0 = time.perf_counter()
        r = c.post("/api/vehicle-bookings", params={"submit": "true"}, headers=heads[u.id],
                   json=body(f"{tag}-{u.id}", chosen[u.id], picks[u.id].id))
        payload = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        if r.status_code != 201:
            print("FAIL", r.status_code, json.dumps(payload, ensure_ascii=False)[:300], flush=True)
        return (time.perf_counter() - t0) * 1000, r.status_code, (payload.get("data") or {}).get("id")

    t0 = time.perf_counter()
    with cf.ThreadPoolExecutor(max_workers=len(creators)) as ex:
        res = list(ex.map(one, creators))
    wall = time.perf_counter() - t0
    ok = [ms for ms, st, _ in res if st == 201]
    picks["_chosen"] = chosen
    return picks, res, {"calls": len(res), "ok": len(ok), "codes": sorted({st for _, st, _ in res}),
                        "p50_ms": pct(ok, .5), "p95_ms": pct(ok, .95), "max_ms": round(max(ok), 1) if ok else None,
                        "wall_s": round(wall, 1)}


def check_engine(db, picks, res, creators):
    bad = []
    for u, (_, st, bid) in zip(creators, res):
        if st != 201:
            bad.append({"status": st})
            continue
        picked = picks[u.id]
        inst = db.query(ApprovalInstance).filter_by(entity="vehicle_booking", entity_id=bid).all()
        tasks = [t for i in inst for t in db.query(ApprovalTask).filter_by(instance_id=i.id, status=2)]
        mails = db.query(EmailLog).filter(EmailLog.event == "dx_submitted", EmailLog.to_email == picked.email,
                                          EmailLog.subject.like(f"%{db.get(VehicleBooking, bid).code}%")).count()
        if len(inst) != 1 or [t.assignee_employee_id for t in tasks] != [picked.employee_id] or mails != 1:
            bad.append({"booking": bid, "instances": len(inst), "tasks": [t.assignee_employee_id for t in tasks],
                        "picked": picked.employee_id, "mails": mails})
    return bad


def check_legacy(db, picks, res, creators):
    bad = []
    for u, (_, st, bid) in zip(creators, res):
        if st != 201:
            bad.append({"status": st})
            continue
        picked = picks[u.id]
        code = db.get(VehicleBooking, bid).code
        bells = {n.user_id for n in db.query(Notification).filter(Notification.title.like(f"%{code}%"))}
        mails = {e.to_email for e in db.query(EmailLog).filter(EmailLog.event == "dx_submitted",
                                                               EmailLog.subject.like(f"%{code}%"))}
        inst = db.query(ApprovalInstance).filter_by(entity="vehicle_booking", entity_id=bid).count()
        if bells != {picked.id} or mails != {picked.email} or inst:
            bad.append({"booking": bid, "bells": sorted(bells), "mails": sorted(mails), "instances": inst})
    return bad


def main():
    db = SessionLocal()
    results = {}
    engine_before = None
    try:
        creators, approvers, heads, companies = setup(db)
        engine_before = set_engine(db, True)
        limits = httpx.Limits(max_connections=400, max_keepalive_connections=400)
        with httpx.Client(base_url=BASE, limits=limits, timeout=120) as c:
            picks, res, stats = submit_wave(c, creators, approvers, heads, companies, "BAT")
            time.sleep(3)   # thư gửi bằng background task sau khi trả lời
            db.expire_all()
            results["A_engine_on_60_submits"] = {**stats, "wrong": check_engine(db, picks, res, creators)}
            print("A", json.dumps(results["A_engine_on_60_submits"], ensure_ascii=False)[:400], flush=True)
            #  Anh Được 24/10: viewer phạm vi công ty ở công ty NGƯỜI TẠO và công ty CHỌN đều mở được phiếu.
            emp_company = {e.id: e.company_id for e in db.query(Employee).filter(Employee.code.like(f"{PREFIX}C%"))}
            user_emp = {u.id: u.employee_id for u in creators}
            seen_both, other_blocked, cross = 0, 0, 0
            for u, (_, st, bid) in zip(creators, res):
                own_cid, picked_cid = emp_company[user_emp[u.id]], picks["_chosen"][u.id]
                if own_cid == picked_cid:
                    continue
                cross += 1
                ok_own = c.get(f"/api/vehicle-bookings/{bid}", headers=heads[VIEWERS[own_cid].id]).status_code == 200
                ok_pick = c.get(f"/api/vehicle-bookings/{bid}", headers=heads[VIEWERS[picked_cid].id]).status_code == 200
                third = [cid for cid in VIEWERS if cid not in (own_cid, picked_cid)]
                blocked = (not third) or c.get(f"/api/vehicle-bookings/{bid}",
                                               headers=heads[VIEWERS[third[0]].id]).status_code == 404
                seen_both += ok_own and ok_pick
                other_blocked += blocked
            results["F_both_companies_see"] = {"cross_company_bookings": cross, "both_see": seen_both,
                                               "third_company_404": other_blocked}
            print("F", results["F_both_companies_see"], flush=True)
            #  Thư đi qua worker Celery THẬT: sau vài giây dòng EmailLog phải rời trạng thái `pending`.
            time.sleep(8)
            db.expire_all()
            logs = db.query(EmailLog).filter(EmailLog.to_email.like("st681-%"), EmailLog.event == "dx_submitted").all()
            results["G_worker_processed"] = {"logs": len(logs),
                                             "still_pending": sum(1 for x in logs if x.status == "pending"),
                                             "statuses": sorted({x.status for x in logs})}
            print("G", results["G_worker_processed"], flush=True)

            set_engine(db, False)
            picks, res, stats = submit_wave(c, creators, approvers, heads, companies, "TAT")
            time.sleep(3)
            db.expire_all()
            results["B_engine_off_60_submits"] = {**stats, "wrong": check_legacy(db, picks, res, creators)}
            #  Review H1: người được chọn (phạm vi CÔNG TY KHÁC phiếu) phải mở được phiếu và bấm Duyệt được.
            acts = []
            for u, (_, st, bid) in zip(creators, res):
                if st != 201:
                    continue
                h = heads[picks[u.id].id]
                acts.append((c.get(f"/api/vehicle-bookings/{bid}", headers=h).status_code,
                             c.post(f"/api/vehicle-bookings/{bid}/approve", headers=h).status_code))
            results["B2_picked_can_open_and_approve"] = {
                "checked": len(acts), "open_200": sum(1 for g, _ in acts if g == 200),
                "approve_200": sum(1 for _, a in acts if a == 200)}
            print("B2", results["B2_picked_can_open_and_approve"], flush=True)
            print("B", json.dumps(results["B_engine_off_60_submits"], ensure_ascii=False)[:400], flush=True)

            h = heads[creators[0].id]
            def get_options(_):
                t0 = time.perf_counter()
                status = c.get("/api/vehicle-bookings/pick-options", headers=h).status_code
                return (time.perf_counter() - t0) * 1000, status

            with cf.ThreadPoolExecutor(max_workers=150) as ex:
                calls = list(ex.map(get_options, range(150)))
            ok = [ms for ms, st in calls if st == 200]
            results["C_pick_options_150"] = {"ok": len(ok), "p50_ms": pct(ok, .5), "p95_ms": pct(ok, .95)}
            print("C", results["C_pick_options_150"], flush=True)

            u0, other_creator = creators[0], creators[1]
            before = db.query(VehicleBooking).filter(VehicleBooking.purpose.like(f"{PREFIX}%")).count()
            codes = {
                "creator_as_approver": c.post("/api/vehicle-bookings", params={"submit": "true"}, headers=heads[u0.id],
                                              json=body("X1", companies[0], other_creator.id)).status_code,
                "self": c.post("/api/vehicle-bookings", params={"submit": "true"}, headers=heads[u0.id],
                               json=body("X2", companies[0], u0.id)).status_code,
                "bad_company": c.post("/api/vehicle-bookings", params={"submit": "true"}, headers=heads[u0.id],
                                      json=body("X3", 987654, approvers[0].id)).status_code,
            }
            db.expire_all()
            after = db.query(VehicleBooking).filter(VehicleBooking.purpose.like(f"{PREFIX}%")).count()
            results["D_bad_picks"] = {"codes": codes, "created": after - before}
            all_codes = [b.code for b in db.query(VehicleBooking).filter(VehicleBooking.purpose.like(f"{PREFIX}%"))]
            results["E_codes"] = {"bookings": len(all_codes), "unique": len(set(all_codes)),
                                  "all_dx": all(code.startswith("DX") for code in all_codes)}
            print("E", results["E_codes"], flush=True)
            print("D", results["D_bad_picks"], flush=True)
    finally:
        if engine_before is not None:
            set_engine(db, engine_before)
        cleanup(db)
        db.close()
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
