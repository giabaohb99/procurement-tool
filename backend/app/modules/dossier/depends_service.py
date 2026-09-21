"""HỒ SƠ TIÊN QUYẾT — `tab_dossier.depends` (đại ca chốt 21/09/2026).

*«Tờ giấy này chỉ làm được sau khi mấy tờ kia xong.»* Khai **một lần cho cả
kho**, ở chính tờ hồ sơ trong phân hệ Hồ sơ — không khai lại trong từng tờ
phiếu: trình tự giấy tờ của công ty là một, đơn mua hàng chỉ phát hành sau khi
hợp đồng ký xong, ở mọi thương vụ.

⚠️ **Ràng buộc dùng chung, TRẠNG THÁI thì riêng.** «Xong» vẫn tính theo từng
phiếu (`tab_dossier_progress`), nên câu hỏi *«tờ này có đang khóa không»* vẫn là
câu hỏi của riêng từng phiếu. Hai thứ đừng gộp: gộp về tờ giấy thì khóa/mở lây
sang mọi phiếu; gộp về phiếu thì mỗi tờ phiếu phải khai lại cả chuỗi. Chỗ tính
khóa nằm ở `applicability_controller._with_lock`.

⚠️ Vòng tiên quyết (A chờ B, B chờ A) làm cả cụm khóa vĩnh viễn mà không ai
hiểu vì sao — chặn lúc LƯU, đừng để nó thành dữ liệu. Ở đây vòng còn **nguy hơn
bản theo-phiếu**: một vòng khai nhầm trong kho làm hỏng MỌI phiếu dùng tới hai
tờ đó, chứ không riêng tờ phiếu đang mở.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .constants import MAX_DOSSIER_DEPENDS
from .model import Dossier


def check_depends(db: Session, dossier_id: int, depends: list[int]) -> list[int]:
    """Kiểm danh sách tiên quyết: có thật, không tự trỏ mình, không tạo VÒNG.

    `dossier_id` bằng `0` khi đang TẠO MỚI — chưa có id thì chưa thể nằm trong
    vòng nào, chỉ cần kiểm mấy tờ được trỏ tới là có thật.

    ⚠️ Vòng dò có TRẦN ĐỘ SÂU, và **chạm trần là CHẶN** chứ không trả về im
    lặng: «dò không thấy» không phải «không có» (bài học `block_manager_cycle`).
    """
    depends = list(dict.fromkeys(int(i) for i in depends))   # khử trùng, giữ thứ tự
    if not depends:
        return []
    if len(depends) > MAX_DOSSIER_DEPENDS:
        raise HTTPException(400, f"Tối đa {MAX_DOSSIER_DEPENDS} hồ sơ tiên quyết")
    if dossier_id and dossier_id in depends:
        raise HTTPException(400, "Hồ sơ không thể là tiên quyết của chính nó")

    #  ⚠️ Đọc CẢ KHO chứ không chỉ mấy tờ được trỏ tới: dò vòng phải đi hết
    #  chuỗi, mà bước thứ hai trở đi là những tờ không có trong `depends`.
    #  Kho hồ sơ cỡ trăm dòng — một truy vấn, không phải chỗ cần tối ưu.
    rows = db.query(Dossier.id, Dossier.depends).all()
    graph = {rid: list(deps or []) for rid, deps in rows}

    thieu = [i for i in depends if i not in graph]
    if thieu:
        raise HTTPException(400, "Hồ sơ tiên quyết không tồn tại")

    if not dossier_id:
        return depends

    graph[dossier_id] = depends                  # đồ thị SAU khi lưu
    seen: set[int] = set()
    stack = list(depends)
    steps = 0
    while stack:
        steps += 1
        if steps > MAX_DOSSIER_DEPENDS * (len(graph) + 1):
            raise HTTPException(400, "Chuỗi tiên quyết quá sâu — rà lại các hồ sơ tiên quyết")
        cur = stack.pop()
        if cur == dossier_id:
            raise HTTPException(400, "Chuỗi tiên quyết tạo thành vòng lặp — hồ sơ sẽ "
                                     "khóa lẫn nhau vĩnh viễn")
        if cur in seen:
            continue
        seen.add(cur)
        stack.extend(graph.get(cur, []))
    return depends


def depends_names(db: Session, depends: list[int]) -> list[dict]:
    """`[{id, code, name}]` của các tờ tiên quyết — để bày, khỏi tra ngược ở giao diện.

    ⚠️ Tờ đã bị XÓA thì bỏ khỏi kết quả, không trả `{id, name: ""}`: màn hình sẽ
    ra một dòng trống không bấm được, và người dùng đi tìm xem mình khai nhầm gì.
    Id chết vẫn nằm dưới cột JSON (xóa hồ sơ không đi dọn cột của tờ khác), nên
    chỗ ĐỌC phải tự lọc.
    """
    if not depends:
        return []
    rows = (
        db.query(Dossier.id, Dossier.code, Dossier.name)
        .filter(Dossier.id.in_(depends))
        .all()
    )
    theo_id = {rid: {"id": rid, "code": code, "name": name} for rid, code, name in rows}
    #  Giữ ĐÚNG thứ tự người dùng khai, không theo thứ tự DB trả về.
    return [theo_id[i] for i in depends if i in theo_id]
