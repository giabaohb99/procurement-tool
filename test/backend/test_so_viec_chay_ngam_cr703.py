"""bao-CR-703 — sổ việc chạy ngầm: ghi mỗi lần task Celery chạy, sổ mô tả lịch beat, API màn Hệ thống > Việc chạy ngầm,
dọn sổ, công cụ CHỈ ĐỌC cho Trợ lý / MCP.

Canh:
  - mọi task trong lịch beat (kể cả lịch bật theo cấu hình) đều có mô tả — thiếu là đỏ;
  - tín hiệu: bắt đầu → Đang chạy; xong → Thành công / Bỏ qua (task tự báo skipped / disabled) / Lỗi; lỗi khi ghi sổ
    KHÔNG làm hỏng task;
  - danh sách: lần chạy gần nhất, số 7 ngày, lọc nhóm / trạng thái (0 = chưa chạy) / chữ, lịch dễ đọc, lần chạy kế;
  - lịch sử một việc: phân trang, lọc trạng thái; dọn sổ quá N ngày, 0 = tắt;
  - API + công cụ gác setting.read.
"""
import re
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from celery.schedules import crontab
from fastapi.testclient import TestClient

from app.core.job_run_codes import JOB_GROUP_LABELS, JobRunStatus
from app.modules.job_run import service, signals
from app.modules.job_run.model import JobRun
from app.modules.job_run.registry import JOBS

S = JobRunStatus


class _Shared:
    """Phiên của bài kiểm cho tín hiệu dùng — close() không đóng phiên thật."""

    def __init__(self, db):
        self._db = db

    def __getattr__(self, name):
        return getattr(self._db, name)

    def close(self):
        pass


@pytest.fixture
def sig_db(db, monkeypatch):
    monkeypatch.setattr(signals, "_session", lambda: _Shared(db))
    return db


# ── Sổ mô tả ──────────────────────────────────────────────────────────────────

def test_moi_task_trong_lich_beat_deu_co_mo_ta():
    src = (Path(service.__file__).resolve().parents[2] / "core" / "celery_app.py").read_text(encoding="utf-8")
    tasks = set(re.findall(r'"task": "([a-z0-9_.]+)"', src))
    missing = sorted(tasks - set(JOBS))
    assert not missing, f"Task trong lịch beat thiếu mô tả ở job_run/registry.py: {missing}"
    assert all(info.group in JOB_GROUP_LABELS and info.name and info.purpose for info in JOBS.values())


def test_lich_de_doc():
    assert service.schedule_label(crontab(minute="*")) == "mỗi phút"
    assert service.schedule_label(crontab(minute="*/15")) == "mỗi 15 phút"
    assert service.schedule_label(crontab(hour=2, minute=45)) == "02:45 mỗi ngày"
    assert service.schedule_label(crontab(day_of_month="1,16", hour=3, minute=30)) == "03:30 ngày 1 và 16 hằng tháng"
    assert service.schedule_label(crontab(day_of_week=1, hour=5, minute=15)) == "05:15 thứ Hai hằng tuần"
    assert service.schedule_label(crontab(minute="7,17,27")) == "phút 7, 17 và 27 mỗi giờ"
    assert service.schedule_label(10.0) == "mỗi 10 giây"
    nxt = service.next_run(crontab(hour=2, minute=45))
    assert nxt is not None and (nxt.hour, nxt.minute) == (2, 45) and nxt > datetime.now() - timedelta(minutes=1)


# ── Tín hiệu ──────────────────────────────────────────────────────────────────

def _rows(db):
    db.expire_all()
    return db.query(JobRun).order_by(JobRun.id).all()


def test_tin_hieu_ghi_bat_dau_xong_bo_qua_va_loi(sig_db):
    signals.record_start("notification.cleanup", "t1", "worker@a")
    assert [(r.status, r.worker) for r in _rows(sig_db)] == [(int(S.RUNNING), "worker@a")]
    signals.record_end("notification.cleanup", "t1", "SUCCESS", {"status": "success", "deleted": 3})
    row = _rows(sig_db)[0]
    assert row.status == int(S.SUCCESS) and row.finished_at and row.duration_ms is not None
    assert '"deleted": 3' in row.result_summary

    signals.record_start("customs.merge_duplicate_lines", "t2")
    signals.record_end("customs.merge_duplicate_lines", "t2", "SUCCESS", {"status": "disabled"})
    signals.record_start("backup.run", "t3")
    signals.record_error("backup.run", "t3", RuntimeError("hết đĩa"))
    signals.record_end("backup.run", "t3", "FAILURE", RuntimeError("hết đĩa"))
    by = {r.task_id: r for r in _rows(sig_db)}
    assert by["t2"].status == int(S.SKIPPED)
    assert by["t3"].status == int(S.FAILED) and "hết đĩa" in by["t3"].error


def test_xong_ma_khong_thay_dong_bat_dau_van_ghi_du(sig_db):
    signals.record_end("coffee.reconcile", "t9", "SUCCESS", {"ok": True})
    (row,) = _rows(sig_db)
    assert (row.task_name, row.status, row.duration_ms) == ("coffee.reconcile", int(S.SUCCESS), 0)


def test_loi_ghi_so_khong_lam_hong_task(monkeypatch):
    def broken():
        raise RuntimeError("DB sập")

    monkeypatch.setattr(signals, "_session", broken)
    signals.record_start("backup.run", "x")
    signals.record_end("backup.run", "x", "SUCCESS", {})
    signals.record_error("backup.run", "x", RuntimeError("y"))
    #  Ba lối ghi đều nuốt lỗi phiên; lỗi trong phiên (commit hỏng) cũng nuốt.
    monkeypatch.setattr(signals, "_session", lambda: SimpleNamespace(
        add=lambda *_: None, commit=lambda: (_ for _ in ()).throw(RuntimeError("commit hỏng")),
        rollback=lambda: None, close=lambda: None))
    signals.record_start("backup.run", "x")


# ── Danh sách + lịch sử ───────────────────────────────────────────────────────

def _run(db, task, status, *, ago=timedelta(hours=1), ms=1000, summary="", error=""):
    start = datetime.now() - ago
    db.add(JobRun(task_name=task, task_id=f"{task}-{start.timestamp()}", started_at=start,
                  finished_at=start + timedelta(milliseconds=ms), duration_ms=ms, status=int(status),
                  result_summary=summary, error=error))
    db.commit()


def test_danh_sach_viec_lan_gan_nhat_so_7_ngay_va_loc(db):
    _run(db, "backup.run", S.SUCCESS, ago=timedelta(days=1), ms=4000)
    _run(db, "backup.run", S.FAILED, ago=timedelta(hours=2), ms=1000, error="hết đĩa")
    _run(db, "backup.run", S.SUCCESS, ago=timedelta(days=9), ms=9000)        # ngoài 7 ngày
    out = service.list_jobs(db)
    jobs = {j["code"]: j for j in out["items"]}
    b = jobs["backup.run"]
    assert (b["name"], b["group"], b["runs_7d"], b["failed_7d"], b["avg_duration_ms_7d"]) == \
        ("Sao lưu cơ sở dữ liệu", "backup", 2, 1, 4000)
    assert b["last_run"]["status"] == int(S.FAILED) and b["last_run"]["error"] == "hết đĩa"
    assert b["schedule_label"] and b["next_run_at"]
    assert {g["code"] for g in out["groups"]} == set(JOB_GROUP_LABELS)
    assert {s["code"] for s in out["statuses"]} == {0, 1, 2, 3, 4}

    assert [j["code"] for j in service.list_jobs(db, status=int(S.FAILED))["items"]] == ["backup.run"]
    never = service.list_jobs(db, status=0)["items"]
    assert never and all(j["last_run"] is None for j in never)
    assert all(j["group"] == "cleanup" for j in service.list_jobs(db, group="cleanup")["items"])
    assert [j["code"] for j in service.list_jobs(db, q="SAO LUU co so")["items"]] == ["backup.run"]


def test_lich_su_mot_viec_phan_trang_va_loc(db):
    for i in range(5):
        _run(db, "notification.cleanup", S.SUCCESS if i % 2 else S.FAILED, ago=timedelta(hours=i + 1))
    page = service.list_runs(db, "notification.cleanup", page=1, page_size=2)
    assert (page["total"], len(page["items"])) == (5, 2)
    assert page["items"][0]["started_at"] > page["items"][1]["started_at"]
    assert service.list_runs(db, "notification.cleanup", status=int(S.FAILED))["total"] == 3
    assert page["items"][0]["status_label"]


def test_don_so_qua_han_va_tat(db):
    _run(db, "backup.run", S.SUCCESS, ago=timedelta(days=100))
    _run(db, "backup.run", S.SUCCESS, ago=timedelta(days=10))
    assert service.cleanup(db, days=0) == {"status": "disabled", "deleted": 0}
    assert service.cleanup(db, days=90)["deleted"] == 1
    assert db.query(JobRun).count() == 1


# ── API + công cụ gác quyền ───────────────────────────────────────────────────

@pytest.fixture
def client_as(db):
    from app.core.auth import get_current_user
    from app.core.database import get_db
    from app.main import app

    def make(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app)
    yield make
    app.dependency_overrides.clear()


def _user(db, code):
    from app.modules.user.model import User

    u = User(email=f"{code.lower()}@x.vn", password_hash="x", is_active=True)
    db.add(u)
    db.commit()
    return u


def test_api_gac_setting_read(db, cap_quyen, client_as):
    _run(db, "backup.run", S.SUCCESS)
    nobody = _user(db, "U703A")
    assert client_as(nobody).get("/api/system/jobs").status_code == 403
    admin = _user(db, "U703B")
    cap_quyen(admin.id, "setting", read=True)
    db.commit()
    c = client_as(admin)
    resp = c.get("/api/system/jobs", params={"status": 2})
    assert resp.status_code == 200, resp.text
    assert [j["code"] for j in resp.json()["data"]["items"]] == ["backup.run"]
    runs = c.get("/api/system/jobs/backup.run/runs", params={"page_size": 5})
    assert runs.status_code == 200 and runs.json()["data"]["total"] == 1


def test_cong_cu_chi_doc_gac_quyen(db, cap_quyen):
    from app.modules.assistant.tools import system_tool
    from app.modules.assistant.tools.base import ToolContext

    _run(db, "backup.run", S.FAILED, error="hết đĩa")
    nobody = _user(db, "U703C")
    assert system_tool._background_jobs(ToolContext(db=db, user=nobody), {}).get("denied")
    admin = _user(db, "U703D")
    cap_quyen(admin.id, "setting", read=True)
    db.commit()
    ctx = ToolContext(db=db, user=admin)
    out = system_tool._background_jobs(ctx, {"status": "error"})
    assert [j["code"] for j in out["items"]] == ["backup.run"] and out["items"][0]["last_run"]["error"] == "hết đĩa"
    runs = system_tool._background_jobs(ctx, {"job": "backup.run", "runs": 99})
    assert runs["total"] == 1 and runs["items"][0]["status"] == int(S.FAILED)
    assert system_tool._background_jobs(ctx, {"job": "khong.co"})["total"] == 0
    assert system_tool._background_jobs(ctx, {"status": "la", "q": "x" * 500})["items"] is not None
