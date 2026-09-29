"""Thêm / sửa / xóa thuốc BVTV trên màn + khóa `customs_pesticide` (duoc-CR-490, 29/09/2026).

Canh:
  · chuỗi dài hơn cột phải là 422 ở tầng SCHEMA — SQLite của pytest KHÔNG ép độ dài, ghi xuống
    rồi đọc lên là xanh giả (duoc-CR-316);
  · nạp lại danh mục GIỮ thuốc tự thêm (kể cả phạm vi sử dụng của nó), không nhân đôi qua nhiều
    lần nạp, không đụng id — và dòng nguồn thiếu mã (`source_id = 0`) KHÔNG bị tưởng là tự thêm;
  · khóa mới không lọt vào vai trò Quản lý thu mua (vòng `_PUR_MANAGER_PERMS` quét cả ENTITIES).
"""
import json

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.permissions import ENTITIES
from app.core.scoping import PUBLIC, SCOPE_FIELDS
from app.modules.customs import pesticide_edit_service as E
from app.modules.customs import pesticide_reader as R
from app.modules.customs import pesticide_service as S
from app.modules.customs.constants import PesticideStatus
from app.modules.customs.model import CustomsPesticide, CustomsPesticideUse
from app.modules.customs.pesticide_schema import PesticideIn


def _body(**over):
    body = {"trade_name": "Tự Thêm 20EC", "active_ingredient": "Abamectin 18g/l",
            "status": int(PesticideStatus.ACTIVE),
            "uses": [{"crop": "lúa", "pest": "sâu cuốn lá", "dosage": "0.3 lít/ha"}]}
    body.update(over)
    return PesticideIn(**body)


def _file(*ids):
    raws = [{"id": i, "ten_thuoc": f"Nguồn {i} 10SC", "hoat_chat": "Chitosan 2%",
             "tinh_trang": "Còn hiệu lực",
             "pham_vi_su_dung": [{"cay_trong": "lúa", "dich_hai": "đạo ôn"}]} for i in ids]
    return R.read_file("thuoc-bvtv.json", json.dumps(raws, ensure_ascii=False).encode())


def test_key_is_declared_public_and_kept_away_from_purchase_manager():
    from app.seed import _PUR_MANAGER_PERMS, _SYS_ENTITIES
    assert "customs_pesticide" in ENTITIES
    assert SCOPE_FIELDS["customs_pesticide"] is PUBLIC
    assert "customs_pesticide" in _SYS_ENTITIES
    assert "customs_pesticide" not in _PUR_MANAGER_PERMS


@pytest.mark.parametrize("field, size", [("trade_name", 255), ("active_ingredient", 500),
                                         ("registration_no", 60), ("concentration", 100),
                                         ("toxicity", 500), ("pest_group", 100)])
def test_overlong_text_is_a_422_not_a_500(field, size):
    assert _body(**{field: "x" * size})
    with pytest.raises(ValidationError):
        _body(**{field: "x" * (size + 1)})


def test_use_rows_have_limits_too():
    with pytest.raises(ValidationError):
        _body(uses=[{"crop": "x" * 256}])
    with pytest.raises(ValidationError):
        _body(uses=[{}] * (R.MAX_USES_PER_RECORD + 1))


@pytest.mark.parametrize("over", [
    {"trade_name": "   "}, {"active_ingredient": ""}, {"status": 99}, {"status": -1},
    {"source_url": "javascript:alert(1)"}, {"source_url": "ftp://x"},
    {"registered_on": "0202-01-01"}, {"expires_on": "9999-12-31"},
    {"registered_on": "2025-05-01", "expires_on": "2024-05-01"},
])
def test_bad_input_is_refused(over):
    with pytest.raises(ValidationError):
        _body(**over)


def test_blank_name_says_so_in_vietnamese():
    with pytest.raises(ValidationError) as exc:
        _body(trade_name="")
    assert "Không được để trống" in str(exc.value)


def test_text_is_trimmed():
    assert _body(trade_name="  Tên  ").trade_name == "Tên"


def test_create_marks_manual_and_writes_uses(db):
    out = E.create_pesticide(db, _body(), user_id=1)
    assert out["is_manual"] is True and out["source_id"] == 0
    assert [u["pest"] for u in out["uses"]] == ["sâu cuốn lá"]
    assert db.get(CustomsPesticide, out["id"]).trade_key == "TỰ THÊM"


def test_update_replaces_fields_and_all_uses(db):
    pid = E.create_pesticide(db, _body(), user_id=1)["id"]
    out = E.update_pesticide(db, pid, _body(trade_name="Đổi Tên 5WG", uses=[
        {"crop": "cà phê"}, {"crop": "tiêu"}]), user_id=2)
    assert out["trade_name"] == "Đổi Tên 5WG"
    assert [u["crop"] for u in out["uses"]] == ["cà phê", "tiêu"]
    assert db.query(CustomsPesticideUse).count() == 2
    assert E.update_pesticide(db, pid, _body(uses=[]), user_id=2)["uses"] == []


def test_update_and_delete_missing_row_is_404(db):
    with pytest.raises(HTTPException) as exc:
        E.update_pesticide(db, 999, _body(), user_id=1)
    assert exc.value.status_code == 404
    with pytest.raises(HTTPException):
        E.delete_pesticide(db, 999, user_id=1)


def test_delete_removes_uses_too(db):
    pid = E.create_pesticide(db, _body(), user_id=1)["id"]
    E.delete_pesticide(db, pid, user_id=1)
    assert db.query(CustomsPesticide).count() == 0
    assert db.query(CustomsPesticideUse).count() == 0


def test_reimport_keeps_manual_rows_and_replaces_sourced_ones(db):
    S.replace_catalog(db, _file(1, 2), user_id=1, filename="a.json")
    manual = E.create_pesticide(db, _body(), user_id=1)
    #  Sửa tay một thuốc TỪ NGUỒN: lần nạp sau ghi đè theo nguồn (đã báo người dùng ở hộp nạp).
    sourced = db.query(CustomsPesticide).filter_by(source_id=1).one()
    E.update_pesticide(db, sourced.id, _body(trade_name="Sửa Tay 1SC", uses=[]), user_id=1)

    result = S.replace_catalog(db, _file(1, 3), user_id=1, filename="b.json")
    assert result["kept_manual"] == 1
    names = sorted(p.trade_name for p in db.query(CustomsPesticide))
    assert names == ["Nguồn 1 10SC", "Nguồn 3 10SC", "Tự Thêm 20EC"]
    kept = db.get(CustomsPesticide, manual["id"])
    assert kept is not None and kept.is_manual
    assert db.query(CustomsPesticideUse).filter_by(pesticide_id=manual["id"]).count() == 1

    #  Nạp lần nữa: không nhân đôi, id không đụng nhau.
    S.replace_catalog(db, _file(1, 3), user_id=1, filename="c.json")
    assert db.query(CustomsPesticide).count() == 3
    assert db.query(CustomsPesticideUse).count() == 3


def test_source_row_without_id_is_not_mistaken_for_manual(db):
    """Bộ đọc cho `source_id = 0` khi dòng nguồn thiếu mã — nếu lấy đó làm dấu «tự thêm» thì
    dòng ấy sống sót qua mỗi lần nạp và nhân đôi."""
    records = _file(5)
    records[0]["source_id"] = 0
    S.replace_catalog(db, records, user_id=1, filename="a.json")
    S.replace_catalog(db, records, user_id=1, filename="b.json")
    assert db.query(CustomsPesticide).count() == 1
    assert S.replace_catalog(db, records, user_id=1, filename="c.json")["kept_manual"] == 0


# ── Tệp đính kèm của thuốc (duoc-CR-494) ─────────────────────────────────────────
from app.core import file_registry as FR  # noqa: E402
from app.modules.attachment import controller as AC  # noqa: E402
from app.modules.attachment.model import FileLink, StoredFile  # noqa: E402


def _attach(db, pesticide_id):
    f = StoredFile(filename="nhan.pdf", file_key="k", source="test")   # `source` ≠ rỗng: không chạm kho
    db.add(f)
    db.flush()
    db.add(FileLink(file_id=f.id, entity="customs_pesticide", entity_id=pesticide_id))
    db.commit()
    return f.id


def _links(db, pesticide_id):
    return db.query(FileLink).filter_by(entity="customs_pesticide", entity_id=pesticide_id).count()


def test_reimport_keeps_ids_so_attachments_keep_their_drug(db):
    """Nạp lại mà cấp id mới thì mọi tệp đính kèm của thuốc từ nguồn mất chủ ngay lần nạp sau."""
    S.replace_catalog(db, _file(1, 2), user_id=1, filename="a.json")
    ids = {p.source_id: p.id for p in db.query(CustomsPesticide)}
    _attach(db, ids[1])
    S.replace_catalog(db, _file(1, 2, 3), user_id=1, filename="b.json")
    after = {p.source_id: p.id for p in db.query(CustomsPesticide)}
    assert after[1] == ids[1] and after[2] == ids[2]
    assert _links(db, ids[1]) == 1


def test_dropped_drug_id_is_never_reused_and_its_files_are_cleaned(db):
    S.replace_catalog(db, _file(1, 2), user_id=1, filename="a.json")
    ids = {p.source_id: p.id for p in db.query(CustomsPesticide)}
    fid = _attach(db, ids[2])
    result = S.replace_catalog(db, _file(1, 9), user_id=1, filename="b.json")
    assert result["dropped"] == 1
    new_id = db.query(CustomsPesticide).filter_by(source_id=9).one().id
    #  Tái dùng id của thuốc 2 thì thuốc 9 «nhận» luôn tệp nhãn của thuốc 2.
    assert new_id > max(ids.values())
    assert _links(db, ids[2]) == 0 and db.get(StoredFile, fid) is None


def test_deleting_a_drug_cleans_its_files(db):
    pid = E.create_pesticide(db, _body(), user_id=1)["id"]
    fid = _attach(db, pid)
    E.delete_pesticide(db, pid, user_id=1)
    assert _links(db, pid) == 0 and db.get(StoredFile, fid) is None


def test_files_are_read_with_customs_price_and_managed_with_customs_pesticide(db, monkeypatch):
    assert FR.policy("customs_pesticide")[0] == "customs_pesticide"
    assert FR.read_parent("customs_pesticide") == "customs_price"
    assert FR.read_parent("contract") == "contract", "entity khác vẫn đọc theo entity cha như cũ"
    asked = []
    monkeypatch.setattr(AC, "user_has_permission",
                        lambda db_, user, entity, action: asked.append((entity, action)) or True)
    monkeypatch.setattr(AC, "ensure_in_scope", lambda *a, **k: None)
    AC._check(db, object(), "customs_pesticide", "read", 1)
    AC._check(db, object(), "customs_pesticide", "manage", 1)
    assert asked[0] == ("customs_price", "read")
    assert asked[1] == ("customs_pesticide", "write")


def test_scope_check_for_reading_files_uses_the_read_key(db, monkeypatch):
    """Soi phạm vi theo `customs_pesticide` lúc ĐỌC thì người chỉ có `customs_price.read` không có
    grant nào trên khóa đó — `apply_scope` ra `false()` và họ bị chặn xem tệp oan."""
    from app.core import attachment_scope as ASC
    pid = E.create_pesticide(db, _body(), user_id=1)["id"]
    seen = []

    def fake_scope(query, model, entity, user, profile, action):
        seen.append((entity, action))
        return query
    monkeypatch.setattr(ASC, "apply_scope", fake_scope)
    monkeypatch.setattr(ASC, "get_perm_profile", lambda *a: None)
    ASC.ensure_in_scope(db, object(), "customs_pesticide", pid, "read")
    ASC.ensure_in_scope(db, object(), "customs_pesticide", pid, "manage")
    assert seen[0] == ("customs_price", "read")
    assert seen[1] == ("customs_pesticide", "write")
    with pytest.raises(HTTPException) as exc:
        ASC.ensure_in_scope(db, object(), "customs_pesticide", 999999, "manage")
    assert exc.value.status_code == 404


# ── Câu mô tả của trang nguồn (duoc-CR-495) ──────────────────────────────────────
def test_reader_keeps_the_source_summary_sentence():
    raw = [{"id": 1, "ten_thuoc": "Nguồn 1 10SC", "hoat_chat": "Chitosan 2%", "tinh_trang": "Còn hiệu lực",
            "tom_tat_su_dung": "  Thuốc trừ bệnh Nguồn 1 10SC hoạt chất Chitosan 2%, sử dụng trên lúa.  ",
            "pham_vi_su_dung": [{"cay_trong": "lúa"}]}]
    rec = R.read_file("thuoc-bvtv.json", json.dumps(raw, ensure_ascii=False).encode())[0]
    assert rec["summary"] == "Thuốc trừ bệnh Nguồn 1 10SC hoạt chất Chitosan 2%, sử dụng trên lúa."


def test_summary_flows_to_detail_and_is_editable_for_manual_drugs(db):
    S.replace_catalog(db, _file(1), user_id=1, filename="a.json")
    pid = E.create_pesticide(db, _body(summary="  Thuốc tự nhập mô tả.  "), user_id=1)["id"]
    assert S.get_pesticide(db, pid)["summary"] == "Thuốc tự nhập mô tả."
    assert E.update_pesticide(db, pid, _body(summary=""), user_id=1)["summary"] == ""
    with pytest.raises(ValidationError):
        _body(summary="x" * (R._TEXT_LIMIT + 1))
