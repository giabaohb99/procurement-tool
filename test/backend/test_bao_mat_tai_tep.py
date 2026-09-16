"""Bảo mật khâu TẢI TỆP LÊN — bao-CR-408, đóng BM-025…BM-031.

Từng dòng dưới đây ứng với một lỗ trong `doc/tai-lieu-ky-thuat/so-ghi-nhan-loi-bao-mat.md`
§2b. Đọc sổ đó trước khi sửa bài kiểm nào ở đây: mỗi bài giữ một câu khẳng định đã được
chứng minh chạy thật trên hệ, không phải suy đoán.

⚠️ `test/backend` chạy SQLite trong RAM, mà SQLite **KHÔNG ép `VARCHAR(n)`**. Bài kiểm
độ dài tên tệp vì vậy phải khẳng định ở TẦNG CHỐT (`upload_guard`), tuyệt đối không ghi
xuống DB rồi khẳng định — viết kiểu đó là xanh giả (đúng cái bẫy của `duoc-CR-316`).
"""
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.file_registry import DIRECT_FILE_POLICY, FILE_POLICY, direct_policy
from app.core.upload_guard import MAX_FILENAME_LEN, content_type_of, guard_upload
from app.modules.attachment.controller import RegisterIn, zip_entry_name
from app.modules.attachment.model import FileLink, StoredFile

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
SVG = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'


def _stored(db, *, owner: int, key: str = "dev/attachment/2026/09/1-a.pdf") -> StoredFile:
    sf = StoredFile(filename="a.pdf", file_key=key, url="http://x/a.pdf",
                    content_type="application/pdf", size=10, sha256="",
                    created_by=owner, updated_by=owner)
    db.add(sf)
    db.commit()
    return sf


# ── BM-025: /register không hỏi tệp của ai ──────────────────────────────────────

def test_register_tu_choi_tep_cua_nguoi_khac(db, monkeypatch):
    """Đoán id tệp của người khác rồi gắn vào phiếu của mình → 403, không mọc dây nào.

    Bỏ qua lớp quyền vai trò (`_check` đã có bài kiểm riêng) để bài này chỉ nói về
    MỘT chuyện: chốt chủ sở hữu.
    """
    from app.modules.attachment import controller as ac
    monkeypatch.setattr(ac, "_check", lambda *a, **k: (set(), 50))
    monkeypatch.setattr(ac, "_block_version_in_approval", lambda *a, **k: None)

    cua_nguoi_khac = _stored(db, owner=99)
    ke_tan_cong = SimpleNamespace(id=7)

    with pytest.raises(HTTPException) as e:
        ac.register_files(RegisterIn(entity="supplier", entity_id=1,
                                     file_ids=[cua_nguoi_khac.id]), db=db, user=ke_tan_cong)
    assert e.value.status_code == 403
    assert db.query(FileLink).count() == 0


def test_khong_tai_duoc_dinh_kem_rieng_tu_qua_day_moi(db, monkeypatch):
    """Tệp của entity RIÊNG TƯ cũng không gắn sang phiếu mình được.

    `document_version` nằm trong `PRIVATE_ENTITIES` nên API không trả `url` công khai;
    đường vòng cũ là gắn chính tệp ấy thêm một dây sang phiếu mình đọc được — dây mới
    mang quyền của phiếu MỚI chứ không phải của tệp gốc.
    """
    from app.modules.attachment import controller as ac
    monkeypatch.setattr(ac, "_check", lambda *a, **k: (set(), 50))
    monkeypatch.setattr(ac, "_block_version_in_approval", lambda *a, **k: None)

    tep_mat = _stored(db, owner=99)
    db.add(FileLink(file_id=tep_mat.id, entity="document_version", entity_id=5,
                    created_by=99, updated_by=99))
    db.commit()

    with pytest.raises(HTTPException) as e:
        ac.register_files(RegisterIn(entity="supplier", entity_id=1,
                                     file_ids=[tep_mat.id]), db=db, user=SimpleNamespace(id=7))
    assert e.value.status_code == 403
    assert db.query(FileLink).filter(FileLink.entity == "supplier").count() == 0


# ── BM-026: ảnh đại diện nằm ngoài mọi chính sách ───────────────────────────────

def test_avatar_tu_choi_duoi_va_kich_thuoc():
    """Cửa ảnh đại diện trước đây KHÔNG kiểm gì: `.exe` 50MB cũng lọt."""
    exts, max_mb = direct_policy("avatar")

    with pytest.raises(HTTPException) as e:
        guard_upload(filename="payload.exe", fileobj=BytesIO(b"MZ" + b"\x00" * 64),
                     exts=exts, max_mb=max_mb)
    assert e.value.status_code == 400

    qua_lon = BytesIO(PNG + b"\x00" * ((max_mb + 1) * 1024 * 1024))
    with pytest.raises(HTTPException) as e:
        guard_upload(filename="to.png", fileobj=qua_lon, exts=exts, max_mb=max_mb)
    assert e.value.status_code == 400

    # Ảnh thật, đúng trần → đi qua
    assert guard_upload(filename="ok.png", fileobj=BytesIO(PNG),
                        exts=exts, max_mb=max_mb) == ("image/png", len(PNG))


# ── BM-027: tin lời khai `content_type`, và `svg` nằm trong danh sách trắng ──────

def test_chu_ky_tu_choi_svg_du_khai_image():
    """`image/svg+xml` bắt đầu bằng `image/` nên chốt cũ cho qua — SVG chạy `<script>`."""
    exts, max_mb = direct_policy("signature")

    with pytest.raises(HTTPException):          # đuôi .svg không còn trong danh sách trắng
        guard_upload(filename="chuky.svg", fileobj=BytesIO(SVG), exts=exts, max_mb=max_mb)

    with pytest.raises(HTTPException) as e:     # đổi đuôi thành .png vẫn không lọt: byte đầu sai
        guard_upload(filename="chuky.png", fileobj=BytesIO(SVG), exts=exts, max_mb=max_mb)
    assert e.value.status_code == 400
    assert "không phải PNG" in e.value.detail


def test_danh_sach_trang_anh_khong_chua_svg():
    """Không một bảng chính sách nào còn nhận `svg` — kể cả bảng của Trung tâm HDSD."""
    for kind, (exts, _) in DIRECT_FILE_POLICY.items():
        assert "svg" not in exts, kind
    for entity, (_, exts, _) in FILE_POLICY.items():
        assert "svg" not in exts, entity


# ── BM-028: `content_type` là lời khai, không phải sự thật ───────────────────────

def test_content_type_lay_tu_noi_dung_khong_lay_tu_loi_khai(db, monkeypatch):
    """`tab_file.content_type` phải suy từ tệp, vì nó thành `media_type` của `/view`."""
    assert content_type_of("anh.png") == "image/png"
    assert content_type_of("la.qwerty") == "application/octet-stream"

    from app.modules.attachment import controller as ac
    monkeypatch.setattr(ac, "upload_fileobj", lambda *a, **k: "http://x/anh.png")
    monkeypatch.setattr(ac, "make_thumb_for", lambda *a, **k: None)

    khai_lao = SimpleNamespace(filename="anh.png", file=BytesIO(PNG),
                               content_type="text/html; charset=utf-8")
    sf = ac._store_one(db, khai_lao, {"png"}, 5, user_id=1)
    assert sf.content_type == "image/png"


# ── BM-029: zip-slip ở /chain/zip ───────────────────────────────────────────────

def test_zip_khong_co_duong_dan_di_len():
    """Tên thô sống sót tới lúc dựng tệp nén — máy NGƯỜI DÙNG là nạn nhân, không phải máy chủ."""
    assert zip_entry_name("../../../../evil.pdf") == "evil.pdf"
    assert zip_entry_name(r"..\..\..\evil.pdf") == "evil.pdf"
    assert zip_entry_name("/etc/passwd") == "passwd"
    assert zip_entry_name("..") == "file"
    assert zip_entry_name("") == "file"
    assert zip_entry_name("bao gia.pdf") == "bao_gia.pdf"


# ── BM-030: cụm độ bền đầu vào ──────────────────────────────────────────────────

def test_ten_tep_qua_dai_tra_422():
    """Tên 304 ký tự từng đi thẳng xuống `String(255)` rồi vỡ thành 500.

    Khẳng định ở TẦNG CHỐT: SQLite của bộ test không ép `VARCHAR(n)` nên ghi xuống DB
    rồi khẳng định là xanh giả.
    """
    ten_dai = "a" * 300 + ".pdf"
    assert len(ten_dai) > MAX_FILENAME_LEN
    with pytest.raises(HTTPException) as e:
        guard_upload(filename=ten_dai, fileobj=BytesIO(b"x" * 10), exts={"pdf"}, max_mb=50)
    assert e.value.status_code == 422

    with pytest.raises(HTTPException) as e:
        guard_upload(filename="   ", fileobj=BytesIO(b"x"), exts={"pdf"}, max_mb=50)
    assert e.value.status_code == 422


def test_tran_so_tep_moi_luot():
    """`files: list[UploadFile]` trước đây nhận bao nhiêu cũng được."""
    from app.core.upload_guard import MAX_FILES_PER_REQUEST, ensure_batch_ok

    ensure_batch_ok([object()] * MAX_FILES_PER_REQUEST)
    with pytest.raises(HTTPException) as e:
        ensure_batch_ok([object()] * (MAX_FILES_PER_REQUEST + 1))
    assert e.value.status_code == 422


# ── BM-031: `__self__` trả về sớm + tệp mồ côi không ai dọn ──────────────────────

def test_upload_file_doi_quyen_voi_comment(db):
    """Cửa tải lên trần của `comment`/`forum_post` không đi qua chốt nào — nay có trần
    tệp-chưa-gắn, và việc định kỳ dọn tệp mồ côi quá hạn."""
    from app.modules.attachment.controller import _check
    from app.modules.attachment.service import (MAX_PENDING_ORPHANS, ORPHAN_KEEP_DAYS,
                                                count_pending_orphans, purge_orphan_files)

    toi = SimpleNamespace(id=7)
    assert _check(db, toi, "comment", "manage") == FILE_POLICY["comment"][1:]

    for i in range(MAX_PENDING_ORPHANS):
        db.add(StoredFile(filename=f"{i}.pdf", file_key=f"dev/attachment/2026/09/{i}-a.pdf",
                          url="", content_type="application/pdf", size=1, sha256="",
                          created_by=toi.id, updated_by=toi.id))
    db.commit()
    assert count_pending_orphans(db, toi.id) == MAX_PENDING_ORPHANS

    with pytest.raises(HTTPException) as e:
        _check(db, toi, "comment", "manage")
    assert e.value.status_code == 429

    # Tệp mới tinh thì việc dọn KHÔNG được đụng tới — có luồng tải hôm nay, mai mới lưu.
    assert purge_orphan_files(db, keep_days=ORPHAN_KEEP_DAYS) == 0
    assert count_pending_orphans(db, toi.id) == MAX_PENDING_ORPHANS


def test_don_tep_mo_coi_khong_dung_anh_dai_dien(db, monkeypatch):
    """Việc dọn chỉ nhắm tệp của khâu ĐÍNH KÈM; ảnh đại diện vốn không có dây theo thiết kế."""
    from app.modules.attachment import service as asv
    monkeypatch.setattr(asv, "delete_key", lambda *a, **k: None)

    avatar = StoredFile(filename="me.png", file_key="dev/avatar/2026/09/1-me.png", url="",
                        content_type="image/png", size=1, sha256="", created_by=7, updated_by=7)
    dinh_kem = StoredFile(filename="bo.pdf", file_key="dev/attachment/2026/09/2-bo.pdf", url="",
                          content_type="application/pdf", size=1, sha256="",
                          created_by=7, updated_by=7)
    db.add_all([avatar, dinh_kem])
    db.commit()

    assert asv.purge_orphan_files(db, keep_days=-1) == 1
    assert db.get(StoredFile, avatar.id) is not None
    assert db.get(StoredFile, dinh_kem.id) is None
