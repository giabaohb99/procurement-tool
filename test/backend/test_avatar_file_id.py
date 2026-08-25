"""Ảnh đại diện chuyển từ URL chuỗi sang tab_user.avatar_file_id → tab_file.

Chốt ba điều dễ vỡ khi đổi kiểu lưu:
1. `user.avatar` (property) vẫn TRẢ VỀ URL chuỗi như trước — mọi nơi đọc
   (đăng nhập, bình luận, phiếu hỗ trợ, nhân sự) không phải sửa.
2. Chưa gắn file thì trả chuỗi rỗng, không nổ.
3. Đổi ảnh thì XÓA hẳn file cũ khỏi tab_file (hết ảnh mồ côi) — đây là lý do
   chính của cả thay đổi này, nên phải có test giữ.
"""
from io import BytesIO

from app.modules.attachment.model import StoredFile
from app.modules.user.model import User
from app.modules.user.service import set_user_avatar


def _png_bytes() -> BytesIO:
    # 1 điểm ảnh PNG hợp lệ — đủ để upload_fileobj (fallback local) ghi ra tệp.
    return BytesIO(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def test_property_avatar_tra_ve_url_cua_file(db):
    f = StoredFile(filename="me.png", file_key="dev/avatar/1/me.png",
                   url="https://cdn.example/dev/avatar/1/me.png")
    db.add(f)
    db.flush()
    u = User(email="a@dego.vn", avatar_file_id=f.id)
    db.add(u)
    db.flush()
    db.refresh(u)

    assert u.avatar == "https://cdn.example/dev/avatar/1/me.png"


def test_property_avatar_rong_khi_chua_co_file(db):
    u = User(email="b@dego.vn", avatar_file_id=0)
    db.add(u)
    db.flush()

    assert u.avatar == ""


def test_doi_anh_xoa_file_cu(db, monkeypatch):
    """Đổi ảnh lần hai: file cũ phải biến mất khỏi tab_file, chỉ còn file mới.

    Mock storage để test chạy offline, KHÔNG ghi/xoá trên R2 thật. Việc xoá dòng
    tab_file (cái ta khẳng định) do `db.delete` lo, độc lập với `delete_key`.
    """
    from app.modules.attachment import service as attach_service
    monkeypatch.setattr(attach_service, "upload_fileobj",
                        lambda fileobj, key, ct="": f"https://cdn.test/{key}")
    monkeypatch.setattr(attach_service, "delete_key", lambda key: None)

    u = User(email="c@dego.vn", avatar_file_id=0)
    db.add(u)
    db.flush()

    set_user_avatar(db, u, fileobj=_png_bytes(), filename="cu.png",
                    content_type="image/png", actor_id=u.id)
    file_cu = u.avatar_file_id
    assert file_cu != 0
    assert db.get(StoredFile, file_cu) is not None

    set_user_avatar(db, u, fileobj=_png_bytes(), filename="moi.png",
                    content_type="image/png", actor_id=u.id)
    file_moi = u.avatar_file_id
    assert file_moi != file_cu
    assert db.get(StoredFile, file_cu) is None, "file cũ phải bị xóa, không để mồ côi"
    assert db.get(StoredFile, file_moi) is not None
