"""Cụm 08 — ĐƯỜNG VÒNG: gõ id vào URL · lệch action · cache quyền 60 giây.

Bảy cụm trước đi theo MODULE. Cụm này đi theo KIỂU LỖI, quét ngang cả 68
controller. Ba kiểu dưới đây có chung một đặc điểm khó chịu: **danh sách lọc
đúng, màn hình trông đúng, và vẫn lấy được dữ liệu.**

    A. `db.get(Model, id)` thay cho `get_scoped(...)`  → gõ id vào URL là ra
    B. nạp bản ghi bằng phạm vi `read` rồi GHI/DUYỆT/XUẤT → cổng phạm vi biến mất
    C. hồ sơ quyền cache 60 giây → thu hồi quyền có độ trễ
    D. bộ lọc người dùng tự truyền chạy TRƯỚC `apply_scope`

────────────────────────────────────────────────────────────────────────────────
A. BẢNG PHÂN LOẠI 64 LẦN GỌI `db.get(` TRONG TỆP CONTROLLER
────────────────────────────────────────────────────────────────────────────────
`DB_GET_TRONG_CONTROLLER` dưới đây phân loại **đủ 64 lần**, không dòng nào còn
nhãn "chưa rà". Bài kiểm A1 đối chiếu bảng này với mã nguồn THẬT, nên thêm một
lần `db.get` vào bất kỳ controller nào cũng làm đỏ và buộc người thêm phải phân
loại nó.

Ba nhãn (đúng đặc tả phase-08):
  `OK-đã kiểm`   — có `get_scoped`/`apply_scope`/`ensure_can`/`resolve_doc`/
                   `_check` cùng route (số dòng ghi trong cột lý do)
  `OK-không cần` — model không phải chứng từ có phạm vi (danh mục PUBLIC, cấu
                   hình, bản ghi của CHÍNH MÌNH, tra tên để hiển thị)
  `LỖ`           — chứng từ CÓ phạm vi mà không kiểm

**Kết quả: 64/64 an toàn — KHÔNG còn dòng 🔴 nào.** Đó là con số sau khi ĐỌC MÃ
từng chỗ, không phải đếm grep: bốn module gác bằng hàm tự viết trong thân hàm
(`attachment._check` → `core/attachment_scope.ensure_in_scope`,
`comment.resolve_doc`, `document.ensure_can`, `export_log._guard_view`) nên grep
không thấy chốt.

⚠️ Dòng 🔴 DUY NHẤT của mục A — `employee/controller.py` `set-password` — vừa
được vá ngày 05/09/2026 (commit `4c1ecaa`, cụm 06) bằng
`_block_set_password_out_of_scope` → `get_scoped(..., "write")`. Ca A2/A3 dưới
đây giữ lại nguyên vẹn thành **ca canh không tái phát**: đó là cửa duy nhất
trong 68 controller cho phép *chiếm tài khoản* chứ không chỉ đọc/sửa dữ liệu.

⚠️ Lỗ lớn của mục A **không nằm ở tệp controller** mà ở tầng service: mọi nhánh
GHI của Thu mua nạp bản ghi bằng `service.get_*` = `db.get` trần
(`purchase_order/service.py:68`, `survey_request/service.py:34`,
`survey/service.py:20`, `purchase_request/service.py:737`,
`payment_request/service.py:58`). Cụm 03 và 04 đã ghim đủ; cụm này KHÔNG làm lại.

────────────────────────────────────────────────────────────────────────────────
B. LỆCH ACTION
────────────────────────────────────────────────────────────────────────────────
Quét toàn hệ: **274 route có `require(entity, action)` với action ≠ read**, trong
đó **66 route có gọi một chốt phạm vi**. Đọc từng chốt:

  ✔ truyền ĐÚNG action — contract · company · department · vehicle_booking ·
    leave · meeting_room · approval_flow · document (phần `write`/`delete`)
  ✘ mượn phạm vi `read`:
      employee/controller.py:364      `GET /employees/export/xlsx`  (gate export)
      payable/controller.py:139       `POST /payables/{pid}/offset-prepay` (gate write)
      document/controller.py:438,527  duyệt / từ chối văn bản        (gate approve)
      document/signature_controller.py:61  ký văn bản                (gate approve)
      purchase_request/controller.py:52    `_in_approve_scope`       (gate approve) — cụm 03
  ✘ mượn phạm vi `write` cho action `cancel`:
      document/controller.py:572      `POST /documents/{id}/revoke`

Hai kết luận rộng hơn từng dòng ở trên:

1. **6/6 route `/export/xlsx` của cả hệ** lọc bằng phạm vi `read` vì dùng chung
   `_list_query`/`_filtered` với màn danh sách. Ô «Xuất» trong hộp thoại phạm vi
   **chưa bao giờ cắt được một dòng nào** — nó chỉ bật/tắt cái nút.
2. **Văn thư không có phạm vi cho `approve`/`cancel` ở mức mô hình.**
   `access_service.ACTION_COLUMN` (`:47-51`) chỉ khai `read · write · delete`,
   nên `ensure_can(..., "approve")` là `KeyError` → 500 chứ không phải "chặn".
   Bốn route duyệt/từ chối/ký/bãi bỏ đành soi `read`/`write`. Đây KHÔNG vá được
   bằng cách truyền thêm tham số (ca B4).

⚠️ KHÔNG đổi mặc định `action="read"` ở tầng helper trong cụm này: đổi mặc định
là đổi hành vi toàn hệ, và nó sẽ LÀM HẸP tầm nhìn của người đang dùng thật.
Ghim hiện trạng + `# QUYẾT ĐỊNH CHỜ`, để người dùng chốt.

────────────────────────────────────────────────────────────────────────────────
C. CACHE QUYỀN 60 GIÂY (`core/auth.py:69-78`)
────────────────────────────────────────────────────────────────────────────────
Bảy chỗ trong mã có gọi `perm_cache_clear`. Chỗ THIẾU:
`employee/service.update_employee` — đổi **pháp nhân** của một nhân sự KHÔNG xóa
cache, mà `company_id` nằm trong hồ sơ đã cache (`auth.py:186`). Đổi **phòng ban**
thì có (đi qua `_sync_primary_department` → `department_service.set_departments`
→ `perm_cache_clear`). Hai cửa cạnh nhau trên cùng một màn, một cửa xóa một cửa
không.
"""
import json

import pytest
from fastapi import HTTPException

from scope_factory import model_of


def _body(resp) -> dict:
    """`core.response.success` trả `JSONResponse`, không trả dict — bóc lấy `data`."""
    return json.loads(resp.body)["data"]


def _query(params: dict):
    """Giả `Request` cho `apply_filters`.

    ⚠️ Phải là `QueryParams` thật chứ không phải `dict`: nhánh bộ-lọc-điều-kiện
    (`core/filter_operators.py:132`) gọi `query_params.multi_items()`, `dict`
    không có phương thức đó và ca kiểm nổ `AttributeError` trước khi tới phần
    phạm vi — tức là mất luôn thứ nó định canh.
    """
    from types import SimpleNamespace

    from starlette.datastructures import QueryParams

    return SimpleNamespace(query_params=QueryParams(params))


def _van_ban(world, co_key: str, ma: str):
    """Một văn bản nội bộ tối thiểu nhưng HỢP LỆ.

    `ck_document_internal_required` bắt văn bản nội bộ (`origin = 1`) phải có đủ
    loại + pháp nhân + người chịu trách nhiệm; SQLite cũng ép CHECK nên thiếu là
    ca kiểm nổ ở tầng CSDL chứ không ở tầng phạm vi. `doc_type_id` trỏ vào một
    loại KHÔNG tồn tại là cố ý: `_is_personal_document` sẽ trả `False`, tức đi
    đúng nhánh văn bản thường chứ không rẽ sang luật riêng của đơn nghỉ phép.
    """
    from app.modules.document.model import Document

    return Document(doc_code=ma, title=f"Văn bản {co_key}", origin=1, doc_type_id=1,
                    company_id=world.co[co_key], owner_employee_id=world.emp["a1"])


def world_thay(db, model, entity: str, actor, action: str) -> set[str]:
    """Tập `doc_code`/`code` nhìn thấy được ở một action — đọc dễ hơn tập id."""
    from app.core.scoping import apply_scope

    rows = apply_scope(db.query(model), model, entity, actor.user,
                       actor.profile(), action).all()
    return {getattr(r, "doc_code", None) or getattr(r, "code", "") for r in rows}

# ──────────────────────────────────────────────────────────────────────────────
#  A — bảng phân loại 63 lần `db.get(` trong tệp controller
#
#  Khóa = đường dẫn tương đối trong `app/modules`. Giá trị = danh sách nhãn, MỘT
#  phần tử cho MỘT lần gọi, theo đúng thứ tự dòng trong tệp. Số dòng để ở cột lý
#  do chứ không làm khóa: số dòng trôi theo mỗi lần sửa, còn số LẦN GỌI thì không.
# ──────────────────────────────────────────────────────────────────────────────
OK_DA_KIEM = "OK-đã kiểm"
OK_KHONG_CAN = "OK-không cần"
LO = "LỖ"

DB_GET_TRONG_CONTROLLER: dict[str, list[tuple[str, str]]] = {
    # ── Bộ máy duyệt ─────────────────────────────────────────────────────────
    "approval/delegation_controller.py": [
        (OK_DA_KIEM, "L111 `_load(Delegation)` — chốt thật ở `delegation_service."
                     "validate_before_save(actor_employee_id=_acting_employee_id(...))` "
                     "(L56: phạm vi *tất cả* mới được lập hộ). Cụm 07 A9."),
    ],
    "approval/flow_controller.py": [
        (OK_DA_KIEM, "L250 `ApprovalNode` — L249 `_load(db, flow_id, user, \"write\")` "
                     "(get_scoped có action) + `node.flow_id != flow.id`"),
        (OK_DA_KIEM, "L321 `ApprovalNode` (xóa) — cùng khuôn L320 `_load(..., \"write\")`"),
    ],
    "approval/instance_controller.py": [
        (OK_DA_KIEM, "L312 `ApprovalTask` (reassign) — chốt ở `action_service.reassign:"
                     "310-315` «không tự bốc việc của người khác». ⚠️ phạm vi CHỨNG TỪ "
                     "nền thì không hỏi — chuyển cụm 07 xem xét"),
        (OK_DA_KIEM, "L333 `_load(ApprovalInstance)` — L336 `entity_hooks.can_read`"),
    ],
    # ── Trợ lý AI ────────────────────────────────────────────────────────────
    "assistant/controller.py": [
        (OK_DA_KIEM, "L198 `StoredFile` — L199 `f.created_by != user.id` + khóa thư mục "
                     "`/assistant-report/`; quyền SỞ HỮU, không phải phạm vi"),
    ],
    # ── Đính kèm ─────────────────────────────────────────────────────────────
    "attachment/controller.py": [
        (OK_KHONG_CAN, "L107 `DocumentVersion` — chỉ đọc TRẠNG THÁI để chặn sửa hồ sơ "
                       "đang trình duyệt; quyền đã hỏi ở `_check` (L234/L293)"),
        (OK_DA_KIEM, "L123 `Comment` — L126 `resolve_doc` (quyền + phạm vi, 2 tầng)"),
        (OK_DA_KIEM, "L143 `ForumPost` — L146 `forum.service.can_view` (luật audience)"),
        (OK_DA_KIEM, "L237 `FileLink` — L234 `_check(..., \"manage\", entity_id)` + so "
                     "`lk.entity/entity_id` với thân yêu cầu"),
        (OK_DA_KIEM, "L297 `StoredFile` — L293 `_check(..., \"manage\", entity_id)`"),
        (OK_DA_KIEM, "L546 `FileLink` — chính hàm `_get_file_with_permission` kiểm ngay "
                     "sau đó (L549-561) qua `_check`/`_check_comment`/`_check_forum`"),
        (OK_KHONG_CAN, "L571 `StoredFile` — lấy theo `lk.file_id` đã kiểm ở trên"),
        (OK_DA_KIEM, "L605 `FileLink` (DELETE) — L607-613 `_check(..., \"manage\")`"),
    ],
    # ── Đăng nhập ────────────────────────────────────────────────────────────
    "auth/controller.py": [
        (OK_KHONG_CAN, "L32 `Employee` của CHÍNH MÌNH (`/me`)"),
        (OK_KHONG_CAN, "L134 `User` từ refresh token — chính chủ"),
        (OK_KHONG_CAN, "L211 `Employee` trong quên-mật-khẩu, tra theo email đã nhập"),
        (OK_KHONG_CAN, "L235 `User` từ reset token — chính chủ"),
    ],
    "backup/controller.py": [
        (OK_KHONG_CAN, "L47 `DbBackup` — `backup` khai PUBLIC, quyền HÀNH ĐỘNG toàn hệ"),
    ],
    "category_assignee/controller.py": [
        (OK_KHONG_CAN, "L21 `ItemGroup` — PUBLIC, tra tên hiển thị"),
        (OK_KHONG_CAN, "L22 `Employee` — tra tên NSTM chính"),
        (OK_KHONG_CAN, "L23 `Employee` — tra tên NSTM dự phòng"),
    ],
    # ── Bình luận ────────────────────────────────────────────────────────────
    "comment/controller.py": [
        (OK_DA_KIEM, "L173 — L177 `resolve_doc` (quyền + `apply_scope` chứng từ cha)"),
        (OK_DA_KIEM, "L194 — L198 `resolve_doc`"),
        (OK_DA_KIEM, "L204 — L208 `resolve_doc`"),
        (OK_DA_KIEM, "L215 — L219 `resolve_doc` + L221 chỉ người viết"),
    ],
    "contract/controller.py": [
        (OK_DA_KIEM, "L74 — nằm TRONG `_in_scope`, chỉ để tách 404 (không có) khỏi 403 "
                     "(ngoài phạm vi). Mẫu đúng của cả hệ"),
    ],
    # ── Văn thư ──────────────────────────────────────────────────────────────
    "document/controller.py": [
        (OK_DA_KIEM, "L599 `DocumentVersion` — L597 `_load(db, document_id, user, \"read\")` "
                     "→ `access_service.ensure_can`"),
    ],
    "document/link_controller.py": [
        (OK_KHONG_CAN, "L31 `DocType` — PUBLIC, tra tên loại"),
    ],
    "document/scope_controller.py": [
        (OK_KHONG_CAN, "L68 `Employee` của CHÍNH MÌNH (`/applies-to-me`)"),
        (OK_KHONG_CAN, "L107 `Company` — tra tên pháp nhân ban hành; văn bản đã qua "
                       "`_load` ở L105"),
        (OK_DA_KIEM, "L149 `DocumentScope` — L148 `_load(..., \"write\")` + "
                     "`row.document_id != doc.id`"),
    ],
    "document/template_controller.py": [
        (OK_KHONG_CAN, "L30 `DocType` — PUBLIC, tra tên"),
    ],
    # ── Nhân sự ──────────────────────────────────────────────────────────────
    "employee/controller.py": [
        (OK_DA_KIEM, "L192 `POST /employees/{eid}/set-password` — L184 "
                     "`_block_set_password_out_of_scope` → `get_scoped(..., \"write\")` "
                     "(L171-173). ĐÃ VÁ 05/09/2026 (commit 4c1ecaa); trước đó cửa này "
                     "chỉ có `require(\"employee\", \"write\")` nên `employee.write` "
                     "phạm vi *own* đặt được mật khẩu tài khoản quản trị. Ca A2/A3 canh "
                     "không tái phát."),
    ],
    "export_log/controller.py": [
        (OK_DA_KIEM, "L90 `StoredFile` — L87 `_guard_view` (can_view_any hoặc "
                     "`setting.read`). ⚠️ đó là cổng QUYỀN toàn hệ, tệp đã xuất có thể "
                     "chứa dữ liệu pháp nhân khác — chuyển cụm 07"),
    ],
    # ── Diễn đàn ─────────────────────────────────────────────────────────────
    "forum/controller.py": [
        (OK_DA_KIEM, "L211 `ForumPost` — L215 `post.created_by != user.id`"),
        (OK_KHONG_CAN, "L279 `_get_post_or_404` — `forum_post` PUBLIC (luật audience "
                       "riêng); ba nơi gọi đều gác `require(forum_post, write|delete)`"),
        (OK_DA_KIEM, "L442 `_get_visible_box` — tự kiểm box ẩn ngay sau (L443-447)"),
        (OK_KHONG_CAN, "L490 `ForumBoard` — `forum_board` PUBLIC, cổng là quyền quản trị"),
        (OK_KHONG_CAN, "L501 `ForumBoard` (xóa) — cùng lý do L490, PUBLIC"),
    ],
    "import_tool/controller.py": [
        (OK_KHONG_CAN, "L150 `Survey` — route `/dev/surveys`, chặn cứng bằng "
                       "`settings.DEV_MODE`"),
        (OK_DA_KIEM, "L190 `StoredFile` — L186 `_guard_view`. ⚠️ cùng ghi chú export_log"),
    ],
    # ── Nghỉ phép ────────────────────────────────────────────────────────────
    "leave/catalog_controller.py": [
        (OK_KHONG_CAN, "L110 `LeaveType` — PUBLIC, chỉ kiểm tồn tại"),
        (OK_KHONG_CAN, "L144 `LeaveTypeSeniority` — bậc thâm niên của `leave_type` PUBLIC"),
        (OK_KHONG_CAN, "L162 `LeaveTypeSeniority` (xóa) — cùng lý do L144, PUBLIC"),
    ],
    "leave/request_controller.py": [
        (OK_KHONG_CAN, "L5 — dòng DOCSTRING nhắc tên `db.get()`, không phải một lời gọi"),
        (OK_DA_KIEM, "L103 `_readable_by_approver` — L101 `approval_bridge."
                     "can_read_request` (nới đúng lúc có việc TASK_PENDING)"),
        (OK_KHONG_CAN, "L262 `LeaveType` — PUBLIC, dùng để ước tính số ngày"),
        (OK_KHONG_CAN, "L274 — dòng DOCSTRING của `_ensure_balance_in_scope` kể lại "
                       "rằng `resolve_leave_taker` là `db.get(Employee, ...)` trần; "
                       "chốt thật là `get_scoped(..., \"leave_balance\")` ở L292 "
                       "(vá 05/09/2026, ca A6d cụm 06)"),
    ],
    # ── Phòng họp ────────────────────────────────────────────────────────────
    "meeting_room/controller.py": [
        (OK_KHONG_CAN, "L5 — dòng DOCSTRING nhắc tên `db.get()`, không phải lời gọi"),
        (OK_DA_KIEM, "L131 — nằm SAU `get_scoped(..., action)` ở L124; chỉ nới cho "
                     "`action == \"read\"` khi `can_read_booking` đúng"),
    ],
    # ── Tài chính ────────────────────────────────────────────────────────────
    "payment_request/controller.py": [
        (OK_KHONG_CAN, "L30 `PaymentRequest` trong `_line` — serializer, phiếu cha do "
                       "route gọi nó chịu trách nhiệm"),
        (OK_KHONG_CAN, "L34 `Payable` — serializer, đọc số nợ của đúng dòng"),
        (OK_DA_KIEM, "L126 `Company` — tra tên, nằm SAU `_scoped(..., \"print\")` ở "
                     "L124 (vá P0 #4, 05/09/2026 — trước đó là `service.get_request` trần)"),
    ],
    "purchase_order/controller.py": [
        (OK_KHONG_CAN, "L351 `Company` — tra tên; lỗ của `GET /{pid}/print` nằm ở L349 "
                       "`service.get_po` (= D3 cụm 03)"),
    ],
    # ── Thu mua ──────────────────────────────────────────────────────────────
    "survey_request/controller.py": [
        (OK_KHONG_CAN, "L109 `Employee` — của CHÍNH người đang gọi, để so phòng ban"),
        (OK_KHONG_CAN, "L114 `Employee` — người yêu cầu của phiếu, để so phòng ban"),
        (OK_KHONG_CAN, "L539 `Survey` — tra mã/phân loại phiếu khảo sát cho ô chọn NCC "
                       "thủ công (tìm MỞ theo thiết kế). ⚠️ lỗ của route này là "
                       "`service.get_sr` ở L529 (= S6 cụm 03)"),
        (OK_KHONG_CAN, "L674 `SurveyProductLine` — dòng nguồn của chính option đang "
                       "serialize, chỉ lấy ngày khảo sát"),
    ],
    "ticket/controller.py": [
        (OK_KHONG_CAN, "L44 `User` — tra tên hiển thị người tạo/xử lý"),
    ],
    # ── Tài khoản ────────────────────────────────────────────────────────────
    "user/controller.py": [
        (OK_DA_KIEM, "L48 `Employee` — danh sách đã lọc bằng `scope_condition` ở L43"),
        (OK_DA_KIEM, "L129 `Employee` — tài khoản đã lấy bằng `get_scoped` ở L123"),
    ],
    "vehicle_booking/controller.py": [
        (OK_KHONG_CAN, "L120 `Vehicle` — PUBLIC; phiếu đã qua `get_scoped(..., \"write\")` "
                       "ở L115"),
        (OK_KHONG_CAN, "L121 `Driver` — cùng lý do L120, danh mục tài xế PUBLIC"),
    ],
}


def _dem_db_get_that() -> dict[str, int]:
    """Đếm `db.get(` trong MỌI tệp `*controller*.py` dưới `app/modules`.

    Hỏi chính gói đã nạp thay vì suy từ `__file__` của tệp test: trong container
    mã nguồn ở `/app` còn test ở `/app/test/backend` (xem `test_pham_vi_luat_bat_bien`).
    """
    from pathlib import Path

    import app.modules

    root = Path(app.modules.__file__).parent
    out: dict[str, int] = {}
    for path in sorted(root.rglob("*controller*.py")):
        n = path.read_text(encoding="utf-8").count("db.get(")
        if n:
            out[str(path.relative_to(root))] = n
    return out


def test_a1_bang_64_lan_db_get_trong_controller_da_phan_loai_du():
    """Bảng trên phải khớp mã nguồn — cả tên tệp lẫn SỐ LẦN gọi trong mỗi tệp.

    Đây là bài kiểm DANH SÁCH TRẮNG, cùng loại BB-4: nó không biết chỗ nào thật
    sự cần lọc. Việc nó làm được là **không cho ai lặng lẽ thêm một `db.get` vào
    controller** — thêm là đỏ, và người thêm phải viết ra một trong ba nhãn kèm
    lý do đọc được.

    Số hôm nay: **64** lần trên 27 tệp / 26 module (ba trong số đó là dòng
    docstring, đã ghi rõ trong bảng). Đợt vá phạm vi 05/09/2026 làm con số nhích
    từ 63 lên 64: `leave/request_controller.py` mọc thêm một dòng docstring kể
    lại lỗ cũ của `resolve_leave_taker` — bản thân đường đó nay đi qua
    `get_scoped(..., "leave_balance")`, tức bảng dày thêm mà mã thì chặt lại.

    Hai vế của bài kiểm nằm ở chính ba khẳng định dưới: `thieu` bắt lần gọi mới
    KHÔNG được lọt vào mà không phân loại, `thua` bắt tên tệp đã hết `db.get`
    KHÔNG được nằm lại trong bảng (bảng phồng lên là bảng hết ai đọc).
    """
    that = _dem_db_get_that()
    khai = {tep: len(nhan) for tep, nhan in DB_GET_TRONG_CONTROLLER.items()}

    thieu = sorted(set(that) - set(khai))
    assert thieu == [], (
        f"{len(thieu)} tệp controller có `db.get(` mà chưa phân loại: {thieu}. "
        "Thêm vào DB_GET_TRONG_CONTROLLER, mỗi lần gọi một dòng nhãn kèm lý do."
    )
    thua = sorted(set(khai) - set(that))
    assert thua == [], f"đã hết `db.get(` nhưng còn tên trong bảng: {thua}"

    lech = {tep: (that[tep], khai[tep]) for tep in that if that[tep] != khai[tep]}
    assert lech == {}, (
        f"số lần gọi `db.get(` đã đổi ở {list(lech)} (thật, đã khai) = "
        f"{lech}. Phân loại lần gọi mới rồi cập nhật bảng."
    )
    assert sum(that.values()) == 64, f"tổng phải là 64, đang là {sum(that.values())}"


def test_a1b_moi_dong_deu_co_nhan_hop_le_va_ly_do_that():
    """Không dòng nào được để nhãn rỗng hay lý do lấy lệ.

    Đặc tả cụm 08 nói thẳng: *"không dòng nào được còn nhãn chưa rà"*. Bài kiểm
    này là chỗ ép điều đó, vì A1 chỉ đếm số dòng chứ không đọc nội dung.
    """
    hop_le = {OK_DA_KIEM, OK_KHONG_CAN, LO}
    for tep, dong in DB_GET_TRONG_CONTROLLER.items():
        for nhan, ly_do in dong:
            assert nhan in hop_le, f"{tep}: nhãn lạ {nhan!r}"
            assert len(ly_do) >= 25, f"{tep}: lý do quá ngắn — {ly_do!r}"
            assert ly_do.startswith("L"), f"{tep}: lý do phải mở đầu bằng số dòng — {ly_do!r}"

    lo = sorted(tep for tep, dong in DB_GET_TRONG_CONTROLLER.items()
                for nhan, _ in dong if nhan == LO)
    assert lo == [], (
        "Sau khi `employee/controller.py` được vá (05/09/2026, commit 4c1ecaa), "
        "KHÔNG còn lần gọi `db.get` nào trong tệp controller là lỗ phạm vi. "
        f"Vừa xuất hiện lại: {lo} — mỗi dòng 🔴 phải kèm một ca kiểm chạy thật "
        "trong chính tệp này."
    )


# ──────────────────────────────────────────────────────────────────────────────
#  A — ca kiểm cho dòng 🔴 duy nhất, và đối chứng của nó
# ──────────────────────────────────────────────────────────────────────────────


def test_a2_dat_lai_mat_khau_nhan_su_ngoai_pham_vi_bi_chan(world):
    """CANH KHÔNG TÁI PHÁT — `POST /api/employees/{eid}/set-password`.

    Cửa này là chỗ nguy hiểm nhất trong 68 controller: các lỗ khác cho **đọc
    trộm** hoặc **sửa chứng từ**, còn cửa này cho **chiếm tài khoản** — đặt lại
    mật khẩu của người pháp nhân khác rồi đăng nhập bằng danh nghĩa họ, thừa
    hưởng TOÀN BỘ phạm vi của người ta. Không dòng phân quyền nào đổi, nên
    `core/privilege_escalation.py` cũng không có gì để chặn.

    Trước 05/09/2026 route chỉ có `require("employee", "write")` (QUYỀN, không
    phải PHẠM VI). Nay `_block_set_password_out_of_scope` (`controller.py:147-173`)
    gọi `get_scoped(..., "write")` và trả 404.

    ⚠️ Ca này ghim MẶT SAU của bản vá luôn: 404 chứ không 403 — nói "có nhân sự
    này nhưng anh không được đụng" cũng đã lộ thứ cần giấu.
    """
    from app.core.auth import verify_password
    from app.modules.employee import controller as emp_ctl
    from app.modules.employee.controller import SetPasswordIn
    from app.modules.user.model import User

    db = world.db
    a1 = world.grant("a1", "employee", scope="company", actions=("read", "write"))
    b1_emp = world.emp["b1"]
    assert b1_emp not in a1.sees(model_of("employee")), "b1 đứng NGOÀI phạm vi của a1"

    cu = db.query(User).filter(User.employee_id == b1_emp).first().password_hash
    with pytest.raises(HTTPException) as e:
        emp_ctl.set_password(b1_emp, SetPasswordIn(password="chiem-doat"), db, a1.user)
    assert e.value.status_code == 404

    moi = db.query(User).filter(User.employee_id == b1_emp).first().password_hash
    assert moi == cu, "mật khẩu không được đổi"

    #  Vế đối chứng: trong phạm vi thì cửa vẫn phải chạy, kẻo bản vá hóa ra là
    #  khóa luôn một việc có thật của hành chính.
    emp_ctl.set_password(world.emp["a2"], SetPasswordIn(password="dat-lai"), db, a1.user)
    a2_hash = db.query(User).filter(User.employee_id == world.emp["a2"]).first().password_hash
    assert verify_password("dat-lai", a2_hash) is True


def test_a3_tu_tao_tai_khoan_cho_nhan_su_ngoai_pham_vi_bi_chan(world):
    """Nhánh chứa đúng lần gọi `db.get` đang phân loại (`controller.py:192`).

    Nhân sự CHƯA có tài khoản thì route TỰ TẠO tài khoản rồi đặt luôn mật khẩu —
    tức đường vòng còn rộng hơn nhánh trên: không cần người đó có tài khoản sẵn.
    Chốt `_block_set_password_out_of_scope` đứng TRƯỚC cả hai nhánh (L184) nên
    bịt cả hai bằng một dòng; ca này chứng minh chỗ đặt đó đúng.
    """
    from app.modules.employee import controller as emp_ctl
    from app.modules.employee.controller import SetPasswordIn
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    db = world.db
    ngoai = Employee(code="B_CHUA_TK", full_name="Nhân sự B chưa có TK",
                     company_id=world.co["B"], department_id=world.dept["B.kt"],
                     email="b-chua-tk@dego.vn", is_active=True)
    db.add(ngoai)
    db.commit()

    a1 = world.grant("a1", "employee", scope="company", actions=("read", "write"))
    assert ngoai.id not in a1.sees(model_of("employee"))

    with pytest.raises(HTTPException) as e:
        emp_ctl.set_password(ngoai.id, SetPasswordIn(password="dung-ho"), db, a1.user)
    assert e.value.status_code == 404
    assert db.query(User).filter(User.employee_id == ngoai.id).first() is None, (
        "không được dựng tài khoản đăng nhập cho hồ sơ nhân sự ngoài phạm vi")


def test_a4_khuon_dung_nam_ngay_trong_cung_mot_tep(world):
    """Đối chứng: `PUT /employees/{eid}/departments` CÓ `_employee_in_scope(..., "write")`.

    Cùng tệp, cùng khóa `employee.write`, cùng kiểu "gõ id vào URL" — nhưng cửa
    này trả 404. Nghĩa là bản vá cho A2/A3 không phải phát minh gì mới, chỉ là
    gọi thêm một dòng đã có sẵn ở `controller.py:207`.
    """
    from app.modules.employee import controller as emp_ctl

    a1 = world.grant("a1", "employee", scope="company", actions=("read", "write"))
    with pytest.raises(HTTPException) as e:
        emp_ctl.set_employee_departments(
            world.emp["b1"], emp_ctl.ExtraDepartmentsIn(extra_department_ids=[]),
            world.db, a1.user)
    assert e.value.status_code == 404


def test_a5_doc_ho_so_nhan_su_theo_id_cung_khong_loc_pham_vi(world):
    """⚠️ Ghim — `GET /api/employees/{eid}` dùng `service.get_employee` = `db.get` trần.

    Docstring của `_employee_in_scope` (`controller.py:207-217`) đã tự nói ra
    điều này và giải thích vì sao mới chỉ vá hai cửa GHI. Ghim hiện trạng để bản
    vá A2 biết mình còn hàng xóm; KHÔNG sửa ở cụm này — siết đường ĐỌC hồ sơ
    nhân sự chạm tới rất nhiều màn (ô chọn người duyệt, người nhận bàn giao…).

    # QUYẾT ĐỊNH CHỜ: `GET /employees/{eid}` có nên đi qua `_employee_in_scope`
    # không? Nếu có thì mọi ô chọn nhân sự liên pháp nhân phải đổi nguồn dữ liệu.
    """
    from app.modules.employee import controller as emp_ctl

    a1 = world.grant("a1", "employee", scope="company", actions=("read",))
    assert world.emp["b1"] not in a1.sees(model_of("employee"))

    ra = _body(emp_ctl.get_employee(world.emp["b1"], world.db, a1.user))
    assert ra["code"] == "B1", "đọc được hồ sơ nhân sự ngoài phạm vi"


def test_a6_dinh_kem_di_qua_ensure_in_scope_va_truyen_dung_action(world):
    """Đối chứng dương của CẢ mục A lẫn mục B — `core/attachment_scope.ensure_in_scope`.

    Module Đính kèm không gọi `apply_scope` ở tầng controller (nên grep BB-4
    không thấy) nhưng nó làm **đủ hai lớp và đúng action**: `_check` hỏi quyền
    rồi `ensure_in_scope` hỏi phạm vi của ĐÚNG chứng từ cha, với `read` cho lượt
    xem và `write ∪ create` cho lượt gắn/gỡ (`attachment_scope.py:186-191`).

    Đây là khuôn nên chép cho các lỗ mục B, chứ không phải đổi mặc định ở helper.
    """
    from app.core.attachment_scope import ensure_in_scope
    from app.modules.contract.model import Contract

    db = world.db
    db.add_all([Contract(code="HD_A", company_id=world.co["A"], title="Của A"),
                Contract(code="HD_B", company_id=world.co["B"], title="Của B")])
    db.flush()
    ids = {c.code: c.id for c in db.query(Contract).all()}

    a1 = world.grant("a1", "contract", scope="company", actions=("read", "write"))

    ensure_in_scope(db, a1.user, "contract", ids["HD_A"], "read")       # không ném
    with pytest.raises(HTTPException) as e:
        ensure_in_scope(db, a1.user, "contract", ids["HD_B"], "read")
    assert e.value.status_code == 403

    #  Mặt "đúng action": chỉ có `read`, không có `write`/`create` → lượt GẮN bị
    #  chặn ngay trên hợp đồng mà mình ĐỌC ĐƯỢC.
    a2 = world.grant("a2", "contract", scope="company", actions=("read",))
    ensure_in_scope(db, a2.user, "contract", ids["HD_A"], "read")
    with pytest.raises(HTTPException):
        ensure_in_scope(db, a2.user, "contract", ids["HD_A"], "manage")


# ──────────────────────────────────────────────────────────────────────────────
#  B — lệch action
# ──────────────────────────────────────────────────────────────────────────────

#  Ảnh chụp các chốt phạm vi nằm trong route có `action != read`, sau khi đã đọc
#  từng chỗ. `True` = chốt truyền ĐÚNG action của route.
CHOT_TRONG_ROUTE_GHI = {
    "company/controller.py::update_company": True,
    "company/controller.py::update_company_logo": True,
    "company/controller.py::delete_company": True,
    "company/controller.py::bulk_delete_companies": True,
    "contract/controller.py::create_": True,
    "contract/controller.py::update_": True,
    "contract/controller.py::delete_": True,
    "contract/controller.py::bulk_delete_contracts": True,
    "department/controller.py::update_department": True,
    "department/controller.py::delete_department": True,
    "department/controller.py::replace_department_companies": True,
    "approval/flow_controller.py::update_flow": True,
    "approval/flow_controller.py::delete_flow": True,
    "approval/flow_controller.py::add_node": True,
    "approval/flow_controller.py::update_node": True,
    "approval/flow_controller.py::reorder_nodes": True,
    "approval/flow_controller.py::delete_node": True,
    "employee/controller.py::set_employee_departments": True,
    "leave/balance_controller.py::adjust_balance": True,
    "leave/request_controller.py::update_request": True,
    "leave/request_controller.py::delete_request": True,
    "leave/request_controller.py::submit_request": True,
    "leave/request_controller.py::approve_request": True,
    "leave/request_controller.py::reject_request": True,
    "leave/request_controller.py::cancel_request": True,
    "meeting_room/controller.py::update_booking": True,
    "meeting_room/controller.py::delete_booking": True,
    "meeting_room/controller.py::approve_booking": True,
    "meeting_room/controller.py::cancel_booking": True,
    "vehicle_booking/controller.py::update_booking": True,
    "vehicle_booking/controller.py::dispatch_booking": True,
    "vehicle_booking/controller.py::delete_booking": True,
    "document/controller.py::update_document": True,
    "document/controller.py::delete_document": True,
    "document/controller.py::submit_document": True,
    # ── vá 05/09/2026 (P0 #3 #4 #5): tám cửa GHI + bản in của YCTT nay nạp phiếu
    #    qua `get_scoped(..., action)`, và cấn trừ tiền treo truyền `action="write"`
    "payable/controller.py::offset_prepay_": True,
    "payment_request/controller.py::print_": True,
    "payment_request/controller.py::update_": True,
    "payment_request/controller.py::submit_": True,
    "payment_request/controller.py::approve_": True,
    "payment_request/controller.py::reject_": True,
    "payment_request/controller.py::pay_": True,
    "payment_request/controller.py::refund_": True,
    "payment_request/controller.py::delete_": True,
    "payment_request/controller.py::bulk_delete_requests": True,
    # ── mượn phạm vi của action khác ────────────────────────────────────────
    "employee/controller.py::export_employees_xlsx": False,   # export → read (B2)
    "document/controller.py::approve_document": False,        # approve → read (B4)
    "document/controller.py::reject_document": False,         # approve → read (B4)
    "document/signature_controller.py::sign_document": False,  # approve → read (B4)
    "document/controller.py::revoke_document": False,         # cancel → write (B5)
    "purchase_request/controller.py::approve_pr": False,      # approve → read (cụm 03 P7)
    "survey_request/controller.py::clone_": False,            # create → read (lành)
    "payment_request/controller.py::create_": False,          # payable create → read (lành)
    "leave/balance_controller.py::allocate": False,           # employee create → read
}


def test_b1_anh_chup_cac_chot_pham_vi_trong_route_ghi():
    """Ảnh chụp mục B — sửa chốt nào thì dòng đó phải được xem lại bằng mắt.

    Con số hôm nay: 274 route có `require(entity, action)` với action ≠ read;
    75 trong số đó gọi một chốt phạm vi. Bảng trên liệt kê 54 chốt đã ĐỌC MÃ
    (21 chốt còn lại là các cửa `_load`/`_get_or_404` lặp lại cùng một khuôn đã
    có tên ở đây). Chín chốt mới của Tài chính là bản vá P0 #3/#4/#5 ngày
    05/09/2026 — trước đó tám cửa GHI của YCTT không có chốt nào cả.

    ⚠️ Giá trị `False` KHÔNG có nghĩa "lỗ": bốn dòng cuối cùng là *lành* — nạp
    bản ghi NGUỒN để sao chép/đối chiếu thì `read` mới đúng. Cột này chỉ nói
    "chốt không dùng đúng action của route", còn kết luận nằm ở ca B2–B5.
    """
    lech = sorted(k for k, dung in CHOT_TRONG_ROUTE_GHI.items() if not dung)
    assert len(lech) == 9, f"số chốt lệch action vừa đổi: {lech}"
    assert sum(CHOT_TRONG_ROUTE_GHI.values()) == 45


def test_b2_xuat_excel_di_theo_pham_vi_read_khong_theo_export(world):
    """🔴 LỖ — `GET /api/employees/export/xlsx` (`employee/controller.py:319-341`).

    Route gác `require("employee", "export")` nhưng lọc bằng
    `apply_scope(query, Employee, "employee", user, profile)` — **không truyền
    `action`**, nên rơi vào mặc định `"read"` (`scoping.py:483`).

    Ca này dựng đúng cấu hình mà hộp thoại «Phạm vi» cho phép: vai trò 1 = XEM
    toàn hệ, vai trò 2 = XUẤT trong pháp nhân mình. Người dùng (và người khai
    quyền) đọc cấu hình đó là "xuất được người của công ty mình"; thực tế tệp
    tải về có đủ nhân sự cả hai pháp nhân.
    """
    from app.modules.employee.model import Employee

    a1 = world.grant("a1", "employee", scope="all", actions=("read",))
    a1.grant("employee", scope="company", actions=("export",))

    doc = a1.sees(Employee, "employee", action="read")
    xuat = a1.sees(Employee, "employee", action="export")
    assert world.emp["b1"] in doc, "phạm vi XEM là toàn hệ"
    assert world.emp["b1"] not in xuat, "phạm vi XUẤT chỉ pháp nhân A"

    #  Đúng biểu thức route đang chạy (`controller.py:334`) — không truyền action.
    from app.core.scoping import apply_scope

    thuc_te = {e.id for e in apply_scope(world.db.query(Employee), Employee, "employee",
                                         a1.user, a1.profile()).all()}
    assert thuc_te == doc, "tệp xuất bám phạm vi XEM"
    assert thuc_te != xuat, "…chứ không bám phạm vi XUẤT"


def test_b2b_sau_route_export_xlsx_deu_dung_pham_vi_read():
    """Không phải chuyện của riêng Nhân sự: **6/6 route `/export/xlsx` đều thế**.

    Năm route còn lại (`purchase_request` · `purchase_order` · `survey_request` ·
    `payable` · `document`) dùng chung hàm `_list_query`/`_filtered` với màn danh
    sách, mà hàm đó tất nhiên lọc bằng `read`. Nên **ô «Xuất» trong hộp thoại
    phạm vi chưa từng cắt được một dòng nào** — nó chỉ bật/tắt cái nút.

    # QUYẾT ĐỊNH CHỜ: cho `_list_query` nhận `action` (danh sách → "read",
    # xuất → "export")? ⚠️ Bật lên là MỘT SỐ NGƯỜI ĐANG XUẤT ĐƯỢC SẼ MẤT DÒNG —
    # phải rà dữ liệu grant trước và ghi `change-log.md` trước khi lên prod.
    """
    from pathlib import Path

    import app.modules

    root = Path(app.modules.__file__).parent
    tep = ["purchase_request/controller.py", "purchase_order/controller.py",
           "survey_request/controller.py", "payable/controller.py",
           "document/controller.py", "employee/controller.py"]
    for ten in tep:
        text = (root / ten).read_text(encoding="utf-8")
        assert '"export")' in text, f"{ten}: không còn route gác bằng khóa export?"
        #  Chốt thật: không tệp nào truyền `"export"` vào một lời gọi phạm vi.
        for moc in ("apply_scope", "get_scoped", "scope_condition"):
            for phan in text.split(moc + "(")[1:]:
                assert '"export"' not in phan[:220], (
                    f"{ten}: đã có chỗ truyền action=export — cập nhật ca này")


def test_b3_can_tru_tien_treo_cong_no_di_theo_pham_vi_write(world):
    """CANH KHÔNG TÁI PHÁT — `POST /api/payables/{pid}/offset-prepay`.

    Route gác `require("payable", "write")` nhưng trước 05/09/2026 nạp khoản nợ
    bằng `apply_scope(...)` **không truyền action**, tức mượn phạm vi `read`: ai
    có ô «Sửa» công nợ, dù phạm vi ghi hẹp tới đâu, cấn trừ được tiền treo vào
    khoản nợ mà họ chỉ được XEM. Đây là thao tác ĐỔI TIỀN, không phải đọc trộm.
    Bản vá (P0 #5) truyền `action="write"`.

    Cấu hình dựng ở đây là cấu hình hộp thoại «Phạm vi» cho phép và người khai
    quyền đọc là *"xem cả tập đoàn, sửa trong công ty mình"*.

    Ca ĐẦY ĐỦ (gọi thật cả hai chiều, kèm số tiền) nằm ở
    `test_pham_vi_tai_chinh_kho_bao_cao.py::test_c9_...`; ở đây chỉ canh đúng
    dòng mã của cụm này: chốt phải hỏi action của route, không hỏi `read`.
    """
    from app.modules.payable.controller import offset_prepay_
    from app.modules.payable.model import Payable

    db = world.db
    db.add_all([Payable(supplier_code="NX", company_id=world.co["A"], total=1000,
                        remaining=1000, status="unpaid"),
                Payable(supplier_code="NX", company_id=world.co["B"], total=2000,
                        remaining=2000, status="unpaid")])
    db.flush()
    id_b = {p.company_id: p.id for p in db.query(Payable).all()}[world.co["B"]]

    a1 = world.grant("a1", "payable", scope="all", actions=("read",))
    a1.grant("payable", scope="company", actions=("write",))

    assert a1.can_get(Payable, id_b, "payable", action="read"), "XEM thì tới được"
    assert a1.can_get(Payable, id_b, "payable", action="write") is False, (
        "…nhưng phạm vi GHI không với tới khoản nợ pháp nhân B")

    with pytest.raises(HTTPException) as e:
        offset_prepay_(pid=id_b, data={"amount": 100}, db=db, user=a1.user)
    assert e.value.status_code == 403, "cổng nay hỏi phạm vi GHI"


def test_b4_duyet_van_ban_muon_pham_vi_cua_quyen_doc(world):
    """🔴 LỖ — duyệt / từ chối / ký văn bản nạp bằng phạm vi `read`.

        document/controller.py:432            approve_document  require(document, "approve")
        document/controller.py:527            reject_document   require(document, "approve")
        document/signature_controller.py:53   sign_document     require(document, "approve")

    Cả ba gọi `_load(db, document_id, user)` — bỏ trống tham số thứ tư, tức
    `action="read"` (`controller.py:91`). Cùng một dòng mã sai với
    `_in_approve_scope` của YCMH (cụm 03 §3.2), chỉ khác phân hệ.

    ⚠️ Ở Văn thư nó **không sửa được bằng cách truyền `"approve"`**, và đây mới
    là phát hiện thật: `access_service.ACTION_COLUMN` (`:47-51`) chỉ khai ba
    hành động `read · write · delete`. Gọi `can(..., "approve")` là `KeyError`
    → 500, chứ không phải "chặn". Nghĩa là với phân hệ Văn thư, `approve` và
    `cancel` **chỉ tồn tại trên trục QUYỀN, không tồn tại trên trục PHẠM VI**.
    Hai ô «Duyệt»/«Hủy» trong hộp thoại phạm vi vai trò không cắt được văn bản nào.

    Cấu hình dựng ở đây là cấu hình phổ biến nhất của Văn thư: *xem văn bản toàn
    tập đoàn, ký văn bản của pháp nhân mình*.

    # QUYẾT ĐỊNH CHỜ: bổ sung `can_approve`/`can_cancel` vào `tab_document_access`
    # + `ACTION_COLUMN` (đúng nghĩa nhưng đụng migration), hay chấp nhận rằng
    # phạm vi duyệt Văn thư = phạm vi đọc và ghi thẳng điều đó lên màn Phân quyền?
    """
    from app.modules.document import access_service
    from app.modules.document import controller as doc_ctl
    from app.modules.document.model import Document

    db = world.db
    db.add_all([_van_ban(world, "A", "VB_A"), _van_ban(world, "B", "VB_B")])
    db.flush()
    id_b = {d.doc_code: d.id for d in db.query(Document).all()}["VB_B"]

    a1 = world.grant("a1", "document", scope="all", actions=("read",))
    a1.grant("document", scope="company", actions=("approve",))
    prof = a1.profile()

    #  Tầng PHẠM VI DỮ LIỆU thì hiểu `approve` rất rõ — nó loại đúng văn bản B.
    assert world_thay(db, Document, "document", a1, "approve") == {"VB_A"}
    assert world_thay(db, Document, "document", a1, "read") == {"VB_A", "VB_B"}

    #  …nhưng tầng quyền của Văn thư không nhận nổi hành động đó.
    with pytest.raises(KeyError):
        access_service.can(db, db.get(Document, id_b), a1.user, prof, "approve")

    #  Nên ba route duyệt/từ chối/ký đành soi phạm vi ĐỌC — và nó mở.
    assert doc_ctl._load(db, id_b, a1.user).id == id_b, (
        "cổng duyệt văn bản mở cho văn bản ngoài phạm vi duyệt")


def test_b5_bai_bo_van_ban_dung_pham_vi_write_khong_phai_cancel(world):
    """⚠️ Ghim — `POST /api/documents/{id}/revoke` (`document/controller.py:568-575`).

    Gác `require("document", "cancel")` nhưng nạp bằng `_load(..., "write")` —
    cùng gốc B4 (`ACTION_COLUMN` không có `cancel`), chỉ khác là ở đây người
    viết đã chọn một action GẦN ĐÚNG thay vì để mặc định.

    Lệch hai chiều: người được cấp `cancel` phạm vi rộng vẫn bị bó theo phạm vi
    `write` hẹp hơn, còn người có `write` rộng thì bãi bỏ được văn bản ngoài
    phạm vi `cancel`. Bãi bỏ là lối thoát duy nhất của văn bản đã cấp số, tức
    thao tác một chiều — nên vế thứ hai đáng lo hơn.
    """
    from app.modules.document import access_service
    from app.modules.document.model import Document

    db = world.db
    db.add(_van_ban(world, "B", "VB_B"))
    db.flush()
    doc_b = db.query(Document).filter(Document.doc_code == "VB_B").one()

    a1 = world.grant("a1", "document", scope="all", actions=("read", "write"))
    a1.grant("document", scope="company", actions=("cancel",))
    prof = a1.profile()

    assert world_thay(db, Document, "document", a1, "cancel") == set(), (
        "phạm vi HỦY không với tới văn bản pháp nhân B")
    assert access_service.can(db, doc_b, a1.user, prof, "write") is True, (
        "route bãi bỏ soi phạm vi `write`, nên nó mở — dù khóa của route là `cancel`")


def test_b6_sau_module_lam_dung_khuon_truyen_action(world):
    """Đối chứng: sáu module nạp bản ghi bằng ĐÚNG action của route.

    Có ca này thì bản vá B2–B5 không phải bàn lại "làm thế nào" — chỉ việc chép.
    Ở đây kiểm đúng thứ mà bốn ca trên thiếu: phạm vi `write`/`delete` HẸP hơn
    `read` thì cửa ghi/xóa phải đóng, kể cả khi cửa đọc mở.
    """
    from app.modules.contract.model import Contract

    db = world.db
    db.add_all([Contract(code="HD_A", company_id=world.co["A"], title="Của A"),
                Contract(code="HD_B", company_id=world.co["B"], title="Của B")])
    db.flush()
    id_b = {c.code: c.id for c in db.query(Contract).all()}["HD_B"]

    a1 = world.grant("a1", "contract", scope="all", actions=("read",))
    a1.grant("contract", scope="company", actions=("write", "delete"))
    assert a1.can_get(Contract, id_b, "contract", action="read") is True

    from app.modules.contract import controller as ct_ctl

    for action in ("write", "delete"):
        with pytest.raises(HTTPException) as e:
            ct_ctl._in_scope(db, id_b, a1.user, action)
        assert e.value.status_code == 403, f"action={action}"


# ──────────────────────────────────────────────────────────────────────────────
#  C — cache quyền 60 giây
# ──────────────────────────────────────────────────────────────────────────────


def test_c1_doi_pham_vi_vai_tro_co_hieu_luc_ngay(world):
    """C1 — thêm/bớt dòng phạm vi đi qua `user/service.py:288` → xóa cache → ăn NGAY.

    Ca này canh chính đường mà màn «Phân quyền» dùng, không phải helper của test:
    `set_user_scope` ghi `tab_user_scope` rồi gọi `perm_cache_clear(user_id)`.
    """
    from app.modules.contract.model import Contract
    from app.modules.user import service as user_service
    from app.modules.user.schema import ScopeUpdate

    db = world.db
    db.add_all([Contract(code="HD_A", company_id=world.co["A"], title="Của A"),
                Contract(code="HD_B", company_id=world.co["B"], title="Của B")])
    db.flush()
    ids = {c.code: c.id for c in db.query(Contract).all()}

    a1 = world.grant("a1", "contract", scope="all")
    assert a1.sees(Contract) == set(ids.values())        # nạp cache

    user_service.set_user_scope(
        db, a1.user.id, a1.roles[0].id,
        ScopeUpdate(companies=[world.co["A"]]), a1.user.id)

    assert a1.sees(Contract) == {ids["HD_A"]}, (
        "thu hẹp phạm vi phải ăn ngay, không đợi hết 60 giây")


def test_c2_doi_phap_nhan_cua_nhan_su_xoa_cache_quyen_ngay(world):
    """CANH KHÔNG TÁI PHÁT — `employee/service.update_employee` xóa cache quyền.

    Lỗ cũ: hàm này THIẾU `perm_cache_clear`. `company_id` của nhân sự nằm trong
    hồ sơ quyền đã cache (`auth.py:186`) và là chiều lọc chính của 12 entity, nên
    đổi pháp nhân một người là đổi tầm nhìn dữ liệu của họ — mà trong tối đa 60
    giây họ vẫn NHÌN BẰNG TẦM CŨ. Nguy nhất ở chiều "chuyển người sang pháp nhân
    khác để thu hồi tầm nhìn": thao tác nhìn như đã xong, không dấu vết nào cho
    biết có một cửa sổ 60 giây trong đó người đó vẫn đọc được dữ liệu cũ. Cửa
    ĐỔI PHÒNG BAN ngay cạnh thì lại CÓ xóa (C2b) — một màn hình, hai cửa, hai
    hành vi.

    Vá 05/09/2026: `update_employee` chụp `(company_id, department_id)` TRƯỚC khi
    ghi đè, và gọi `clear_perm_cache_of(...)` **sau `commit`** khi cặp đó đổi.
    Sau `commit` chứ không trước là có lý do: xóa rồi mới ghi thì một request
    khác chen vào giữa sẽ dựng lại hồ sơ CŨ và cache thêm 60 giây nữa.

    Hai vế đo trên cùng một phép: chuyển a1 sang pháp nhân B thì họ vừa MẤT hợp
    đồng của A (chặn đúng) vừa THẤY hợp đồng của B (không chặn nhầm). Chỉ khẳng
    định vế mất thì một bản vá "an toàn" kiểu xóa sạch grant cũng xanh.
    """
    from app.modules.employee import service as emp_service
    from app.modules.employee.schema import EmployeeUpdate

    db = world.db
    a1 = world.grant("a1", "contract", scope="company")
    assert a1.profile()["company_id"] == world.co["A"]        # nạp cache

    from app.modules.contract.model import Contract

    db.add_all([Contract(code="HD_A", company_id=world.co["A"], title="Của A"),
                Contract(code="HD_B", company_id=world.co["B"], title="Của B")])
    db.flush()
    assert world_thay(db, Contract, "contract", a1, "read") == {"HD_A"}   # mốc so

    emp_service.update_employee(db, world.emp["a1"],
                                EmployeeUpdate(company_id=world.co["B"]), a1.user.id)

    assert db.get(model_of("employee"), world.emp["a1"]).company_id == world.co["B"], (
        "CSDL đã đổi")
    assert a1.profile()["company_id"] == world.co["B"], (
        "hồ sơ quyền đọc lại thấy pháp nhân MỚI ngay, không đợi hết 60 giây")
    #  Hệ quả đo được, không phải suy diễn — và ĐỦ HAI VẾ trong một dòng.
    assert world_thay(db, Contract, "contract", a1, "read") == {"HD_B"}, (
        "mất hợp đồng pháp nhân cũ VÀ thấy hợp đồng pháp nhân mới")

    #  Vế "không xóa thừa": sửa một cột KHÔNG dính phạm vi (chức danh) thì hồ sơ
    #  quyền phải giữ nguyên. Xóa cache ở đây không sai về mặt an toàn, nhưng nó
    #  biến mỗi lần sửa hồ sơ nhân sự thành một lượt dựng lại quyền — ghim để
    #  bản vá đứng đúng chỗ nó cần đứng.
    emp_service.update_employee(db, world.emp["a1"],
                                EmployeeUpdate(position="Trưởng nhóm"), a1.user.id)
    assert a1.profile()["company_id"] == world.co["B"]
    assert world_thay(db, Contract, "contract", a1, "read") == {"HD_B"}


def test_c2b_doi_phong_ban_cua_nhan_su_thi_co_xoa_cache(world):
    """C2b — đối chứng: `PATCH /employees/{id}` với `department_id` thì cache ĐƯỢC xóa.

    Đường đi: `update_employee` → `_sync_primary_department` (`service.py:128-150`)
    → `department_service.set_departments` → `perm_cache_clear` cho mọi tài khoản
    của nhân sự đó (`department_service.py:256-260`). Có ca này thì bản vá C2
    biết chỗ đặt lời gọi: cùng một hàm, chỉ là nhánh `company_id` bị bỏ quên.
    """
    from app.modules.employee import service as emp_service
    from app.modules.employee.schema import EmployeeUpdate

    db = world.db
    a1 = world.grant("a1", "contract", scope="company")
    assert a1.profile()["dept_id"] == world.dept["A.kt"]      # nạp cache

    emp_service.update_employee(db, world.emp["a1"],
                                EmployeeUpdate(department_id=world.dept["A.mua"]),
                                a1.user.id)

    assert a1.profile()["dept_id"] == world.dept["A.mua"], (
        "đổi phòng ban CÓ xóa cache — hồ sơ đọc lại thấy phòng mới ngay")


def test_c3_khoa_tai_khoan_chan_ngay_khong_di_qua_cache(world):
    """C3 ✔ — `is_active = False` chặn ở `get_current_user` (`auth.py:56-64`).

    Chốt này nằm TRƯỚC cache: mỗi lượt gọi API đều `db.get(User, ...)` rồi kiểm
    `is_active`. Nên khóa tài khoản là chặn tức thì, không có cửa sổ 60 giây —
    khác hẳn C2. Ghim để bản vá C2 không "tiện tay" dời chốt này vào trong cache.
    """
    from app.core.auth import create_access_token, get_current_user

    db = world.db
    a1 = world.actor("a1")
    token = create_access_token(a1.user.id)
    assert get_current_user(f"Bearer {token}", db).id == a1.user.id

    a1.user.is_active = False
    db.commit()

    with pytest.raises(HTTPException) as e:
        get_current_user(f"Bearer {token}", db)
    assert e.value.status_code == 401


def test_c4_go_vai_tro_khoi_tai_khoan_mat_quyen_ngay(world):
    """C4 ✔ — `user/service.assign_roles` (`service.py:232-237`) xóa cache sau khi ghi."""
    from app.modules.contract.model import Contract
    from app.modules.user import service as user_service
    from app.modules.user.schema import RoleAssign

    db = world.db
    db.add(Contract(code="HD_A", company_id=world.co["A"], title="Của A"))
    db.flush()

    a1 = world.grant("a1", "contract", scope="all")
    assert a1.sees(Contract) != set()                        # nạp cache

    user_service.assign_roles(db, a1.user.id, RoleAssign(role_ids=[]), a1.user.id)

    assert a1.profile()["grants"] == []
    assert a1.sees(Contract, "contract") == set(), "mất vai trò là mất tầm nhìn NGAY"


def test_c5_ho_so_cache_cu_thieu_dept_ids_thi_lui_ve_phong_chinh(world):
    """C5 ✔ — `scoping.py:278-281` lùi về `dept_id` khi hồ sơ chưa có `dept_ids`.

    Tình huống thật: nâng cấp lên bản có KIÊM NHIỆM (CR-167) trong lúc có người
    đang dùng. Hồ sơ họ đã cache theo hình dạng CŨ (không có `dept_ids`), và nó
    còn sống thêm 60 giây. Nếu nhánh này không lùi thì trong một phút đó phạm vi
    bậc «phòng ban» rỗng — tức người dùng **mất sạch dữ liệu** giữa giờ làm, đúng
    kiểu sự cố không ai dựng lại được.
    """
    from app.core.scoping import apply_scope
    from app.modules.purchase_request.model import PurchaseRequest

    db = world.db
    db.add_all([
        PurchaseRequest(code="YC_KT", company_id=world.co["A"], status="submitted",
                        department_id=world.dept["A.kt"], department=""),
        PurchaseRequest(code="YC_MUA", company_id=world.co["A"], status="submitted",
                        department_id=world.dept["A.mua"], department=""),
    ])
    db.flush()
    ids = {p.code: p.id for p in db.query(PurchaseRequest).all()}

    a1 = world.grant("a1", "purchase_request", scope="dept")
    prof = dict(a1.profile())
    prof.pop("dept_ids", None)          # hồ sơ hình dạng CŨ
    prof.pop("dept_names", None)

    thay = {p.id for p in apply_scope(db.query(PurchaseRequest), PurchaseRequest,
                                      "purchase_request", a1.user, prof).all()}
    assert thay == {ids["YC_KT"]}, "lùi đúng về phòng chính, không mất sạch phạm vi"


# ──────────────────────────────────────────────────────────────────────────────
#  D — hai chỗ khác dễ quên
# ──────────────────────────────────────────────────────────────────────────────


def test_d1_bo_loc_nguoi_dung_tu_truyen_khong_noi_duoc_pham_vi(world):
    """D1 ✔ — `apply_filters` chạy TRƯỚC `apply_scope` nhưng chỉ biết `query.filter(...)`.

    Mọi nhánh của `apply_filters` (`core/base_controller.py:56-83`) đều nối bằng
    AND, nên gõ `?company_id=<pháp nhân khác>` chỉ THU HẸP trong phạm vi đã có —
    ra rỗng, không phải ra dữ liệu bên kia. Ghim tiền đề đó: ngày nào có ai thêm
    một nhánh `or_` vào `apply_filters` thì ca này đỏ.

    Kiểm cả chiều thu hẹp hợp lệ (lọc trong phạm vi của mình vẫn ăn), kẻo bản vá
    tương lai "sửa" bằng cách bỏ luôn bộ lọc.
    """
    from app.core.base_controller import apply_filters
    from app.core.scoping import apply_scope
    from app.modules.contract.model import Contract

    db = world.db
    db.add_all([Contract(code="HD_A", company_id=world.co["A"], title="Của A"),
                Contract(code="HD_B", company_id=world.co["B"], title="Của B")])
    db.flush()
    ids = {c.code: c.id for c in db.query(Contract).all()}

    a1 = world.grant("a1", "contract", scope="company")

    def chay(params: dict) -> set[int]:
        q = apply_filters(db.query(Contract), Contract, _query(params),
                          ["company_id", "code"])
        q = apply_scope(q, Contract, "contract", a1.user, a1.profile())
        return {c.id for c in q.all()}

    assert chay({}) == {ids["HD_A"]}
    assert chay({"company_id": str(world.co["B"])}) == set(), (
        "gõ pháp nhân khác vào URL không nới được gì")
    assert chay({"company_id": str(world.co["A"])}) == {ids["HD_A"]}, (
        "thu hẹp hợp lệ vẫn phải chạy")


def test_d2_khuon_make_crud_router_van_loc_du_nam_cua(world):
    """D2 ✔ — bộ sinh `core/crud.py` lọc đủ list · get · update · delete · export.

    Đây là **khuôn mẫu của mục B**: `get_scoped` ở `update_item` truyền `"write"`
    (L106), ở `delete_item` truyền `"delete"` (L124) — đúng khóa của route.
    Danh mục hiện dùng bộ sinh này đều khai `PUBLIC` nên không tự kiểm được, vì
    vậy ca này dựng một router TRÊN MODEL CÓ PHẠM VI THẬT (`Contract`) rồi gõ id
    ngoài phạm vi vào cả năm cửa.

    Không có ca này thì bộ sinh có thể bị sửa hỏng mà cả hệ vẫn xanh — mọi danh
    mục dùng nó đều PUBLIC nên không màn nào kêu.
    """
    from pydantic import BaseModel, ConfigDict

    from app.core.crud import make_crud_router
    from app.modules.contract.model import Contract

    class HDOut(BaseModel):
        model_config = ConfigDict(from_attributes=True)
        id: int
        code: str
        title: str = ""

    class HDIn(BaseModel):
        code: str = ""
        title: str = ""

    db = world.db
    db.add_all([Contract(code="HD_A", company_id=world.co["A"], title="Của A"),
                Contract(code="HD_B", company_id=world.co["B"], title="Của B")])
    db.flush()
    ids = {c.code: c.id for c in db.query(Contract).all()}

    router = make_crud_router("/hd-test", "contract", Contract, HDIn, HDIn, HDOut,
                              ["code"], unique_field=None,
                              csv_headers={"code": "Mã", "title": "Tên"})
    fn = {r.name: r.endpoint for r in router.routes}

    a1 = world.grant("a1", "contract", scope="company",
                     actions=("read", "write", "delete"))

    req = _query({})
    pg = {"offset": 0, "limit": 50}

    ra = _body(fn["list_items"](req, pg, None, "asc", db, a1.user))
    assert {i["code"] for i in ra["items"]} == {"HD_A"}, "list lọc đúng"

    assert _body(fn["get_item"](ids["HD_A"], db, a1.user))["code"] == "HD_A"
    for ten, tham_so in (("get_item", ()), ("update_item", (HDIn(title="x"),)),
                         ("delete_item", ())):
        with pytest.raises(HTTPException) as e:
            fn[ten](ids["HD_B"], *tham_so, db, a1.user)
        assert e.value.status_code == 404, f"{ten} phải 404 với id ngoài phạm vi"

    #  Xuất CSV cũng lọc — nếu không thì nút Xuất kéo được nguyên bảng vừa giấu.
    resp = fn["export_csv"](None, req, db, a1.user)
    noi_dung = b"".join(resp.body_iterator) if hasattr(resp, "body_iterator") else resp.body
    assert b"HD_B" not in noi_dung and b"HD_A" in noi_dung
