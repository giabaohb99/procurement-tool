"""HỒ SƠ TIÊN QUYẾT — `tab_dossier.depends` (đại ca chốt 21/09/2026).

*«Tờ giấy này chỉ làm được sau khi mấy tờ kia xong.»* Ràng buộc khai **một lần
cho cả kho**, ở chính tờ hồ sơ — không khai lại trong từng tờ phiếu.

⚠️ Vòng tiên quyết ở đây NGUY HƠN bản theo-phiếu từng làm trước đó: một vòng
khai nhầm trong kho làm hỏng MỌI phiếu dùng tới hai tờ đó, chứ không riêng tờ
phiếu đang mở. Nên bộ kiểm này soi kỹ phần dò vòng.

Chặn lúc LƯU, đừng để nó thành dữ liệu: vòng đã nằm dưới DB rồi thì người dùng
chỉ thấy mấy tờ giấy không bao giờ tick được, và không có gì trên màn hình chỉ
ra nguyên nhân.
"""
import pytest
from fastapi import HTTPException

from app.modules.dossier.constants import MAX_DOSSIER_DEPENDS
from app.modules.dossier.depends_service import check_depends, depends_names
from app.modules.dossier.model import Dossier


def _ho_so(db, name: str, depends=None) -> Dossier:
    row = Dossier(
        code=f"HS{name[:6]}",
        name=name,
        dossier_type_id=1,
        dossier_type_name="Pháp lý",
        depends=depends or [],
    )
    db.add(row)
    db.flush()
    return row


# ── Chốt cơ bản ─────────────────────────────────────────────────────────────
def test_rong_thi_tra_rong_khong_cham_db(db):
    """Xóa hết tiên quyết luôn hợp lệ — không được vướng chốt nào."""
    assert check_depends(db, 1, []) == []


def test_khong_tu_tro_chinh_minh(db):
    a = _ho_so(db, "A")
    with pytest.raises(HTTPException) as e:
        check_depends(db, a.id, [a.id])
    assert "chính nó" in e.value.detail


def test_tro_toi_ho_so_khong_ton_tai_thi_chan(db):
    _ho_so(db, "A")
    with pytest.raises(HTTPException) as e:
        check_depends(db, 1, [999999])
    assert "không tồn tại" in e.value.detail


def test_khu_trung_va_giu_thu_tu(db):
    a, b, c = _ho_so(db, "A"), _ho_so(db, "B"), _ho_so(db, "C")
    assert check_depends(db, c.id, [b.id, a.id, b.id]) == [b.id, a.id]


def test_vuot_tran_so_luong_thi_chan(db):
    rows = [_ho_so(db, f"T{i}") for i in range(MAX_DOSSIER_DEPENDS + 1)]
    goc = _ho_so(db, "GOC")
    with pytest.raises(HTTPException) as e:
        check_depends(db, goc.id, [r.id for r in rows])
    assert "Tối đa" in e.value.detail


# ── Dò vòng ─────────────────────────────────────────────────────────────────
def test_chan_vong_hai_buoc(db):
    """A chờ B, rồi B chờ A."""
    a = _ho_so(db, "A")
    b = _ho_so(db, "B", depends=[a.id])
    with pytest.raises(HTTPException) as e:
        check_depends(db, a.id, [b.id])
    assert "vòng lặp" in e.value.detail


def test_chan_vong_dai_ba_buoc(db):
    """A→B→C→A. Chỉ soi một bước thì lọt, và cái lọt là vòng khóa vĩnh viễn."""
    a = _ho_so(db, "A")
    c = _ho_so(db, "C", depends=[a.id])
    b = _ho_so(db, "B", depends=[c.id])
    with pytest.raises(HTTPException) as e:
        check_depends(db, a.id, [b.id])
    assert "vòng lặp" in e.value.detail


def test_chuoi_thang_khong_phai_vong(db):
    """A→B→C là hợp lệ. Chặn nhầm nó thì không khai nổi một quy trình bình thường."""
    c = _ho_so(db, "C")
    b = _ho_so(db, "B", depends=[c.id])
    a = _ho_so(db, "A")
    assert check_depends(db, a.id, [b.id]) == [b.id]


def test_hai_nhanh_gap_nhau_khong_phai_vong(db):
    """A chờ B và C, cả hai cùng chờ D. Đồ thị hình kim cương, KHÔNG có vòng.

    Dò mà không nhớ đỉnh đã qua (`seen`) thì nhánh chung bị đi lại nhiều lần và
    chạm trần độ sâu → chặn NHẦM một khai báo hoàn toàn hợp lệ.
    """
    d = _ho_so(db, "D")
    b = _ho_so(db, "B", depends=[d.id])
    c = _ho_so(db, "C", depends=[d.id])
    a = _ho_so(db, "A")
    assert check_depends(db, a.id, [b.id, c.id]) == [b.id, c.id]


def test_tao_moi_chua_co_id_thi_chi_kiem_ton_tai(db):
    """`dossier_id = 0` = đang TẠO. Chưa tồn tại thì chưa thể nằm trong vòng nào."""
    b = _ho_so(db, "B")
    assert check_depends(db, 0, [b.id]) == [b.id]


def test_vong_tu_tro_cua_to_khac_khong_lam_treo(db):
    """Dữ liệu cũ có thể mang một vòng đã lọt từ trước.

    Dò phải DỪNG được, không lặp vô hạn — `seen` là thứ giữ cho nó dừng.
    """
    b = _ho_so(db, "B")
    b.depends = [b.id]          # vòng tự trỏ, ghi thẳng DB không qua chốt
    db.flush()
    a = _ho_so(db, "A")
    assert check_depends(db, a.id, [b.id]) == [b.id]


# ── Bày ra ──────────────────────────────────────────────────────────────────
def test_depends_names_giu_dung_thu_tu_nguoi_dung_khai(db):
    a, b, c = _ho_so(db, "A"), _ho_so(db, "B"), _ho_so(db, "C")
    out = depends_names(db, [c.id, a.id, b.id])
    assert [x["name"] for x in out] == ["C", "A", "B"]


def test_depends_names_bo_id_chet(db):
    """Xóa một hồ sơ KHÔNG đi dọn cột `depends` của tờ khác, nên id chết còn lại.

    Trả `{id, name: ""}` thì màn hình ra một dòng trống không bấm được, và người
    dùng đi tìm xem mình khai nhầm gì.
    """
    a = _ho_so(db, "A")
    assert depends_names(db, [a.id, 999999]) == [
        {"id": a.id, "code": a.code, "name": "A"}
    ]


def test_depends_names_rong_thi_khong_cham_db(db):
    assert depends_names(db, []) == []
