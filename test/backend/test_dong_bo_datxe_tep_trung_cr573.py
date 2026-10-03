"""bao-CR-573: phiếu app cũ khai CÙNG một tệp hai lần thì không được ghi đôi liên kết.

Lượt quét toàn bộ đầu tiên trên prod 02/10/2026 ghi đôi liên kết tệp cho 19 phiếu
dấu, vì phiên DB tắt autoflush nên lần gặp thứ hai không thấy liên kết vừa thêm.
Từ đó mọi lần cập nhật phiếu đều nổ `MultipleResultsFound`, bộ chạy lại thử ba lần
rồi bỏ, và đổi gì bên app cũ thì ERP không thấy nữa.

Fixture `db` dùng `autoflush=False` đúng như prod nên tái hiện được lỗi gốc.
"""
from sqlalchemy import func, select

from app.core.legacy_files import SOURCE_DATXE
from app.modules.attachment.model import FileLink, StoredFile
from app.modules.legacy_datxe.service import ENTITY_SEAL, sync_legacy_attachments


def _add_legacy_file(db, external_id: str) -> StoredFile:
    sf = StoredFile(filename=f"{external_id}.pdf", file_key=f"uploads/u/{external_id}.pdf",
                    source=SOURCE_DATXE, external_id=external_id)
    db.add(sf)
    db.flush()
    return sf


def _count_links(db, entity_id: int) -> int:
    return db.execute(select(func.count(FileLink.id)).where(
        FileLink.entity == ENTITY_SEAL, FileLink.entity_id == entity_id)).scalar_one()


def test_tep_khai_hai_lan_trong_mot_phieu_chi_tao_mot_lien_ket(db):
    _add_legacy_file(db, "f1")
    _add_legacy_file(db, "f2")
    node = {"details": {"attachedFileIds": ["f1", "f2", "f1"]}}

    added = sync_legacy_attachments(db, entity=ENTITY_SEAL, entity_id=10, node=node)
    db.flush()

    assert added == 2
    assert _count_links(db, 10) == 2


def test_lien_ket_trung_do_loi_cu_tu_don_va_khong_no(db):
    sf = _add_legacy_file(db, "f1")
    for _ in range(2):
        db.add(FileLink(file_id=sf.id, entity=ENTITY_SEAL, entity_id=20, doc_type="signed_doc"))
    db.flush()
    keep_id = db.execute(select(func.min(FileLink.id)).where(
        FileLink.entity_id == 20)).scalar_one()
    node = {"details": {"attachedFileIds": ["f1"]}}

    added = sync_legacy_attachments(db, entity=ENTITY_SEAL, entity_id=20, node=node)
    db.flush()

    assert added == 0
    left = list(db.execute(select(FileLink.id).where(FileLink.entity_id == 20)).scalars())
    assert left == [keep_id]


def test_chay_lai_khong_sinh_them_lien_ket(db):
    _add_legacy_file(db, "f1")
    node = {"details": {"attachedFileIds": ["f1", "f1"]}}

    sync_legacy_attachments(db, entity=ENTITY_SEAL, entity_id=30, node=node)
    db.flush()
    added = sync_legacy_attachments(db, entity=ENTITY_SEAL, entity_id=30, node=node)
    db.flush()

    assert added == 0
    assert _count_links(db, 30) == 1
