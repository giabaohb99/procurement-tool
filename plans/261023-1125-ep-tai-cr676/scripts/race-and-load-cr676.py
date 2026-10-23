"""Ép tải duoc-CR-676 trên MySQL THẬT: tranh chấp đồng thời + tải HTTP.

Chạy TRONG container api (gọi thẳng uvicorn, không qua nginx):
    docker compose cp plans/261023-1125-ep-tai-cr676/scripts/race-and-load-cr676.py api:/tmp/r.py
    docker compose exec -T api python /tmp/r.py > plans/261023-1125-ep-tai-cr676/results/concurrent.json

Dựng 51 hồ sơ `ST676-xx` + tài khoản qua ORM (không `mysql -e` có chữ Việt), mở phiên + phát vé thẳng
qua `start_session` / `create_access_token` (cổng `/api/auth/login` có trần lượt / phút → 429),
chạy xong thì xóa sạch hồ sơ, tài khoản, đề nghị, phiên. Người duyệt = admin (quản trị hệ thống).
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import sys
import time

import httpx

import app.core.all_models  # noqa: F401 — nạp đủ model trước khi truy vấn
from app.core.auth import create_access_token, hash_password, perm_cache_clear
from app.core.database import SessionLocal
from app.modules.employee.change_request_model import EmployeeChangeRequest
from app.modules.employee.model import Employee
from app.modules.login_session.model import LoginSession
from app.modules.login_session.service import start_session
from app.modules.user.model import User

BASE = "http://127.0.0.1:8000"
PREFIX = "ST676-"
N_EMP = 51
PWD = "St676-Pass!x"


def setup() -> list[tuple[int, str]]:
    db = SessionLocal()
    try:
        cleanup(db)
        out = []
        for i in range(N_EMP):
            emp = Employee(code=f"{PREFIX}{i:02d}", full_name=f"Ep tai {i}", major="goc", is_active=True)
            db.add(emp)
            db.flush()
            user = User(email=f"st676-{i}@local.test", password_hash=hash_password(PWD), employee_id=emp.id,
                        is_active=True)
            db.add(user)
            db.flush()
            out.append((emp.id, _token(db, user)))
        db.commit()
        return out
    finally:
        db.close()


def _token(db, user) -> dict:
    sess = start_session(db, user, ip="127.0.0.1", user_agent="ep-tai-cr676")
    return {"Authorization": f"Bearer {create_access_token(user.id, sess.token_id, sess.token_version)}"}


def admin_headers() -> dict:
    db = SessionLocal()
    try:
        h = _token(db, db.query(User).filter(User.email == "admin").first() or db.get(User, 1))
        db.commit()
        return h
    finally:
        db.close()


def cleanup(db) -> None:
    ids = [e.id for e in db.query(Employee).filter(Employee.code.like(f"{PREFIX}%"))]
    if ids:
        db.query(EmployeeChangeRequest).filter(EmployeeChangeRequest.employee_id.in_(ids)).delete(False)
        uids = [u.id for u in db.query(User).filter(User.employee_id.in_(ids))]
        db.query(LoginSession).filter(LoginSession.user_id.in_(uids)).delete(False)
        db.query(User).filter(User.employee_id.in_(ids)).delete(False)
        db.query(Employee).filter(Employee.id.in_(ids)).delete(False)
        db.commit()
    perm_cache_clear()


def submit(c, h, major: str):
    return c.post("/api/employees/me/change-requests", headers=h, json={"personal": {"major": major}})


def parallel(fns):
    with cf.ThreadPoolExecutor(max_workers=len(fns)) as ex:
        return list(ex.map(lambda f: f(), fns))


def race_double_submit(c, h, eid) -> dict:
    res = parallel([lambda k=k: submit(c, h, f"trung-{k}") for k in range(20)])
    codes = sorted(r.status_code for r in res)
    db = SessionLocal()
    pending = db.query(EmployeeChangeRequest).filter_by(employee_id=eid, status=1).count()
    db.close()
    return {"codes": {s: codes.count(s) for s in set(codes)}, "pending_in_db": pending,
            "ok": codes.count(200) == 1 and pending == 1 and set(codes) <= {200, 409}}


def race_withdraw_vs_approve(c, h_emp, h_admin, eid, rounds=50) -> dict:
    bad, tally = [], {"approved": 0, "withdrawn": 0}
    for i in range(rounds):
        rid = submit(c, h_emp, f"rut-duyet-{i}").json()["data"]["id"]
        w, a = parallel([lambda: c.post(f"/api/employees/me/change-requests/{rid}/withdraw", headers=h_emp),
                         lambda: c.post(f"/api/employees/change-requests/{rid}/approve", headers=h_admin)])
        db = SessionLocal()
        st = db.get(EmployeeChangeRequest, rid).status
        major = db.get(Employee, eid).major
        db.close()
        ok = (st == 2 and major == f"rut-duyet-{i}" and a.status_code == 200 and w.status_code == 409) or \
             (st == 4 and major != f"rut-duyet-{i}" and w.status_code == 200 and a.status_code == 409)
        tally["approved" if st == 2 else "withdrawn"] += 1
        if not ok:
            bad.append({"round": i, "status": st, "major": major, "withdraw": w.status_code, "approve": a.status_code})
    return {"rounds": rounds, **tally, "inconsistent": bad, "ok": not bad}


def race_approve_vs_reject(c, h_emp, h_admin, rounds=30) -> dict:
    bad = []
    for i in range(rounds):
        rid = submit(c, h_emp, f"duyet-tuchoi-{i}").json()["data"]["id"]
        a, r = parallel([lambda: c.post(f"/api/employees/change-requests/{rid}/approve", headers=h_admin),
                         lambda: c.post(f"/api/employees/change-requests/{rid}/reject", headers=h_admin,
                                        json={"reason": "ep tai"})])
        if sorted([a.status_code, r.status_code]) != [200, 409]:
            bad.append({"round": i, "approve": a.status_code, "reject": r.status_code})
    return {"rounds": rounds, "bad": bad, "ok": not bad}


def pct(v, p):
    return round(sorted(v)[min(len(v) - 1, int(len(v) * p))], 1) if v else None


def timed(c, method, path, h, body=None):
    t0 = time.perf_counter()
    try:
        r = c.request(method, path, headers=h, json=body, timeout=90)
        return (time.perf_counter() - t0) * 1000, r.status_code
    except httpx.HTTPError as exc:
        return (time.perf_counter() - t0) * 1000, exc.__class__.__name__


def summarize(calls):
    ok = [ms for ms, s in calls if s == 200]
    return {"calls": len(calls), "ok": len(ok), "errors": sorted({str(s) for _, s in calls if s != 200}),
            "p50_ms": pct(ok, .5), "p95_ms": pct(ok, .95), "max_ms": round(max(ok), 1) if ok else None}


def load_hr(c, h_admin, rid) -> dict:
    paths = ["/api/employees/change-requests?status=1&page_size=50", "/api/employees/change-requests/pending-count",
             f"/api/employees/change-requests/{rid}"]
    out = {}
    for n in (1, 10, 50, 150):
        jobs = [lambda p=p: timed(c, "GET", p, h_admin) for _ in range(n) for p in paths]
        t0 = time.perf_counter()
        with cf.ThreadPoolExecutor(max_workers=min(len(jobs), 300)) as ex:
            calls = list(ex.map(lambda f: f(), jobs))
        out[f"{n}x"] = {**summarize(calls), "wall_s": round(time.perf_counter() - t0, 1)}
        print(f"HR {n:>3}: {out[f'{n}x']}", file=sys.stderr, flush=True)
        time.sleep(2)
    return out


def load_submit(c, heads) -> dict:
    jobs = [lambda h=h: timed(c, "POST", "/api/employees/me/change-requests", h, {"personal": {"major": "tai"}})
            for h in heads]
    with cf.ThreadPoolExecutor(max_workers=len(jobs)) as ex:
        return summarize(list(ex.map(lambda f: f(), jobs)))


def main():
    emps = setup()
    limits = httpx.Limits(max_connections=500, max_keepalive_connections=500)
    results = {}
    try:
        with httpx.Client(base_url=BASE, limits=limits, timeout=90) as c:
            h_admin = admin_headers()
            heads = [h for _, h in emps]
            eid0, h0 = emps[0][0], heads[0]
            results["double_submit_20"] = race_double_submit(c, h0, eid0)
            #  dọn đề nghị đang chờ của người 0 trước các vòng sau
            rid = c.get("/api/employees/me/change-requests", headers=h0).json()["data"]["items"][0]["id"]
            c.post(f"/api/employees/me/change-requests/{rid}/withdraw", headers=h0)
            results["withdraw_vs_approve"] = race_withdraw_vs_approve(c, h0, h_admin, eid0)
            results["approve_vs_reject"] = race_approve_vs_reject(c, h0, h_admin)
            for k in ("double_submit_20", "withdraw_vs_approve", "approve_vs_reject"):
                print(k, json.dumps(results[k], ensure_ascii=False)[:300], file=sys.stderr, flush=True)
            results["submit_50_at_once"] = load_submit(c, heads[1:])
            print("submit50", results["submit_50_at_once"], file=sys.stderr, flush=True)
            pending_rid = c.get("/api/employees/me/change-requests", headers=heads[1]).json()["data"]["items"][0]["id"]
            results["hr_load"] = load_hr(c, h_admin, pending_rid)
    finally:
        db = SessionLocal()
        cleanup(db)
        db.close()
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
