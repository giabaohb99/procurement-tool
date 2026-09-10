"""bao-CR-360 (CR-312 P3a) — phiên đăng nhập phía máy chủ, phần LÕI.

Đây là bộ kiểm đóng **BM-002**: trước bản này, bấm *Đăng xuất* chỉ xóa vé ở
trình duyệt, còn refresh token bị cắp thì sống trọn bảy ngày và không ai cắt
được. Sáu câu hỏi mà tệp này chốt:

1. Đăng nhập có đẻ ra một dòng phiên, và vé có mang `jti` + `ver` không.
2. Cửa chặn (`get_current_user`) có điền `session_id` vào ngữ cảnh không — sợi
   chỉ nối hai nửa của **QĐ-D**, thiếu nó thì dấu vết mất chỗ neo.
3. Đăng xuất có giết vé của **riêng** thiết bị đó không (và KHÔNG đụng máy khác).
4. Đổi mật khẩu có cắt các thiết bị khác mà **giữ** thiết bị đang thao tác không.
5. `force_relogin` có hiệu lực **tức thì**, xuyên qua đệm 60 giây, không.
6. `jti` của người này ghép với `sub` của người kia có bị chặn không.

⚠️ Bài kiểm nào cũng chạy trên MỘT `Session` SQLite (fixture `db`), trong khi ở
chạy thật middleware mở `SessionLocal()` riêng. Vì vậy mọi hàm của
`login_session/service.py` đều nhận `db` làm tham số — thiết kế đó là để kiểm
được, đừng đổi sang tự mở kết nối bên trong.
"""
import pytest
from fastapi import HTTPException

from app.core.auth import create_access_token, get_current_user
from app.core.logging_codes import SOURCE_API
from app.core.request_context import open_context
from app.modules.auth.controller import change_password, logout
from app.modules.login_session.constants import DeviceType, LoginMethod, RevokeReason
from app.modules.login_session.model import LoginSession
from app.modules.login_session.service import (describe_device, force_relogin, resolve_session,
                                               revoke_session, start_session, touch_is_due,
                                               touch_session)
from app.modules.user.model import User

CHROME_WINDOWS = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
SAFARI_IPHONE = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                 "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")


def _fake_request(ip="10.0.0.5"):
    """Đủ dùng cho `_client_ip` — nó chỉ đọc `headers` và `client.host`."""
    from types import SimpleNamespace

    from starlette.datastructures import Headers
    return SimpleNamespace(headers=Headers({}), client=SimpleNamespace(host=ip))


def _login(db, user, ip="10.0.0.5", user_agent=CHROME_WINDOWS):
    """Mở phiên + vé truy cập của phiên đó, như `/api/auth/login` vẫn làm."""
    session = start_session(db, user, ip=ip, user_agent=user_agent)
    return session, create_access_token(user.id, session.token_id, session.token_version)


# ── Nhận dạng thiết bị ──────────────────────────────────────────────────────────
def test_nhan_dang_thiet_bi_dung_ba_manh():
    pc = describe_device(CHROME_WINDOWS)
    assert (pc["browser"], pc["os"], pc["device_type"]) == ("chrome", "windows", DeviceType.DESKTOP)
    assert "Chrome" in pc["device_label"] and "Windows" in pc["device_label"]

    phone = describe_device(SAFARI_IPHONE)
    assert (phone["browser"], phone["os"], phone["device_type"]) == ("safari", "ios",
                                                                     DeviceType.MOBILE)


def test_user_agent_rong_ra_khong_ro_chu_khong_ra_may_tinh():
    """`_device_kind` lùi về `desktop`, nhưng đó là giá trị lùi chứ không phải kết luận."""
    assert describe_device("")["device_type"] == DeviceType.UNKNOWN
    assert describe_device("")["device_label"] == "Không rõ thiết bị"


# ── Mở phiên + cửa chặn ─────────────────────────────────────────────────────────
def test_mo_phien_ghi_du_dau_vet_va_ve_mang_jti(db, seed):
    user = db.get(User, seed.u_req_id)
    session, token = _login(db, user, ip="203.0.113.9")

    assert session.id and session.token_id and session.revoked_at is None
    assert session.login_method == LoginMethod.PASSWORD
    assert session.ip == "203.0.113.9" and session.last_seen_ip == "203.0.113.9"
    assert session.user_agent == CHROME_WINDOWS   # ở bảng này lưu NGUYÊN VĂN, khác request_log

    from jose import jwt

    from app.core.config import settings
    claims = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    assert claims["jti"] == session.token_id and claims["ver"] == session.token_version


def test_cua_chan_cho_qua_va_dien_session_id_vao_ngu_canh(db, seed):
    """Nửa trên của QĐ-D. Không có dòng này thì nửa dưới (middleware) mù."""
    user = db.get(User, seed.u_req_id)
    session, token = _login(db, user)

    with open_context(SOURCE_API) as ctx:
        assert get_current_user(f"Bearer {token}", db).id == user.id
        assert ctx.session_id == session.id


def test_ve_khong_co_jti_bi_chan(db, seed):
    """Vé phát trước bao-CR-360 — ca «mọi người bị đăng xuất một lần» lúc deploy."""
    user = db.get(User, seed.u_req_id)
    with pytest.raises(HTTPException) as exc:
        get_current_user(f"Bearer {create_access_token(user.id)}", db)
    assert exc.value.status_code == 401


def test_jti_cua_nguoi_nay_ghep_sub_cua_nguoi_kia_bi_chan(db, seed):
    """Ghép chéo là ca phải chặn ở CẢ đệm lẫn DB, nên kiểm hai lượt liền nhau."""
    victim = db.get(User, seed.u_req_id)
    other = db.get(User, seed.u_nstm_id)
    session, _ = _login(db, victim)

    forged = create_access_token(other.id, session.token_id, session.token_version)
    for _ in range(2):   # lượt hai đi qua đệm — vẫn phải chặn
        with pytest.raises(HTTPException) as exc:
            get_current_user(f"Bearer {forged}", db)
        assert exc.value.status_code == 401
    #  Và vé thật của chính chủ KHÔNG bị đệm sai lây sang.
    assert resolve_session(db, session.token_id, victim.id) == session.id


# ── Đăng xuất ───────────────────────────────────────────────────────────────────
def test_dang_xuat_giet_ve_cua_chinh_thiet_bi_do(db, seed):
    """Đây chính là BM-002. Trước bản này, vé vẫn dùng được sau khi đăng xuất."""
    user = db.get(User, seed.u_req_id)
    session, token = _login(db, user)

    with open_context(SOURCE_API) as ctx:
        get_current_user(f"Bearer {token}", db)          # điền ctx.session_id
        logout(_fake_request(), user=user, db=db)

    db.refresh(session)
    assert session.revoked_at is not None
    assert session.revoke_reason == RevokeReason.SELF_LOGOUT and session.revoked_by == user.id
    with pytest.raises(HTTPException) as exc:
        get_current_user(f"Bearer {token}", db)
    assert exc.value.status_code == 401


def test_dang_xuat_khong_dung_toi_thiet_bi_khac(db, seed):
    user = db.get(User, seed.u_req_id)
    pc, pc_token = _login(db, user, user_agent=CHROME_WINDOWS)
    phone, phone_token = _login(db, user, user_agent=SAFARI_IPHONE)

    with open_context(SOURCE_API):
        get_current_user(f"Bearer {pc_token}", db)
        logout(_fake_request(), user=user, db=db)

    db.refresh(phone)
    assert phone.revoked_at is None
    with open_context(SOURCE_API):
        assert get_current_user(f"Bearer {phone_token}", db).id == user.id
    with pytest.raises(HTTPException):
        get_current_user(f"Bearer {pc_token}", db)
    assert pc.id != phone.id


# ── Đổi mật khẩu / bắt đăng nhập lại ────────────────────────────────────────────
def test_doi_mat_khau_cat_may_khac_nhung_giu_may_dang_thao_tac(db, seed):
    """Cố ý KHÔNG tăng `token_version`: tăng là đá luôn người vừa bấm nút."""
    from app.core.auth import hash_password

    user = db.get(User, seed.u_req_id)
    user.password_hash = hash_password("matkhaucu1")
    db.commit()
    here, here_token = _login(db, user)
    there, there_token = _login(db, user, user_agent=SAFARI_IPHONE)

    with open_context(SOURCE_API):
        get_current_user(f"Bearer {here_token}", db)
        change_password({"old_password": "matkhaucu1", "new_password": "matkhaumoi9"},
                        user=user, db=db)

    db.refresh(here)
    db.refresh(there)
    assert here.revoked_at is None, "phiên đang thao tác phải sống tiếp"
    assert there.revoked_at is not None
    assert there.revoke_reason == RevokeReason.PASSWORD_CHANGED
    with open_context(SOURCE_API):
        assert get_current_user(f"Bearer {here_token}", db).id == user.id
    with pytest.raises(HTTPException):
        get_current_user(f"Bearer {there_token}", db)


def test_bat_dang_nhap_lai_co_hieu_luc_ngay_khong_doi_dem(db, seed):
    """`token_version` là đường KHÔNG qua đệm — đó là lý do nó tồn tại.

    Cố ý hâm nóng đệm trước (một lượt gọi hợp lệ) rồi mới `force_relogin`: nếu ai
    đó dời chốt này xuống dưới đệm tra phiên thì bài kiểm đỏ, còn ở chạy thật thì
    «đăng xuất mọi thiết bị» im lặng trễ tới một phút.
    """
    user = db.get(User, seed.u_req_id)
    session, token = _login(db, user)
    with open_context(SOURCE_API):
        get_current_user(f"Bearer {token}", db)          # nạp đệm

    force_relogin(db, user, RevokeReason.FORCE_RELOGIN, revoked_by=user.id)

    assert user.token_version == 2
    db.refresh(session)
    assert session.revoked_at is not None
    with pytest.raises(HTTPException) as exc:
        get_current_user(f"Bearer {token}", db)
    assert exc.value.status_code == 401


def test_thu_hoi_lan_hai_khong_de_len_ly_do_lan_dau(db, seed):
    user = db.get(User, seed.u_req_id)
    session, _ = _login(db, user)
    revoke_session(db, session, RevokeReason.SELF_LOGOUT, user.id)
    first = session.revoked_at

    revoke_session(db, session, RevokeReason.ADMIN_KICK, 999)
    db.refresh(session)
    assert session.revoke_reason == RevokeReason.SELF_LOGOUT
    assert session.revoked_by == user.id and session.revoked_at == first


# ── Tiết lưu last_seen (nửa dưới của QĐ-D) ──────────────────────────────────────
def test_dap_last_seen_co_tiet_luu(db, seed):
    """Không có trần này thì mỗi lượt gọi API là một `UPDATE` trên cùng một dòng."""
    user = db.get(User, seed.u_req_id)
    session, _ = _login(db, user, ip="10.0.0.5")

    #  `start_session` đã bấm mốc, nên lượt ngay sau đó KHÔNG được ghi lại.
    assert touch_is_due(session.id) is False
    assert touch_session(db, session.id, "198.51.100.7") is False
    db.refresh(session)
    assert session.last_seen_ip == "10.0.0.5"

    from app.modules.login_session import service as login_session_service
    login_session_service.touch_state_clear()            # giả lập đã qua 5 phút
    assert touch_is_due(session.id) is True
    assert touch_session(db, session.id, "198.51.100.7") is True
    db.refresh(session)
    assert session.last_seen_ip == "198.51.100.7"
    assert session.ip == "10.0.0.5", "cột `ip` là IP LÚC ĐĂNG NHẬP, không được dập"


def test_khong_co_phien_thi_khong_dap_gi(db):
    """Lượt gọi công khai (chưa đăng nhập) không có phiên — middleware phải im."""
    assert touch_is_due(0) is False
    assert touch_session(db, 0, "10.0.0.5") is False
    assert db.query(LoginSession).count() == 0
