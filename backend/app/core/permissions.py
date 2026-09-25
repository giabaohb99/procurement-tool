"""Danh sách quyền dùng chung (nguồn chân lý duy nhất).

Quyền = ENTITY (đối tượng) x ACTION (hành động). Seed & kiểm tra đều dựa vào đây.
"""

ENTITIES = [
    "company", "department", "employee", "user", "role",
    "warehouse", "unit", "item_group", "brand",
    "supplier", "product", "contract",
    "purchase_request", "survey", "purchase_order", "goods_receipt",
    "inventory", "payable", "payment", "payment_request",
    "report", "setting", "category_assignee", "survey_request", "import", "backup",
    "help_article", "ticket", "mailbox",
    # Phân hệ Văn thư
    #  ⚠️ MỘT KHÓA = MỘT MÀN HÌNH. Trước 25/08/2026 bốn màn danh mục (Loại văn
    #  bản · Thư viện mẫu · Quy tắc đánh số · Quy tắc quan hệ) dùng CHUNG khóa
    #  `doc_type`, nên cho ai sửa quy tắc đánh số là cho họ sửa luôn loại văn
    #  bản — ba việc do ba người khác nhau làm mà không tách được (CR-157).
    "doc_type", "doc_template", "doc_numbering_rule", "doc_link_rule",
    "external_party", "document_book", "document", "security_level",
    #  Cây thư mục văn bản (phase 03, duoc-CR-475). Phạm vi dữ liệu THẬT (theo
    #  pháp nhân + ACL thư mục) chưa xong ở phase này — nằm ở
    #  `doc_catalog/folder_tree_service._visible_folder_ids`, sẽ thay bằng
    #  `folder_access_service` ở phase 04. Khóa này CHỈ gác "có được đụng vào
    #  màn Quản lý cây thư mục không", cùng vai trò với các khóa Văn thư khác.
    "doc_folder",
    # Phân hệ Duyệt dấu
    "seal_request", "seal_type",
    # Phân hệ Đặt xe
    "vehicle_booking", "vehicle", "driver",
    # Bộ máy phê duyệt dùng chung — KHÔNG thuộc phân hệ nào, mọi loại chứng từ
    # đều chạy qua nó.
    "approval_flow",
    # Trợ lý AI — cổng bật/tắt theo vai trò (chỉ ban lãnh đạo). Không có bảng
    # dữ liệu để lọc theo dòng nên khai PUBLIC ở scoping.
    "assistant",
    # Diễn đàn nội bộ — entity này chỉ dành cho vai trò `forum_admin` (ẩn/xóa
    # bài người khác, QĐ-D1). Người dùng thường KHÔNG cần grant: đăng/đọc đi
    # theo luật audience riêng trong API diễn đàn, giống comment CR-033.
    "forum_post",
    # F13a: cấu trúc chuyên mục (nhóm/box kiểu VOZ) — cũng chỉ của `forum_admin`.
    # Tách khỏi `forum_post` để "quyền dựng box" gán được riêng với "quyền ẩn bài".
    "forum_board",
    # Phân hệ Công việc (CR-216) — MỘT khóa cho cả phân hệ, cố ý không tách
    # `work_list` riêng: mọi quyền thật nằm ở tầng THÀNH VIÊN (bảng
    # `tab_work_list_member`), tách hai khóa chỉ đẻ thêm ô ma trận không ai hiểu.
    # Tên có tiền tố `work_` vì chữ "task" trần đã bị chiếm hai chỗ: task của bộ
    # máy duyệt và `/api/dashboard/tasks` (Việc cần làm). Xem
    # `doc/erp/cong-viec/04-phan-quyen.md` §1.
    "work_task",
    # Phân hệ Nghỉ phép (CR-259). Bốn khóa vì bốn màn hình do BA nhóm người
    # khác nhau dùng, và gộp lại thì không tách được:
    #  · `leave_request` — nhân viên nộp đơn, trưởng phòng duyệt;
    #  · `leave_balance` — Nhân sự cấp phát và chỉnh quỹ (cho quyền này là cho
    #    quyền tặng thêm ngày phép, không thể chung khóa với việc nộp đơn);
    #  · `leave_type`    — cấu hình luật nghỉ (V1-6), việc của quản trị;
    #  · `holiday`       — lịch ngày lễ, cũng của quản trị nhưng đổi theo năm
    #    nên thường giao cho hành chính, tách khỏi `leave_type`.
    "leave_request", "leave_balance", "leave_type", "holiday",
    # Phân hệ Đặt phòng họp (duoc-CR-279). Hai khóa vì hai nhóm người:
    #  · `room_booking` — ai cũng đặt được, trưởng bộ phận/hành chính duyệt;
    #  · `meeting_room` — khai danh mục phòng, việc quản trị. Cho quyền sửa danh
    #    mục KHÁC cho quyền đặt phòng, gộp một khóa là không tách được.
    "room_booking", "meeting_room",
    # Hồ sơ nhân sự mở rộng (08/09/2026) — nhóm trường NHẠY CẢM: ngày sinh, MST,
    # địa chỉ nhà, tài khoản ngân hàng, CCCD, số BHXH, và hai bảng người thân.
    #
    # Vì sao là khóa RIÊNG chứ không phải một action của `employee`: `employee.read`
    # là quyền đang có của gần như mọi vai trò — cần nó để đổ ô chọn người trong
    # form. Nhét nhóm nhạy cảm vào đó là mọi người trong công ty đọc được số tài
    # khoản ngân hàng của nhau. Cùng lý lẽ đã tách `leave_balance` khỏi
    # `leave_request`.
    #
    # ⚠️ Không có bảng nào để lọc — đây là cổng `require()` thuần, phạm vi dữ
    # liệu vẫn do khóa `employee` quyết định. Nên khai PUBLIC ở `scoping.py`.
    # ⚠️ Hai bảng con (`tab_employee_contact`, `tab_employee_family`) CỐ Ý KHÔNG
    # có khóa riêng — chúng không có màn hình riêng, và phạm vi của chúng là
    # phạm vi của hồ sơ cha. Xem `modules/employee/sensitive.py`.
    "employee_sensitive",
    # Danh mục CHỨC VỤ (duoc-CR-320) — nguồn của ô chọn «Vị trí / Chức vụ».
    #
    # Khóa riêng theo luật «một khóa = một màn hình» (CR-157), và vì hai việc do
    # hai người làm: ai cũng cần `employee.read` để đổ ô chọn người, nhưng THÊM
    # BỚT chức vụ là việc của Nhân sự — gộp vào `employee.write` thì hành chính
    # sửa số điện thoại một hồ sơ cũng dựng thêm được chức vụ mới.
    "job_position",
    # Danh mục LOẠI HỒ SƠ (phân hệ Hồ sơ, 16/09/2026) — nguồn của ô chọn «Loại
    # hồ sơ» và là chỗ khai hạn hiệu lực mặc định của từng loại giấy tờ.
    #
    # Khóa riêng theo luật «một khóa = một màn hình» (CR-157): nó có màn quản lý
    # riêng `/dossier/types`. Đừng gộp với khóa `dossier` của bảng hồ sơ (chưa
    # dựng) — đọc hồ sơ là việc hằng ngày của nhiều người, còn thêm bớt LOẠI là
    # đổi luật phân loại cho cả công ty.
    "dossier_type",
    # HỒ SƠ (`tab_dossier`, 16/09/2026) — bộ giấy tờ công ty đang giữ.
    #
    # Tách khỏi `dossier_type` theo luật «một khóa = một màn hình» (CR-157), và
    # vì hai việc do hai người làm: lập hồ sơ là việc hằng ngày của hành chính
    # mỗi phòng, còn thêm bớt LOẠI là đổi luật phân loại — và đổi luôn KHUÔN
    # BIỂU MẪU (`field_schema`) cho cả công ty. Gộp một khóa thì ai lập được một
    # tờ giấy phép cũng xóa được ô «Số giấy phép» khỏi mọi hồ sơ cùng loại.
    #
    # ⚠️ Khai CỘT THẬT ở `SCOPE_FIELDS`, không PUBLIC: hồ sơ thuộc về một phòng
    # và một người, khác hẳn danh mục loại.
    "dossier",
    # Phân hệ Điểm cà phê × POS365 (doc/erp/diem-ca-phe/04-phan-quyen.md). Bốn
    # khóa vì ba quyền của PS12 phải TÁCH được: xem sổ người khác
    # (`coffee_ledger.read` + scope rộng) · điều chỉnh tay (`coffee_ledger.write`)
    # · chạy đồng bộ (`pos_order.write`). Ví của tôi KHÔNG cần grant — đi endpoint
    # riêng `/api/coffee/my-wallet` chỉ đòi đăng nhập. Nhật ký đồng bộ đọc/ghi
    # qua quyền của `pos_order` (cùng mối quan tâm vận hành, không thêm khóa thứ 5).
    "coffee_policy", "coffee_member", "coffee_ledger", "pos_order",
    # Phiên đăng nhập (bao-CR-395 / CR-312 P3b, doc nhat-ky-va-phien-dang-nhap §8.5).
    # MỘT khóa cho cả ba màn: `/system/sessions` (admin, scope all + delete) ·
    # tab «Tài khoản & thiết bị» trong hồ sơ nhân sự (HR, read all) · tab «Thiết bị
    # của tôi» ở `/me`. ⚠️ Riêng «của tôi» đi endpoint `/api/auth/sessions` CHỈ đòi
    # đăng nhập, KHÔNG đòi khóa này — hệ đang chạy thì vai trò cũ không tự có khóa
    # mới (D-018), mà ai cũng phải đá được thiết bị lạ của chính mình.
    "login_session",
    # Nhật ký hệ thống (bao-CR-407 / CR-312 P5, doc nhat-ky-va-phien-dang-nhap §7).
    # HAI khóa chứ không một, vì đó là hai câu hỏi khác hẳn nhau về mức nhạy cảm:
    #   `audit`      = tra TOÀN HỆ ai làm gì lúc nào (màn `/system/logs`, dòng
    #                  thời gian gộp) — vẫn chỉ là câu tiếng Việt tóm tắt.
    #   `change_log` = xem GIÁ TRỊ TRƯỚC/SAU của từng ô, thân yêu cầu, chi tiết
    #                  lỗi. Giá trị cũ có thể chứa TÊN NHÀ CUNG CẤP — đúng thứ cả
    #                  cơ chế phương án dựng ra để giấu với người yêu cầu. Gộp
    #                  chung một khóa là ai tra được nhật ký cũng đọc được nó.
    # ⚠️ Xem dòng thời gian của CHÍNH một phiếu thì vẫn đi bằng quyền `read` của
    # phiếu đó, không đòi hai khóa này (D-018: hệ đang chạy, vai trò cũ không tự có).
    "audit", "change_log",
    # Sổ đồng bộ với hệ ngoài (P0 đồng bộ app đặt xe, doc dong-bo-dat-xe-duyet-dau §3.3).
    # MỘT khóa cho MỌI nguồn (app đặt xe, POS365, đơn hàng...) vì chỉ có một màn:
    # `/system/sync-logs`. `write` KHÔNG phải quyền sửa dòng sổ — sổ không sửa được —
    # mà là nút «Chạy lại», tức gọi lại sang hệ ngoài.
    # ⚠️ Nhật ký đồng bộ RIÊNG của POS365 (`/api/coffee/sync/runs`) vẫn đi bằng
    # `pos_order.read` như cũ dù nay đọc chung một bảng.
    "sync_log",
    "purchase_cost_type",   # bao-CR-453 — danh mục Loại chi phí thu mua
    # Tra cứu giá hải quan (bao-CR-470, doc/erp/hai-quan). MỘT khóa cho cả màn tra cứu:
    # read = xem danh sách + biểu đồ · write = nạp tệp GTT02 · delete = hoàn tác lô.
    # Không vai trò nào tự có — đại ca tick tay trên màn Phân quyền (xem `_SYS_ENTITIES`).
    "customs_price",
    # Danh mục hóa chất theo văn bản của phân hệ hải quan (bao-CR-470, HQ6): NĐ 24/2026
    # PL I–IV (có ngưỡng kg), hoạt chất cấm TT 75/2025, hóa chất phải công bố TT 01/2026.
    # Khóa RIÊNG vì là màn riêng và `write` = sửa ngưỡng pháp lý (một khóa = một màn, CR-157).
    "customs_regulation",
    # Việc của bot Agent Hub (ai-CR-036) — màn `/system/agent-tasks`: danh sách việc Đậu Đậu
    # đã nhận, lịch sử từng bước, chi phí model. Chỉ ĐỌC: mọi thao tác trên việc vẫn đi qua
    # Telegram. Quản trị hệ thống, không phải thu mua (nằm trong `_SYS_ENTITIES` của seed).
    "agent_task",
]

ACTIONS = ["read", "create", "write", "delete", "approve", "cancel", "print", "export"]

# Nhãn tiếng Việt để hiển thị ở màn cấu hình phân quyền
ENTITY_LABELS = {
    "company": "Công ty (pháp nhân)",
    "department": "Phòng ban",
    "employee": "Nhân viên",
    "employee_sensitive": "Nhân viên — thông tin nhạy cảm (CCCD, ngân hàng, địa chỉ)",
    "job_position": "Danh mục Chức vụ",
    "dossier_type": "Danh mục Loại hồ sơ",
    "dossier": "Hồ sơ (giấy tờ công ty)",
    "user": "Tài khoản",
    "role": "Vai trò & phân quyền",
    "warehouse": "Kho",
    "unit": "Đơn vị tính",
    "item_group": "Phân loại VTBB/NL",
    "brand": "Thương hiệu / Bộ phận",
    "supplier": "Nhà cung cấp",
    "product": "Sản phẩm / Hàng hóa",
    "contract": "Hợp đồng",
    "purchase_request": "Yêu cầu mua hàng",
    "survey": "Khảo sát",
    "purchase_order": "Đơn mua hàng",
    "goods_receipt": "Nhận hàng (GR)",
    "inventory": "Kho / Tồn",
    "payable": "Công nợ",
    "payment": "Thanh toán",
    "payment_request": "Yêu cầu thanh toán",
    "report": "Báo cáo",
    "setting": "Cấu hình hệ thống",
    "category_assignee": "Phân công phụ trách (theo phân loại)",
    "survey_request": "Yêu cầu báo giá",
    "import": "Nhập dữ liệu (Import)",
    "backup": "Sao lưu CSDL",
    "help_article": "Hướng dẫn sử dụng (Help Center)",
    "ticket": "Phiếu hỗ trợ",
    #  Ai được KHAI hộp thư gửi và cấp cho người khác dùng. Khác hẳn quyền
    #  *dùng* một hộp thư — cái đó khai đích danh ở `tab_mailbox_member`.
    "mailbox": "Hộp thư gửi (gửi danh nghĩa địa chỉ khác)",
    #  Nhãn đi theo ĐƯỜNG MENU chứ không theo tên bảng: người khai quyền tìm
    #  theo thứ họ bấm trên màn hình, không theo thứ lập trình viên đặt tên.
    "doc_type": "Văn thư › Thiết lập › Loại văn bản",
    "doc_template": "Văn thư › Thiết lập › Thư viện văn bản mẫu",
    "doc_numbering_rule": "Văn thư › Quy tắc đánh số",
    "doc_link_rule": "Văn thư › Quy tắc quan hệ",
    "external_party": "Văn thư › Thiết lập › Đơn vị gửi nhận",
    "security_level": "Văn thư › Thiết lập › Mức mật / Độ khẩn",
    "document_book": "Văn thư › Sổ văn bản",
    "document": "Văn thư › Văn bản",
    "doc_folder": "Văn thư › Cây thư mục",
    "seal_request": "Yêu cầu duyệt dấu",
    "seal_type": "Loại con dấu",
    "vehicle_booking": "Yêu cầu đặt xe",
    "vehicle": "Phương tiện (Xe)",
    "driver": "Tài xế",
    "approval_flow": "Luồng phê duyệt (dùng chung)",
    "assistant": "Trợ lý AI",
    "forum_post": "Diễn đàn › Kiểm duyệt bài viết",
    "forum_board": "Diễn đàn › Quản trị chuyên mục (box)",
    "work_task": "Công việc (task list, kanban)",
    "leave_request": "Nghỉ phép › Đơn nghỉ phép",
    "leave_balance": "Nghỉ phép › Quỹ phép năm",
    "leave_type": "Nghỉ phép › Thiết lập › Loại nghỉ",
    "holiday": "Nghỉ phép › Thiết lập › Lịch ngày lễ",
    "room_booking": "Phiếu đặt phòng họp",
    "meeting_room": "Phòng họp (danh mục)",
    "coffee_policy": "Điểm cà phê › Chính sách cấp điểm",
    "coffee_member": "Điểm cà phê › Thành viên & ghép POS365",
    "coffee_ledger": "Điểm cà phê › Sổ điểm & điều chỉnh",
    "pos_order": "Điểm cà phê › Đơn POS365 & đồng bộ",
    "login_session": "Phiên đăng nhập",
    "audit": "Nhật ký hệ thống (tra toàn hệ)",
    "change_log": "Nhật ký hệ thống › Giá trị trước/sau",
    "sync_log": "Sổ đồng bộ với hệ ngoài",
    "customs_price": "Tra cứu giá hải quan",
    "customs_regulation": "Danh mục hóa chất theo văn bản (hải quan)",
    "purchase_cost_type": "Danh mục Loại chi phí thu mua",
    "agent_task": "Trợ lý Telegram › Việc của bot",
}

ACTION_LABELS = {
    "read": "Xem", "create": "Tạo", "write": "Sửa", "delete": "Xóa",
    "approve": "Duyệt", "cancel": "Hủy", "print": "In", "export": "Xuất",
}

# Phạm vi theo cấp bậc (tương đối với công ty/phòng ban của chính user)
# "assigned" (Được giao) = của mình HOẶC được phân bổ cho mình — dùng cho nhân viên thu mua trên PYC.
# "dept_proc" (bao-CR-414, phòng ban tự mua hàng) = `proc` NHƯNG chỉ trong phòng mình: phiếu đã
# duyệt mà phòng lập phiếu HOẶC phòng được nhờ xử lý (`handler_dept_id`) là một trong các phòng
# của người xem. Dùng cho người quản lý thu mua của một phòng tự mua (nhà máy).
SCOPES = ["own", "assigned", "proc", "dept_proc", "dept", "company", "all"]
SCOPE_LABELS = {
    #  bao-CR-428: nhãn hai bậc `proc`/`dept_proc` viết TỔNG QUÁT (không gắn chữ "Thu mua"),
    #  vì cùng một bậc cấp được cho bất kỳ khóa nào có trạng thái duyệt.
    "own": "Của mình", "assigned": "Được giao", "proc": "Được giao + đã duyệt",
    "dept_proc": "Được giao + đã duyệt trong phòng",
    "dept": "Phòng ban", "company": "Công ty", "all": "Tất cả",
}
SCOPE_RANK = {"own": 0, "assigned": 1, "proc": 1, "dept_proc": 1, "dept": 2, "company": 3, "all": 4}
