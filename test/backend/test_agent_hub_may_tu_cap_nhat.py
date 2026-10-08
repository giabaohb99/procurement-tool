"""ai-CR-124: máy sửa mã tự cập nhật cho khớp bản mã của bot — đại ca 08/10: «tự khắc phục lỗi này đi, khỏi cần thông
báo nữa» (thẻ «MÁY SỬA MÃ VÀ BOT LỆCH BẢN» báo sau mỗi lần deploy dev).

Container kiểm không có git: bước kéo / xuất mã thay bằng chép một thư mục mẫu, phần còn lại (vân tay, chờ, bận, chọn
nhánh khớp, ghi `current`, khởi động lại) chạy thật.
"""
import shutil
from pathlib import Path

import pytest

from app.core.config import settings


def _tree(root: Path, body: str) -> Path:
    """Một cây `backend/app/modules/{agent_hub,assistant}` tối thiểu, nội dung đổi theo `body`."""
    mods = root / "backend" / "app" / "modules"
    (mods / "agent_hub").mkdir(parents=True, exist_ok=True)
    (mods / "assistant").mkdir(parents=True, exist_ok=True)
    (mods / "agent_hub" / "x.py").write_text(body)
    (mods / "assistant" / "y.py").write_text("Y = 1\n")
    return mods


@pytest.fixture
def runner_env(db, tmp_path, monkeypatch):
    from app.modules.agent_hub import runner_update as ru, runners

    monkeypatch.setattr(settings, "AGENT_RUNNER_NAME", "may-test")
    monkeypatch.setattr(settings, "AGENT_RUNNER_SELF_UPDATE", True)
    monkeypatch.setattr(settings, "AGENT_WORKTREE_ROOT", str(tmp_path / "wt"))
    monkeypatch.setattr(settings, "AGENT_RUNNER_UPDATE_BRANCHES", "erp-v2,agent-hub-bac-1")
    monkeypatch.setattr(ru, "BUSY_FILE", tmp_path / "busy")
    ru._state.update({"skew_since": None, "next_try": 0.0, "last_bad": ""})
    #  Hai «nhánh» trên GitHub: erp-v2 còn mã cũ, agent-hub-bac-1 đúng bản bot đang chạy.
    src = {"erp-v2": _tree(tmp_path / "src-old", "A = 'cũ'\n").parents[2],
           "agent-hub-bac-1": _tree(tmp_path / "src-new", "A = 'mới'\n").parents[2]}
    shas = {"erp-v2": "a" * 40, "agent-hub-bac-1": "b" * 40}
    exported: list[str] = []
    monkeypatch.setattr(ru, "_base_repo", lambda: str(tmp_path / "base"))
    monkeypatch.setattr(ru, "_rev_parse", lambda base, ref: shas[ref.split("/", 1)[1]])

    def fake_export(base, sha, dest):
        branch = next(b for b, s in shas.items() if s == sha)
        exported.append(branch)
        shutil.copytree(src[branch], dest)

    monkeypatch.setattr(ru, "_export", fake_export)
    bot_fp = runners.fingerprint_dir(src["agent-hub-bac-1"] / "backend" / "app" / "modules")
    #  Máy đang chạy một bản khác cả hai.
    monkeypatch.setattr(runners, "code_fingerprint", lambda: "0123456789ab")
    monkeypatch.setattr(runners, "fingerprint_dir", runners.fingerprint_dir)
    return ru, runners, bot_fp, exported, tmp_path


def _publish(db, runners, fp: str, monkeypatch):
    monkeypatch.setattr(runners, "code_fingerprint", lambda: fp)
    runners.publish_bot_fingerprint(db)
    db.commit()
    monkeypatch.setattr(runners, "code_fingerprint", lambda: "0123456789ab")


def test_may_lech_ban_tu_keo_nhanh_khop_bot_roi_khoi_dong_lai(db, runner_env, monkeypatch):
    ru, runners, bot_fp, exported, tmp = runner_env
    _publish(db, runners, bot_fp, monkeypatch)
    assert ru.bot_fingerprint(db) == bot_fp
    restarted: list[int] = []
    #  Mới lệch: chờ (bot và máy hay lên bản lệch nhau vài phút).
    assert ru.tick(db, now=1000.0, restart=lambda: restarted.append(1)) == "lệch bản, chờ"
    assert ru.tick(db, now=1000.0 + ru.SKEW_GRACE_SEC - 1, restart=lambda: restarted.append(1)) == "lệch bản, chờ"
    #  Đang làm vé: không đổi mã giữa chừng.
    ru.mark_busy(True)
    assert ru.tick(db, now=1000.0 + ru.SKEW_GRACE_SEC + 1, restart=lambda: restarted.append(1)) == \
        "lệch bản, máy đang làm vé"
    ru.mark_busy(False)
    out = ru.tick(db, now=1000.0 + ru.SKEW_GRACE_SEC + 2, restart=lambda: restarted.append(1))
    assert out == "đã cập nhật " + "b" * 10 and restarted == [1]
    #  Thử erp-v2 trước (không khớp), rồi agent-hub-bac-1 (khớp) → chọn bản đó.
    assert exported == ["erp-v2", "agent-hub-bac-1"]
    root = tmp / "wt" / ".runner-code"
    assert (root / "current").read_text() == "b" * 40
    assert runners.fingerprint_dir(root / ("b" * 40) / "backend" / "app" / "modules") == bot_fp


def test_khong_nhanh_nao_khop_thi_khong_doi_va_khong_keo_lien_tuc(db, runner_env, monkeypatch):
    ru, runners, _bot_fp, exported, tmp = runner_env
    _publish(db, runners, "ffffffffffff", monkeypatch)       # bot chạy mã chưa đẩy lên GitHub
    restarted: list[int] = []
    ru.tick(db, now=0.0)
    assert ru.tick(db, now=float(ru.SKEW_GRACE_SEC + 1), restart=lambda: restarted.append(1)) == "không nhánh nào khớp"
    assert restarted == [] and not (tmp / "wt" / ".runner-code" / "current").exists()
    n = len(exported)
    #  Không kéo lại mỗi nhịp tim: chờ RETRY_SEC.
    assert ru.tick(db, now=float(ru.SKEW_GRACE_SEC + 60)) == "lệch bản, chờ" and len(exported) == n


def test_cung_ban_hoac_tat_tu_cap_nhat_thi_khong_lam_gi(db, runner_env, monkeypatch):
    ru, runners, bot_fp, exported, _ = runner_env
    _publish(db, runners, "0123456789ab", monkeypatch)        # bot cùng bản với máy
    assert ru.tick(db, now=0.0) == "" and ru.tick(db, now=10_000.0) == ""
    _publish(db, runners, bot_fp, monkeypatch)
    monkeypatch.setattr(settings, "AGENT_RUNNER_SELF_UPDATE", False)
    assert ru.tick(db, now=0.0) == "" and ru.tick(db, now=10_000.0) == "" and exported == []


def test_bot_ghi_van_tay_moi_vong_canh_may_va_the_bao_chi_con_khi_tu_cap_nhat_that_bai(db, monkeypatch):
    from datetime import datetime, timedelta

    from app.modules.agent_hub import runner_update as ru, runners
    from app.modules.agent_hub.model import AgentRunner

    r = AgentRunner(name="may-dai-ca", token_hash="x", version="fp:aaaaaaaaaaaa", last_seen_at=datetime.now(),
                    created_by=0, updated_by=0)
    db.add(r)
    db.commit()
    sent: list[str] = []
    now = datetime.now()
    runners.watch(db, now=now, notify=sent.append)
    assert ru.bot_fingerprint(db) == runners.code_fingerprint()
    r.last_seen_at = now + timedelta(minutes=31)
    db.commit()
    runners.watch(db, now=now + timedelta(minutes=31), notify=sent.append)
    assert len(sent) == 1 and "chưa tự cập nhật được" in sent[0]
