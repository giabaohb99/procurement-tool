"""bao-CR-316 — tách *Ngày tiếp nhận* ra cột riêng `received_date`.

Trước CR này chỉ có MỘT cột `request_date`: lúc lập phiếu nó là ngày lập, tới lúc điều phối
`dispatch_pr` ghi đè nó thành ngày tiếp nhận (bao-CR-293). Một cột mang hai nghĩa nên ngày lập
phiếu mất hẳn, và ô lọc "Ngày lập" trên danh sách trả về lẫn lộn hai loại ngày.

Bộ test này canh ba thứ:
  1. `sla_base_date` — MỐC ĐẾM hạn: ưu tiên `received_date`, chưa có thì lùi về `request_date`;
  2. `dispatch_pr` KHÔNG được đụng vào `request_date` nữa;
  3. hạn (`regulated_date` / cờ Đơn gấp) đếm theo mốc mới chứ không theo ngày lập.
"""
from datetime import date, timedelta

from app.modules.catalog import lead_time
from app.modules.purchase_request import service as S
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem


def _days_ago(days: int) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


def _make_pr(db, seed, code: str, request_date: str, lines: list[dict] | None = None):
    pr = PurchaseRequest(code=code, company_id=seed.company_id, requester="Người YC",
                         requester_id=seed.emp_req_id, department="Phòng Test",
                         status="approved", request_date=request_date,
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    for i, ln in enumerate(lines or []):
        db.add(PurchaseRequestItem(pr_id=pr.id, product_code=f"SP-316-{i:02d}",
                                   product_name=f"Hàng {i}", item_group=ln.get("group", "Nhãn"),
                                   qty=5, unit="cái", price=1000,
                                   required_date=ln.get("required") or "",
                                   expected_date=ln.get("expected") or "",
                                   created_by=seed.u_req_id, updated_by=seed.u_req_id))
    db.commit()
    db.refresh(pr)
    return pr


# --- sla_base_date: bốn tổ hợp của hai cột ---------------------------------------------------

def test_moc_dem_uu_tien_ngay_tiep_nhan():
    """Có cả hai ngày → lấy Ngày tiếp nhận, vì thu mua đã thật sự nhận việc."""
    class _PR:
        request_date = "2026-08-01"
        received_date = "2026-08-20"
    assert S.sla_base_date(_PR()) == "2026-08-20"


def test_moc_dem_lui_ve_ngay_lap_khi_chua_tiep_nhan():
    """Chưa điều phối → tạm đếm từ ngày lập, để cảnh báo trễ hạn có hiệu lực ngay lúc lập."""
    class _PR:
        request_date = "2026-08-01"
        received_date = ""
    assert S.sla_base_date(_PR()) == "2026-08-01"


def test_moc_dem_rong_khi_ca_hai_cot_deu_trong():
    """Phiếu legacy trống cả hai → không có mốc, KHÔNG được suy ra hôm nay."""
    class _PR:
        request_date = ""
        received_date = ""
    assert S.sla_base_date(_PR()) == ""


def test_moc_dem_chiu_duoc_none_va_khoang_trang():
    """Cột kiểu chuỗi nhưng dữ liệu cũ có thể là NULL hoặc toàn khoảng trắng."""
    class _PR:
        request_date = "  2026-08-01  "
        received_date = None
    assert S.sla_base_date(_PR()) == "2026-08-01"
    assert S.sla_base_date(None) == ""


def test_moc_dem_bo_qua_ngay_tiep_nhan_toan_khoang_trang():
    """`received_date` chỉ có khoảng trắng vẫn là CHƯA tiếp nhận, không được lấy làm mốc."""
    class _PR:
        request_date = "2026-08-01"
        received_date = "   "
    assert S.sla_base_date(_PR()) == "2026-08-01"


# --- dispatch_pr: hai cột đứng riêng ---------------------------------------------------------

def test_dieu_phoi_khong_dung_vao_ngay_lap(db, seed):
    """Điều phối chỉ ghi `received_date`; `request_date` giữ nguyên ngày lập phiếu."""
    lap = _days_ago(12)
    pr = _make_pr(db, seed, "PYC-316-01", lap, [{"group": "Nhãn"}])
    pr2, _, _ = S.dispatch_pr(db, pr.id, seed.u_req_id)
    assert pr2.request_date == lap
    assert pr2.received_date == date.today().isoformat()
    assert S.sla_base_date(pr2) == date.today().isoformat()


def test_phieu_moi_chua_tiep_nhan_thi_ngay_tiep_nhan_rong(db, seed):
    """Phiếu vừa lập: cột Ngày tiếp nhận phải RỖNG, không tự điền ngày lập vào."""
    pr = _make_pr(db, seed, "PYC-316-02", _days_ago(1))
    assert pr.received_date == ""


def test_han_dem_tu_ngay_tiep_nhan_chu_khong_tu_ngay_lap(db, seed):
    """Sau điều phối, ngày QĐ có hàng phải dời theo mốc mới — đó là mục đích của CR-293."""
    std = lead_time.std_days_map(db)
    lap = _days_ago(20)
    pr = _make_pr(db, seed, "PYC-316-03", lap, [{"group": "Nhãn"}])
    pr2, _, _ = S.dispatch_pr(db, pr.id, seed.u_req_id)
    theo_moc_moi = lead_time.regulated_date(std, "Nhãn", date.today().isoformat())
    assert lead_time.regulated_date(std, "Nhãn", S.sla_base_date(pr2)) == theo_moc_moi
    assert theo_moc_moi != lead_time.regulated_date(std, "Nhãn", lap)


def test_don_gap_soat_lai_theo_moc_moi(db, seed):
    """Dòng cần hàng sớm hơn ngày QĐ tính theo MỐC MỚI → điều phối phải bật cờ Đơn gấp.

    Ngày cần hàng đặt ngay ngày mai: mốc cũ (20 ngày trước) thì đã quá hạn nên không ai để ý,
    nhưng đếm lại từ hôm nay thì chắc chắn sớm hơn ngày QĐ."""
    pr = _make_pr(db, seed, "PYC-316-04", _days_ago(20),
                  [{"group": "Nhãn", "required": (date.today() + timedelta(days=1)).isoformat()}])
    assert pr.is_urgent is False
    pr2, _, _ = S.dispatch_pr(db, pr.id, seed.u_req_id)
    assert pr2.is_urgent is True


def test_urgent_reasons_khong_moc_thi_khong_bao_gap(db, seed):
    """Không có mốc nào (cả hai cột trống) → không suy ra ngày QĐ, không báo gấp bừa."""
    std = lead_time.std_days_map(db)
    pr = _make_pr(db, seed, "PYC-316-05", "",
                  [{"group": "Nhãn", "required": (date.today() + timedelta(days=1)).isoformat()}])
    assert S.urgent_reasons(std, S.sla_base_date(pr), S.items_of(db, pr.id)) == []
