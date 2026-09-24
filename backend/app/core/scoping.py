"""Lọc dữ liệu theo phạm vi — Lớp B (mô hình GRANT).

Mỗi vai trò của user là 1 grant: có quyền hành động + phạm vi riêng
(cấp bậc own/dept/company/all theo vai trò + chọn cụ thể công ty/phòng ban/nhân sự + loại trừ).
`apply_scope` = HỢP (OR) điều kiện của mọi grant có quyền `action` trên entity.

**B-07 — thiếu khai là CHẶN, không phải bỏ qua.** Trước đợt này `_role_scope_cond` trả `None`
cho entity vắng mặt trong `SCOPE_FIELDS`, mà `None` nghĩa là *thấy tất*. Mới khai 12/39 entity
nên 27 entity còn lại im lặng không lọc gì. Nay `SCOPE_FIELDS` phải khai **đủ mọi entity** — loại
nào cố ý không lọc thì khai thẳng là `PUBLIC`, kèm lý do — và entity lạ thì trả `false()`.
`test/backend/test_pham_vi_khai_du_b07.py` chốt con số ENTITIES == SCOPE_FIELDS, nên thêm entity mới vào
`core/permissions.ENTITIES` mà quên khai ở đây là **test đỏ**, không phải lỗ hổng lặng lẽ.
"""
import logging

from sqlalchemy import and_, exists, false, func, or_, select

from app.core.auth import get_perm_profile  # noqa: F401  (re-export tiện dùng)

log = logging.getLogger("app.scoping")


class _Public(dict):
    """Nhãn 'entity này CỐ Ý không lọc phạm vi' — khác hẳn với 'quên khai'.

    Kế thừa `dict` rỗng để mọi chỗ đang gọi `f.get("company")` chạy nguyên như cũ;
    phần phân biệt nằm ở `entity in SCOPE_FIELDS` chứ không ở giá trị.
    """


PUBLIC = _Public()

# Entity → tên cột theo từng chiều. Thiếu chiều nào = không lọc theo chiều đó.
#
# CR-086 — chiều phòng ban: `dept_id` là NGUỒN SỰ THẬT. `dept_name` chỉ còn là ĐƯỜNG LÙI cho
# phiếu cũ chưa điền lùi được id (`department_id = 0`), xem `_dept_match`. Entity nào khai cả
# hai thì bỏ `dept_name` đi là xong phần lùi — làm cùng lúc với việc xóa cột text (N-008).
#
# bao-CR-414 — chiều `handler_dept`: cột "phòng được nhờ xử lý" (`handler_dept_id`, 0 = chưa
# nhờ). Khai chiều này thì `_dept_match` coi phiếu thuộc phòng mình khi phòng lập phiếu HOẶC
# phòng được nhờ là phòng mình — cùng một chỗ, nên bậc `dept`, ô "Phòng ban được xem" và bậc
# `dept_proc` đều tự thấy phiếu được nhờ.
SCOPE_FIELDS = {
    "purchase_request": {"company": "company_id", "dept_id": "department_id",
                         "dept_name": "department", "handler_dept": "handler_dept_id",
                         "owner": "created_by"},
    "survey_request":   {"company": "company_id", "dept_id": "department_id",
                         "dept_name": "department", "handler_dept": "handler_dept_id",
                         "owner": "created_by"},
    "purchase_order":   {"company": "company_id", "dept_id": "department_id",
                         "dept_name": "department", "handler_dept": "handler_dept_id",
                         "owner": "created_by"},
    # bao-CR-414 GĐ4: công nợ + YCTT mang cột phòng ẩn (`department_id` = phòng xử lý đơn
    # lúc nợ sinh ra). Khai `dept_id` là đủ để `dept_proc` / `dept` / loại trừ phòng lọc được;
    # nợ cũ department_id = 0 nên người có bậc phòng KHÔNG thấy nợ cũ — cố ý, không backfill.
    "payable":          {"company": "company_id", "dept_id": "department_id", "owner": "created_by"},
    # Hợp đồng: neo theo PHÁP NHÂN ĐỨNG TÊN (`company_id`). Trước đây entity này không có
    # trong bảng nên `_role_scope_cond` trả None — ai có `contract.read` là đọc hợp đồng của
    # MỌI công ty, kể cả khi phạm vi vai trò đặt là `company`/`own`. KHÔNG có chiều phòng ban:
    # hợp đồng thuộc pháp nhân chứ không thuộc phòng nào.
    "contract":         {"company": "company_id", "owner": "created_by"},
    "payment_request":  {"company": "company_id", "dept_id": "department_id", "owner": "created_by"},
    "inventory":        {"company": "company_id"},
    "survey":           {"owner": "created_by"},
    "employee":         {"company": "company_id", "dept_id": "department_id", "self": "id"},
    "ticket":           {"company": "company_id", "owner": "created_by"},
    # Sổ văn bản: chỉ lọc theo pháp nhân sở hữu sổ. KHÔNG có chiều phòng ban —
    # quyền xem sổ cấp cho người đích danh qua tab_document_book_member.
    "document_book":    {"company": "company_id", "owner": "created_by"},
    # Văn bản: lọc theo pháp nhân BAN HÀNH + phòng chủ trì. `owner` là tài khoản
    # người tạo, không phải `owner_employee_id` (người chịu trách nhiệm nội dung)
    # — hai thứ khác nhau, người tạo hộ vẫn phải thấy phiếu mình vừa nhập.
    "document":         {"company": "company_id", "dept_id": "department_id",
                         "owner": "created_by"},
    #  Cây thư mục (phase 03, duoc-CR-475) — PUBLIC ở ĐÂY là cố ý và TẠM THỜI.
    #  `apply_scope`/`get_scoped` không được gọi trên `DocFolder` ở tầng
    #  `folder_controller.py` (nó không có cột `company_id` filter kiểu
    #  một-cột thông thường — mọi thư mục con kế thừa pháp nhân từ thư mục gốc
    #  qua CÂY, không phải qua một điều kiện SQL đơn). Lọc "thấy nhánh pháp
    #  nhân nào" + ACL từng thư mục nằm ở
    #  `doc_catalog/folder_tree_service._visible_folder_ids` — phase 04 sẽ thay
    #  thân hàm đó, KHÔNG sửa dòng PUBLIC này.
    "doc_folder":       PUBLIC,

    # ------------------------------------------------------------------ B-07
    # Từ đây xuống là 27 entity trước kia KHÔNG có mặt trong bảng này. Vắng mặt
    # không phải "không cần lọc" — nó là *thấy tất*, vì `_role_scope_cond` trả
    # `None`. Nay mỗi entity phải nằm ở đúng một trong hai nhóm dưới.

    # --- Nhóm 1: CÓ chiều thật, nay lọc thật ---
    # Pháp nhân: chiều của chính nó là `id`, không phải `company_id`.
    "company":          {"company": "id"},
    # Phòng ban: neo theo pháp nhân chủ quản. CẨN THẬN — `tab_department_company`
    # cho phép một phòng phục vụ nhiều pháp nhân, nên `company_id` ở đây chỉ là
    # pháp nhân CHÍNH. Ai cần "thấy phòng của mọi pháp nhân mình phục vụ" thì
    # dùng phần chọn đích danh (`_dept_include_cond`), đừng nới lỏng dòng này.
    "department":       {"company": "company_id", "owner": "created_by"},
    # Tài khoản: `tab_user` KHÔNG có `company_id` — chiều pháp nhân nằm ở nhân sự
    # gắn kèm. Chỉ khai `self` để `own` nghĩa là "tài khoản của chính tôi";
    # `dept`/`company` sẽ rơi xuống chặn, đúng ý: người xem hẹp không duyệt danh
    # sách tài khoản toàn hệ.
    "user":             {"self": "employee_id"},
    "approval_flow":    {"company": "company_id", "owner": "created_by"},
    "goods_receipt":    {"company": "company_id", "owner": "created_by"},
    "seal_request":     {"company": "company_id", "dept_id": "department_id",
                         "owner": "created_by"},
    "vehicle_booking":  {"company": "company_id", "dept_id": "department_id",
                         "owner": "created_by"},

    # --- Nhóm 2: CỐ Ý công khai (xem `PUBLIC`) ---
    # 2a. Dữ liệu gốc dùng chung MỌI pháp nhân. Sản phẩm và nhà cung cấp là chỗ
    # các phân hệ nối vào nhau bằng CHUỖI `product_code` / mã NCC (xem
    # `mo-hinh-du-lieu-san-pham.md`). Lọc chúng theo pháp nhân là cắt đứt chính
    # mối nối đó: đơn của công ty A trỏ vào mã sản phẩm do công ty B nhập.
    # Muốn giấu NCC thì tắt bằng QUYỀN `supplier.read`, không phải bằng phạm vi.
    "product":          PUBLIC,
    "supplier":         PUBLIC,
    # Dữ liệu thị trường BÊN NGOÀI (tờ khai hải quan GTT02, bao-CR-470): không thuộc
    # pháp nhân hay phòng ban nào của mình, ai được tick `customs_price.read` thì
    # thấy TOÀN BỘ (đại ca chốt 23/09/2026). Giấu thì tắt bằng quyền, không bằng phạm vi.
    "customs_price":    PUBLIC,
    #  Danh mục hóa chất theo văn bản — dữ liệu pháp lý chung, không thuộc pháp nhân nào.
    "customs_regulation": PUBLIC,
    # 2b. Danh mục KHÔNG có chiều pháp nhân trong bảng. Đây là khoảng trống của
    # mô hình dữ liệu chứ không phải của tệp này — ngày nào thêm `company_id`
    # vào bảng nào thì đổi luôn dòng tương ứng ở đây.
    "warehouse":        PUBLIC,
    "unit":             PUBLIC,
    "item_group":       PUBLIC,
    "brand":            PUBLIC,
    #  Bốn danh mục nền của Văn thư: dùng chung cho mọi pháp nhân, không có cột
    #  nào để lọc. Tách khóa ra bốn cái là để phân quyền THEO MÀN HÌNH (CR-157),
    #  không đổi gì về phạm vi dữ liệu.
    "doc_type":         PUBLIC,
    "doc_template":     PUBLIC,
    "doc_numbering_rule": PUBLIC,
    "doc_link_rule":    PUBLIC,
    "security_level":   PUBLIC,
    "external_party":   PUBLIC,
    "seal_type":        PUBLIC,
    "vehicle":          PUBLIC,
    "driver":           PUBLIC,
    "help_article":     PUBLIC,
    "category_assignee": PUBLIC,
    "role":             PUBLIC,
    "setting":          PUBLIC,
    #  Danh mục quản trị, cố ý KHÔNG lọc theo `company_id` dù bảng có cột đó:
    #  cột ấy là bộ LỌC HIỂN THỊ lúc chọn hộp thư, còn chốt "ai gửi được danh
    #  nghĩa địa chỉ này" nằm ở bảng thành viên `tab_mailbox_member`.
    "mailbox":          PUBLIC,
    # 2c. Quyền HÀNH ĐỘNG, không có bảng nào để lọc. `report`/`backup` là ô tick
    # trong ma trận phân quyền; `payment`/`import` thì đến model cũng không có
    # (không một chỗ nào gọi `require("payment", ...)`) — khai ra đây để bài
    # kiểm ENTITIES == SCOPE_FIELDS khỏi phải chừa ngoại lệ, và để ai xóa chúng khỏi `ENTITIES`
    # thì thấy luôn là xóa được.
    "report":           PUBLIC,
    "backup":           PUBLIC,
    "import":           PUBLIC,
    "payment":          PUBLIC,
    # `assistant` là cổng require() thuần (chỉ ban lãnh đạo), không có bảng nào
    # để lọc theo dòng — dữ liệu bot đọc đã đi qua apply_scope của từng tool.
    "assistant":        PUBLIC,
    # Diễn đàn: ai thấy bài nào KHÔNG đi theo phạm vi RBAC mà theo luật audience
    # riêng (phòng ban / pháp nhân / public đóng băng trên từng bài — QĐ-D3),
    # viết thẳng trong WHERE của API feed. Entity này chỉ gác cổng kiểm duyệt
    # của `forum_admin` bằng require(), nên khai PUBLIC.
    "forum_post":       PUBLIC,
    # F13a: cùng lý do — box đợt đầu toàn PUBLIC (QĐ-D7a), ai thấy gì do luật
    # audience của API diễn đàn, entity chỉ gác CRUD cấu trúc của `forum_admin`.
    "forum_board":      PUBLIC,
    # Công việc (CR-216): phạm vi thật là "theo TƯ CÁCH THÀNH VIÊN của list",
    # không diễn đạt được bằng cột phòng ban/pháp nhân của khuôn `apply_scope`.
    # Khai PUBLIC ở đây là CÓ CHỦ Ý, kèm một nghĩa vụ bắt buộc:
    #
    #   ⚠️ MỌI query của `app/modules/work/` PHẢI tự lọc qua `visible_list_ids(...)`.
    #   Khai PUBLIC mà quên lọc là lộ sạch việc của cả công ty — đọc
    #   `doc/erp/cong-viec/04-phan-quyen.md` §2 trước khi viết endpoint đầu tiên.
    "work_task":        PUBLIC,

    # --- Nghỉ phép (CR-259) ---
    #  Đơn nghỉ khai CẢ `owner` LẪN `self`, và đó là điểm khác mọi entity phía
    #  trên. Lý do: một tờ đơn có HAI người dính tới nó — người NGHỈ
    #  (`employee_id`) và người LẬP (`created_by`, hành chính lập hộ là việc có
    #  thật). Chỉ khai `owner` thì người nghỉ ở phạm vi `own` không thấy đơn của
    #  chính mình; chỉ khai `self` thì người lập hộ nộp xong mất dấu tờ đơn.
    #  Nhánh `own` ở `_role_scope_cond` HỢP cả hai — xem ghi chú tại đó.
    "leave_request":    {"company": "company_id", "dept_id": "department_id",
                         "owner": "created_by", "self": "employee_id"},
    #  Quỹ phép KHÔNG có `owner`: `created_by` là người Nhân sự bấm nút cấp phát,
    #  lấy đó làm "của mình" thì nhân viên xem quỹ của chính họ lại không ra dòng
    #  nào. Chỉ `self` — `own` nghĩa là "quỹ của tôi".
    "leave_balance":    {"company": "company_id", "self": "employee_id"},
    #  Loại nghỉ: danh mục luật dùng chung MỌI pháp nhân, bảng không có cột nào
    #  để lọc. Ai được SỬA thì gác bằng quyền `leave_type.write`, không phải
    #  bằng phạm vi.
    "leave_type":       PUBLIC,
    #  Lịch lễ: bảng CÓ `company_id` nhưng cố ý không lọc theo nó — `0` ở đây
    #  nghĩa là "áp cho mọi pháp nhân", mà `company_id == <của tôi>` thì cắt mất
    #  đúng những dòng dùng chung ấy. Lọc đúng nằm ở `workday_service` (gộp dòng
    #  của pháp nhân mình VỚI dòng dùng chung), không diễn đạt được bằng khuôn
    #  một-cột của `apply_scope`.
    "holiday":          PUBLIC,

    # --- Đặt phòng họp (duoc-CR-279) ---
    #  Phiếu đặt khai CẢ `owner` LẪN `self`, cùng lẽ với đơn nghỉ phép: một phiếu
    #  có hai người dính tới nó — người ĐẶT (`requester_employee_id`, chủ trì) và
    #  người LẬP (`created_by`, thư ký đặt hộ). Chỉ khai một vế thì vế kia mất
    #  dấu phiếu ở phạm vi `own`.
    "room_booking":     {"company": "company_id", "dept_id": "department_id",
                         "owner": "created_by", "self": "requester_employee_id"},
    #  Danh mục phòng: bảng CÓ `company_id` nhưng cố ý không lọc theo nó — `0`
    #  nghĩa là "phòng dùng chung mọi pháp nhân", mà lọc `company_id == <của
    #  tôi>` thì cắt mất đúng những phòng dùng chung ấy. Lọc đúng nằm ở
    #  `service.list_availability` (gộp phòng của pháp nhân mình VỚI phòng dùng
    #  chung), không diễn đạt được bằng khuôn một-cột của `apply_scope`. Ai được
    #  SỬA thì gác bằng quyền `meeting_room.write`, không phải bằng phạm vi.
    "meeting_room":     PUBLIC,

    # --- Hồ sơ nhân sự mở rộng (08/09/2026) ---
    #  Cổng `require()` thuần: nó trả lời "được xem NỘI DUNG nhạy cảm hay
    #  không", còn "được xem HỒ SƠ NÀO" thì khóa `employee` phía trên đã trả lời
    #  rồi. Hai câu hỏi khác nhau, và cả hai đều phải qua — trưởng phòng có
    #  `employee.read` phạm vi *dept* mà thêm khóa này thì đọc được CCCD của
    #  phòng mình, không phải của cả công ty.
    #
    #  ⚠️ PUBLIC ở đây KHÔNG có nghĩa là dữ liệu công khai. Nghĩa là entity này
    #  không có bảng riêng để `apply_scope` lọc. Che nội dung nằm ở
    #  `modules/employee/sensitive.py`, và ai xóa dòng này thì đọc đó trước.
    "employee_sensitive": PUBLIC,

    #  Danh mục CHỨC VỤ (duoc-CR-320). Bảng CÓ `department_id` nhưng cố ý không
    #  lọc theo nó — `0` nghĩa là "chức vụ dùng chung mọi phòng ban", nên lọc
    #  `department_id == <phòng tôi>` cắt mất đúng những dòng dùng chung ấy
    #  (cùng bẫy đã ghi ở `meeting_room`). Danh mục này ai đọc cũng được, vì
    #  thiếu nó thì ô chọn chức vụ trên hồ sơ rỗng; ai được SỬA thì gác bằng
    #  `job_position.write`.
    "job_position":     PUBLIC,

    #  Danh mục LOẠI HỒ SƠ (16/09/2026). Không có chiều pháp nhân / phòng ban
    #  nào — một loại giấy tờ là một loại giấy tờ với cả công ty. Ai đọc cũng
    #  được, vì thiếu nó thì ô chọn loại trên màn hồ sơ rỗng sạch và người dùng
    #  đọc ra "công ty chưa khai loại nào" trong khi thứ họ gặp là 403 bị nuốt;
    #  ai được SỬA thì gác bằng `dossier_type.write`.
    "dossier_type":     PUBLIC,

    #  HỒ SƠ (16/09/2026) — **cột thật, KHÔNG PUBLIC**. Đây là chỗ khác căn bản
    #  với danh mục loại ngay trên: một loại giấy tờ là chuyện chung cả công ty,
    #  còn một bộ hồ sơ thì thuộc về một pháp nhân, một phòng và một người.
    #
    #  Khai cả `owner` LẪN `self` (khuôn của `leave_request`, CR-259): một bộ hồ
    #  sơ có HAI người dính tới nó — người LẬP (`created_by`, hành chính nhập
    #  hộ) và người PHỤ TRÁCH theo dõi (`owner_employee_id`). Cả hai đều phải
    #  thấy nó ở phạm vi «của mình», nếu không thì người được giao theo dõi hồ
    #  sơ lại không mở được chính hồ sơ ấy. Nhánh `own` của `_role_scope_cond`
    #  đã HỢP hai cột và tự chặn khi `employee_id = 0` — thiếu chốt đó thì
    #  `owner_employee_id == 0` trúng mọi hồ sơ CHƯA GẮN người phụ trách, tức là
    #  mở rộng phạm vi thay vì thu hẹp.
    "dossier":          {"company": "company_id", "dept_id": "department_id",
                         "owner": "created_by", "self": "owner_employee_id"},

    # --- Điểm cà phê × POS365 (doc/erp/diem-ca-phe/04-phan-quyen.md) ---
    #  Sổ điểm và thành viên khai `self` theo `employee_id` — "nhân viên chỉ thấy
    #  sổ của mình" là một phép áp scope, không phải một câu hứa (nghiệm thu 4 của
    #  `09` §11). KHÔNG khai `owner`: `created_by` của dòng sổ là người/task GHI hộ
    #  (0 = tự động), lấy đó làm "của mình" thì mọi dòng task tự ghi thành ví chung.
    "coffee_policy":    {"company": "company_id"},
    "coffee_member":    {"company": "company_id", "self": "employee_id"},
    "coffee_ledger":    {"company": "company_id", "self": "employee_id"},
    #  Đơn POS365 là dữ liệu vận hành/đối soát — lọc theo pháp nhân của quán;
    #  người thường không có grant nên không thấy gì (đúng ý).
    "pos_order":        {"company": "company_id"},

    # --- Phiên đăng nhập (bao-CR-395 / CR-312 P3b) ---
    #  Bảng `tab_login_session` chỉ có `user_id` — không cột công ty/phòng ban, và
    #  cố ý không nối sang nhân sự để lọc: một phiên thuộc về TÀI KHOẢN, không thuộc
    #  về phòng. Nên chỉ hai mức có nghĩa: `all` (quản trị / Nhân sự) và `own`
    #  (thiết bị của tôi). `dept` rơi về `own` theo nhánh chung của `_role_scope_cond`,
    #  `company` không có cột thì bị chặn — đúng ý, đừng khai thêm chiều cho có.
    "login_session":    {"owner": "user_id"},

    # --- Nhật ký hệ thống (bao-CR-407 / CR-312 P5) ---
    #  PUBLIC, và đó là một quyết định chứ không phải chỗ khai cho đủ. Nhật ký là
    #  thứ dùng để ĐI TRA SỰ CỐ: cắt nó theo phòng ban của người tra thì cú gọi
    #  cần nhìn nhất — lượt 403 của người ngoài phạm vi, lượt script chạy dưới
    #  `user_id = 0` — biến mất đúng lúc cần. Chốt là ở cửa: hai khóa này CHỈ cấp
    #  cho quản trị, còn ai muốn xem dòng thời gian của phiếu mình thì đi bằng
    #  `read` của phiếu đó và đã bị `apply_scope` lọc sẵn ở đó rồi.
    "audit":            PUBLIC,
    "change_log":       PUBLIC,

    # --- Sổ đồng bộ với hệ ngoài (P0 đặt xe) ---
    #  PUBLIC cùng một lý do với nhật ký hệ thống, và còn dứt khoát hơn: một dòng
    #  sổ đồng bộ nói về BẢN GHI CỦA BÊN KIA (`legacy_id`), lúc nó hỏng thì phía
    #  ERP thường CHƯA có bản ghi nào để mà xét công ty/phòng ban. Cắt theo phạm vi
    #  ở đây nghĩa là đúng những dòng lỗi nặng nhất thì không ai nhìn thấy.
    #  Chốt là ở cửa: khóa `sync_log` chỉ cấp cho quản trị hệ thống.
    "sync_log":         PUBLIC,
    "purchase_cost_type": PUBLIC,   # bao-CR-453 — danh mục dùng chung, không có chủ
}


def _dept_match(model, f, dept_ids, dept_names):
    """Điều kiện "phiếu thuộc một trong các phòng này" — CR-086.

    Khớp bằng ID. Chỉ những phiếu KHÔNG điền lùi được id (`department_id = 0`, phòng đã đổi
    tên hoặc dữ liệu nhập tay) mới rơi về so tên, nên tên không bao giờ đè lên id. Xóa nhánh
    tên khi bỏ cột text (N-008). None = không có gì để so.
    """
    col_id, col_name = f.get("dept_id"), f.get("dept_name")
    cs = []
    if col_id and dept_ids:
        cs.append(getattr(model, col_id).in_(list(dept_ids)))
    if col_name and dept_names:
        legacy = getattr(model, col_name).in_(list(dept_names))
        cs.append(and_(getattr(model, col_id) == 0, legacy) if col_id else legacy)
    # bao-CR-414: phiếu ĐƯỢC NHỜ cho phòng mình cũng là "phiếu thuộc phòng mình".
    col_handler = f.get("handler_dept")
    if col_handler and dept_ids:
        cs.append(getattr(model, col_handler).in_(list(dept_ids)))
    if not cs:
        return None
    return or_(*cs) if len(cs) > 1 else cs[0]


def _handler_dept_cond(model, f, dept_ids):
    """Điều kiện "phiếu được NHỜ cho một trong các phòng này" — bao-CR-414. None = không có."""
    col_handler = f.get("handler_dept")
    if not col_handler or not dept_ids:
        return None
    return getattr(model, col_handler).in_(list(dept_ids))


def approves_only_in_dept_proc(profile: dict, entity: str) -> bool:
    """Người này duyệt/điều phối `entity` CHỈ bằng bậc `dept_proc` (phòng tự mua) — bao-CR-414.

    Dùng để quyết định tự gán theo nhóm hàng có được RƠI VỀ bộ "Thu mua chung" (phòng 0 của
    `category_assignee`) hay không: quản lý thu mua của phòng chỉ dùng bộ riêng của phòng mình,
    rơi về bộ chung là đẩy việc của phòng nhà máy sang tay thu mua chung. Có thêm một grant
    `proc`/`all` có `approve` thì tra cả bộ chung như cũ.
    """
    seen_dept_proc = False
    for grant in profile.get("grants", []):
        perms = grant["perms"].get(entity)
        if not perms or not perms.get("approve"):
            continue
        if perms.get("scope", "all") == "dept_proc":
            seen_dept_proc = True
        else:
            return False
    return seen_dept_proc


def holds_handling_dept(profile: dict, entity: str, ticket) -> bool:
    """Người này có đang là quản lý thu mua của PHÒNG ĐANG XỬ LÝ phiếu không — bao-CR-414 GĐ5.

    Dùng cho nút "Chuyển phòng xử lý" / "Trả về phòng lập": chỉ phòng đang cầm phiếu (hoặc
    người có phạm vi toàn hệ) mới được đẩy đi. Grant `approve` bậc `proc`/`all` = toàn hệ;
    bậc `dept_proc` = phải trùng phòng đang xử lý (`handler_dept_id`, không thì phòng lập).
    Bậc `dept` (trưởng phòng duyệt bước 1) và grant không có `approve` KHÔNG tính.
    """
    from app.modules.category_assignee.service import handling_dept_of
    dept_ids = set(int(x) for x in (profile.get("dept_ids") or []) if x)
    current = int(handling_dept_of(ticket) or 0)
    for grant in profile.get("grants", []):
        perms = grant["perms"].get(entity)
        if not perms or not perms.get("approve"):
            continue
        scope = perms.get("scope", "all")
        if scope in ("proc", "all"):
            return True
        if scope == "dept_proc" and current and current in dept_ids:
            return True
    return False


def _emp_match(model, col_id: str, col_name: str, emp_id: int, emp_name: str):
    """Điều kiện "ô nhân sự này là mình" — CR-087, cùng khuôn với `_dept_match`.

    `tab_employee.full_name` KHÔNG duy nhất nên khớp bằng tên là cho người trùng tên thấy
    việc của nhau. Khớp bằng id; chỉ dòng chưa điền lùi được (`<col_id> = 0`) mới rơi về so
    tên. Xóa nhánh tên khi bỏ cột chuỗi (N-008). None = không có gì để so.
    """
    cs = []
    if emp_id:
        cs.append(getattr(model, col_id) == emp_id)
    if emp_name:
        cs.append(and_(getattr(model, col_id) == 0, getattr(model, col_name) == emp_name))
    if not cs:
        return None
    return or_(*cs) if len(cs) > 1 else cs[0]


def _proc_status_cond(model, statuses: list[str]):
    """Nhánh "nhặt việc" của bậc `proc` / `dept_proc`: phiếu ở các trạng thái sau duyệt.

    bao-CR-434 ĐẢO P1-1 (kế hoạch 12, CR-164): trước đây nhánh này AND thêm pháp nhân của
    người xem khi hồ sơ nhân sự đã gắn `company_id`. Đại ca chốt 21/09/2026: pháp nhân trên
    hồ sơ chỉ là chuyện pháp lý — phòng nhà máy (Dego Organic) mua cho nhiều công ty và ghi
    hóa đơn về công ty khác mình, nên điền ô Pháp nhân cho một người là họ MẤT phiếu của các
    công ty còn lại mà không ai được báo. Từ nay hồ sơ KHÔNG tự thu hẹp gì cả; muốn nhốt một
    tài khoản vào một pháp nhân thì khai tận tay ở ô «Chỉ trong công ty» của hộp thoại Phạm
    vi (`_explicit_cond`, chiều `company`) — giới hạn nào cũng phải là thứ quản trị nhìn thấy.
    """
    return getattr(model, "status").in_(statuses)


def _chan(entity, scope, user, reason):
    """Phạm vi hẹp nhưng không dựng nổi điều kiện → CHẶN, và nói ra vì sao — B-07.

    Trước đợt này mọi nhánh kiểu này đều lặng lẽ `return None`, mà `None` là *thấy tất*:
    phạm vi đặt hẹp bao nhiêu cũng vô nghĩa và không có một dòng log nào để biết. Dòng
    WARNING dưới đây chính là thứ để đi gom danh sách người bị ảnh hưởng — đừng bỏ nó khi
    dọn log, và khi thấy nó nổi lên thì việc phải làm gần như luôn là **sửa dữ liệu**
    (gắn pháp nhân/phòng ban cho nhân sự), không phải nới lại điều kiện ở đây.
    """
    log.warning("scope chan: entity=%s scope=%s user=%s — %s",
                entity, scope, getattr(user, "id", None), reason)
    return false()


def _role_scope_cond(model, entity, scope, user, profile, perms=None):
    """Điều kiện theo cấp bậc vai trò (own/dept/company/all). None = 'all' (không giới hạn).

    `perms` = bộ quyền của CHÍNH grant đang xét ({action: bool, scope}). Cần cho Duyệt
    dấu để tách Văn thư (grant company CÓ `write` → đóng dấu) khỏi Giám đốc (grant
    company CHỈ `read` → xem phiếu đã duyệt). Đọc `perms_union` toàn cục là sai: ai
    cũng có `write` phạm vi own (vai trò nền `employee`) nên Giám đốc bị nhận nhầm."""
    if scope == "all":
        return None
    # B-07: KHÔNG khai = CHẶN. Trước đây nhánh này trả `None` nên 27 entity vắng mặt trong
    # `SCOPE_FIELDS` được xem thoải mái bất kể phạm vi vai trò. Entity cố ý không lọc thì
    # phải khai thẳng là `PUBLIC` ở trên; rơi vào đây nghĩa là ai đó vừa thêm entity mới
    # vào `core/permissions.ENTITIES` mà quên khai (bài kiểm ENTITIES == SCOPE_FIELDS sẽ đỏ).
    if entity not in SCOPE_FIELDS:
        log.error("scope thieu khai: entity=%s chua co trong SCOPE_FIELDS — dang chan het", entity)
        return false()
    f = SCOPE_FIELDS[entity]
    if isinstance(f, _Public):
        return None
    company_id = profile.get("company_id") or 0
    #  KIÊM NHIỆM (CR-167) — người này có thể có chân ở NHIỀU phòng, phạm vi bậc
    #  «phòng ban» phải mở đủ cả. Lùi về phòng chính khi hồ sơ quyền chưa có
    #  danh sách (bản cache cũ còn sống trong 60 giây sau khi nâng cấp).
    dept_ids = [x for x in (profile.get("dept_ids") or []) if x] \
        or ([profile["dept_id"]] if profile.get("dept_id") else [])
    dept_names = [x for x in (profile.get("dept_names") or []) if x] \
        or ([profile["dept_name"]] if profile.get("dept_name") else [])

    # "Được giao": của mình HOẶC được phân bổ cho mình (áp cho PYC)
    # bao-CR-414 — "dept_proc" = đúng nhánh `proc` NHƯNG AND thêm "phiếu thuộc phòng mình"
    # (phòng lập phiếu hoặc phòng được nhờ, xem `_dept_match`). Người chưa gắn phòng thì CHẶN,
    # cùng luật với bậc `dept`.
    if scope in ("assigned", "proc", "dept_proc"):
        in_dept_proc = scope == "dept_proc"
        is_proc = scope in ("proc", "dept_proc")

        def _narrow_to_dept(cond):
            if not in_dept_proc:
                return cond
            dm = _dept_match(model, f, dept_ids, dept_names)
            if dm is None:
                return _chan(entity, scope, user, "bac dept_proc nhung nhan su chua gan phong ban")
            return and_(cond, dm)

        if entity == "purchase_request":
            from app.modules.purchase_request.model import (STATUS_AFTER_APPROVE,
                                                            PurchaseRequestItem)
            conds = [model.created_by == user.id]
            if profile.get("employee_id"):
                conds.append(model.requester_id == profile["employee_id"])   # phiếu mình là người yêu cầu
            # "proc" (NV/Admin thu mua): thấy thêm MỌI phiếu đã duyệt để nhặt việc + phân bổ.
            # CR-034: gồm cả 'approved' (TP duyệt xong, ĐANG CHỜ ĐIỀU PHỐI) — thiếu trạng thái này
            # thì chính người phải điều phối lại không nhìn thấy phiếu.
            # Nhánh này CỐ Ý không lọc pháp nhân (bao-CR-434 đảo P1-1, xem `_proc_status_cond`):
            # nhà máy mua cho nhiều công ty; nhốt theo pháp nhân là việc của ô «Chỉ trong
            # công ty», không phải của hồ sơ nhân sự.
            # bao-CR-371: phải là CẢ vòng đời sau duyệt, không chỉ 2 mốc đầu. Liệt kê tay
            # ["approved","dispatched"] nghĩa là phiếu vừa chạy sang 'processing' là BIẾN MẤT
            # khỏi mắt chính người thu mua đang xử lý nó (mở link ra thì "Không tìm thấy"),
            # trừ khi tình cờ họ là người tạo / người yêu cầu / người được gán.
            if is_proc:
                conds.append(_proc_status_cond(model, list(STATUS_AFTER_APPROVE)))
            if profile.get("employee_id"):
                conds.append(model.assignee_id == profile["employee_id"])
            if profile.get("emp_code"):
                sub = select(PurchaseRequestItem.pr_id).where(PurchaseRequestItem.assignee == profile["emp_code"])
                conds.append(model.id.in_(sub))
            return _narrow_to_dept(or_(*conds))
        if entity == "survey_request":
            from app.modules.survey_request.model import SurveyRequestLine
            conds = [model.created_by == user.id]   # phiếu MÌNH tạo → thấy mọi trạng thái
            # "Việc thu mua của tôi" CHỈ áp cho phiếu ĐÃ DUYỆT (bỏ nháp/chờ duyệt/từ chối).
            # NSTM chỉ thấy phiếu khi CÓ DÒNG gán mã mình — việc khảo sát nằm ở DÒNG.
            # (Bỏ điều kiện theo `assignee_id` đầu phiếu: trường đó chỉ ghi 1 lần lúc duyệt và
            #  không đồng bộ khi đổi NSTM dòng → người cũ vẫn thấy phiếu không còn phần việc nào.)
            emp_id = profile.get("employee_id") or 0
            if emp_id:
                conds.append(model.requester_id == emp_id)   # phiếu mình là người yêu cầu → thấy mọi trạng thái
            if profile.get("emp_code"):
                code_sub = (select(SurveyRequestLine.survey_request_id)
                            .where(SurveyRequestLine.assignee == profile["emp_code"]))
                conds.append(and_(model.status.notin_(["draft", "submitted", "rejected"]),
                                  model.id.in_(code_sub)))
            if in_dept_proc:
                # bao-CR-414: quản lý thu mua CỦA PHÒNG phải thấy mọi YCBG của phòng mình từ lúc
                # gửi duyệt trở đi để duyệt + gán NSTM (bậc `proc` giữ nguyên: chỉ dòng gán mình,
                # vì thu mua chung có `pur_manager` bậc `all` lo phần duyệt). AND phòng ở dưới
                # khoanh lại đúng phòng mình.
                conds.append(model.status != "draft")
            return _narrow_to_dept(or_(*conds))
        if entity == "purchase_order":
            # ĐMH: thấy đơn MÌNH tạo HOẶC đơn có NSPT phụ trách = mình.
            # CR-087: khớp bằng `nspt_id`; tên chỉ còn là đường lùi cho đơn cũ (`nspt_id = 0`).
            conds = [model.created_by == user.id]
            if is_proc:
                # bao-CR-371: cùng lỗi với YCMH — nhận hàng xong (`partial`/`received`/
                # `completed`) thì đơn không được biến mất khỏi mắt người thu mua đang theo nó.
                from app.modules.purchase_order.model import STATUS_AFTER_APPROVE as PO_AFTER_APPROVE
                conds.append(_proc_status_cond(model, list(PO_AFTER_APPROVE)))
            ec = _emp_match(model, "nspt_id", "nspt",
                            profile.get("employee_id") or 0, profile.get("emp_name") or "")
            if ec is not None:
                conds.append(ec)
            return _narrow_to_dept(or_(*conds))
        if entity == "vehicle_booking":
            # Tài xế thấy phiếu ĐƯỢC PHÂN cho mình (nối qua Driver.user_id) + phiếu mình
            # tạo. Nhờ vậy nút Chấp nhận/Bắt đầu/Hoàn tất mới tới được đúng tài xế.
            from app.modules.vehicle_booking.model import Driver
            conds = [model.created_by == user.id]
            drv_sub = select(Driver.id).where(Driver.user_id == user.id)
            conds.append(model.assigned_driver_id.in_(drv_sub))
            # bao-CR-446: trước đây nhánh này `return` thẳng, bỏ qua `_narrow_to_dept`, nên
            # với đặt xe `dept_proc` == `assigned` (không khoanh phòng, không chặn người chưa
            # gắn phòng) — lệch với luật chung của bậc này ghi ở đầu khối. Nay đi qua cùng
            # một cửa với ba chứng từ thu mua: `assigned`/`proc` giữ nguyên, `dept_proc`
            # AND thêm «phiếu thuộc phòng mình».
            return _narrow_to_dept(or_(*conds))
        if in_dept_proc:
            # bao-CR-414: entity không phải chứng từ thu mua → `dept_proc` rơi về bậc `dept`
            # (thấy trong phòng mình), không rơi về `own` như `assigned`/`proc`.
            dm = _dept_match(model, f, dept_ids, dept_names)
            if dm is None:
                return _chan(entity, scope, user, "bac dept_proc nhung nhan su chua gan phong ban")
            return dm
        scope = "own"   # entity khác chưa có phân bổ → coi như của mình

    if scope == "own":
        if f.get("owner"):
            cond = getattr(model, f["owner"]) == user.id
            # Người YÊU CẦU cũng thấy phiếu của mình dù người khác (admin) tạo giùm
            rid = profile.get("employee_id") or 0
            if rid and hasattr(model, "requester_id"):
                cond = or_(cond, model.requester_id == rid)
            #  CR-259 — entity khai CẢ `owner` LẪN `self`: chứng từ có hai người
            #  dính tới nó, người LẬP và người CHỊU (đơn nghỉ phép: `created_by`
            #  và `employee_id`). Cả hai đều phải thấy nó ở phạm vi «của mình».
            #  Cùng ý với nhánh `requester_id` ngay trên, chỉ khác là tên cột do
            #  `SCOPE_FIELDS` khai chứ không đoán bằng `hasattr`.
            #  ⚠️ Chặn `rid = 0`: `employee_id == 0` sẽ trúng mọi dòng chưa gắn
            #  nhân sự, tức là mở rộng phạm vi thay vì thu hẹp.
            if rid and f.get("self"):
                cond = or_(cond, getattr(model, f["self"]) == rid)
            return cond
        if f.get("self"):   # entity không có owner (vd. employee) → chỉ chính mình
            #  ⚠️ CÙNG CHỐT `rid` với nhánh có `owner` ngay trên — B11/#21. Nhánh
            #  này trước đây so thẳng `== (employee_id or 0)`, nên tài khoản CHƯA
            #  GẮN hồ sơ nhân sự nhận điều kiện `<cột self> == 0`, mà `0` là đúng
            #  giá trị của MỌI dòng chưa gắn nhân sự: đặt phạm vi `own` trên
            #  `user` là thấy hết tài khoản chưa gắn nhân sự của cả hệ. Thiếu dữ
            #  liệu thì CHẶN, đúng tinh thần B-07 (và có một dòng log để đi tìm
            #  người phải gắn hồ sơ), chứ không nới ra.
            rid = profile.get("employee_id") or 0
            if not rid:
                return _chan(entity, scope, user, "tai khoan chua gan ho so nhan su")
            return getattr(model, f["self"]) == rid
        scope = "company"

    if scope == "dept":
        cs = []
        if f.get("company") and company_id:
            cs.append(getattr(model, f["company"]) == company_id)
        if f.get("dept_id") or f.get("dept_name"):
            dc = _dept_match(model, f, dept_ids, dept_names)
            # Người dùng chưa gắn phòng nào → không có gì để so → không thấy gì. (Luật cũ so
            # `department == ""` nên cũng gần như không ra phiếu nào; ở đây nói thẳng ra.)
            cs.append(dc if dc is not None else false())
        elif f.get("owner"):
            cs.append(getattr(model, f["owner"]) == user.id)
        if not cs:
            return _chan(entity, scope, user, "entity khong co chieu phong ban lan chu so huu")
        return and_(*cs)

    if scope == "company":
        #  DUYỆT DẤU — Văn thư / Giám đốc: MỘT phiếu gắn NHIỀU công ty (bảng nối
        #  `tab_seal_request_company`), nên lọc theo BẢNG NỐI chứ không theo cột
        #  `company_id` (công ty chính) — Văn thư của BẤT KỲ công ty nào trong danh
        #  sách đều thấy phiếu. Và chỉ thấy phiếu ĐÃ QUA TBP (Đã duyệt / Hoàn thành);
        #  phiếu nháp/chờ duyệt KHÔNG hiện. Subquery chạy được cả MySQL lẫn SQLite.
        #  `own`/`dept` KHÔNG chặn ở đây — nhánh chung phía trên đã đúng: `own` =
        #  người tạo ∨ người yêu cầu; `dept` = cùng công ty chính ∧ cùng phòng.
        if entity == "seal_request":
            from app.modules.seal_request.model import (SEAL_APPROVED, SEAL_COMPLETED,
                                                        SealRequestCompany as _SRC)
            approved = model.status.in_([SEAL_APPROVED, SEAL_COMPLETED])
            #  VĂN THƯ (có quyền `write`) — lọc theo BẢNG PHÂN CÔNG `tab_seal_clerk`,
            #  KHÔNG theo `company_id` hồ sơ: chỉ thấy phiếu MỘT công ty của công ty
            #  mình phụ trách; phiếu ĐA công ty chỉ về VĂN THƯ TỔNG (`is_head`).
            #  Chỉ dùng điều kiện SQL (không cần `db`) nên chạy cả MySQL lẫn SQLite.
            #  Văn thư = grant NÀY (phạm vi company) có `write`; Giám đốc = chỉ `read`.
            has_write = bool(perms and perms.get("write"))
            if has_write:
                from app.modules.seal_clerk.model import CLERK_ACTIVE, SealClerk
                emp_id = profile.get("employee_id") or 0
                if not emp_id:
                    return _chan(entity, scope, user, "van thu chua gan ho so nhan su")
                single = (select(_SRC.seal_request_id)
                          .group_by(_SRC.seal_request_id).having(func.count() == 1))
                #  Chỉ dòng phân công ĐANG HOẠT ĐỘNG mới nhận phiếu — Tạm dừng thì bỏ qua.
                my_companies = select(SealClerk.company_id).where(
                    SealClerk.employee_id == emp_id, SealClerk.is_head.is_(False),
                    SealClerk.company_id != 0, SealClerk.status == CLERK_ACTIVE)
                mine = select(_SRC.seal_request_id).where(_SRC.company_id.in_(my_companies))
                cond = and_(model.id.in_(single), model.id.in_(mine))
                multi = (select(_SRC.seal_request_id)
                         .group_by(_SRC.seal_request_id).having(func.count() > 1))
                head = select(SealClerk.id).where(
                    SealClerk.employee_id == emp_id, SealClerk.is_head.is_(True),
                    SealClerk.status == CLERK_ACTIVE)
                cond = or_(cond, and_(model.id.in_(multi), exists(head)))
                return and_(cond, approved)
            #  GIÁM ĐỐC (chỉ `read` phạm vi công ty) — giữ nguyên: thấy mọi phiếu đã
            #  duyệt có công ty MÌNH (hồ sơ) trong bảng nối, để giám sát toàn công ty.
            if not company_id:
                return _chan(entity, scope, user, "nguoi dung chua gan phap nhan (company_id=0)")
            sub = select(_SRC.seal_request_id).where(_SRC.company_id == company_id)
            return and_(model.id.in_(sub), approved)
        if not f.get("company"):
            # Entity không có cột pháp nhân (vd. `survey`, `user`). Không có gì để lọc mà vẫn
            # trả None thì "company" hóa ra rộng bằng "all" — đúng lỗ N-14.
            return _chan(entity, scope, user, "entity khong co cot phap nhan")
        if not company_id:
            # NGƯỜI DÙNG CHƯA GẮN PHÁP NHÂN. Cùng luật với nhánh `dept` ở trên (chưa gắn
            # phòng → không thấy gì): thiếu dữ liệu thì chặn, chứ mở toang là nguy hiểm hơn.
            # ⚠️ Trước khi đưa lên môi trường thật phải gắn `company_id` cho nhân sự — xem
            # phần B-07 trong `doc/erp/15-do-be-tong-nen-v2.md`, đã đếm sẵn số người dính.
            return _chan(entity, scope, user, "nguoi dung chua gan phap nhan (company_id=0)")
        return getattr(model, f["company"]) == company_id

    return _chan(entity, scope, user, "pham vi la khong hieu duoc")


def _parse_int_values(entity, dim, box, values):
    """Lọc lấy giá trị SỐ trong một ô phạm vi, kêu lên khi gặp rác — B11/#34.

    `auth.py` CỐ Ý giữ nguyên chuỗi khi giá trị `dim=company` không phải số
    (`int(s.value) if (s.value or "").isdigit() else s.value`), nên một dòng
    `tab_user_scope` hỏng — gõ tay vào DB, nhập nhầm, hay dữ liệu di trú cũ — đi
    thẳng xuống đây. `int(v)` trần thì `ValueError` bay lên tận controller ⇒
    **500 ở MỌI màn danh sách** của riêng người đó, và họ không tự gỡ được vì
    màn nào cũng chết. Bỏ qua giá trị rác là cách duy nhất còn chừa đường vào để
    sửa dữ liệu; dòng WARNING (cùng khuôn `_chan`) là chỗ để đi tìm nó.
    """
    good, bad = [], []
    for v in values:
        try:
            good.append(int(v))
        except (TypeError, ValueError):
            bad.append(v)
    if bad:
        log.warning("scope gia tri khong phai so: entity=%s dim=%s o=%s — bo qua %r",
                    entity, dim, box, bad)
    return good


def _explicit_cond(model, entity, scopeconf, profile=None):
    """Điều kiện THU HẸP: include công ty/nhân sự + MỌI loại trừ (AND).
    Riêng 'Phòng ban được xem' (department include) = CỘNG THÊM → xử lý ở apply_scope.

    bao-CR-414: ô "Loại trừ phòng ban" KHÔNG chặn phiếu mà phòng đó NHỜ phòng mình xử lý
    (`handler_dept_id` là phòng của người xem) — thu mua chung loại trừ nhà máy nhưng nhà máy
    nhờ thì vẫn thấy. Cần `profile` để biết phòng mình; không có thì loại trừ như cũ."""
    f = SCOPE_FIELDS.get(entity) or {}
    cs = []
    for dim, col in (("company", f.get("company")), ("employee", f.get("owner"))):
        if not col:
            continue
        column = getattr(model, col)
        raw_inc = (scopeconf.get("inc") or {}).get(dim) or []
        raw_exc = (scopeconf.get("exc") or {}).get(dim) or []
        inc = _parse_int_values(entity, dim, "chon", raw_inc)
        exc = _parse_int_values(entity, dim, "loai tru", raw_exc)
        if inc:
            cs.append(column.in_(inc))
        elif raw_inc:
            #  Ô CHỌN có giá trị nhưng KHÔNG giá trị nào dùng được. Bỏ qua ô này
            #  là phạm vi NỞ ra đúng bằng bậc vai trò — ngược hẳn ý người khai.
            #  Chặn, cùng luật với `_chan`. (Ô LOẠI TRỪ toàn rác thì bỏ qua là
            #  đúng: cột số không bao giờ khớp một chuỗi rác, giữ hay bỏ đều
            #  không loại được dòng nào.)
            cs.append(false())
        if exc:
            cs.append(~column.in_(exc))
    # Phòng ban: include là CỘNG THÊM (xem `_dept_include_cond`), ở đây chỉ còn loại trừ.
    # Loại trừ CHỈ so cột phòng lập phiếu (không so cột phòng được nhờ): nhờ phòng mình
    # thì phải thấy, nhờ phòng khác thì phiếu vẫn là của phòng bị loại trừ.
    f_no_handler = {k: v for k, v in f.items() if k != "handler_dept"}
    dc = _dept_match(model, f_no_handler, (scopeconf.get("exc") or {}).get("department") or [],
                     (scopeconf.get("exc") or {}).get("department_name") or [])
    if dc is not None:
        my_dept_ids = [x for x in ((profile or {}).get("dept_ids") or []) if x] \
            or ([profile["dept_id"]] if (profile or {}).get("dept_id") else [])
        handed_to_me = _handler_dept_cond(model, f, my_dept_ids)
        cs.append(or_(~dc, handed_to_me) if handed_to_me is not None else ~dc)
    return and_(*cs) if cs else None


def _dept_include_cond(model, entity, scopeconf):
    """'Phòng ban được xem' → điều kiện CỘNG THÊM (OR với phạm vi vai trò). None = không chọn phòng nào.

    `department` = danh sách ID, `department_name` = tên tương ứng (chỉ để lùi cho phiếu cũ).
    Hai khóa này do `core/auth.py` dựng sẵn khi đọc `tab_user_scope`.
    """
    inc = (scopeconf.get("inc") or {})
    return _dept_match(model, SCOPE_FIELDS.get(entity) or {},
                       inc.get("department") or [], inc.get("department_name") or [])


def has_global_scope(profile: dict, entity: str, action: str) -> bool:
    """Người này có grant `action` trên `entity` với phạm vi **tất cả** không?

    Khác `scope_condition(...) is None` ở chỗ: hàm kia cần một `model` để dựng
    điều kiện SQL, mà có những thứ phải phân biệt "quản trị toàn hệ" hay không
    NHƯNG không gắn với bảng nào — điển hình là quyền **lập ủy quyền hộ người
    khác** và **bàn giao việc duyệt của người khác**.

    Dùng nó để mở ngoại lệ, đừng dùng để cấp quyền: nó chỉ trả lời "người này có
    phải quản trị toàn hệ trên khóa đó không", còn hành động có được phép hay
    không vẫn do `require(...)` gác ở tầng controller.
    """
    for grant in profile.get("grants", []):
        perms = grant["perms"].get(entity)
        if perms and perms.get(action) and perms.get("scope", "all") == "all":
            return True
    return False


def scope_condition(model, entity: str, user, profile: dict, action: str = "read"):
    """ĐIỀU KIỆN phạm vi (chưa gắn vào query nào) = HỢP các grant có `action`.

    Ba giá trị trả về, phân biệt rõ:
      * `None` — thấy TẤT CẢ, không lọc gì;
      * `false()` — không grant nào cấp quyền này, không thấy gì;
      * điều kiện — phạm vi thật.

    Tách khỏi `apply_scope` để chỗ nào cần **OR thêm** một nguồn quyền khác còn
    ghép được. Chỗ đang cần: văn bản được chia sẻ đích danh cho một người — văn
    bản đó nằm NGOÀI phạm vi vai trò của họ, mà `apply_scope` thì chỉ biết thu
    hẹp, không biết mở thêm.
    """
    conds = []
    for g in profile.get("grants", []):
        p = g["perms"].get(entity)
        if not p or not p.get(action):
            continue
        scopeconf = g.get("scope") or {}
        rc = _role_scope_cond(model, entity, p.get("scope", "all"), user, profile, perms=p)
        # 'Phòng ban được xem' = CỘNG THÊM vào phạm vi vai trò.
        # rc None (scope=all) → đã thấy hết, bỏ qua để không thu hẹp nhầm.
        dept_add = _dept_include_cond(model, entity, scopeconf)
        base = or_(rc, dept_add) if (rc is not None and dept_add is not None) else rc
        ec = _explicit_cond(model, entity, scopeconf, profile)   # thu hẹp: company include + mọi loại trừ
        parts = [c for c in (base, ec) if c is not None]
        if not parts:
            return None           # grant này thấy tất cả → không lọc
        conds.append(and_(*parts))
    if not conds:
        return false()            # không grant nào cấp quyền này → không thấy gì
    return or_(*conds)


def apply_scope(query, model, entity: str, user, profile: dict, action: str = "read"):
    """Lọc query theo HỢP các grant có quyền `action` trên entity."""
    cond = scope_condition(model, entity, user, profile, action)
    return query if cond is None else query.filter(cond)


def get_scoped(db, model, entity: str, oid: int, user, profile: dict, action: str = "read"):
    """Lấy MỘT bản ghi, chỉ khi nó nằm trong phạm vi — trả `None` nếu không.

    Sinh ra cho các endpoint lấy/sửa/xóa một dòng: `db.get(Model, oid)` đi thẳng vào khóa
    chính nên bỏ qua sạch phần lọc phạm vi — danh sách giấu đúng, nhưng gõ thẳng id vào URL
    là ra. Nơi gọi cứ trả **404 "Không tìm thấy"** như với id không tồn tại: người ngoài
    phạm vi không cần biết bản ghi đó có thật hay không, và cũng không phải thêm mã lỗi mới.
    """
    cond = scope_condition(model, entity, user, profile, action)
    if cond is None:
        return db.get(model, oid)
    return db.query(model).filter(model.id == oid, cond).first()
