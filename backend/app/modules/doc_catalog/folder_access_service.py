"""QUYỀN HIỆU LỰC trên từng thư mục — điểm nối DUY NHẤT mà mọi nơi khác phải
đi qua (`folder_tree_service._visible_folder_ids`, gắn/gỡ văn bản, CRUD thư
mục). Không có chỗ nào khác được tự tính lại "thấy thư mục nào" — lệch ở đây
là lệch giữa cây / tìm kiếm / chi tiết (`plan.md` phase 04 §"Rủi ro").

Luật (đúng thứ tự, xem bảng đầy đủ ở
`frontend-v2/plans/260923-1000-van-ban-thu-muc-nguoi-duyet/phase-04-phan-quyen-thu-muc.md`):

1. **Mức NỀN** — nếu quyền `document.read` của người này "với tới" pháp nhân
   của thư mục (chốt 3: scope `all`, scope hẹp hơn nhưng CÙNG pháp nhân, hoặc
   được include đích danh pháp nhân đó) thì lấy `default_access` của thư mục
   TỔ TIÊN gần nhất có khai (đi từ gốc xuống, `NULL` = chưa khai = kế thừa).
2. **CỘNG ACL cho** của thư mục VÀ tổ tiên (kế thừa xuống), lấy mức cao nhất,
   HỢP với mức nền ở bước 1 (lấy `max`) — nên dù không với tới pháp nhân, một
   dòng CHO đích danh vẫn mở được thư mục cụ thể đó (chia sẻ xuyên pháp nhân).
3. **ACL cấm** của thư mục hoặc tổ tiên khớp người này → không thấy, CẤM
   THẮNG mọi nguồn ở bước 1-2.
4. Vai trò có `doc_folder.write` với tới pháp nhân đó → luôn **Quản lý**,
   KỂ CẢ bị cấm ở bước 3 (quản trị văn thư phải luôn gỡ được quyền sai).

Hai truy vấn SQL CỐ ĐỊNH cho MỌI kích cỡ cây (không N+1): toàn bộ `tab_doc_folder`
+ toàn bộ `tab_doc_folder_access` khớp chủ thể của người gọi. Phần "pháp nhân
tôi với tới" tính thẳng từ `profile` (đã có sẵn từ `get_perm_profile`, không
cần hỏi DB thêm) — nên tổng chi phí vẫn là hằng số theo số thư mục/dòng ACL,
đúng tinh thần "3 truy vấn cố định" của đặc tả dù đếm câu SQL thực ra là 2.

⚠️ KHÔNG cache `effective_levels()` xuyên request (khác `get_perm_profile`,
cache 60s) — quyền đổi (cấp/thu/sửa `default_access`) phải có hiệu lực ngay
lượt gọi kế tiếp, không đợi cache hết hạn (`plan.md` §"Rủi ro").
"""
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile
from app.core.subject_match import EFFECT_DENY, subject_match_condition, still_live_condition

from .folder_access_model import DocFolderAccess
from .folder_constants import FOLDER_ACCESS_LEVEL_LABELS, FolderAccessLevel, FolderKind
from .folder_model import DocFolder

ENTITY_DOCUMENT = "document"
ENTITY_FOLDER_ADMIN = "doc_folder"


def _int_or_none(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def company_reach(profile: dict, entity: str, action: str = "read") -> set[int] | None:
    """Tập id PHÁP NHÂN mà quyền `<entity>.<action>` của người này "với tới" —
    quyết định NHÁNH pháp nhân nào hiện trên cây, KHÔNG phải văn bản nào đọc
    được (đó vẫn là việc của `document/access_service.visible_condition`).

    CÔNG KHAI (không còn `_` đầu tên, rà soát 23/09/2026 — M3): dùng lại ở
    `document/approval_preview_controller.py` để chặn `company_id` ngoài
    phạm vi `document.create` của người xem trước luồng duyệt, không riêng gì
    thư mục.

    `None` = với tới MỌI pháp nhân. Đúng "chốt 3" của đặc tả — ba nguồn CỘNG
    (OR) nhau cho mỗi grant có `action` trên `entity`:
      * scope `all` (không bị ô "Chỉ trong công ty" thu hẹp) → mọi pháp nhân;
      * scope hẹp hơn (own/dept/dept_proc/proc/company)      → pháp nhân CHÍNH
        của người này (`profile.company_id`) — mọi bậc hẹp hơn `all` đều không
        vượt ra khỏi pháp nhân mình;
      * ô "Chỉ trong công ty" (include, bất kể bậc)           → CỘNG THÊM đúng
        những pháp nhân đó — cách một admin mở quyền nhìn sang pháp nhân khác.
    "Loại trừ" (exclude) trừ khỏi tập, nhất quán với việc loại trừ vốn đã khóa
    hẳn văn bản của pháp nhân đó ở `core/scoping._explicit_cond`.
    """
    own_company = profile.get("company_id") or 0
    reach: set[int] = set()
    for grant in profile.get("grants", []):
        perms = grant["perms"].get(entity)
        if not perms or not perms.get(action):
            continue
        scope = perms.get("scope", "own")
        scopeconf = grant.get("scope") or {}
        inc = {v for raw in (scopeconf.get("inc") or {}).get("company") or []
              if (v := _int_or_none(raw)) is not None}
        exc = {v for raw in (scopeconf.get("exc") or {}).get("company") or []
              if (v := _int_or_none(raw)) is not None}

        if scope == "all" and not inc:
            return None   # thấy MỌI pháp nhân — không grant nào khác thu hẹp lại được nữa
        grant_reach = set(inc)
        if scope != "all" and own_company:
            grant_reach.add(own_company)
        reach |= (grant_reach - exc)
    return reach


def _ancestor_chain(folder) -> list[int]:
    """Id của TỔ TIÊN + chính nó, từ gốc xuống — đọc thẳng `path` vật hóa."""
    return [int(p) for p in (folder.path or "").strip("/").split("/") if p]


def _resolve_base_level(chain: list[int], by_id: dict[int, DocFolder]) -> int:
    """Mức nền của một thư mục: `default_access` của tổ tiên GẦN NHẤT có khai,
    đi từ gốc xuống. `PRIVATE` là lưới đỡ cuối cùng nếu dữ liệu thiếu (gốc pháp
    nhân luôn tự khai lúc `ensure_company_roots`, nên trên cây lành thực tế
    không rơi vào nhánh này)."""
    current = int(FolderAccessLevel.PRIVATE)
    for fid in chain:
        node = by_id.get(fid)
        if node is not None and node.default_access is not None:
            current = node.default_access
    return current


def _acl_rows(db: Session, profile: dict) -> tuple[dict[int, int], set[int]]:
    """`({folder_id: mức CHO cao nhất}, {folder_id bị CẤM})` khớp chủ thể của
    người gọi — MỘT truy vấn, dùng chung cho toàn cây."""
    match = subject_match_condition(DocFolderAccess, profile)
    allow_by_folder: dict[int, int] = {}
    deny_folders: set[int] = set()
    if match is None:
        return allow_by_folder, deny_folders
    rows = (db.query(DocFolderAccess.folder_id, DocFolderAccess.effect, DocFolderAccess.level)
           .filter(match, still_live_condition(DocFolderAccess)).all())
    for folder_id, effect, level in rows:
        if effect == EFFECT_DENY:
            deny_folders.add(folder_id)
        else:
            allow_by_folder[folder_id] = max(allow_by_folder.get(folder_id, -1), level)
    return allow_by_folder, deny_folders


def role_level_cap(profile: dict) -> int:
    """Mức CAO NHẤT mà VAI TRÒ cho phép dùng tới — trần của mọi mức thư mục.

    Thư mục pháp nhân mặc định «Đóng góp» cho cả pháp nhân, nên người chỉ có
    quyền ĐỌC vẫn nhận `my_level = 2` — giao diện vẽ «Quyền: Đóng góp», nút
    «+ Mới», «Thêm thư mục con»… để rồi bấm vào ăn 403 vì `require(...)` của
    từng đường ghi chặn ở vai trò (lỗi lead bắt khi test UI 24/09/2026). Trần ở
    ĐÂY để `my_level` nói đúng điều người đó làm được, và mọi chỗ ở giao diện
    đang đọc `my_level` tự đúng theo, không phải vá từng nút.

    Không có quyền GHI nào (`doc_folder.create/write`, `document.create/write`)
    → tối đa Xem. Có ít nhất một thì KHÔNG trần — mức Quản lý do ACL cấp (vd
    người tạo thư mục riêng) giữ nguyên như cũ.
    """
    union = profile.get("perms_union") or {}
    for entity in (ENTITY_FOLDER_ADMIN, ENTITY_DOCUMENT):
        perms = union.get(entity) or {}
        if perms.get("create") or perms.get("write"):
            return int(FolderAccessLevel.MANAGE)
    return int(FolderAccessLevel.VIEW)


def _folders_of_shared_documents(db: Session, profile: dict) -> set[int]:
    """Id thư mục chứa văn bản mà người này được CHO PHÉP đọc đích danh (và
    không bị cấm đích danh) — một truy vấn, không kể văn bản thấy nhờ phạm vi
    vai trò (cái đó đã có luật thư mục riêng ở trên)."""
    from app.modules.document.access_model import EFFECT_ALLOW, EFFECT_DENY
    from app.modules.document.access_service import _document_ids

    from .folder_link_model import DocumentFolderLink

    allow = _document_ids(profile, "read", EFFECT_ALLOW)
    if allow is None:
        return set()
    query = db.query(DocumentFolderLink.folder_id).filter(DocumentFolderLink.document_id.in_(allow))
    deny = _document_ids(profile, "read", EFFECT_DENY)
    if deny is not None:
        query = query.filter(DocumentFolderLink.document_id.not_in(deny))
    return {folder_id for (folder_id,) in query.distinct()}


def effective_levels(db: Session, user, profile: dict | None = None) -> dict[int, int]:
    """`{folder_id: mức hiệu lực}` — CHỈ những thư mục người này THẤY được
    (mức ≥ `VIEW`). Đây là hàm DUY NHẤT tính luật ở đầu tệp; mọi nơi khác gọi
    qua đây, không tự suy diễn lại."""
    profile = profile or get_perm_profile(db, user)
    folders = db.query(DocFolder).all()
    if not folders:
        return {}
    by_id = {f.id: f for f in folders}

    doc_reach = company_reach(profile, ENTITY_DOCUMENT, "read")
    admin_reach = company_reach(profile, ENTITY_FOLDER_ADMIN, "write")
    allow_by_folder, deny_folders = _acl_rows(db, profile)
    cap = role_level_cap(profile)

    result: dict[int, int] = {}
    for f in folders:
        chain = _ancestor_chain(f)
        is_admin = admin_reach is None or f.company_id in admin_reach

        candidates: list[int] = []
        if doc_reach is None or f.company_id in doc_reach:
            candidates.append(_resolve_base_level(chain, by_id))
        allow_max = max((allow_by_folder[a] for a in chain if a in allow_by_folder), default=None)
        if allow_max is not None:
            candidates.append(allow_max)

        level: int | None = max(candidates) if candidates else None
        if not is_admin and any(a in deny_folders for a in chain):
            level = None   # CẤM thắng — trừ quản trị (bước 4)
        if is_admin:
            level = int(FolderAccessLevel.MANAGE)   # quản trị KHÔNG bị cấm chặn

        if level is not None and level >= int(FolderAccessLevel.VIEW):
            #  Trần theo vai trò CHỈ hạ mức, không bao giờ làm mất quyền THẤY
            #  (`cap` luôn ≥ Xem) — xem `role_level_cap`.
            result[f.id] = min(level, cap)

    #  Văn bản được CHIA ĐÍCH DANH → thư mục chứa nó (+ tổ tiên) tự hiện mức
    #  XEM (đại ca chốt 25/09/2026): chia văn bản cho người ngoài phạm vi thư
    #  mục thì họ phải lần tới được nó trong cây, chỉ là không thấy văn bản
    #  khác trong đó — danh sách vẫn lọc bằng `visible_condition` như mọi khi.
    #  SUY RA mỗi lần tính, không ghi dòng quyền thư mục nào: thu hồi chia sẻ
    #  là thư mục tự biến mất. Thư mục bị CẤM đích danh vẫn giữ cấm.
    for folder_id in _folders_of_shared_documents(db, profile):
        f = by_id.get(folder_id)
        if f is None:
            continue
        chain = _ancestor_chain(f)
        if any(a in deny_folders for a in chain):
            continue
        for ancestor in chain:
            result.setdefault(ancestor, int(FolderAccessLevel.VIEW))

    #  Thư mục NHÓM «Công ty» là LỐI VÀO của thư mục pháp nhân — ai thấy ít
    #  nhất MỘT thư mục pháp nhân thì phải thấy nó, không thì thư mục của họ
    #  mồ côi (cha vô hình). Không thấy pháp nhân nào thì cũng không bày ra
    #  một thư mục rỗng. Chỉ XEM; quản trị toàn hệ thì Quản lý.
    admin_everywhere = admin_reach is None
    sees_a_company = any(
        f.kind == int(FolderKind.COMPANY) and f.id in result for f in folders)
    for f in folders:
        if f.kind != int(FolderKind.COMPANY_GROUP):
            continue
        if admin_everywhere:
            result[f.id] = int(FolderAccessLevel.MANAGE)
        elif sees_a_company:
            result[f.id] = int(FolderAccessLevel.VIEW)
        else:
            result.pop(f.id, None)
    return result


def my_level(db: Session, user, folder: DocFolder, profile: dict | None = None,
            levels: dict[int, int] | None = None) -> int:
    """`0` nếu không thấy — dùng cho trường `my_level` ở JSON chi tiết, KHÔNG
    ném lỗi (khác `ensure_level`).

    `levels` TÙY CHỌN (M1, rà soát 23/09/2026) — người gọi đã có sẵn kết quả
    `effective_levels()` (vd đang kiểm NHIỀU thư mục trong một vòng lặp) thì
    truyền vào để khỏi tính lại TOÀN BỘ (2 truy vấn: mọi thư mục + mọi dòng
    ACL) ở MỖI lượt lặp — không đổi gì với người gọi cũ (không truyền, hành
    vi y hệt trước)."""
    if levels is None:
        profile = profile or get_perm_profile(db, user)
        levels = effective_levels(db, user, profile)
    return levels.get(folder.id, 0)


def ensure_level(db: Session, user, folder: DocFolder, min_level: int,
                 profile: dict | None = None, levels: dict[int, int] | None = None) -> int:
    """Như `my_level` nhưng ném lỗi khi thiếu.

    **Không thấy → 404, không phải 403** — cùng luật với
    `document/access_service.ensure_can`: 403 đã xác nhận "có thư mục này,
    anh không được xem", chỉ riêng việc đó đã lộ thông tin. Thấy rồi nhưng
    thiếu mức thì 403, nói rõ mức đang có và mức cần.

    `levels` TÙY CHỌN — xem `my_level`.
    """
    from fastapi import HTTPException

    if levels is None:
        profile = profile or get_perm_profile(db, user)
        levels = effective_levels(db, user, profile)
    level = levels.get(folder.id)
    if level is None:
        raise HTTPException(404, "Không tìm thấy thư mục")
    if level < min_level:
        raise HTTPException(
            403,
            f"Cần quyền {FOLDER_ACCESS_LEVEL_LABELS.get(min_level, '')} trở lên trên thư "
            f"mục này — bạn đang ở mức {FOLDER_ACCESS_LEVEL_LABELS.get(level, '')}")
    return level
