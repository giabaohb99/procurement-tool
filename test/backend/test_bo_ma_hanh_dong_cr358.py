"""BỘ MÃ HÀNH ĐỘNG là tập ĐÓNG — bài kiểm canh cửa (bao-CR-358 / CR-312 P2, NT-4).

Bài kiểm cũ (`test_va_nhat_ky_thao_tac.py`) đã quét `ast` tìm lời gọi
`record(...)` và đòi mọi mã có nhãn. Nó bắt được thật, nhưng chỉ bắt phần **mã
viết thẳng thành chuỗi hằng** trong chính lời gọi đó. Quét lại ngày 10/09/2026:
30 mã hằng — và **17 chỗ truyền `action` là BIẾN, f-string hoặc biểu thức điều
kiện**. Mười bảy chỗ đó vô hình với bài kiểm cũ, và đúng ở đó có mã thiếu nhãn:

* `purchase_request/option_service.py` ghi `"option_unchoose" if already else
  "option_choose"` — **cả hai** đều không có trong bảng nhãn (bảng có
  `option_add`/`option_remove` và `choose_option`/`unchoose_option`, hai bộ tên
  khác);
* `document/file_access_log.py` ghi `download_file` và `file_alert` — không mã
  nào có nhãn;
* sáu hàm `set_status(...)` ghi thẳng giá trị `status` làm mã hành động, nên
  `partial`, `received`, `draft`, `open`, `in_progress`, `answered`, `done`,
  `survey_done` đều là mã hành động thật mà chưa ai khai.

Nên bài kiểm này canh theo BA lối, không chỉ một:

1. bản thân bảng khai có sạch không;
2. mã hằng trong `record(...)` — quét cả `app/core`, không riêng `app/modules`;
3. **mã đi đường vòng**: giá trị hằng truyền vào `set_status(...)` và
   `_write_log(...)`, cộng một sổ khai tay cho 17 chỗ động. Sổ đó chốt cả DANH
   SÁCH CHỖ: mọc thêm một chỗ động mới mà không khai thì đỏ, vì chỗ động là
   thứ không cách nào tự dò ra giá trị.
"""
import ast
import pathlib

import pytest

import app
from app.core.action_catalog import (ACTION_CATALOG, ACTION_FAMILIES, ACTION_LABELS,
                                     action_options, group_of_action, is_known_action,
                                     label_of_action)
from app.core.logging_codes import ACTION_GROUP_LABELS, ACTION_GROUP_UNKNOWN
from app.core.permissions import ACTIONS

APP_ROOT = pathlib.Path(app.__file__).parent

#  Tên hàm nào coi là "ghi một dòng dấu vết".
RECORD_FUNCS = ("record", "audit_record")

#  Hàm trung gian nhận mã hành động qua THAM SỐ rồi mới gọi `record(...)`:
#  tên hàm -> vị trí của đối số mã trong lời gọi. Quét lời gọi tới chúng là dò
#  được giá trị hằng mà lối quét thẳng `record(...)` không thấy.
RELAY_FUNCS = {
    #  `set_status(db, id, status, user_id, ...)` — sáu phiếu, cùng một chữ ký.
    "set_status": 2,
    #  `_write_log(db, id, instance, action, message)` — ba cầu nối bộ máy duyệt.
    "_write_log": 3,
}

#  ---------------------------------------------------------------------------
#  SỔ CHỖ TRUYỀN MÃ ĐỘNG — khai tay, cố ý.
#
#  Khóa là `<đường dẫn>::<tên hàm bao ngoài>` (không dùng số dòng: sửa một chú
#  thích ở trên là số dòng trôi, bài kiểm đỏ oan). Giá trị là MỌI mã mà chỗ đó
#  có thể sinh ra — đọc từ các lời gọi tới nó.
#
#  ⚠️ Thêm một lời gọi `record(...)` với `action` không phải chuỗi hằng thì
#  PHẢI thêm một dòng vào đây. Không có đường nào khác: máy không đọc được giá
#  trị của một biến, nên chỗ nào máy không đọc được thì người phải khai.
#  ---------------------------------------------------------------------------
DYNAMIC_ACTION_SITES: dict[str, tuple[str, ...]] = {
    #  `f"tool:{name}"` — 34 công cụ của trợ lý AI, khai thành HỌ mã.
    "modules/assistant/tools/__init__.py::_audit": ("tool:list_purchase_orders",),
    "modules/category_assignee/service.py::bulk_upsert": ("create", "update"),
    #  Bốn kết cục của luồng duyệt Văn thư.
    "modules/document/approval_bridge.py::_write_log": (
        "approved", "rejected", "returned", "withdrawn"),
    "modules/document/file_access_log.py::log_and_alert": ("view_file", "download_file"),
    "modules/document/file_access_log.py::_raise_alert": ("file_alert",),
    "modules/payment_request/service.py::set_status": (
        "submitted", "approved", "cancelled", "paid"),
    #  ĐMH có nhiều mã nhất: bốn mã do người bấm, ba mã do `_recalc_status` tự
    #  đặt lại theo số lượng đã nhận, cộng `draft` của đường hủy duyệt.
    "modules/purchase_order/service.py::set_status": (
        "submitted", "approved", "cancelled", "rejected", "completed",
        "draft", "received", "partial"),
    "modules/purchase_request/option_service.py::choose_option": (
        "option_choose", "option_unchoose"),
    "modules/purchase_request/service.py::set_status": ("submitted", "approved", "rejected"),
    "modules/seal_request/approval_bridge.py::_write_log": ("approve", "cancel", "update"),
    "modules/survey/service.py::set_status": (
        "submitted", "approved", "rejected", "cancelled"),
    "modules/survey_request/service.py::set_status": (
        "submitted", "approved", "processing", "rejected", "cancelled",
        "done", "survey_done"),
    "modules/survey_request/service.py::choose_option": ("choose_option", "unchoose_option"),
    "modules/ticket/service.py::assign": ("assign", "unassign"),
    "modules/ticket/service.py::set_status": ("open", "in_progress", "answered", "closed"),
    "modules/user/service.py::set_active": ("activate", "deactivate"),
    "modules/vehicle_booking/approval_bridge.py::_write_log": ("approve", "cancel", "update"),
}


def _parse_app_files():
    """Duyệt mọi tệp `.py` của `app/`, trả `(đường dẫn tương đối, cây cú pháp)`."""
    for path in sorted(APP_ROOT.rglob("*.py")):
        try:
            yield path.relative_to(APP_ROOT).as_posix(), ast.parse(
                path.read_text(encoding="utf-8"))
        except SyntaxError:  # pragma: no cover - tệp hỏng thì bài kiểm khác lo
            continue


def _tag_enclosing_function(tree: ast.AST) -> None:
    """Gắn tên hàm bao ngoài vào từng nút, để định danh chỗ gọi mà không cần số dòng."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(node):
                if not hasattr(child, "enclosing_function"):
                    child.enclosing_function = node.name


def _called_name(call: ast.Call) -> str:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _arg_at(call: ast.Call, index: int, keyword: str | None = None) -> ast.expr | None:
    if len(call.args) > index:
        return call.args[index]
    if keyword:
        return next((kw.value for kw in call.keywords if kw.arg == keyword), None)
    return None


def _scan_record_calls() -> tuple[set[str], set[str]]:
    """Trả `(mã hằng, khóa của những chỗ truyền mã động)`."""
    constants: set[str] = set()
    dynamic_sites: set[str] = set()
    for rel, tree in _parse_app_files():
        _tag_enclosing_function(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or _called_name(node) not in RECORD_FUNCS:
                continue
            arg = _arg_at(node, 4, "action")
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                constants.add(arg.value)
            else:
                dynamic_sites.add(f"{rel}::{getattr(node, 'enclosing_function', '?')}")
    return constants, dynamic_sites


def _scan_relay_calls() -> set[str]:
    """Mã hằng truyền vào các hàm trung gian (`set_status`, `_write_log`)."""
    found: set[str] = set()
    for _rel, tree in _parse_app_files():
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            index = RELAY_FUNCS.get(_called_name(node))
            if index is None:
                continue
            arg = _arg_at(node, index)
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                found.add(arg.value)
    return found


# ===========================================================================
# 1. Bảng khai có sạch không
# ===========================================================================

def test_moi_ma_deu_co_nhan_tieng_viet_va_nhom_hop_le():
    """Nhãn rỗng còn tệ hơn mã trần: dòng dấu vết mất luôn phần «làm gì»."""
    for value, code in ACTION_CATALOG.items():
        assert code.value == value, f"khóa và mã lệch nhau: {value} / {code.value}"
        assert (code.label or "").strip(), f"mã «{value}» thiếu nhãn tiếng Việt"
        assert code.group in ACTION_GROUP_LABELS, f"mã «{value}» khai nhóm lạ: {code.group}"
        assert code.group != ACTION_GROUP_UNKNOWN, (
            f"mã «{value}» khai nhóm «Không rõ» — nhóm 0 là chỗ dành cho mã CHƯA "
            "khai, khai thẳng vào đó thì mất luôn ý nghĩa của nó")


def test_hai_dang_cua_cung_mot_viec_noi_giong_nhau():
    """«approve» và «approved» là một việc — hai nhãn khác nhau thì cùng một
    hành động đọc ra hai kiểu trên cùng một dòng thời gian."""
    for infinitive, past in [("approve", "approved"), ("reject", "rejected"),
                             ("return", "returned"), ("withdraw", "withdrawn"),
                             ("cancel", "cancelled"), ("submit", "submitted")]:
        assert ACTION_LABELS[infinitive] == ACTION_LABELS[past], infinitive
        assert group_of_action(infinitive) == group_of_action(past), infinitive


def test_moi_hanh_dong_trong_bang_quyen_deu_co_ma():
    """`ACTIONS` là bộ hành động mà MỌI endpoint gác theo, nên bất kỳ cái nào
    cũng có thể rơi vào dấu vết. Trừ `read` — đọc bản ghi không ghi dấu vết
    (đo lại 04/09/2026), lượt đọc nằm ở `tab_request_log` chứ không ở đây."""
    missing = [a for a in ACTIONS if a != "read" and a not in ACTION_CATALOG]
    assert missing == [], f"hành động gác được nhưng chưa có mã: {missing}"


# ===========================================================================
# 2. Mã hằng trong lời gọi `record(...)`
# ===========================================================================

def test_moi_ma_hang_trong_record_deu_da_khai():
    constants, _ = _scan_record_calls()
    assert constants, "quét hỏng: không tìm thấy lời gọi record(...) nào"
    missing = sorted(c for c in constants if not is_known_action(c))
    assert missing == [], (
        f"{len(missing)} mã hành động được ghi vào nhật ký mà chưa khai: {missing}. "
        "Thêm một dòng ở `app/core/action_catalog.py` — thiếu thì dòng dấu vết "
        "hiện mã Anh trần và rơi vào nhóm «Không rõ».")


# ===========================================================================
# 3. Mã đi đường vòng
# ===========================================================================

def test_moi_ma_truyen_qua_ham_trung_gian_deu_da_khai():
    """`set_status(db, id, "partial", ...)` cũng là ghi mã hành động `partial`,
    chỉ là chuỗi nằm cách lời gọi `record(...)` vài tệp."""
    relayed = _scan_relay_calls()
    assert relayed, "quét hỏng: không tìm thấy lời gọi set_status/_write_log nào"
    missing = sorted(c for c in relayed if not is_known_action(c))
    assert missing == [], (
        f"{len(missing)} giá trị truyền vào {sorted(RELAY_FUNCS)} rơi thẳng vào cột "
        f"`action` mà chưa khai: {missing}")


def test_so_cho_truyen_ma_dong_van_dung_nhu_da_khai():
    """Mọc thêm một chỗ truyền `action` động mà không khai vào sổ thì đỏ.

    Đây là chốt quan trọng nhất của bài kiểm: chỗ động là chỗ máy KHÔNG đọc
    được giá trị, nên nếu không bắt buộc khai thì nó lặng lẽ nằm ngoài mọi
    bài kiểm — đúng cách `option_choose` và `download_file` sống sót tới hôm nay.
    """
    _, sites = _scan_record_calls()
    declared = set(DYNAMIC_ACTION_SITES)
    added = sorted(sites - declared)
    removed = sorted(declared - sites)
    assert added == [], (
        f"{len(added)} chỗ truyền `action` động chưa khai: {added}. Mở "
        "`DYNAMIC_ACTION_SITES` ở đầu tệp này, thêm một dòng liệt kê MỌI mã mà "
        "chỗ đó có thể sinh ra, rồi khai những mã đó ở `action_catalog.py`.")
    assert removed == [], (
        f"{len(removed)} chỗ khai trong sổ nhưng không còn trong mã nguồn: {removed}. "
        "Đã đổi thành mã hằng hoặc đổi tên hàm thì xóa dòng khai đi.")


@pytest.mark.parametrize("site,actions", sorted(DYNAMIC_ACTION_SITES.items()))
def test_moi_ma_khai_o_cho_dong_deu_co_trong_bo_ma(site, actions):
    assert actions, f"{site}: khai chỗ động mà không liệt kê mã nào"
    missing = sorted(a for a in actions if not is_known_action(a))
    assert missing == [], f"{site} sinh ra mã chưa khai: {missing}"


# ===========================================================================
# 4. Cư xử lúc chạy
# ===========================================================================

def test_ma_la_khong_lam_sap_gi_ca():
    """NT-5: lớp nhật ký không bao giờ là thứ làm hỏng lớp nghiệp vụ. Mã lạ ra
    nhóm «Không rõ» và nhãn là chính nó — không ném, không đoán bừa."""
    assert group_of_action("khong_he_ton_tai") == ACTION_GROUP_UNKNOWN
    assert label_of_action("khong_he_ton_tai") == "khong_he_ton_tai"
    assert is_known_action("khong_he_ton_tai") is False
    #  Chuỗi rỗng / None cũng phải chịu được: `record(...)` có nơi gọi với biến.
    assert group_of_action("") == ACTION_GROUP_UNKNOWN
    assert label_of_action("") == ""


def test_ho_ma_theo_tien_to_doc_duoc_ten_cong_cu():
    """34 công cụ của trợ lý AI không khai thành 34 dòng — nếu tra bảng phẳng
    thì mọi dòng đó hiện `tool:search_products` trần."""
    prefix = ACTION_FAMILIES[0].prefix
    assert is_known_action(f"{prefix}search_products")
    label = label_of_action(f"{prefix}search_products")
    assert "search_products" in label and not label.startswith(prefix)
    assert group_of_action(f"{prefix}search_products") == ACTION_FAMILIES[0].group
    #  Tiền tố trần, không có tên công cụ, KHÔNG phải mã hợp lệ.
    assert is_known_action(prefix) is False


def test_danh_sach_cho_o_chon_xep_theo_nhom():
    options = action_options()
    assert len(options) == len(ACTION_CATALOG)
    groups = [o["group"] for o in options]
    assert groups == sorted(groups), "ô chọn phải gom các mã cùng nhóm liền nhau"
    assert all(o["label"] for o in options)
