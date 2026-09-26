"""ĐỌC cây thư mục — dựng danh sách phẳng + số đếm + breadcrumb.

Mẫu: `help_center/service.get_tree` (client tự dựng cây từ danh sách phẳng
`parent_id`), và `search_articles` (gập dấu, đoạn trích). Khác biệt lớn nhất so
với help_center: số đếm văn bản trong mỗi thư mục phải lọc theo QUYỀN ĐỌC của
người xem (`document/access_service.visible_condition`) — "quyền thư mục KHÔNG
mở quyền văn bản" (luật phải giữ, `plan.md`).

ĐIỂM NỐI ACL (phase 04, duoc-CR-475): `_visible_levels()` gọi thẳng
`folder_access_service.effective_levels()` — MỘT điểm duy nhất mọi hàm public
ở tệp này đi qua (`tree`, `search_folders`), không có chỗ nào khác tự tính lại
"thấy thư mục nào". Luôn trả về một DICT CỤ THỂ (có thể rỗng) — không còn ca
`None`="thấy tất" của phase 03, vì từ nay mỗi người thấy một phần cây khác
nhau tùy phạm vi pháp nhân + ACL.

`my_level` (phase 06, duoc-CR-476): `tree()`/`search_folders()` trả kèm mức
hiệu lực của NGƯỜI GỌI trên từng nút — ô chọn thư mục ở màn tạo văn bản lọc
mức ≥ Đóng góp ở phía backend response, không đoán lại ở client (giữ đúng luật
"giao diện không tự tính quyền" của phase 04). Không thêm truy vấn nào: cùng
một `effective_levels()` mà `_filter_visible` đã phải gọi để biết thư mục nào
được thấy.
"""
import bisect

from sqlalchemy import false
from sqlalchemy.orm import Session

from .folder_constants import FOLDER_KIND_LABELS, FOLDER_STATUS_LABELS, FolderKind, FolderStatus
from .folder_model import DocFolder

SEARCH_LIMIT = 50


def _visible_levels(db: Session, user) -> dict[int, int]:
    from .folder_access_service import effective_levels
    return effective_levels(db, user)


def _company_names(db: Session, company_ids: set[int]) -> dict[int, str]:
    from app.modules.company.model import Company

    if not company_ids:
        return {}
    return dict(db.query(Company.id, Company.name).filter(Company.id.in_(company_ids)).all())


def _company_short_names(db: Session, company_ids: set[int]) -> dict[int, str]:
    """Tên gọi tắt (`Company.short_name`) — CHỈ dùng làm `display_name` của
    thư mục PHÁP NHÂN trên cây (yêu cầu giao diện kiểu VS Code, 23/09/2026).
    Công ty chưa khai gọi tắt thì không có mặt trong dict — `_display_label_of`
    tự lùi về tên đầy đủ, không coi chuỗi rỗng là một giá trị."""
    from app.modules.company.model import Company

    if not company_ids:
        return {}
    rows = db.query(Company.id, Company.short_name).filter(Company.id.in_(company_ids)).all()
    return {cid: short_name for cid, short_name in rows if short_name}


def _label_of(folder: DocFolder, company_names: dict[int, str]) -> str:
    return folder.name or company_names.get(folder.company_id, "")


def _display_label_of(
    folder: DocFolder, company_names: dict[int, str], company_short_names: dict[int, str],
) -> str:
    """Tên NGẮN để vẽ trên cây — thư mục pháp nhân ưu tiên `short_name`
    ("DEGO Holding" thay vì "CÔNG TY TNHH ...", đỡ tràn khung 200-480px);
    thư mục thường không có khái niệm tên gọi tắt nên luôn trùng `name`.
    Không lưu cột riêng: tính lại mỗi lần đọc, cùng lối với `_label_of`."""
    #  Tên đặt tay (kể cả thư mục pháp nhân đã đổi tên, mở 24/09/2026) luôn thắng.
    if folder.name or folder.kind != int(FolderKind.COMPANY):
        return folder.name
    return company_short_names.get(folder.company_id) or company_names.get(folder.company_id, "")


def _filter_visible(query, levels: dict[int, int], *, include_archived: bool):
    if not include_archived:
        query = query.filter(DocFolder.status == int(FolderStatus.ACTIVE))
    visible_ids = set(levels.keys())
    return query.filter(DocFolder.id.in_(visible_ids) if visible_ids else false())


def _document_counts(db: Session, user, folders: list[DocFolder]) -> tuple[dict[int, int], dict[int, int]]:
    """`(đếm TRỰC TIẾP, đếm CẢ NHÁNH đã khử trùng)` — đúng HAI truy vấn cho cả
    trang: một cho danh sách thư mục (do nơi gọi làm), một cho cặp
    `(folder_id, document_id)` ở đây.
    """
    if not folders:
        return {}, {}
    from app.core.auth import get_perm_profile
    from app.modules.document import access_service
    from app.modules.document.model import Document

    from .folder_link_model import DocumentFolderLink

    folder_ids = [f.id for f in folders]
    profile = get_perm_profile(db, user)
    visible = access_service.visible_condition(user, profile)
    q = (
        db.query(DocumentFolderLink.folder_id, DocumentFolderLink.document_id)
        .join(Document, Document.id == DocumentFolderLink.document_id)
        .filter(DocumentFolderLink.folder_id.in_(folder_ids))
    )
    if visible is not None:
        q = q.filter(visible)

    direct: dict[int, int] = {}
    doc_ids_by_folder: dict[int, set[int]] = {}
    for folder_id, document_id in q.all():
        direct[folder_id] = direct.get(folder_id, 0) + 1
        doc_ids_by_folder.setdefault(folder_id, set()).add(document_id)

    #  Cả nhánh, khử trùng: hợp tập id văn bản của mọi thư mục có `path` bắt
    #  đầu bằng `path` của thư mục đang xét — tính trong Python, không thêm
    #  truy vấn nào nữa.
    #
    #  ⚠️ O(n log n), không phải O(n²) (M1, rà soát 23/09/2026) — sắp thư mục
    #  theo `path` rồi NHỊ PHÂN tìm dải hậu duệ LIÊN TỤC thay vì so từng cặp
    #  (folder, folder). Đúng tính chất của materialized path: với một tiền
    #  tố P bất kỳ, MỌI chuỗi bắt đầu bằng P luôn nằm THÀNH MỘT DẢI LIÊN TỤC
    #  trong danh sách đã sắp theo thứ tự từ điển — chặn trên bằng `P + "￿"`
    #  (ký tự cao hơn mọi ký tự `path` thật dùng, chỉ gồm chữ số và `/`).
    #  Cây 6 cấp × hàng trăm thư mục thì khác biệt không lớn, nhưng thuật toán
    #  đúng cấp thì không phải lo lại lúc dữ liệu phình.
    ordered = sorted(folders, key=lambda f: f.path)
    paths = [f.path for f in ordered]
    branch: dict[int, int] = {}
    for f in folders:
        lo = bisect.bisect_left(paths, f.path)
        hi = bisect.bisect_left(paths, f.path + "￿")
        ids: set[int] = set()
        for other in ordered[lo:hi]:
            ids |= doc_ids_by_folder.get(other.id, set())
        branch[f.id] = len(ids)
    return direct, branch


def _creator_names(db: Session, user_ids: set[int]) -> dict[int, str]:
    """Tên người tạo thư mục — MỘT truy vấn cho cả cây, không truy vấn trong vòng lặp."""
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    ids = {uid for uid in user_ids if uid}
    if not ids:
        return {}
    rows = (db.query(User.id, Employee.full_name)
            .outerjoin(Employee, Employee.id == User.employee_id)
            .filter(User.id.in_(ids)).all())
    return {uid: name or "" for uid, name in rows}


def _node(f: DocFolder, company_names: dict[int, str], company_short_names: dict[int, str],
          direct: dict[int, int], branch: dict[int, int], levels: dict[int, int],
          creators: dict[int, str] | None = None) -> dict:
    return {
        "id": f.id,
        "company_id": f.company_id,
        "parent_id": f.parent_id,
        "kind": f.kind,
        "kind_label": FOLDER_KIND_LABELS.get(f.kind, ""),
        "name": _label_of(f, company_names),
        #  Tên NGẮN cho giao diện cây (VS Code Explorer, 23/09/2026) — `name`
        #  giữ nguyên tên PHÁP LÝ đầy đủ cho tooltip/bản in, không đổi ý nghĩa.
        "display_name": _display_label_of(f, company_names, company_short_names),
        "code": f.code,
        "path": f.path,
        "depth": f.depth,
        "sort_order": f.sort_order,
        "status": f.status,
        "status_label": FOLDER_STATUS_LABELS.get(f.status, ""),
        "document_count": direct.get(f.id, 0),
        "document_count_branch": branch.get(f.id, 0),
        #  Mức hiệu lực của NGƯỜI GỌI trên đúng nút này (`0` không xảy ra ở
        #  đây — không thấy thì `_filter_visible` đã loại khỏi `folders`).
        "my_level": levels.get(f.id, 0),
        #  Cột «Người tạo» / «Ngày tạo» của dòng thư mục trong danh sách (25/09/2026).
        #  `created_by = 0` = hệ thống tự dựng (thư mục pháp nhân, nhóm «Công ty»).
        "created_at": f.created_at,
        "created_by_name": (creators or {}).get(f.created_by or 0, "") if f.created_by else "Hệ thống",
    }


def tree(db: Session, user, *, include_archived: bool = False) -> list[dict]:
    """Danh sách PHẲNG — client tự dựng cây theo `parent_id`, cùng lối
    `help_center.get_tree`."""
    levels = _visible_levels(db, user)
    query = _filter_visible(db.query(DocFolder), levels, include_archived=include_archived)
    folders = query.order_by(DocFolder.depth.asc(), DocFolder.sort_order.asc(),
                             DocFolder.id.asc()).all()

    company_ids = {f.company_id for f in folders}
    company_names = _company_names(db, company_ids)
    company_short_names = _company_short_names(db, company_ids)
    direct, branch = _document_counts(db, user, folders)
    creators = _creator_names(db, {f.created_by for f in folders})
    return [_node(f, company_names, company_short_names, direct, branch, levels, creators)
            for f in folders]


def breadcrumb_map(db: Session, folder_ids: set[int]) -> dict[int, list[dict]]:
    """`{folder_id: [{id, name}, ...]}` từ gốc tới thư mục — MỘT lượt cho cả trang."""
    if not folder_ids:
        return {}
    folders = {f.id: f for f in db.query(DocFolder).filter(DocFolder.id.in_(folder_ids)).all()}

    needed_ids: set[int] = set()
    for f in folders.values():
        needed_ids |= {int(p) for p in (f.path or "").strip("/").split("/") if p}
    all_nodes = {f.id: f for f in db.query(DocFolder).filter(DocFolder.id.in_(needed_ids)).all()}
    company_names = _company_names(
        db, {f.company_id for f in all_nodes.values() if f.kind == int(FolderKind.COMPANY)})

    result: dict[int, list[dict]] = {}
    for fid in folder_ids:
        f = folders.get(fid)
        if not f or not f.path:
            result[fid] = []
            continue
        chain_ids = [int(p) for p in f.path.strip("/").split("/") if p]
        result[fid] = [
            {"id": node.id, "name": _label_of(node, company_names)}
            for cid in chain_ids if (node := all_nodes.get(cid))
        ]
    return result


def get_detail(db: Session, folder: DocFolder, user) -> dict:
    """Chi tiết MỘT thư mục, kèm breadcrumb + `my_level`/`effective_access`
    (phase 04, gắn ở `folder_access_view_service.annotate_detail`)."""
    from . import folder_access_view_service

    company_names = _company_names(db, {folder.company_id})
    company_short_names = _company_short_names(db, {folder.company_id})
    #  Đếm CẢ NHÁNH phải có mặt thư mục con — chỉ đưa `[folder]` thì
    #  `document_count_branch` = số trực tiếp, và tiêu đề thư mục gốc «Công ty»
    #  ghi «0 văn bản» trong khi bảng (mặc định «Gồm thư mục con») liệt kê 7
    #  (lỗi người dùng chụp 24/09/2026). Cùng bộ lọc thấy/lưu trữ với `tree()`.
    branch_folders = _filter_visible(
        db.query(DocFolder).filter(DocFolder.path.like(f"{folder.path}%")),
        _visible_levels(db, user), include_archived=False,
    ).all() if folder.path else []
    if folder not in branch_folders:
        branch_folders.append(folder)
    direct, branch = _document_counts(db, user, branch_folders)
    crumbs = breadcrumb_map(db, {folder.id})
    #  `_node` cần một dict — `annotate_detail` ngay dưới đây tính LẠI đúng
    #  giá trị qua `my_level()` (bảo toàn hành vi cũ, kể cả `0` khi tới đây
    #  bằng đường nội bộ khác `get_folder_or_404` + `ensure_level`), nên tạm
    #  truyền dict rỗng ở đây là an toàn — không có ai đọc giá trị tạm này.
    node = _node(folder, company_names, company_short_names, direct, branch, {},
                 _creator_names(db, {folder.created_by}))
    node["description"] = folder.description
    node["breadcrumb"] = crumbs.get(folder.id, [])
    #  Hộp «Chia sẻ» kiểu Drive cần đọc ĐÚNG mức mặc định đang khai để hiện sẵn
    #  trong ô chọn «Quyền chung» (rà UI 23/09/2026 — trước nay cột này chỉ
    #  NHẬN qua `FolderUpdate`, chưa từng có mặt trong response nào, nên ô chọn
    #  luôn hiện placeholder dù đã có giá trị). Chỉ thêm ở CHI TIẾT — `tree()`
    #  không cần, giữ nguyên hình dạng cũ để không phình response của MỌI nút.
    node["default_access"] = folder.default_access
    return folder_access_view_service.annotate_detail(db, user, folder, node)


def _search_rank(folded_label: str, folded_kw: str, depth: int) -> tuple[int, int, int]:
    """Khóa sắp kết quả tìm: trùng hẳn tên → tên BẮT ĐẦU bằng từ khóa → chứa
    ở giữa; cùng hạng thì thư mục nông (gần gốc) trước, tên ngắn trước. Không
    sắp thì trần `SEARCH_LIMIT` cắt theo thứ tự DB trả về — thư mục trùng
    đúng tên có thể bị cắt mất trong khi 50 thư mục chỉ chứa từ khóa lọt vào."""
    if folded_label == folded_kw:
        tier = 0
    elif folded_label.startswith(folded_kw):
        tier = 1
    else:
        tier = 2
    return tier, depth, len(folded_label)


def search_folders(db: Session, user, keyword: str) -> list[dict]:
    """Tìm theo TÊN, gập dấu — trần `SEARCH_LIMIT`, trả kèm đường dẫn đầy đủ.

    Tối ưu 26/09/2026: nạp cả bảng thư mục ĐÚNG MỘT lần và dùng lại cho cả ba
    việc — tính quyền (`effective_levels(folders=...)`), khớp tên, dựng
    breadcrumb. Bản cũ nạp cả bảng trong `effective_levels`, rồi hỏi lại
    `IN (mọi id thấy được)`, rồi `breadcrumb_map` hỏi thêm hai lượt nữa — cây
    100 cấp thì 50 kết quả kéo theo tới 5000 id tổ tiên trong một câu `IN`.
    Breadcrumb giữ đúng hành vi cũ: đủ tổ tiên kể cả nút người gọi không thấy.
    """
    from .folder_access_service import effective_levels
    from .folder_naming import fold

    kw = (keyword or "").strip()
    if not kw:
        return []

    all_folders = db.query(DocFolder).all()
    levels = effective_levels(db, user, folders=all_folders)
    by_id = {f.id: f for f in all_folders}
    company_names = _company_names(
        db, {f.company_id for f in all_folders if f.kind == int(FolderKind.COMPANY)})

    folded_kw = fold(kw)
    scored = []
    for f in all_folders:
        if f.id not in levels or f.status != int(FolderStatus.ACTIVE):
            continue
        folded_label = fold(_label_of(f, company_names))
        if folded_kw in folded_label:
            scored.append((_search_rank(folded_label, folded_kw, f.depth), f))
    scored.sort(key=lambda item: item[0])

    results = []
    for _, f in scored[:SEARCH_LIMIT]:
        label = _label_of(f, company_names)
        path_crumbs = [
            {"id": node.id, "name": _label_of(node, company_names)}
            for part in (f.path or "").strip("/").split("/")
            if part and (node := by_id.get(int(part)))
        ]
        results.append({
            "id": f.id,
            "name": label,
            "company_id": f.company_id,
            "path_display": " / ".join(c["name"] for c in path_crumbs) or label,
            "breadcrumb": path_crumbs,
            #  Mức hiệu lực của người gọi — ô chọn thư mục lọc ≥ Đóng góp
            #  ngay trên kết quả tìm, không riêng trên `/tree` (phase 06).
            "my_level": levels.get(f.id, 0),
        })
    return results
