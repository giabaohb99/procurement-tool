"""bao-CR-735 — chống treo prod: healthcheck trong container, bộ tự chữa trên máy chủ, bộ canh prod từ ngoài."""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2] / "backend"
if not (BACKEND / "healthcheck.py").exists():  # chạy trong container: backend mount ở /app
    BACKEND = Path("/app")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


hc = _load("healthcheck_cr735", BACKEND / "healthcheck.py")
pw = _load("prod_watch_cr735", BACKEND / "scripts" / "ops" / "prod_watch.py")


# ---------- healthcheck.py ----------

def test_api_dang_migration_thi_coi_la_khoe():
    ok, why = hc.check_api(url="http://127.0.0.1:1/khong-co", cmdline="sh start.prod.sh")
    assert ok and "khởi động" in why


def test_api_da_len_uvicorn_ma_khong_tra_loi_la_hong():
    ok, _ = hc.check_api(url="http://127.0.0.1:1/api/health",
                           cmdline="/usr/local/bin/python3.12 /usr/local/bin/uvicorn app.main:app --workers 2")
    assert not ok


def test_ten_worker_theo_tien_to():
    assert hc.worker_name("celery", "abc123") == "celery@abc123"
    assert hc.worker_name("agent-worker", "abc123") == "agent-worker@abc123"


def test_loai_kiem_la_thi_hong(capsys):
    assert hc.main(["healthcheck.py", "khong-biet"]) == 1


# ---------- prod_watch.py: máy trạng thái ----------

KW = {"name": "Prod", "url": "https://x/api/health", "threshold": 2, "remind_minutes": 60}


def _run(seq, start=1_000_000.0, gap=60):
    """seq: chuỗi True/False từng phút → danh sách tin đã gửi (None nếu không gửi)."""
    state, msgs = {}, []
    for i, ok in enumerate(seq):
        state, msg = pw.step(state, ok, "ok" if ok else "TimeoutError", start + i * gap, **KW)
        msgs.append(msg)
    return state, msgs


def test_hong_mot_luot_khong_bao():
    state, msgs = _run([False, True])
    assert msgs == [None, None] and state["fails"] == 0


def test_hong_hai_luot_lien_bao_dung_mot_lan():
    _, msgs = _run([False, False, False, False, False])
    sent = [m for m in msgs if m]
    assert len(sent) == 1 and sent[0].startswith("[CẢNH BÁO]") and msgs[1] is sent[0]


def test_hoi_lai_bao_kem_thoi_gian_dung():
    _, msgs = _run([False, False, False, False, True, True])
    assert msgs[4].startswith("[ĐÃ HỒI]") and "4 phút" in msgs[4]
    assert msgs[5] is None


def test_hong_xen_ke_khong_bao():
    _, msgs = _run([False, True, False, True, False, True])
    assert not any(msgs)


def test_nhac_lai_moi_60_phut_khong_lap_moi_phut():
    _, msgs = _run([False] * 125)
    sent = [m for m in msgs if m]
    assert len(sent) == 3  # báo ở phút 2, nhắc ở phút 62 và 122
    assert sent[1].startswith("[VẪN HỎNG]")


def test_tat_nhac_lai():
    state, msg = {}, None
    sent = []
    for i in range(200):
        state, msg = pw.step(state, False, "x", 1_000_000 + i * 60, **{**KW, "remind_minutes": 0})
        sent.append(msg)
    assert len([m for m in sent if m]) == 1


def test_gui_hong_thi_luot_sau_gui_lai():
    old = {}
    new, msg = pw.step(old, False, "x", 1_000_000, **KW)
    new, msg = pw.step(new, False, "x", 1_000_060, **KW)
    assert msg
    kept = pw.keep_unsent(old={**new, "alerted": False, "last_alert": None}, new=new, ok=False)
    _, again = pw.step(kept, False, "x", 1_000_120, **KW)
    assert again and again.startswith("[CẢNH BÁO]")


def test_tin_hoi_gui_hong_thi_giu_moc_dung_cu():
    state, _ = _run([False, False, False])
    after, msg = pw.step(state, True, "ok", 1_000_000 + 600, **KW)
    assert msg and after["alerted"] is False
    kept = pw.keep_unsent(state, after, ok=True)
    _, again = pw.step(kept, True, "ok", 1_000_000 + 660, **KW)
    assert again.startswith("[ĐÃ HỒI]") and "11 phút" in again


def test_tin_khong_lo_khoa(monkeypatch, capsys):
    import urllib.error

    def boom(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 401, "Unauthorized", {}, None)

    monkeypatch.setattr(pw.urllib.request, "urlopen", boom)
    assert pw.send_telegram("BI-MAT-123", "42", "chao") is False
    assert "BI-MAT-123" not in capsys.readouterr().out


def test_luu_va_doc_trang_thai(tmp_path):
    path = str(tmp_path / "a" / "state.json")
    assert pw.load(path)["fails"] == 0
    pw.save(path, {**pw.EMPTY, "fails": 3})
    assert pw.load(path)["fails"] == 3


# ---------- autoheal.sh với docker giả ----------

FAKE_DOCKER = """#!/bin/sh
case "$1" in
  ps) cat "$FAKE_DIR/unhealthy" ;;
  inspect) echo "TimeoutError: timed out" ;;
  restart) echo "$@" >> "$FAKE_DIR/restarted"; [ ! -f "$FAKE_DIR/restart_fails" ] ;;
esac
"""


@pytest.fixture
def heal(tmp_path):
    if not shutil.which("bash") or not shutil.which("flock"):
        pytest.skip("cần bash + flock")
    fake = tmp_path / "docker"
    fake.write_text(FAKE_DOCKER)
    fake.chmod(0o755)
    (tmp_path / "unhealthy").write_text("dev-api-1\n")
    env = {**os.environ, "DOCKER": str(fake), "FAKE_DIR": str(tmp_path),
           "AUTOHEAL_STATE": str(tmp_path / "state" / "restarts.log"),
           "AUTOHEAL_LOCK": str(tmp_path / "lock"), "DEGO_ALERT_ENV": str(tmp_path / "khong-co.env")}

    def run():
        subprocess.run(["bash", str(BACKEND / "scripts" / "ops" / "autoheal.sh")], env=env, check=True,
                       capture_output=True, text=True)
        restarted = tmp_path / "restarted"
        return restarted.read_text().splitlines() if restarted.exists() else []

    run.dir = tmp_path
    return run


def test_autoheal_khoi_dong_lai_container_unhealthy(heal):
    assert heal() == ["restart -t 20 dev-api-1"]


def test_autoheal_tran_3_lan_moi_gio_roi_thoi(heal):
    for _ in range(6):
        restarted = heal()
    assert len(restarted) == 3
    lines = (heal.dir / "state" / "restarts.log").read_text().splitlines()
    assert sum(1 for line in lines if line.endswith("giveup")) == 1  # báo "cần người xem" đúng một lần


def test_autoheal_khong_co_container_hong_thi_im(heal):
    (heal.dir / "unhealthy").write_text("")
    assert heal() == []


def test_autoheal_restart_hong_van_tinh_vao_tran(heal):
    (heal.dir / "restart_fails").write_text("1")
    for _ in range(5):
        restarted = heal()
    assert len(restarted) == 3
