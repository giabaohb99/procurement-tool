"""BỘ MÃ HÀNH ĐỘNG của nhật ký ba tầng — nơi khai DUY NHẤT (CR-312 P2 / NT-4).

Cột `action` của `tab_audit_log` là một **tập mã ĐÓNG**. Trước tệp này nó chỉ
đóng trên giấy: mã sinh ra ở 213 lời gọi `record(...)` rải khắp `app/`, còn hai
thứ đi kèm mỗi mã thì nằm ở hai tệp khác nhau, chẳng cái nào biết cái nào —

* **nhãn tiếng Việt** ở `ACTION_LABEL` của `modules/audit/controller.py`;
* **nhóm hành động** ở `ACTION_GROUP_BY_ACTION` của `core/logging_codes.py`.

Thêm một lời gọi `record(...)` với mã mới là hợp lệ về cú pháp, chạy được, và
lặng lẽ sinh ra dòng nhật ký **không nhãn** (người đọc thấy mã Anh trần giữa
câu tiếng Việt: *«Dego Admin — assign: Phân bổ NSTM»*) và **không nhóm**
(`action_group = 0`, tức dòng đó biến mất khỏi mọi bộ lọc theo nhóm). Đo trên
dữ liệu thật ngày 05/09/2026: **971 dòng** mất nhãn, 36 dòng `closed` mất nhóm.
Không ai làm sai cả — cơ chế "nhớ cập nhật thêm hai bảng nữa" là thứ sai.

Nay **một dòng khai đủ ba thứ**, và nhãn tiếng Việt là **điều kiện để mã tồn
tại**: `_build()` ném ngay lúc import nếu nhãn rỗng. Muốn thêm mã hành động thì
chỉ có một chỗ để thêm, và không thêm thiếu được.

⚠️ **`action` cố ý vẫn là `VARCHAR`, không đổi sang `SMALLINT`** dù luật R2/QĐ-11
bắt mọi cột phân loại MỚI phải là số. Lý do y hệt ngoại lệ QĐ-9 của Thu mua:
4.201 dòng đã ghi bằng chữ, và lúc có sự cố người ta đọc thẳng bảng bằng SQL —
`WHERE action = 'delete'` đọc được, `WHERE action = 4` thì phải mở mã nguồn ra
tra. Tập đóng ở đây thay cho kiểu dữ liệu số. Mọi cột phân loại KHÁC của lớp
nhật ký (`actor_kind`, `action_group`, `op`, `device_type`…) vẫn là `SMALLINT`.

Ba thứ tệp này KHÔNG làm, cố ý:

* **Không tự sửa mã sai thành mã đúng.** Mã lạ vẫn được ghi xuống nguyên văn —
  nhật ký phải chép lại đúng thứ đã xảy ra, kể cả khi thứ đó là một lỗi lập
  trình. Nó chỉ ghi thêm một dòng cảnh báo vào `app.action_catalog`.
* **Không chặn nghiệp vụ.** `record(...)` mà ném ngoại lệ vì mã lạ thì một lỗi
  hiển thị của nhật ký làm hỏng việc lưu đơn hàng. Xem NT-5: lớp nhật ký không
  bao giờ là thứ làm sập lớp nghiệp vụ.
* **Không đoán nhóm theo tên mã.** Mã lạ nhận nhóm `0` (*Không rõ*) chứ không
  suy từ hậu tố — đoán sai thì dòng đó nằm nhầm nhóm, còn tệ hơn nằm ở
  *Không rõ*, vì *Không rõ* thì người ta còn đi tra.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from app.core.logging_codes import (ACTION_GROUP_APPROVE, ACTION_GROUP_AUTH,
                                    ACTION_GROUP_DELETE, ACTION_GROUP_EDIT,
                                    ACTION_GROUP_EXPORT, ACTION_GROUP_LABELS,
                                    ACTION_GROUP_PERMISSION,
                                    ACTION_GROUP_UNKNOWN, ACTION_GROUP_VIEW)

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ActionCode:
    """Một mã hành động: mã máy đọc + nhãn người đọc + nhóm để lọc."""

    value: str
    label: str
    group: int


@dataclass(frozen=True)
class ActionFamily:
    """HỌ mã sinh theo tiền tố — dùng cho thứ không đếm hết được lúc khai.

    Chỉ có đúng một họ (`tool:`), và ngưỡng để thêm họ thứ hai nên rất cao:
    mỗi họ là một lỗ trên tập đóng, phần đuôi sau tiền tố không ai canh được.
    """

    prefix: str
    label_prefix: str
    group: int


#  =====================================================================
#  1. NHÓM SỬA DỮ LIỆU
#  =====================================================================
_EDIT = (
    ActionCode("create", "Tạo mới", ACTION_GROUP_EDIT),
    ActionCode("update", "Cập nhật", ACTION_GROUP_EDIT),
    #  Bảng quyền gọi việc sửa là `write`, dấu vết cũ gọi là `update` — hai chữ
    #  cho một việc, và cả hai đều đang được ghi ở đâu đó.
    ActionCode("write", "Cập nhật", ACTION_GROUP_EDIT),
    ActionCode("adjust", "Điều chỉnh tồn", ACTION_GROUP_EDIT),
    ActionCode("assign", "Phân bổ", ACTION_GROUP_EDIT),
    #  `ticket/service.py` ghi `"assign" if assignee_id else "unassign"` —
    #  nhánh gỡ người phụ trách trước CR-358 KHÔNG có nhãn.
    ActionCode("unassign", "Bỏ phân bổ", ACTION_GROUP_EDIT),
    ActionCode("dispatched", "Điều phối", ACTION_GROUP_EDIT),
    ActionCode("paid", "Ghi nhận đã chi", ACTION_GROUP_EDIT),
    ActionCode("fill_line", "Bổ sung dòng", ACTION_GROUP_EDIT),
    ActionCode("item_progress", "Cập nhật tiến độ dòng", ACTION_GROUP_EDIT),
    ActionCode("item_progress_auto", "Tự cập nhật tiến độ dòng", ACTION_GROUP_EDIT),
    ActionCode("document_status", "Đổi trạng thái chứng từ", ACTION_GROUP_EDIT),
    ActionCode("line_status", "Đổi trạng thái dòng", ACTION_GROUP_EDIT),
    ActionCode("expected_date", "Đổi ngày dự kiến", ACTION_GROUP_EDIT),
    ActionCode("pr_created", "Sinh yêu cầu mua hàng", ACTION_GROUP_EDIT),
    ActionCode("reply", "Phản hồi", ACTION_GROUP_EDIT),
)

#  ---------------------------------------------------------------------
#  1b. TRẠNG THÁI PHIẾU dùng luôn làm mã hành động
#
#  Sáu hàm `set_status(db, id, status, ...)` (YCMH · YCBG · Phiếu khảo sát ·
#  ĐMH · YCTT · Phiếu hỗ trợ) đều kết thúc bằng `record(db, uid, ENTITY, id,
#  status, ...)` — tức **mọi giá trị `status` hợp lệ của sáu phiếu đó là một mã
#  hành động**. Đây là nguồn mã ngầm lớn nhất của cả hệ, và là lý do bài kiểm
#  chỉ quét chuỗi hằng trong lời gọi `record(...)` không đủ: chuỗi nằm ở lời
#  gọi `set_status(...)` bên controller, cách đó vài tệp.
#  ---------------------------------------------------------------------
_STATUS_AS_ACTION = (
    ActionCode("processing", "Đang xử lý", ACTION_GROUP_EDIT),
    ActionCode("completed", "Hoàn tất", ACTION_GROUP_EDIT),
    ActionCode("auto_done", "Tự động hoàn tất", ACTION_GROUP_EDIT),
    #  YCBG: `done` = chốt xong toàn bộ yêu cầu, `survey_done` = phần khảo sát
    #  xong nhưng yêu cầu chưa đóng. Hai mốc khác nhau, đừng gộp nhãn.
    ActionCode("done", "Hoàn tất yêu cầu", ACTION_GROUP_EDIT),
    ActionCode("survey_done", "Khảo sát xong", ACTION_GROUP_EDIT),
    #  ĐMH: `_recalc_status` đặt lại theo số lượng đã nhận.
    ActionCode("received", "Đã nhận đủ hàng", ACTION_GROUP_EDIT),
    ActionCode("partial", "Nhận hàng một phần", ACTION_GROUP_EDIT),
    #  Phiếu hỗ trợ — `ticket/service.STATUSES`.
    ActionCode("open", "Mở phiếu", ACTION_GROUP_EDIT),
    ActionCode("in_progress", "Đang xử lý", ACTION_GROUP_EDIT),
    ActionCode("answered", "Đã trả lời", ACTION_GROUP_EDIT),
    #  Từng RƠI RA NGOÀI bảng nhóm — 36 dòng trên prod mang `action_group = 0`,
    #  tức lọc theo nhóm thì chúng biến mất khỏi mọi kết quả.
    ActionCode("closed", "Đóng phiếu", ACTION_GROUP_EDIT),
)

#  ---------------------------------------------------------------------
#  1c. PHƯƠNG ÁN — BỐN mã cho HAI việc, và đó là lỗi đã xảy ra
#
#  `add_option`/`del_option`/`choose_option`/`unchoose_option` là thao tác trên
#  Yêu cầu BÁO GIÁ (CR-311). `option_add`/`option_remove`/`option_choose`/
#  `option_unchoose` là thao tác trên Yêu cầu MUA HÀNG (CR-310). Hai phân hệ,
#  hai người viết, hai quy ước đặt tên ngược nhau.
#
#  ⚠️ Đúng chỗ này lộ ra cái giá của việc khai nhãn tách khỏi nơi ghi: bảng nhãn
#  cũ có `option_add`/`option_remove` (CR-310) và `choose_option`/
#  `unchoose_option` (CR-311) nhưng **thiếu `option_choose`/`option_unchoose`**
#  — mà đó lại chính là hai mã mà `purchase_request/option_service.py:298` đang
#  ghi. Người khai nhãn đọc tên hàm CR-310 rồi suy ra tên mã, và suy sai. Không
#  bài kiểm nào bắt được vì hai mã đó nằm trong một biểu thức điều kiện, không
#  phải hằng chuỗi.
#  ---------------------------------------------------------------------
_OPTION = (
    ActionCode("sync_options", "Đồng bộ phương án", ACTION_GROUP_EDIT),
    ActionCode("add_option", "Gắn phương án", ACTION_GROUP_EDIT),
    ActionCode("del_option", "Gỡ phương án", ACTION_GROUP_EDIT),
    ActionCode("choose_option", "Chốt phương án", ACTION_GROUP_EDIT),
    ActionCode("unchoose_option", "Bỏ chốt phương án", ACTION_GROUP_EDIT),
    ActionCode("option_add", "Gắn phương án", ACTION_GROUP_EDIT),
    ActionCode("option_remove", "Gỡ phương án", ACTION_GROUP_EDIT),
    ActionCode("option_choose", "Chốt phương án", ACTION_GROUP_EDIT),
    ActionCode("option_unchoose", "Bỏ chốt phương án", ACTION_GROUP_EDIT),
)

#  =====================================================================
#  2. NHÓM BỘ MÁY DUYỆT — mỗi việc HAI dạng chữ
#
#  Dạng QUÁ KHỨ (`approved`) là trạng thái phiếu, dạng NGUYÊN THỂ (`approve`) là
#  tên hành động trong bảng quyền (`core/permissions.ACTIONS`). Controller viết
#  sau quen tay ghi dấu vết bằng dạng nguyên thể. Nhận CẢ HAI thay vì đi sửa lời
#  gọi: dữ liệu đã ghi bằng dạng nguyên thể vẫn nằm trong bảng, sửa mã nguồn
#  không làm nó đọc được. Hai dạng của cùng một việc phải MANG CÙNG MỘT NHÃN —
#  có bài kiểm canh, kẻo cùng một hành động đọc ra hai kiểu trên một dòng thời
#  gian.
#  =====================================================================
_APPROVAL = (
    ActionCode("submit", "Gửi duyệt", ACTION_GROUP_APPROVE),
    ActionCode("submitted", "Gửi duyệt", ACTION_GROUP_APPROVE),
    ActionCode("approve", "Duyệt", ACTION_GROUP_APPROVE),
    ActionCode("approved", "Duyệt", ACTION_GROUP_APPROVE),
    ActionCode("reject", "Từ chối", ACTION_GROUP_APPROVE),
    ActionCode("rejected", "Từ chối", ACTION_GROUP_APPROVE),
    ActionCode("return", "Trả về", ACTION_GROUP_APPROVE),
    ActionCode("returned", "Trả về", ACTION_GROUP_APPROVE),
    ActionCode("withdraw", "Rút phiếu", ACTION_GROUP_APPROVE),
    ActionCode("withdrawn", "Rút phiếu", ACTION_GROUP_APPROVE),
    ActionCode("cancel", "Hủy", ACTION_GROUP_APPROVE),
    ActionCode("cancelled", "Hủy", ACTION_GROUP_APPROVE),
    ActionCode("line_approve", "Duyệt dòng", ACTION_GROUP_APPROVE),
    #  Duyệt dấu — cổng 2 (Văn thư): đóng dấu / trả / từ chối. Vai trò "(Văn thư)"
    #  gắn SAU TÊN người ở `audit/controller._CLERK_ROLE_ACTIONS`, không nhét vào nhãn.
    ActionCode("seal_completed", "Hoàn thành (đóng dấu)", ACTION_GROUP_APPROVE),
    ActionCode("seal_return_clerk", "Cập nhật", ACTION_GROUP_APPROVE),
    ActionCode("seal_reject_clerk", "Từ chối", ACTION_GROUP_APPROVE),
    #  `unapprove_po` đưa đơn ĐÃ DUYỆT về Nháp để sửa (CR-108) rồi ghi dấu vết
    #  bằng chính trạng thái mới. Nhãn nói rõ "hủy duyệt" chứ không nói "nháp":
    #  người đọc nhật ký cần biết đơn vừa TỤT khỏi trạng thái đã duyệt.
    ActionCode("draft", "Hủy duyệt, đưa về Nháp", ACTION_GROUP_APPROVE),
)

#  =====================================================================
#  3. XÓA
#  =====================================================================
_DELETE = (
    ActionCode("delete", "Xóa", ACTION_GROUP_DELETE),
)

#  =====================================================================
#  4. PHIÊN ĐĂNG NHẬP
#  =====================================================================
_AUTH = (
    ActionCode("login", "Đăng nhập", ACTION_GROUP_AUTH),
    ActionCode("login_failed", "Đăng nhập thất bại", ACTION_GROUP_AUTH),
    ActionCode("logout", "Đăng xuất", ACTION_GROUP_AUTH),
    #  bao-CR-313 / BM-003 — gia hạn phiên bằng refresh token nay có dấu vết.
    #  QĐ-A ban đầu định BỎ dòng `refresh` thành công cho đỡ ồn; đảo lại ngày
    #  10/09/2026 vì đó chính là dòng chứng minh một token bị đánh cắp vẫn đang
    #  sống. Xem §4.2 của `nhat-ky-va-phien-dang-nhap.md`.
    ActionCode("refresh", "Gia hạn phiên", ACTION_GROUP_AUTH),
    ActionCode("refresh_failed", "Gia hạn phiên thất bại", ACTION_GROUP_AUTH),
    #  ⚠️ CHƯA chỗ nào ghi mã này — nó là chỗ đặt sẵn cho P3 (phiên phía máy
    #  chủ, BM-002), lúc `tab_login_session` biết được IP của lần cấp token đầu
    #  để so. Giữ trong bảng chứ không xóa: P3 thêm lời gọi là chạy ngay.
    ActionCode("refresh_ip_changed", "Gia hạn phiên từ IP khác", ACTION_GROUP_AUTH),
)

#  =====================================================================
#  5. XUẤT DỮ LIỆU
#  =====================================================================
_EXPORT = (
    ActionCode("export", "Xuất dữ liệu", ACTION_GROUP_EXPORT),
    ActionCode("print", "In", ACTION_GROUP_EXPORT),
)

#  =====================================================================
#  6. ĐỌC — bao-CR-346 / BM-009
#
#  ⚠️ `download_file` xếp nhóm XEM chứ không xếp nhóm XUẤT DỮ LIỆU, dù tải tệp
#  về đúng là mang dữ liệu ra khỏi hệ. Lý do là câu hỏi mà nhóm này phải trả
#  lời: *"ai đã đọc bản hợp đồng này"*. Tách xem/tải sang hai nhóm thì lọc nhóm
#  XEM ra thiếu đúng nửa số người, mà nửa bị thiếu lại là nửa đáng ngại hơn.
#  Phân biệt xem/tải vẫn còn nguyên — nó nằm ở chính mã hành động.
#  =====================================================================
_VIEW = (
    ActionCode("view_file", "Xem tệp", ACTION_GROUP_VIEW),
    ActionCode("download_file", "Tải tệp về", ACTION_GROUP_VIEW),
    #  Không phải người làm: `file_access_log` ghi mã này với `user_id = 0` để
    #  đánh dấu "đã gửi cảnh báo rồi", dùng luôn nhật ký làm chỗ nhớ thay vì đẻ
    #  bảng mới. `entity_id` của dòng này là id NGƯỜI bị cảnh báo, không phải id
    #  văn bản — đọc nhầm thì tra ra một văn bản không liên quan.
    ActionCode("file_alert", "Cảnh báo mở tệp dồn dập", ACTION_GROUP_VIEW),
)

#  =====================================================================
#  7. PHÂN QUYỀN — bao-CR-346 / BM-010
#
#  Trước 10/09/2026 cả `role/` lẫn `user/` không gọi `record(...)` lấy một lần,
#  nên câu hỏi *"ai cấp cho tài khoản này quyền duyệt đơn hàng, lúc nào"* không
#  tra được bằng dữ liệu, và bộ lọc "Phân quyền" của màn nhật ký luôn rỗng —
#  trông y như "chưa ai đổi quyền bao giờ".
#  =====================================================================
_PERMISSION = (
    ActionCode("set_permissions", "Sửa ma trận phân quyền", ACTION_GROUP_PERMISSION),
    ActionCode("assign_roles", "Gán vai trò", ACTION_GROUP_PERMISSION),
    ActionCode("set_scope", "Đặt phạm vi dữ liệu", ACTION_GROUP_PERMISSION),
    ActionCode("reset_password", "Đặt lại mật khẩu", ACTION_GROUP_PERMISSION),
    ActionCode("activate", "Mở khóa tài khoản", ACTION_GROUP_PERMISSION),
    ActionCode("deactivate", "Khóa tài khoản", ACTION_GROUP_PERMISSION),
)

#  =====================================================================
#  8. HỌ MÃ SINH THEO TIỀN TỐ
#
#  `assistant/tools/__init__.py` ghi `f"tool:{name}"` cho mỗi lượt trợ lý AI gọi
#  công cụ — 34 công cụ hôm nay, và danh sách đó còn dài ra. Khai đủ 34 dòng ở
#  trên thì mỗi lần thêm công cụ lại phải nhớ thêm một dòng nhật ký, đúng cái
#  cơ chế mà tệp này sinh ra để bỏ. Nên khai thành HỌ.
#
#  Nhóm XEM vì mọi công cụ của trợ lý đều là công cụ ĐỌC — nếu có ngày một công
#  cụ GHI ra đời thì nó phải mang mã riêng, không núp dưới họ này.
#  =====================================================================
ACTION_FAMILIES: tuple[ActionFamily, ...] = (
    ActionFamily("tool:", "Trợ lý AI gọi công cụ", ACTION_GROUP_VIEW),
)


def _build(*groups: tuple[ActionCode, ...]) -> dict[str, ActionCode]:
    """Gộp các nhóm thành một bảng tra, chặn hai lỗi khai ngay lúc import."""
    table: dict[str, ActionCode] = {}
    for group in groups:
        for code in group:
            if not (code.label or "").strip():
                #  Nhãn rỗng còn tệ hơn mã trần: dòng dấu vết mất luôn phần
                #  "làm gì", người đọc không có gì để suy ra.
                raise ValueError(f"mã hành động «{code.value}» thiếu nhãn tiếng Việt")
            if code.group not in ACTION_GROUP_LABELS:
                raise ValueError(f"mã hành động «{code.value}» khai nhóm lạ: {code.group}")
            if code.value in table:
                raise ValueError(f"mã hành động «{code.value}» khai hai lần")
            table[code.value] = code
    return table


ACTION_CATALOG: dict[str, ActionCode] = _build(
    _EDIT, _STATUS_AS_ACTION, _OPTION, _APPROVAL, _DELETE,
    _AUTH, _EXPORT, _VIEW, _PERMISSION,
)

#  Bảng nhãn phẳng — thay cho `ACTION_LABEL` cũ của `modules/audit/controller.py`.
ACTION_LABELS: dict[str, str] = {v: c.label for v, c in ACTION_CATALOG.items()}

#  Mã nào đã kêu rồi thì thôi, kẻo một vòng lặp ghi 500 dòng nhật ký sinh 500
#  dòng cảnh báo giống hệt nhau và chôn mất những cảnh báo khác.
_warned: set[str] = set()


def _warn_once(action: str) -> None:
    if action in _warned:
        return
    _warned.add(action)
    LOGGER.warning(
        "Mã hành động chưa khai trong ACTION_CATALOG: %r. Dòng nhật ký vẫn được "
        "ghi nhưng người đọc thấy mã Anh trần và nó rơi vào nhóm «Không rõ». "
        "Khai thêm một dòng ở app/core/action_catalog.py.", action)


def is_known_action(action: str) -> bool:
    """Mã có nằm trong tập đóng không (tính cả họ mã theo tiền tố)."""
    if action in ACTION_CATALOG:
        return True
    return any(action.startswith(f.prefix) and len(action) > len(f.prefix)
               for f in ACTION_FAMILIES)


def label_of_action(action: str) -> str:
    """Nhãn tiếng Việt của một mã. Mã lạ trả về CHÍNH NÓ.

    Trả lại mã trần chứ không trả chuỗi rỗng hay "Không rõ": dòng nhật ký xấu
    vẫn hơn dòng nhật ký mất nội dung, và mã trần là manh mối để đi tìm lời gọi
    đã sinh ra nó.
    """
    action = action or ""
    code = ACTION_CATALOG.get(action)
    if code is not None:
        return code.label
    for family in ACTION_FAMILIES:
        if action.startswith(family.prefix) and len(action) > len(family.prefix):
            return f"{family.label_prefix} «{action[len(family.prefix):]}»"
    if action:
        _warn_once(action)
    return action


def group_of_action(action: str) -> int:
    """Nhóm của một mã hành động; `0` (*Không rõ*) nếu chưa khai."""
    action = action or ""
    code = ACTION_CATALOG.get(action)
    if code is not None:
        return code.group
    for family in ACTION_FAMILIES:
        if action.startswith(family.prefix) and len(action) > len(family.prefix):
            return family.group
    if action:
        _warn_once(action)
    return ACTION_GROUP_UNKNOWN


def action_options() -> list[dict[str, object]]:
    """Danh sách cho ô chọn của màn Nhật ký hệ thống, xếp theo nhóm rồi theo nhãn."""
    return [{"value": c.value, "label": c.label, "group": c.group}
            for c in sorted(ACTION_CATALOG.values(), key=lambda c: (c.group, c.label, c.value))]
