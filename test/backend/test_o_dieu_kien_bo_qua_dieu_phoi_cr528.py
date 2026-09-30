"""bao-CR-528 — ô «Điều kiện bỏ qua điều phối» (`pr_dispatch_skip_rules`) dùng BỘ CHỌN, không gõ JSON.

Đại ca chê ô cũ: «cấu hình là gõ code vào à». Giao diện nay vẽ bộ chọn điều kiện theo cờ
`type: "condition"` + `condition_entity: "pr_dispatch"` của backend. Dưới DB vẫn là chuỗi JSON
cú pháp bộ máy duyệt (bao-CR-497 đọc y như cũ). Điều mới ở backend là CỬA LƯU:

  · điều kiện hợp lệ → lưu nguyên văn;
  · JSON hỏng / không phải danh sách / trường lạ / phép lạ / thiếu giá trị → 400 bằng câu tiếng Việt
    (trước CR này gõ sai là lặng lẽ thành «không bỏ qua phiếu nào»);
  · để trống hoặc `[]` → xóa điều kiện;
  · giá trị hỏng CŨ đang nằm dưới DB không được chặn lần lưu của người chỉ sửa ô khác;
  · lúc CHẠY vẫn khoan dung như cũ — đã có bài kiểm của bao-CR-497 canh.
"""
import json
import time

import pytest
from fastapi import HTTPException

from app.core import app_settings
from app.modules.approval import condition_service
from app.modules.audit.model import AuditLog
from app.modules.purchase_request import service as pr_service
from app.modules.setting import service
from app.modules.setting.model import Setting

KEY = "pr_dispatch_skip_rules"
FACTORY_RULE = '[{"field": "handler_dept_id", "op": "not_empty"}]'


@pytest.fixture(autouse=True)
def _settings_read_test_db(db, monkeypatch):
    """`app_settings` đọc từ DB của bài kiểm (bản thật mở `SessionLocal` MySQL), dọn đệm mỗi bài."""
    def load_from_test_db():
        app_settings._cache = {s.skey: s.svalue for s in db.query(Setting).all()}
        app_settings._exp = time.time() + app_settings._TTL

    monkeypatch.setattr(app_settings, "_load", load_from_test_db)
    app_settings.refresh()
    yield
    app_settings.refresh()


def _stored(db) -> str | None:
    row = db.query(Setting).filter(Setting.skey == KEY).first()
    return row.svalue if row else None


def _save_error(db, value) -> str:
    with pytest.raises(HTTPException) as e:
        service.save(db, {KEY: value}, user_id=7)
    assert e.value.status_code == 400
    return str(e.value.detail)


# ---------------------------------------------------------------------------
# Cờ giao diện
# ---------------------------------------------------------------------------
def test_field_is_flagged_as_condition_builder_but_stored_as_string():
    field = next(f for f in service.get_all()["fields"] if f["key"] == KEY)
    assert field["type"] == "condition"
    assert field["condition_entity"] == "pr_dispatch"
    #  Lớp đọc cấu hình vẫn coi là chuỗi — `_cast` không đổi gì.
    assert app_settings.REGISTRY[KEY][0] == "str"


def test_hint_no_longer_asks_admin_to_type_json():
    field = next(f for f in service.FIELDS if f["key"] == KEY)
    assert "JSON" not in field["hint"]
    assert '"field"' not in field["hint"]
    assert "Phòng xử lý có giá trị" in field["hint"]


def test_condition_fields_match_dispatch_context_keys(db, seed):
    """Bộ trường cửa lưu chấp nhận phải đúng bằng bộ khóa `dispatch_context` đưa vào điều kiện."""
    from app.modules.purchase_request.model import PurchaseRequest
    pr = PurchaseRequest(code="PYC-528-A", company_id=seed.company_id, requester="X",
                         requester_id=seed.emp_req_id, department="P", status="draft",
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.commit()
    assert set(pr_service.dispatch_context(db, pr)) == set(pr_service.DISPATCH_CONTEXT_FIELDS)


# ---------------------------------------------------------------------------
# Cửa lưu — nhận
# ---------------------------------------------------------------------------
def test_valid_factory_rule_is_saved_verbatim(db):
    service.save(db, {KEY: FACTORY_RULE}, user_id=7)
    assert _stored(db) == FACTORY_RULE
    assert app_settings.get(KEY) == FACTORY_RULE


def test_every_field_and_value_shape_the_builders_produce_is_accepted(db):
    rule = json.dumps([
        {"field": "handler_dept_id", "op": "in", "value": [5, 7]},
        {"field": "department_id", "op": "not_in", "value": [3]},
        {"field": "company_id", "op": "in", "value": [1]},
        {"field": "requester_id", "op": "in", "value": [42]},
        {"field": "is_urgent", "op": "eq", "value": False},
        {"field": "line_count", "op": "lte", "value": 0},
    ])
    service.save(db, {KEY: rule}, user_id=7)
    assert _stored(db) == rule


@pytest.mark.parametrize("empty", ["", "   ", "[]", None])
def test_empty_or_empty_list_clears_the_rule(db, empty):
    service.save(db, {KEY: FACTORY_RULE}, user_id=7)
    service.save(db, {KEY: empty}, user_id=7)
    assert _stored(db) == ""
    assert pr_service.dispatch_skip_rules() == ""


# ---------------------------------------------------------------------------
# Cửa lưu — chặn
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("raw", ["[{", "abc", '[{"field": "handler_dept_id", "op": "not_empty"}'])
def test_malformed_json_is_rejected(db, raw):
    message = _save_error(db, raw)
    assert "sai cú pháp" in message
    assert _stored(db) is None, "lỗi thì không ghi gì xuống bảng"


@pytest.mark.parametrize("raw", ['{"field": "handler_dept_id", "op": "not_empty"}', '"x"', "42", "null"])
def test_non_list_is_rejected(db, raw):
    assert "danh sách" in _save_error(db, raw)


def test_row_that_is_not_an_object_is_rejected(db):
    assert "dòng 1 không phải một điều kiện" in _save_error(db, '["handler_dept_id"]')


def test_unknown_field_is_rejected_with_the_usable_list(db):
    message = _save_error(db, '[{"field": "handler_dept", "op": "not_empty"}]')
    assert "«handler_dept»" in message
    assert "Phòng xử lý (handler_dept_id)" in message


def test_field_of_wrong_type_is_rejected_not_crashed(db):
    """Trường là danh sách (không băm được) thì báo lỗi, không nổ 500."""
    assert "dòng 1" in _save_error(db, '[{"field": ["handler_dept_id"], "op": "not_empty"}]')


def test_unknown_op_is_rejected(db):
    message = _save_error(db, '[{"field": "line_count", "op": "like", "value": 1}]')
    assert "phép so «like»" in message


def test_error_names_the_offending_row(db):
    raw = json.dumps([
        {"field": "handler_dept_id", "op": "not_empty"},
        {"field": "line_count", "op": "between", "value": 1},
    ])
    assert "dòng 2" in _save_error(db, raw)


@pytest.mark.parametrize("row", [
    {"field": "company_id", "op": "in", "value": []},
    {"field": "company_id", "op": "not_in"},
    {"field": "line_count", "op": "gte"},
    {"field": "line_count", "op": "eq", "value": ""},
])
def test_row_without_a_value_to_compare_is_rejected(db, row):
    """`in: []` không bao giờ khớp; thiếu giá trị thì so với `None` — cả hai là điều kiện chết."""
    assert "chưa" in _save_error(db, json.dumps([row]))


def test_one_bad_field_blocks_the_whole_save(db):
    """Không có chuyện lưu được nửa chừng: ô khác trong cùng lần lưu cũng không được ghi."""
    with pytest.raises(HTTPException):
        service.save(db, {"smtp_host": "moi.example.com", KEY: "[{"}, user_id=7)
    assert db.query(Setting).filter(Setting.skey == "smtp_host").first() is None


def test_legacy_broken_value_does_not_block_saving_other_fields(db):
    """Màn hình gửi lại MỌI ô: giá trị hỏng cũ dưới DB không được chặn người chỉ sửa ô email."""
    db.add(Setting(skey=KEY, svalue="[{"))
    db.commit()
    app_settings.refresh()

    service.save(db, {"smtp_host": "moi.example.com", KEY: "[{"}, user_id=7)

    assert db.query(Setting).filter(Setting.skey == "smtp_host").one().svalue == "moi.example.com"
    assert _stored(db) == "[{", "giá trị cũ giữ nguyên, không ai đụng tới"


def test_legacy_broken_value_is_still_blocked_when_changed_to_another_broken_value(db):
    db.add(Setting(skey=KEY, svalue="[{"))
    db.commit()
    app_settings.refresh()
    _save_error(db, "abc")


# ---------------------------------------------------------------------------
# Nhật ký đọc ra câu, không bày JSON
# ---------------------------------------------------------------------------
def test_audit_log_describes_the_rule_in_words(db):
    service.save(db, {KEY: FACTORY_RULE}, user_id=7)
    log = db.query(AuditLog).filter(AuditLog.entity == "setting").order_by(AuditLog.id.desc()).first()
    assert "(trống) -> Phòng xử lý có giá trị" in log.message
    assert '"field"' not in log.message


# ---------------------------------------------------------------------------
# Lúc chạy vẫn khoan dung
# ---------------------------------------------------------------------------
def test_runtime_parse_stays_lenient():
    """Cửa lưu chặt, lúc chạy vẫn nuốt lỗi: một ô hỏng không được chặn phiếu nào."""
    assert condition_service.parse("[{") == []
    assert condition_service.matches('[{"field": "nope", "op": "like"}]', {}) is False
    assert condition_service.find_error("[{", {"a": "A"})
    assert condition_service.find_error("", {"a": "A"}) == ""
